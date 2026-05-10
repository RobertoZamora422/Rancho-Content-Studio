from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.events import ContentEvent
from app.models.media import OriginalMedia
from app.schemas.importing import MetadataProcessResponse
from app.services.config_service import get_config_value
from app.services.event_service import require_event
from app.services.import_service import get_event_path
from app.services.job_service import add_job_log, finish_job, start_job, update_job_progress
from app.services.thumbnail_service import generate_thumbnail
from app.utils.media_files import file_modified_datetime
from app.utils.tool_validation import resolve_tool_path

EXIF_DATE_CANDIDATES = (
    ("DateTimeOriginal", "exiftool:DateTimeOriginal"),
    ("CreateDate", "exiftool:CreateDate"),
    ("MediaCreateDate", "exiftool:MediaCreateDate"),
    ("TrackCreateDate", "exiftool:TrackCreateDate"),
)


@dataclass(frozen=True)
class MetadataResult:
    capture_datetime: datetime
    date_source: str
    width: int | None
    height: int | None
    duration_seconds: float | None
    metadata_json: str
    warnings: list[str]


def process_event_metadata_and_thumbnails(
    db: Session,
    event_id: int,
) -> MetadataProcessResponse:
    event = require_event(db, event_id)
    event_path = get_event_path(event)
    media_items = list_event_media(db, event.id)
    exiftool_command, exiftool_error = resolve_tool_path(
        get_config_value(db, "tools.exiftool_path"),
        "exiftool",
    )
    configured_ffmpeg_path = get_config_value(db, "tools.ffmpeg_path")

    metadata_job = start_job(db, "write_metadata", event.id)
    if exiftool_error:
        add_job_log(
            db,
            metadata_job,
            "warning",
            f"ExifTool no disponible; se usaran metadatos locales. {exiftool_error}",
        )

    metadata_updated = 0
    metadata_failed = 0
    for media in media_items:
        try:
            source_path = require_existing_media_path(media)
            result = extract_metadata(media, source_path, event, exiftool_command)
            media.capture_datetime = result.capture_datetime
            media.date_source = result.date_source
            media.width = result.width
            media.height = result.height
            media.duration_seconds = result.duration_seconds
            media.metadata_json = result.metadata_json
            media.original_exists = True
            metadata_updated += 1
            for warning in result.warnings:
                add_job_log(
                    db,
                    metadata_job,
                    "warning",
                    warning,
                    file_path=str(source_path),
                    original_media_id=media.id,
                )
        except Exception as error:  # noqa: BLE001 - per-file errors must not stop the job.
            metadata_failed += 1
            media.original_exists = Path(media.original_path).is_file()
            add_job_log(
                db,
                metadata_job,
                "error",
                str(error),
                file_path=media.original_path,
                original_media_id=media.id,
            )
        update_job_progress(metadata_job, len(media_items), metadata_updated, metadata_failed)
        db.flush()

    finish_job(
        metadata_job,
        "completed" if metadata_failed == 0 else "completed_with_errors",
        total_items=len(media_items),
        processed_items=metadata_updated,
        failed_items=metadata_failed,
    )

    thumbnail_job = start_job(db, "generate_thumbnails", event.id)
    thumbnails_generated = 0
    thumbnail_failed = 0
    for media in media_items:
        try:
            source_path = require_existing_media_path(media)
            output_path = thumbnail_output_path(event_path, media)
            result = generate_thumbnail(
                source_path,
                output_path,
                media.media_type,
                configured_ffmpeg_path,
            )
            media.thumbnail_path = str(result.thumbnail_path.relative_to(event_path))
            thumbnails_generated += 1
            if result.warning:
                add_job_log(
                    db,
                    thumbnail_job,
                    "warning",
                    result.warning,
                    file_path=str(source_path),
                    original_media_id=media.id,
                )
            add_job_log(
                db,
                thumbnail_job,
                "info",
                f"Miniatura generada con {result.generated_from}.",
                file_path=str(source_path),
                original_media_id=media.id,
            )
        except Exception as error:  # noqa: BLE001 - per-file errors must not stop the job.
            thumbnail_failed += 1
            add_job_log(
                db,
                thumbnail_job,
                "error",
                str(error),
                file_path=media.original_path,
                original_media_id=media.id,
            )
        update_job_progress(
            thumbnail_job,
            len(media_items),
            thumbnails_generated,
            thumbnail_failed,
        )
        db.flush()

    finish_job(
        thumbnail_job,
        "completed" if thumbnail_failed == 0 else "completed_with_errors",
        total_items=len(media_items),
        processed_items=thumbnails_generated,
        failed_items=thumbnail_failed,
    )
    db.commit()

    return MetadataProcessResponse(
        metadata_job_id=metadata_job.id,
        thumbnail_job_id=thumbnail_job.id,
        total_files=len(media_items),
        metadata_updated=metadata_updated,
        metadata_failed=metadata_failed,
        thumbnails_generated=thumbnails_generated,
        thumbnail_failed=thumbnail_failed,
    )


def list_event_media(db: Session, event_id: int) -> list[OriginalMedia]:
    return list(
        db.scalars(
            select(OriginalMedia)
            .where(OriginalMedia.event_id == event_id)
            .order_by(OriginalMedia.imported_at.asc(), OriginalMedia.id.asc())
        ).all()
    )


def extract_metadata(
    media: OriginalMedia,
    source_path: Path,
    event: ContentEvent,
    exiftool_command: str | None,
) -> MetadataResult:
    warnings: list[str] = []
    exiftool_metadata: dict[str, Any] = {}
    if exiftool_command:
        exiftool_metadata, exiftool_warning = read_exiftool_metadata(exiftool_command, source_path)
        if exiftool_warning:
            warnings.append(exiftool_warning)

    local_metadata, local_warnings = read_local_metadata(source_path, media.media_type)
    warnings.extend(local_warnings)

    capture_datetime, date_source, date_warning = determine_capture_datetime(
        exiftool_metadata,
        source_path,
        event.event_date,
    )
    if date_warning:
        warnings.append(date_warning)

    width = first_int(
        exiftool_metadata.get("ImageWidth"),
        exiftool_metadata.get("ExifImageWidth"),
        local_metadata.get("width"),
        media.width,
    )
    height = first_int(
        exiftool_metadata.get("ImageHeight"),
        exiftool_metadata.get("ExifImageHeight"),
        local_metadata.get("height"),
        media.height,
    )
    duration_seconds = first_float(
        exiftool_metadata.get("Duration"),
        local_metadata.get("duration_seconds"),
        media.duration_seconds,
    )

    metadata_payload = {
        "extractor": "exiftool" if exiftool_metadata else "local_basic",
        "exiftool_fields": exiftool_metadata,
        "local_fields": local_metadata,
        "warnings": warnings,
    }
    return MetadataResult(
        capture_datetime=capture_datetime,
        date_source=date_source,
        width=width,
        height=height,
        duration_seconds=duration_seconds,
        metadata_json=json.dumps(metadata_payload, ensure_ascii=True, default=str),
        warnings=warnings,
    )


def read_exiftool_metadata(command: str, source_path: Path) -> tuple[dict[str, Any], str | None]:
    try:
        completed = subprocess.run(
            [
                command,
                "-j",
                "-n",
                "-DateTimeOriginal",
                "-CreateDate",
                "-MediaCreateDate",
                "-TrackCreateDate",
                "-ImageWidth",
                "-ImageHeight",
                "-ExifImageWidth",
                "-ExifImageHeight",
                "-Duration",
                "-Orientation",
                "-Rotation",
                "-Make",
                "-Model",
                str(source_path),
            ],
            capture_output=True,
            check=False,
            text=True,
            timeout=15,
        )
    except OSError as error:
        return {}, f"No se pudo ejecutar ExifTool: {error}"
    except subprocess.TimeoutExpired:
        return {}, "ExifTool excedio el tiempo de espera."

    if completed.returncode != 0:
        output = (completed.stderr or completed.stdout).strip()
        return {}, output or f"ExifTool finalizo con codigo {completed.returncode}."

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        return {}, f"ExifTool devolvio JSON invalido: {error}"

    if not payload:
        return {}, "ExifTool no devolvio metadatos para el archivo."
    first_item = payload[0]
    if not isinstance(first_item, dict):
        return {}, "ExifTool devolvio un formato inesperado."
    first_item.pop("SourceFile", None)
    return first_item, None


def read_local_metadata(source_path: Path, media_type: str) -> tuple[dict[str, Any], list[str]]:
    metadata: dict[str, Any] = {
        "file_modified_time": file_modified_datetime(source_path).isoformat(),
        "file_size_bytes": source_path.stat().st_size,
    }
    warnings: list[str] = []

    if media_type == "image":
        try:
            with Image.open(source_path) as image:
                metadata["width"] = image.width
                metadata["height"] = image.height
                metadata["image_format"] = image.format
        except (OSError, UnidentifiedImageError) as error:
            warnings.append(f"No se pudieron leer dimensiones locales de imagen: {error}")

    return metadata, warnings


def determine_capture_datetime(
    exiftool_metadata: dict[str, Any],
    source_path: Path,
    event_date: date | None,
) -> tuple[datetime, str, str | None]:
    candidate_warning: str | None = None
    for key, source_name in EXIF_DATE_CANDIDATES:
        value = exiftool_metadata.get(key)
        parsed = parse_exif_datetime(value)
        if parsed is not None:
            candidate_warning = warn_if_future(parsed, source_name)
            if candidate_warning is None:
                return parsed, source_name, None
            continue

    try:
        return file_modified_datetime(source_path), "file_modified_time", candidate_warning
    except OSError as error:
        if event_date is not None:
            return (
                datetime.combine(event_date, time.min, tzinfo=timezone.utc),
                "event_date",
                f"No se pudo leer fecha de archivo; se uso fecha del evento: {error}",
            )
        raise ValueError("No se pudo determinar fecha de captura.") from error


def parse_exif_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None

    match = re.search(
        r"(?P<year>\d{4})[:\-](?P<month>\d{2})[:\-](?P<day>\d{2})"
        r"[ T](?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})"
        r"(?P<tz>Z|[+-]\d{2}:?\d{2})?",
        text,
    )
    if not match:
        return None

    year = int(match.group("year"))
    if year <= 1900:
        return None

    tz = match.group("tz")
    iso_tz = ""
    if tz == "Z":
        iso_tz = "+00:00"
    elif tz:
        iso_tz = tz if ":" in tz else f"{tz[:3]}:{tz[3:]}"
    parsed = datetime.fromisoformat(
        "{year}-{month}-{day}T{hour}:{minute}:{second}{tz}".format(
            year=match.group("year"),
            month=match.group("month"),
            day=match.group("day"),
            hour=match.group("hour"),
            minute=match.group("minute"),
            second=match.group("second"),
            tz=iso_tz,
        )
    )
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def warn_if_future(value: datetime, source_name: str) -> str | None:
    now = datetime.now(timezone.utc)
    comparable = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if comparable > now + timedelta(days=2):
        return f"Fecha {source_name} parece futura; se uso fallback local."
    return None


def first_int(*values: Any) -> int | None:
    for value in values:
        if value is None:
            continue
        try:
            return int(float(str(value).split()[0]))
        except (TypeError, ValueError):
            continue
    return None


def first_float(*values: Any) -> float | None:
    for value in values:
        if value is None:
            continue
        try:
            return float(str(value).split()[0])
        except (TypeError, ValueError):
            continue
    return None


def thumbnail_output_path(event_path: Path, media: OriginalMedia) -> Path:
    return event_path / "metadata" / "thumbnails" / f"original_{media.id}.jpg"


def require_existing_media_path(media: OriginalMedia) -> Path:
    path = Path(media.original_path)
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo original importado: {media.original_path}")
    return path


def get_thumbnail_path(db: Session, media_id: int) -> Path:
    media = db.get(OriginalMedia, media_id)
    if media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medio no encontrado.")
    if not media.thumbnail_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El medio no tiene miniatura generada.",
        )

    event_path = get_event_path(media.event)
    thumbnail_path = Path(media.thumbnail_path)
    if not thumbnail_path.is_absolute():
        thumbnail_path = event_path / thumbnail_path

    resolved_event_path = event_path.resolve()
    resolved_thumbnail_path = thumbnail_path.resolve()
    try:
        resolved_thumbnail_path.relative_to(resolved_event_path)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La miniatura esta fuera de la carpeta del evento.",
        ) from error

    if not resolved_thumbnail_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe el archivo de miniatura.",
        )
    return resolved_thumbnail_path
