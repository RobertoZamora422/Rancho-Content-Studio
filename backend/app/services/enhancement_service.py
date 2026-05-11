from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.identity import VisualStylePreset
from app.models.jobs import DecisionLog
from app.models.media import CuratedMedia, EnhancedMedia, OriginalMedia
from app.schemas.importing import (
    EnhancedMediaListResponse,
    EnhancedMediaResponse,
    EnhancedMediaUpdate,
    PhotoEnhancementRequest,
    PhotoEnhancementResponse,
)
from app.services.config_service import get_config_value
from app.services.event_service import require_event
from app.services.import_service import get_event_path, to_original_media_response
from app.services.job_service import add_job_log, finish_job, start_job, update_job_progress
from app.services.metadata_service import require_existing_media_path
from app.utils.event_folders import safe_windows_name
from app.utils.media_files import file_modified_datetime
from app.utils.tool_validation import resolve_tool_path

SELECTED_STATUSES = {"selected", "user_selected"}
VALID_ENHANCED_STATUSES = {"approved", "rejected"}
DEFAULT_PRESET_SLUG = "natural_premium"


@dataclass(frozen=True)
class PresetSettings:
    slug: str
    brightness: float
    contrast: float
    color: float
    sharpness: float
    autocontrast_cutoff: int = 1
    unsharp_percent: int = 110


PRESET_SETTINGS: dict[str, PresetSettings] = {
    "natural_premium": PresetSettings("natural_premium", 1.03, 1.08, 1.04, 1.08),
    "calido_elegante": PresetSettings("calido_elegante", 1.04, 1.10, 1.08, 1.06),
    "color_vivo_fiesta": PresetSettings("color_vivo_fiesta", 1.05, 1.15, 1.18, 1.10),
    "suave_bodas": PresetSettings("suave_bodas", 1.07, 0.98, 1.03, 1.04, autocontrast_cutoff=0),
    "brillante_xv": PresetSettings("brillante_xv", 1.10, 1.08, 1.12, 1.08),
    "sobrio_corporativo": PresetSettings("sobrio_corporativo", 1.02, 1.06, 0.96, 1.05),
}


def enhance_event_photos(
    db: Session,
    event_id: int,
    payload: PhotoEnhancementRequest,
) -> PhotoEnhancementResponse:
    event = require_event(db, event_id)
    event_path = get_event_path(event)
    output_dir = event_path / "04_Mejorados"
    output_dir.mkdir(exist_ok=True)

    preset = resolve_preset(db, payload.preset_slug)
    curated_items = list_selected_curated_media(db, event.id)
    exiftool_command, exiftool_error = resolve_tool_path(
        get_config_value(db, "tools.exiftool_path"),
        "exiftool",
    )

    job = start_job(db, "enhance_photos", event.id)
    if exiftool_error:
        add_job_log(
            db,
            job,
            "warning",
            f"ExifTool no disponible; se conservara EXIF existente y se ajustara fecha de archivo. {exiftool_error}",
        )

    enhanced_count = 0
    skipped = 0
    failed = 0

    for curated in curated_items:
        media = curated.original_media
        try:
            if media.media_type != "image":
                skipped += 1
                add_job_log(
                    db,
                    job,
                    "info",
                    "Medio omitido: Fase 10 solo mejora fotos.",
                    file_path=media.original_path,
                    original_media_id=media.id,
                )
                continue

            source_path = require_existing_media_path(media)
            output_path = next_enhanced_output_path(output_dir, source_path, preset.slug)
            result = create_enhanced_photo(source_path, output_path, preset)
            capture_datetime = media.capture_datetime or file_modified_datetime(source_path)
            metadata_status = apply_output_date_metadata(
                output_path,
                capture_datetime,
                exiftool_command,
            )

            enhanced = EnhancedMedia(
                event_id=event.id,
                original_media_id=media.id,
                curated_media_id=curated.id,
                output_path=str(output_path.relative_to(event_path)),
                enhancement_type="photo_basic",
                preset_slug=preset.slug,
                status="completed",
                width=result.width,
                height=result.height,
                notes=json.dumps(
                    {
                        "preset": preset.slug,
                        "metadata_status": metadata_status,
                        "source_capture_datetime": capture_datetime.isoformat(),
                        "source_date_source": media.date_source,
                    },
                    ensure_ascii=True,
                    default=str,
                ),
            )
            db.add(enhanced)
            db.flush()
            db.add(
                DecisionLog(
                    event_id=event.id,
                    original_media_id=media.id,
                    entity_type="enhanced_media",
                    entity_id=enhanced.id,
                    decision_type="enhancement_generated",
                    reason=f"Version mejorada creada con preset {preset.slug}.",
                    actor="system",
                )
            )
            enhanced_count += 1
            add_job_log(
                db,
                job,
                "info",
                f"Version mejorada creada en 04_Mejorados con preset {preset.slug}.",
                file_path=str(output_path),
                original_media_id=media.id,
            )
        except Exception as error:  # noqa: BLE001 - per-file errors must not stop the job.
            failed += 1
            add_job_log(
                db,
                job,
                "error",
                str(error),
                file_path=media.original_path,
                original_media_id=media.id,
            )

        update_job_progress(job, len(curated_items), enhanced_count + skipped, failed)
        db.flush()

    finish_job(
        job,
        "completed" if failed == 0 else "completed_with_errors",
        total_items=len(curated_items),
        processed_items=enhanced_count + skipped,
        failed_items=failed,
    )
    db.commit()

    return PhotoEnhancementResponse(
        job_id=job.id,
        total_selected=len(curated_items),
        enhanced=enhanced_count,
        skipped=skipped,
        failed=failed,
        preset_slug=preset.slug,
    )


def list_enhanced_media(db: Session, event_id: int) -> EnhancedMediaListResponse:
    require_event(db, event_id)
    items = db.scalars(
        select(EnhancedMedia)
        .where(EnhancedMedia.event_id == event_id)
        .options(
            selectinload(EnhancedMedia.original_media).selectinload(OriginalMedia.analysis),
        )
        .order_by(EnhancedMedia.created_at.desc(), EnhancedMedia.id.desc())
    ).all()
    return EnhancedMediaListResponse(items=[to_enhanced_media_response(item) for item in items])


def update_enhanced_media_status(
    db: Session,
    event_id: int,
    enhanced_id: int,
    payload: EnhancedMediaUpdate,
) -> EnhancedMediaResponse:
    require_event(db, event_id)
    status_value = payload.status.strip()
    if status_value not in VALID_ENHANCED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado de version mejorada no permitido.",
        )

    enhanced = db.scalar(
        select(EnhancedMedia)
        .where(EnhancedMedia.id == enhanced_id, EnhancedMedia.event_id == event_id)
        .options(selectinload(EnhancedMedia.original_media).selectinload(OriginalMedia.analysis))
    )
    if enhanced is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version mejorada no encontrada.")

    now = datetime.now(timezone.utc)
    previous_status = enhanced.status
    enhanced.status = status_value
    if status_value == "approved":
        enhanced.approved_at = now
        enhanced.rejected_at = None
    else:
        enhanced.rejected_at = now
        enhanced.approved_at = None

    db.add(
        DecisionLog(
            event_id=event_id,
            original_media_id=enhanced.original_media_id,
            entity_type="enhanced_media",
            entity_id=enhanced.id,
            decision_type="enhancement_manual",
            reason=payload.reason or f"{previous_status} -> {status_value}.",
            actor="user",
        )
    )
    db.commit()
    db.refresh(enhanced)
    return to_enhanced_media_response(enhanced)


def get_enhanced_media_file_path(db: Session, enhanced_id: int) -> Path:
    enhanced = db.scalar(
        select(EnhancedMedia)
        .where(EnhancedMedia.id == enhanced_id)
        .options(selectinload(EnhancedMedia.event))
    )
    if enhanced is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version mejorada no encontrada.")

    event_path = get_event_path(enhanced.event)
    output_path = Path(enhanced.output_path)
    if not output_path.is_absolute():
        output_path = event_path / output_path

    resolved_event_path = event_path.resolve()
    resolved_output_path = output_path.resolve()
    try:
        resolved_output_path.relative_to(resolved_event_path)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La version mejorada esta fuera de la carpeta del evento.",
        ) from error

    if not resolved_output_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe el archivo de la version mejorada.",
        )
    return resolved_output_path


def resolve_preset(db: Session, requested_slug: str) -> PresetSettings:
    slug = requested_slug.strip() or DEFAULT_PRESET_SLUG
    preset = db.scalar(
        select(VisualStylePreset).where(
            VisualStylePreset.slug == slug,
            VisualStylePreset.is_active.is_(True),
        )
    )
    if preset is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Preset visual no disponible: {slug}",
        )

    base = PRESET_SETTINGS.get(slug, PRESET_SETTINGS[DEFAULT_PRESET_SLUG])
    custom = parse_preset_settings(preset.settings_json)
    return PresetSettings(
        slug=slug,
        brightness=float(custom.get("brightness", base.brightness)),
        contrast=float(custom.get("contrast", base.contrast)),
        color=float(custom.get("color", base.color)),
        sharpness=float(custom.get("sharpness", base.sharpness)),
        autocontrast_cutoff=int(custom.get("autocontrast_cutoff", base.autocontrast_cutoff)),
        unsharp_percent=int(custom.get("unsharp_percent", base.unsharp_percent)),
    )


def parse_preset_settings(settings_json: str | None) -> dict[str, Any]:
    if not settings_json:
        return {}
    try:
        payload = json.loads(settings_json)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def list_selected_curated_media(db: Session, event_id: int) -> list[CuratedMedia]:
    return list(
        db.scalars(
            select(CuratedMedia)
            .where(
                CuratedMedia.event_id == event_id,
                CuratedMedia.selection_status.in_(SELECTED_STATUSES),
            )
            .options(
                selectinload(CuratedMedia.original_media).selectinload(OriginalMedia.analysis),
            )
            .order_by(CuratedMedia.score.desc(), CuratedMedia.id.asc())
        ).all()
    )


@dataclass(frozen=True)
class EnhancedPhotoResult:
    width: int
    height: int


def create_enhanced_photo(
    source_path: Path,
    output_path: Path,
    preset: PresetSettings,
) -> EnhancedPhotoResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with Image.open(source_path) as source_image:
            exif = source_image.getexif()
            if exif:
                exif[274] = 1
            image = ImageOps.exif_transpose(source_image)
            if image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
            if image.mode == "L":
                image = image.convert("RGB")

            enhanced = apply_preset_adjustments(image, preset)
            save_kwargs: dict[str, Any] = {"quality": 92, "optimize": True}
            if exif:
                save_kwargs["exif"] = exif.tobytes()
            enhanced.save(output_path, format="JPEG", **save_kwargs)
            return EnhancedPhotoResult(width=enhanced.width, height=enhanced.height)
    except UnidentifiedImageError as error:
        raise ValueError(f"No se pudo abrir la foto para mejora: {source_path.name}") from error


def apply_preset_adjustments(image: Image.Image, preset: PresetSettings) -> Image.Image:
    enhanced = ImageOps.autocontrast(image, cutoff=preset.autocontrast_cutoff)
    enhanced = ImageEnhance.Brightness(enhanced).enhance(preset.brightness)
    enhanced = ImageEnhance.Contrast(enhanced).enhance(preset.contrast)
    enhanced = ImageEnhance.Color(enhanced).enhance(preset.color)
    enhanced = ImageEnhance.Sharpness(enhanced).enhance(preset.sharpness)
    return enhanced.filter(ImageFilter.UnsharpMask(radius=1.2, percent=preset.unsharp_percent, threshold=3))


def next_enhanced_output_path(output_dir: Path, source_path: Path, preset_slug: str) -> Path:
    stem = safe_windows_name(source_path.stem, fallback="foto")
    slug = safe_windows_name(preset_slug, fallback="preset")
    for version in range(1, 10000):
        candidate = output_dir / f"{stem}_{slug}_v{version:02d}.jpg"
        if not candidate.exists():
            return candidate
    raise RuntimeError("No se pudo generar una ruta unica para la version mejorada.")


def apply_output_date_metadata(
    output_path: Path,
    capture_datetime: datetime,
    exiftool_command: str | None,
) -> str:
    normalized = capture_datetime
    if normalized.tzinfo is None:
        normalized = normalized.replace(tzinfo=timezone.utc)
    timestamp = normalized.timestamp()
    os.utime(output_path, (timestamp, timestamp))

    if not exiftool_command:
        return "file_mtime_written_exiftool_unavailable"

    exif_value = normalized.astimezone(timezone.utc).strftime("%Y:%m:%d %H:%M:%S")
    try:
        completed = subprocess.run(
            [
                exiftool_command,
                "-overwrite_original",
                f"-DateTimeOriginal={exif_value}",
                f"-CreateDate={exif_value}",
                f"-ModifyDate={exif_value}",
                str(output_path),
            ],
            capture_output=True,
            check=False,
            text=True,
            timeout=15,
        )
    except OSError as error:
        return f"file_mtime_written_exiftool_failed:{error}"
    except subprocess.TimeoutExpired:
        return "file_mtime_written_exiftool_timeout"

    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout).strip()
        os.utime(output_path, (timestamp, timestamp))
        return f"file_mtime_written_exiftool_failed:{message or completed.returncode}"
    os.utime(output_path, (timestamp, timestamp))
    return "file_mtime_and_exif_written"


def to_enhanced_media_response(item: EnhancedMedia) -> EnhancedMediaResponse:
    return EnhancedMediaResponse(
        id=item.id,
        event_id=item.event_id,
        original_media_id=item.original_media_id,
        curated_media_id=item.curated_media_id,
        output_path=item.output_path,
        output_url=f"/api/media/enhanced/{item.id}/file",
        enhancement_type=item.enhancement_type,
        preset_slug=item.preset_slug,
        status=item.status,
        width=item.width,
        height=item.height,
        duration_seconds=item.duration_seconds,
        notes=item.notes,
        created_at=item.created_at,
        approved_at=item.approved_at,
        rejected_at=item.rejected_at,
        media=to_original_media_response(item.original_media),
    )
