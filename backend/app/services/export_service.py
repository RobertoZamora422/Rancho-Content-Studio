from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, time, timezone
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.content import ContentPiece, ContentPieceMedia, GeneratedCopy
from app.models.events import ContentEvent
from app.models.jobs import DecisionLog, ExportPackage, ExportPackageItem
from app.models.media import EnhancedMedia, OriginalMedia
from app.schemas.exporting import (
    ExportPackageItemResponse,
    ExportPackageListResponse,
    ExportPackageRequest,
    ExportPackageResponse,
    ExportPackageRunResponse,
    OpenExportFolderResponse,
)
from app.services.config_service import get_config_value
from app.services.enhancement_service import apply_output_date_metadata
from app.services.event_service import require_event
from app.services.import_service import get_event_path
from app.services.job_service import add_job_log, finish_job, start_job, update_job_progress
from app.utils.event_folders import safe_windows_name
from app.utils.media_files import file_modified_datetime
from app.utils.tool_validation import resolve_tool_path

VALID_EXPORT_TYPES = {
    "ready_to_publish",
    "reels_only",
    "carousel_only",
    "stories_only",
    "full_event_package",
    "google_photos_upload_package",
}

EXPORT_TYPE_PIECES = {
    "reels_only": {"reel"},
    "carousel_only": {"carousel"},
    "stories_only": {"story"},
}

PIECE_DIRECTORIES = {
    "carousel": "Carruseles",
    "promo_piece": "Promocionales",
    "reel": "Reels",
    "single_post": "Posts",
    "story": "Historias",
}

STANDALONE_EXPORT_TYPES = {
    "ready_to_publish",
    "full_event_package",
    "google_photos_upload_package",
}

EXPORT_TYPE_SLUGS = {
    "carousel_only": "carruseles",
    "full_event_package": "evento",
    "google_photos_upload_package": "gphotos",
    "ready_to_publish": "publicar",
    "reels_only": "reels",
    "stories_only": "historias",
}


def export_event_package(
    db: Session,
    event_id: int,
    payload: ExportPackageRequest,
) -> ExportPackageRunResponse:
    event = require_event(db, event_id)
    validate_export_request(payload)
    event_path = get_event_path(event)
    approved_pieces = list_approved_pieces(db, event.id, payload.export_type)
    used_media_ids = enhanced_ids_in_pieces(approved_pieces)
    standalone_media = list_standalone_approved_media(
        db,
        event.id,
        event_path,
        used_media_ids,
        payload.export_type,
    )

    if not approved_pieces and not standalone_media:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay piezas aprobadas ni medios mejorados aprobados para exportar.",
        )

    exiftool_command, exiftool_error = resolve_tool_path(
        get_config_value(db, "tools.exiftool_path"),
        "exiftool",
    )
    job = start_job(db, "export_package", event.id)
    if exiftool_error and payload.write_event_date_metadata:
        add_job_log(
            db,
            job,
            "warning",
            f"ExifTool no disponible; se escribira fecha de archivo solamente. {exiftool_error}",
        )

    package_dir = unique_export_package_dir(event_path, event, payload.export_type)
    package_dir.mkdir(parents=True, exist_ok=False)
    package = ExportPackage(
        event_id=event.id,
        name=package_dir.name,
        export_type=payload.export_type,
        output_path=relative_to_event(event_path, package_dir),
        status="pending",
    )
    db.add(package)
    db.flush()

    total_expected = estimate_total_items(approved_pieces, standalone_media, payload)
    media_exported = 0
    copies_exported = 0
    failed_items = 0
    summary_exported = 0
    order = 0

    for piece_index, piece in enumerate(approved_pieces, start=1):
        piece_dir = export_piece_dir(package_dir, piece, piece_index, payload.group_by_type)
        piece_dir.mkdir(parents=True, exist_ok=True)
        approved_copies = sorted(
            [copy for copy in piece.copies if copy.status == "approved"],
            key=lambda item: (item.copy_type, item.id),
        )
        if payload.include_copies and not approved_copies:
            add_job_log(
                db,
                job,
                "warning",
                f"Pieza aprobada sin copy aprobado: {piece.title}.",
            )

        for media_item in sorted(piece.media_items, key=lambda item: item.position):
            order += 1
            try:
                item = export_piece_media(
                    db,
                    event,
                    event_path,
                    package,
                    piece,
                    media_item,
                    piece_dir,
                    order,
                    payload.write_event_date_metadata,
                    exiftool_command,
                )
                media_exported += 1
                add_job_log(db, job, "info", "Medio exportado.", file_path=item.output_path)
            except Exception as error:  # noqa: BLE001 - file-level export errors must continue.
                failed_items += 1
                add_export_error_item(
                    db,
                    package,
                    "media",
                    piece.id,
                    media_item.enhanced_media_id,
                    None,
                    piece_dir / fallback_media_name(piece, media_item, order),
                    event_path,
                    order,
                    str(error),
                )
                add_job_log(
                    db,
                    job,
                    "error",
                    str(error),
                    file_path=str(piece_dir),
                    original_media_id=media_item.original_media_id,
                )
            update_job_progress(
                job,
                total_expected,
                media_exported + copies_exported + summary_exported,
                failed_items,
            )
            db.flush()

        if payload.include_copies:
            copies_dir = package_dir / "Copies"
            copies_dir.mkdir(exist_ok=True)
            for generated_copy in approved_copies:
                order += 1
                try:
                    item = export_copy_file(
                        db,
                        event,
                        event_path,
                        package,
                        piece,
                        generated_copy,
                        copies_dir,
                        order,
                    )
                    copies_exported += 1
                    add_job_log(db, job, "info", "Copy exportado.", file_path=item.output_path)
                except Exception as error:  # noqa: BLE001 - copy-level errors must continue.
                    failed_items += 1
                    add_export_error_item(
                        db,
                        package,
                        "copy",
                        piece.id,
                        None,
                        generated_copy.id,
                        copies_dir / fallback_copy_name(piece, generated_copy, order),
                        event_path,
                        order,
                        str(error),
                    )
                    add_job_log(db, job, "error", str(error), file_path=str(copies_dir))
                update_job_progress(
                    job,
                    total_expected,
                    media_exported + copies_exported + summary_exported,
                    failed_items,
                )
                db.flush()

    if standalone_media:
        standalone_dir = package_dir / "Medios_Aprobados"
        standalone_dir.mkdir(exist_ok=True)
        for media in standalone_media:
            order += 1
            try:
                item = export_standalone_media(
                    db,
                    event,
                    event_path,
                    package,
                    media,
                    standalone_dir,
                    order,
                    payload.write_event_date_metadata,
                    exiftool_command,
                )
                media_exported += 1
                add_job_log(
                    db,
                    job,
                    "info",
                    "Medio aprobado exportado sin pieza.",
                    file_path=item.output_path,
                )
            except Exception as error:  # noqa: BLE001 - keep exporting other files.
                failed_items += 1
                add_export_error_item(
                    db,
                    package,
                    "standalone_media",
                    None,
                    media.id,
                    None,
                    standalone_dir / fallback_standalone_name(media, order),
                    event_path,
                    order,
                    str(error),
                )
                add_job_log(
                    db,
                    job,
                    "error",
                    str(error),
                    file_path=str(standalone_dir),
                    original_media_id=media.original_media_id,
                )
            update_job_progress(
                job,
                total_expected,
                media_exported + copies_exported + summary_exported,
                failed_items,
            )
            db.flush()

    summary_path: str | None = None
    if payload.include_summary:
        order += 1
        summary = write_export_summary(
            event,
            event_path,
            package,
            package_dir,
            approved_pieces,
            media_exported,
            copies_exported,
            failed_items,
        )
        summary_path = relative_to_event(event_path, summary)
        db.add(
            ExportPackageItem(
                package_id=package.id,
                item_type="summary",
                output_path=summary_path,
                item_order=order,
                metadata_written=False,
                metadata_status="summary_created",
            )
        )
        add_job_log(db, job, "info", "Resumen de exportacion creado.", file_path=summary_path)
        summary_exported = 1
        update_job_progress(
            job,
            total_expected,
            media_exported + copies_exported + summary_exported,
            failed_items,
        )

    package.status = "generated" if media_exported or copies_exported else "failed"
    package.finished_at = datetime.now(timezone.utc)
    event.status = "exported" if package.status == "generated" else event.status
    db.add(
        DecisionLog(
            event_id=event.id,
            entity_type="export_package",
            entity_id=package.id,
            decision_type="package_exported",
            reason=(
                f"Exportacion {payload.export_type}: {media_exported} medios, "
                f"{copies_exported} copies, {failed_items} fallas."
            ),
            actor="system",
        )
    )
    finish_job(
        job,
        "completed" if failed_items == 0 else "completed_with_errors",
        total_items=total_expected,
        processed_items=media_exported + copies_exported + summary_exported,
        failed_items=failed_items,
    )
    db.commit()

    refreshed = require_export_package(db, event.id, package.id)
    return ExportPackageRunResponse(
        job_id=job.id,
        package=to_export_package_response(refreshed, event_path),
        total_pieces=len(approved_pieces),
        media_exported=media_exported,
        copies_exported=copies_exported,
        failed_items=failed_items,
        summary_path=summary_path,
    )


def list_event_export_packages(db: Session, event_id: int) -> ExportPackageListResponse:
    event = require_event(db, event_id)
    event_path = get_event_path(event)
    packages = db.scalars(
        select(ExportPackage)
        .where(ExportPackage.event_id == event.id)
        .options(selectinload(ExportPackage.items))
        .order_by(ExportPackage.created_at.desc(), ExportPackage.id.desc())
    ).all()
    return ExportPackageListResponse(
        items=[to_export_package_response(item, event_path) for item in packages]
    )


def open_export_package_folder(
    db: Session,
    event_id: int,
    package_id: int,
) -> OpenExportFolderResponse:
    event = require_event(db, event_id)
    event_path = get_event_path(event)
    package = require_export_package(db, event.id, package_id)
    folder_path = resolve_package_path(event_path, package)
    if not folder_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe la carpeta final de exportacion.",
        )

    try:
        open_folder(folder_path)
    except Exception as error:  # noqa: BLE001 - return the path even when opening is blocked.
        return OpenExportFolderResponse(
            package_id=package.id,
            path=str(folder_path),
            opened=False,
            message=f"No se pudo abrir automaticamente: {error}",
        )
    return OpenExportFolderResponse(
        package_id=package.id,
        path=str(folder_path),
        opened=True,
        message="Carpeta final abierta.",
    )


def validate_export_request(payload: ExportPackageRequest) -> None:
    if payload.export_type not in VALID_EXPORT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de exportacion no permitido.",
        )


def list_approved_pieces(db: Session, event_id: int, export_type: str) -> list[ContentPiece]:
    allowed_types = EXPORT_TYPE_PIECES.get(export_type)
    query = (
        select(ContentPiece)
        .where(ContentPiece.event_id == event_id, ContentPiece.status == "approved")
        .options(
            selectinload(ContentPiece.media_items)
            .selectinload(ContentPieceMedia.enhanced_media)
            .selectinload(EnhancedMedia.original_media),
            selectinload(ContentPiece.copies),
        )
        .order_by(ContentPiece.approved_at.asc(), ContentPiece.id.asc())
    )
    if allowed_types:
        query = query.where(ContentPiece.piece_type.in_(allowed_types))
    return list(db.scalars(query).all())


def enhanced_ids_in_pieces(pieces: list[ContentPiece]) -> set[int]:
    return {
        item.enhanced_media_id
        for piece in pieces
        for item in piece.media_items
        if item.enhanced_media_id is not None
    }


def list_standalone_approved_media(
    db: Session,
    event_id: int,
    event_path: Path,
    used_media_ids: set[int],
    export_type: str,
) -> list[EnhancedMedia]:
    if export_type not in STANDALONE_EXPORT_TYPES:
        return []
    media_items = db.scalars(
        select(EnhancedMedia)
        .where(EnhancedMedia.event_id == event_id, EnhancedMedia.status == "approved")
        .options(selectinload(EnhancedMedia.original_media))
        .order_by(EnhancedMedia.approved_at.asc(), EnhancedMedia.id.asc())
    ).all()
    available: list[EnhancedMedia] = []
    for media in media_items:
        if media.id in used_media_ids:
            continue
        source_path = resolve_event_path(event_path, media.output_path)
        if source_path.is_file():
            available.append(media)
    return available


def estimate_total_items(
    pieces: list[ContentPiece],
    standalone_media: list[EnhancedMedia],
    payload: ExportPackageRequest,
) -> int:
    media_count = sum(len(piece.media_items) for piece in pieces)
    copy_count = 0
    if payload.include_copies:
        copy_count = sum(1 for piece in pieces for copy in piece.copies if copy.status == "approved")
    summary_count = 1 if payload.include_summary else 0
    return media_count + copy_count + len(standalone_media) + summary_count


def unique_export_package_dir(event_path: Path, event: ContentEvent, export_type: str) -> Path:
    output_root = event_path / "09_Listo_Para_Publicar"
    output_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%y%m%d%H%M%S")
    export_slug = EXPORT_TYPE_SLUGS.get(export_type, "paquete")
    base_name = f"pkg_{timestamp}_{export_slug}"
    candidate = output_root / base_name
    if not candidate.exists():
        return candidate
    for index in range(2, 1000):
        next_candidate = output_root / f"{base_name}_{index:03d}"
        if not next_candidate.exists():
            return next_candidate
    raise RuntimeError("No se pudo crear una carpeta unica de exportacion.")


def export_piece_dir(
    package_dir: Path,
    piece: ContentPiece,
    piece_index: int,
    group_by_type: bool,
) -> Path:
    base_dir = package_dir / PIECE_DIRECTORIES.get(piece.piece_type, "Piezas")
    if not group_by_type:
        base_dir = package_dir
    return base_dir


def export_piece_media(
    db: Session,
    event: ContentEvent,
    event_path: Path,
    package: ExportPackage,
    piece: ContentPiece,
    media_item: ContentPieceMedia,
    piece_dir: Path,
    item_order: int,
    write_metadata: bool,
    exiftool_command: str | None,
) -> ExportPackageItem:
    enhanced = media_item.enhanced_media
    if enhanced is None:
        raise FileNotFoundError("La pieza tiene un medio sin version mejorada asociada.")
    source_path = resolve_event_path(event_path, enhanced.output_path)
    if not source_path.is_file():
        raise FileNotFoundError(f"No existe el medio mejorado: {enhanced.output_path}")

    destination = unique_file_path(
        piece_dir,
        media_export_filename(piece, media_item, source_path),
    )
    copy_export_file(source_path, destination)
    metadata_status = apply_export_metadata(
        event,
        enhanced.original_media,
        source_path,
        destination,
        write_metadata,
        exiftool_command,
    )
    item = ExportPackageItem(
        package_id=package.id,
        content_piece_id=piece.id,
        enhanced_media_id=enhanced.id,
        item_type="media",
        output_path=relative_to_event(event_path, destination),
        item_order=item_order,
        metadata_written=metadata_status.startswith("file_mtime"),
        metadata_status=metadata_status,
    )
    db.add(item)
    db.flush()
    return item


def export_standalone_media(
    db: Session,
    event: ContentEvent,
    event_path: Path,
    package: ExportPackage,
    media: EnhancedMedia,
    output_dir: Path,
    item_order: int,
    write_metadata: bool,
    exiftool_command: str | None,
) -> ExportPackageItem:
    source_path = resolve_event_path(event_path, media.output_path)
    if not source_path.is_file():
        raise FileNotFoundError(f"No existe el medio aprobado: {media.output_path}")

    destination = unique_file_path(output_dir, standalone_media_filename(media, source_path))
    copy_export_file(source_path, destination)
    metadata_status = apply_export_metadata(
        event,
        media.original_media,
        source_path,
        destination,
        write_metadata,
        exiftool_command,
    )
    item = ExportPackageItem(
        package_id=package.id,
        enhanced_media_id=media.id,
        item_type="standalone_media",
        output_path=relative_to_event(event_path, destination),
        item_order=item_order,
        metadata_written=metadata_status.startswith("file_mtime"),
        metadata_status=metadata_status,
    )
    db.add(item)
    db.flush()
    return item


def export_copy_file(
    db: Session,
    event: ContentEvent,
    event_path: Path,
    package: ExportPackage,
    piece: ContentPiece,
    generated_copy: GeneratedCopy,
    copies_dir: Path,
    item_order: int,
) -> ExportPackageItem:
    destination = unique_file_path(copies_dir, copy_export_filename(piece, generated_copy))
    destination.write_text(
        build_copy_export_text(event, piece, generated_copy),
        encoding="utf-8",
    )
    item = ExportPackageItem(
        package_id=package.id,
        content_piece_id=piece.id,
        generated_copy_id=generated_copy.id,
        item_type="copy",
        output_path=relative_to_event(event_path, destination),
        item_order=item_order,
        metadata_written=False,
        metadata_status="text_exported",
    )
    db.add(item)
    db.flush()
    return item


def add_export_error_item(
    db: Session,
    package: ExportPackage,
    item_type: str,
    piece_id: int | None,
    enhanced_media_id: int | None,
    copy_id: int | None,
    destination: Path,
    event_path: Path,
    item_order: int,
    error_message: str,
) -> None:
    db.add(
        ExportPackageItem(
            package_id=package.id,
            content_piece_id=piece_id,
            enhanced_media_id=enhanced_media_id,
            generated_copy_id=copy_id,
            item_type=item_type,
            output_path=relative_to_event(event_path, destination),
            item_order=item_order,
            metadata_written=False,
            metadata_status="failed",
            error_message=error_message[:2000],
        )
    )


def copy_export_file(source_path: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination)


def apply_export_metadata(
    event: ContentEvent,
    media: OriginalMedia | None,
    source_path: Path,
    destination: Path,
    write_metadata: bool,
    exiftool_command: str | None,
) -> str:
    if not write_metadata:
        return "metadata_not_requested"
    reference = export_reference_datetime(event, media, source_path)
    return apply_output_date_metadata(destination, reference, exiftool_command)


def export_reference_datetime(
    event: ContentEvent,
    media: OriginalMedia | None,
    source_path: Path,
) -> datetime:
    if event.event_date is not None:
        return datetime.combine(event.event_date, time(hour=12), tzinfo=timezone.utc)
    if media is not None and media.capture_datetime is not None:
        capture = media.capture_datetime
        if capture.tzinfo is None:
            capture = capture.replace(tzinfo=timezone.utc)
        return capture
    return file_modified_datetime(source_path)


def write_export_summary(
    event: ContentEvent,
    event_path: Path,
    package: ExportPackage,
    package_dir: Path,
    pieces: list[ContentPiece],
    media_exported: int,
    copies_exported: int,
    failed_items: int,
) -> Path:
    summary_path = package_dir / "resumen_exportacion.txt"
    package_items = sorted(package.items, key=lambda item: item.item_order or item.id)
    lines = [
        "Rancho Content Studio - Resumen de exportacion",
        "",
        f"Evento: {event.name}",
        f"Fecha del evento: {event.event_date.isoformat() if event.event_date else 'Sin fecha'}",
        f"Tipo de paquete: {package.export_type}",
        f"Paquete: {package.name}",
        f"Carpeta: {package.output_path}",
        "",
        f"Piezas aprobadas incluidas: {len(pieces)}",
        f"Medios exportados: {media_exported}",
        f"Copies exportados: {copies_exported}",
        f"Errores registrados: {failed_items}",
        "",
        "Piezas:",
    ]
    if pieces:
        for piece in pieces:
            lines.append(f"- #{piece.id} {piece.piece_type}: {piece.title}")
    else:
        lines.append("- Sin piezas aprobadas; se exportaron medios aprobados sueltos.")

    lines.extend(["", "Archivos:"])
    for item in package_items:
        if item.item_type == "summary":
            continue
        status_text = item.metadata_status or "sin_estado"
        error_text = f" | ERROR: {item.error_message}" if item.error_message else ""
        lines.append(f"- {item.item_type}: {item.output_path} | {status_text}{error_text}")

    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary_path


def media_export_filename(
    piece: ContentPiece,
    media_item: ContentPieceMedia,
    source_path: Path,
) -> str:
    source_name = short_safe_name(source_path.stem, "medio", 28)
    suffix = source_path.suffix.lower() or ".bin"
    return f"p{piece.id:04d}_{media_item.position:02d}_{source_name}{suffix}"


def standalone_media_filename(media: EnhancedMedia, source_path: Path) -> str:
    source_name = short_safe_name(source_path.stem, "medio", 34)
    suffix = source_path.suffix.lower() or ".bin"
    media_type = media.original_media.media_type if media.original_media else "medio"
    return f"{media.id:04d}_{media_type}_{source_name}{suffix}"


def copy_export_filename(piece: ContentPiece, generated_copy: GeneratedCopy) -> str:
    copy_type = short_safe_name(generated_copy.copy_type, "copy", 14)
    return f"p{piece.id:04d}_{copy_type}_{generated_copy.id:04d}.txt"


def fallback_media_name(piece: ContentPiece, media_item: ContentPieceMedia, item_order: int) -> str:
    piece_name = short_safe_name(piece.title, "pieza", 28)
    return f"{item_order:03d}_{piece_name}_medio_{media_item.id}.bin"


def fallback_standalone_name(media: EnhancedMedia, item_order: int) -> str:
    return f"{item_order:03d}_medio_aprobado_{media.id}.bin"


def fallback_copy_name(piece: ContentPiece, generated_copy: GeneratedCopy, item_order: int) -> str:
    piece_name = short_safe_name(piece.title, "pieza", 28)
    return f"{item_order:03d}_{piece_name}_copy_{generated_copy.id}.txt"


def short_safe_name(value: str | None, fallback: str, max_length: int) -> str:
    safe = safe_windows_name(value or "", fallback=fallback)
    return safe[:max_length].strip(" ._") or fallback


def build_copy_export_text(
    event: ContentEvent,
    piece: ContentPiece,
    generated_copy: GeneratedCopy,
) -> str:
    hashtags: list[str] = []
    if generated_copy.hashtags_json:
        try:
            parsed = json.loads(generated_copy.hashtags_json)
            if isinstance(parsed, list):
                hashtags = [str(item) for item in parsed]
        except json.JSONDecodeError:
            hashtags = []
    lines = [
        f"Evento: {event.name}",
        f"Fecha: {event.event_date.isoformat() if event.event_date else 'Sin fecha'}",
        f"Pieza: {piece.title}",
        f"Tipo de pieza: {piece.piece_type}",
        f"Plataforma: {piece.target_platform or 'Sin plataforma'}",
        f"Copy: {generated_copy.variant_label or generated_copy.copy_type}",
        "",
        generated_copy.body.strip(),
        "",
    ]
    if generated_copy.cta:
        lines.extend(["CTA:", generated_copy.cta.strip(), ""])
    if hashtags:
        lines.extend(["Hashtags:", " ".join(hashtags), ""])
    return "\n".join(lines)


def unique_file_path(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    for index in range(2, 10000):
        next_candidate = directory / f"{stem}_{index:03d}{suffix}"
        if not next_candidate.exists():
            return next_candidate
    raise RuntimeError("No se pudo generar un nombre unico de exportacion.")


def resolve_event_path(event_path: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = event_path / path
    return path


def relative_to_event(event_path: Path, path: Path) -> str:
    try:
        return str(path.relative_to(event_path))
    except ValueError:
        return str(path)


def resolve_package_path(event_path: Path, package: ExportPackage) -> Path:
    return resolve_event_path(event_path, package.output_path)


def require_export_package(db: Session, event_id: int, package_id: int) -> ExportPackage:
    package = db.scalar(
        select(ExportPackage)
        .where(ExportPackage.event_id == event_id, ExportPackage.id == package_id)
        .options(selectinload(ExportPackage.items))
    )
    if package is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paquete de exportacion no encontrado.",
        )
    return package


def open_folder(folder_path: Path) -> None:
    if sys.platform.startswith("win"):
        os.startfile(folder_path)  # type: ignore[attr-defined]
        return
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(folder_path)])
        return
    subprocess.Popen(["xdg-open", str(folder_path)])


def to_export_package_response(
    package: ExportPackage,
    event_path: Path,
) -> ExportPackageResponse:
    package_path = resolve_package_path(event_path, package)
    return ExportPackageResponse(
        id=package.id,
        event_id=package.event_id,
        name=package.name,
        export_type=package.export_type,
        output_path=package.output_path,
        absolute_output_path=str(package_path),
        status=package.status,
        created_at=package.created_at,
        updated_at=package.updated_at,
        finished_at=package.finished_at,
        items=[
            to_export_item_response(item, event_path)
            for item in sorted(package.items, key=lambda item: item.item_order or item.id)
        ],
    )


def to_export_item_response(
    item: ExportPackageItem,
    event_path: Path,
) -> ExportPackageItemResponse:
    output_path = resolve_event_path(event_path, item.output_path)
    return ExportPackageItemResponse(
        id=item.id,
        package_id=item.package_id,
        content_piece_id=item.content_piece_id,
        generated_copy_id=item.generated_copy_id,
        enhanced_media_id=item.enhanced_media_id,
        item_type=item.item_type,
        output_path=item.output_path,
        absolute_output_path=str(output_path),
        item_order=item.item_order,
        metadata_written=item.metadata_written,
        metadata_status=item.metadata_status,
        error_message=item.error_message,
        created_at=item.created_at,
    )
