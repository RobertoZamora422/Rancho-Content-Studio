from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.events import ContentEvent, LocalMediaSource
from app.models.media import OriginalMedia
from app.schemas.importing import (
    ImportResponse,
    MediaAnalysisResponse,
    OriginalMediaResponse,
    ScanResponse,
    ScanSourceSummary,
    SourceCreate,
    SourceResponse,
)
from app.services.event_service import require_event
from app.services.job_service import add_job_log, finish_job, start_job
from app.utils.event_folders import EVENT_SUBDIRECTORIES
from app.utils.media_files import (
    copy_media_file,
    file_modified_datetime,
    iter_files,
    is_supported_media,
    media_type_for_path,
    mime_type_for_path,
    safe_media_filename,
    sha256_file,
    unique_destination,
)


def add_source(db: Session, event_id: int, payload: SourceCreate) -> SourceResponse:
    event = require_event(db, event_id)
    source_path = Path(payload.source_path).expanduser().resolve()
    if not source_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No existe la carpeta fuente: {payload.source_path}",
        )

    event_path = get_event_path(event)
    if is_relative_to(source_path, event_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fuente debe estar fuera de la carpeta del evento.",
        )

    existing = db.scalar(
        select(LocalMediaSource).where(
            LocalMediaSource.event_id == event.id,
            LocalMediaSource.source_path == str(source_path),
        )
    )
    if existing is not None:
        return to_source_response(existing)

    source = LocalMediaSource(
        event_id=event.id,
        source_path=str(source_path),
        source_type="local_folder",
        status="registered",
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return to_source_response(source)


def list_sources(db: Session, event_id: int) -> list[SourceResponse]:
    require_event(db, event_id)
    sources = db.scalars(
        select(LocalMediaSource)
        .where(LocalMediaSource.event_id == event_id)
        .order_by(LocalMediaSource.created_at.desc())
    ).all()
    return [to_source_response(source) for source in sources]


def scan_event_sources(db: Session, event_id: int) -> ScanResponse:
    event = require_event(db, event_id)
    sources = get_sources_or_fail(db, event.id)
    job = start_job(db, "scan_folder", event.id)

    summaries: list[ScanSourceSummary] = []
    total_supported = 0
    total_unsupported = 0
    total_failed = 0

    for source in sources:
        supported = 0
        unsupported = 0
        failed = 0
        source_path = Path(source.source_path)

        try:
            files = iter_files(source_path)
        except OSError as error:
            failed += 1
            add_job_log(db, job, "error", str(error), file_path=str(source_path))
            files = []

        for file_path in files:
            try:
                if is_supported_media(file_path):
                    supported += 1
                else:
                    unsupported += 1
            except OSError as error:
                failed += 1
                add_job_log(db, job, "error", str(error), file_path=str(file_path))

        source.file_count = supported
        source.status = "scanned"
        source.scanned_at = datetime.now(timezone.utc)
        source.notes = f"{supported} compatibles, {unsupported} no compatibles."
        summaries.append(
            ScanSourceSummary(
                source_id=source.id,
                source_path=source.source_path,
                supported_files=supported,
                unsupported_files=unsupported,
                failed_files=failed,
            )
        )
        total_supported += supported
        total_unsupported += unsupported
        total_failed += failed

    finish_job(
        job,
        "completed",
        total_items=total_supported + total_unsupported + total_failed,
        processed_items=total_supported + total_unsupported,
        failed_items=total_failed,
    )
    db.commit()

    return ScanResponse(
        job_id=job.id,
        total_sources=len(sources),
        supported_files=total_supported,
        unsupported_files=total_unsupported,
        failed_files=total_failed,
        sources=summaries,
    )


def import_event_media(db: Session, event_id: int) -> ImportResponse:
    event = require_event(db, event_id)
    sources = get_sources_or_fail(db, event.id)
    originals_dir = get_event_path(event) / "01_Originales"
    originals_dir.mkdir(exist_ok=True)
    job = start_job(db, "import_media", event.id)

    total_files = 0
    imported = 0
    skipped = 0
    failed = 0

    for source in sources:
        source_path = Path(source.source_path)
        try:
            files = [path for path in iter_files(source_path) if is_supported_media(path)]
        except OSError as error:
            failed += 1
            add_job_log(db, job, "error", str(error), file_path=str(source_path))
            files = []

        total_files += len(files)

        for file_path in files:
            try:
                source_checksum = sha256_file(file_path)
                existing_by_checksum = db.scalar(
                    select(OriginalMedia).where(
                        OriginalMedia.event_id == event.id,
                        OriginalMedia.checksum_sha256 == source_checksum,
                    )
                )
                if existing_by_checksum is not None:
                    skipped += 1
                    add_job_log(
                        db,
                        job,
                        "info",
                        "Archivo omitido porque ya fue importado por checksum.",
                        file_path=str(file_path),
                        original_media_id=existing_by_checksum.id,
                    )
                    continue

                destination = unique_destination(originals_dir, safe_media_filename(file_path))
                copy_media_file(file_path, destination)
                relative_path = str(destination.relative_to(get_event_path(event)))
                media = OriginalMedia(
                    event_id=event.id,
                    source_id=source.id,
                    original_path=str(destination),
                    relative_path=relative_path,
                    filename=destination.name,
                    extension=destination.suffix.lower(),
                    media_type=media_type_for_path(destination),
                    mime_type=mime_type_for_path(destination),
                    file_size_bytes=destination.stat().st_size,
                    checksum_sha256=source_checksum,
                    capture_datetime=file_modified_datetime(file_path),
                    date_source="file_modified_time",
                    status="imported",
                    original_exists=True,
                )
                db.add(media)
                db.flush()
                imported += 1
                add_job_log(
                    db,
                    job,
                    "info",
                    "Archivo importado a 01_Originales.",
                    file_path=str(file_path),
                    original_media_id=media.id,
                )
            except Exception as error:  # noqa: BLE001 - per-file errors must not stop import.
                failed += 1
                add_job_log(db, job, "error", str(error), file_path=str(file_path))

        source.status = "imported"
        source.imported_at = datetime.now(timezone.utc)

    finish_job(
        job,
        "completed" if failed == 0 else "completed_with_errors",
        total_items=total_files,
        processed_items=imported + skipped,
        failed_items=failed,
    )
    db.commit()

    return ImportResponse(
        job_id=job.id,
        imported_files=imported,
        skipped_files=skipped,
        failed_files=failed,
        total_files=total_files,
    )


def list_original_media(db: Session, event_id: int) -> list[OriginalMediaResponse]:
    require_event(db, event_id)
    media_items = db.scalars(
        select(OriginalMedia)
        .where(OriginalMedia.event_id == event_id)
        .options(selectinload(OriginalMedia.analysis))
        .order_by(OriginalMedia.imported_at.desc(), OriginalMedia.id.desc())
    ).all()
    return [to_original_media_response(media) for media in media_items]


def get_sources_or_fail(db: Session, event_id: int) -> list[LocalMediaSource]:
    sources = db.scalars(
        select(LocalMediaSource).where(LocalMediaSource.event_id == event_id)
    ).all()
    if not sources:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registra al menos una carpeta fuente antes de escanear o importar.",
        )
    return list(sources)


def get_event_path(event: ContentEvent) -> Path:
    if not event.root_path or not event.folder_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El evento no tiene carpeta local configurada.",
        )
    event_path = Path(event.root_path) / event.folder_name
    if not event_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No existe la carpeta local del evento: {event_path}",
        )
    return event_path


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def to_source_response(source: LocalMediaSource) -> SourceResponse:
    return SourceResponse(
        id=source.id,
        event_id=source.event_id,
        source_path=source.source_path,
        source_type=source.source_type,
        status=source.status,
        file_count=source.file_count,
        scanned_at=source.scanned_at,
        imported_at=source.imported_at,
        notes=source.notes,
        created_at=source.created_at,
        updated_at=source.updated_at,
    )


def to_original_media_response(media: OriginalMedia) -> OriginalMediaResponse:
    return OriginalMediaResponse(
        id=media.id,
        event_id=media.event_id,
        source_id=media.source_id,
        original_path=media.original_path,
        relative_path=media.relative_path,
        filename=media.filename,
        extension=media.extension,
        media_type=media.media_type,
        mime_type=media.mime_type,
        file_size_bytes=media.file_size_bytes,
        checksum_sha256=media.checksum_sha256,
        capture_datetime=media.capture_datetime,
        date_source=media.date_source,
        width=media.width,
        height=media.height,
        duration_seconds=media.duration_seconds,
        thumbnail_path=media.thumbnail_path,
        thumbnail_url=f"/api/media/original/{media.id}/thumbnail" if media.thumbnail_path else None,
        metadata_json=media.metadata_json,
        analysis=to_media_analysis_response(media.analysis) if media.analysis else None,
        status=media.status,
        original_exists=media.original_exists,
        imported_at=media.imported_at,
    )


def to_media_analysis_response(analysis) -> MediaAnalysisResponse:
    return MediaAnalysisResponse(
        sharpness_score=analysis.sharpness_score,
        brightness_score=analysis.brightness_score,
        contrast_score=analysis.contrast_score,
        noise_score=analysis.noise_score,
        exposure_score=analysis.exposure_score,
        overall_quality_score=analysis.overall_quality_score,
        perceptual_hash=analysis.perceptual_hash,
        analysis_version=analysis.analysis_version,
        raw_metrics_json=analysis.raw_metrics_json,
        analyzed_at=analysis.analyzed_at,
    )
