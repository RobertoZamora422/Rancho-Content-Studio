from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.content import ContentPiece, ContentPieceMedia, GeneratedCopy
from app.models.events import ContentEvent
from app.models.media import CuratedMedia, EnhancedMedia, OriginalMedia
from app.schemas.library import (
    LibraryCopyItem,
    LibraryCopyListResponse,
    LibraryMediaItem,
    LibraryMediaListResponse,
    LibraryPieceItem,
    LibraryPieceListResponse,
    LibrarySearchItem,
    LibrarySearchResponse,
)


def list_library_media(
    db: Session,
    event_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    event_type: str | None = None,
    file_type: str | None = None,
    status: str | None = None,
    query: str | None = None,
    source_type: str | None = None,
    limit: int = 100,
) -> LibraryMediaListResponse:
    source = normalize_filter(source_type)
    items: list[LibraryMediaItem] = []

    if source in {None, "original"}:
        items.extend(
            to_original_library_item(media)
            for media in query_original_media(
                db,
                event_id,
                date_from,
                date_to,
                event_type,
                file_type,
                status,
                query,
                limit,
            )
        )
    if source in {None, "curated"}:
        items.extend(
            to_curated_library_item(item)
            for item in query_curated_media(
                db,
                event_id,
                date_from,
                date_to,
                event_type,
                file_type,
                status,
                query,
                limit,
            )
        )
    if source in {None, "enhanced"}:
        items.extend(
            to_enhanced_library_item(item)
            for item in query_enhanced_media(
                db,
                event_id,
                date_from,
                date_to,
                event_type,
                file_type,
                status,
                query,
                limit,
            )
        )

    items.sort(key=lambda item: (item.created_at, item.id), reverse=True)
    return LibraryMediaListResponse(items=items[:limit])


def list_library_pieces(
    db: Session,
    event_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    event_type: str | None = None,
    piece_type: str | None = None,
    status: str | None = None,
    query: str | None = None,
    limit: int = 100,
) -> LibraryPieceListResponse:
    statement = (
        select(ContentPiece)
        .join(ContentPiece.event)
        .where(ContentEvent.status != "deleted")
        .options(
            selectinload(ContentPiece.event),
            selectinload(ContentPiece.copies),
            selectinload(ContentPiece.media_items)
            .selectinload(ContentPieceMedia.enhanced_media)
            .selectinload(EnhancedMedia.original_media),
        )
        .order_by(ContentPiece.updated_at.desc(), ContentPiece.id.desc())
    )
    statement = apply_event_filters(statement, event_id, date_from, date_to, event_type)
    if piece_type:
        statement = statement.where(ContentPiece.piece_type == piece_type)
    if status:
        statement = statement.where(ContentPiece.status == status)
    normalized_query = normalize_filter(query)
    if normalized_query:
        like = f"%{normalized_query}%"
        statement = statement.where(
            or_(
                func.lower(ContentPiece.title).like(like),
                func.lower(ContentPiece.purpose).like(like),
                func.lower(ContentPiece.output_path).like(like),
                func.lower(ContentEvent.name).like(like),
            )
        )
    pieces = db.scalars(statement.limit(limit)).all()
    return LibraryPieceListResponse(items=[to_library_piece_item(piece) for piece in pieces])


def list_library_copies(
    db: Session,
    event_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    event_type: str | None = None,
    copy_type: str | None = None,
    status: str | None = None,
    query: str | None = None,
    limit: int = 100,
) -> LibraryCopyListResponse:
    statement = (
        select(GeneratedCopy)
        .join(GeneratedCopy.piece)
        .join(ContentPiece.event)
        .where(ContentEvent.status != "deleted")
        .options(selectinload(GeneratedCopy.piece).selectinload(ContentPiece.event))
        .order_by(GeneratedCopy.updated_at.desc(), GeneratedCopy.id.desc())
    )
    statement = apply_event_filters(statement, event_id, date_from, date_to, event_type)
    if copy_type:
        statement = statement.where(GeneratedCopy.copy_type == copy_type)
    if status:
        statement = statement.where(GeneratedCopy.status == status)
    normalized_query = normalize_filter(query)
    if normalized_query:
        like = f"%{normalized_query}%"
        statement = statement.where(
            or_(
                func.lower(GeneratedCopy.body).like(like),
                func.lower(GeneratedCopy.variant_label).like(like),
                func.lower(GeneratedCopy.copy_type).like(like),
                func.lower(GeneratedCopy.output_path).like(like),
                func.lower(ContentPiece.title).like(like),
                func.lower(ContentEvent.name).like(like),
            )
        )
    copies = db.scalars(statement.limit(limit)).all()
    return LibraryCopyListResponse(items=[to_library_copy_item(copy) for copy in copies])


def search_library(
    db: Session,
    event_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    event_type: str | None = None,
    file_type: str | None = None,
    status: str | None = None,
    query: str | None = None,
    limit: int = 100,
) -> LibrarySearchResponse:
    media = list_library_media(
        db,
        event_id=event_id,
        date_from=date_from,
        date_to=date_to,
        event_type=event_type,
        file_type=file_type,
        status=status,
        query=query,
        limit=limit,
    ).items
    pieces = list_library_pieces(
        db,
        event_id=event_id,
        date_from=date_from,
        date_to=date_to,
        event_type=event_type,
        piece_type=file_type,
        status=status,
        query=query,
        limit=limit,
    ).items
    copies = list_library_copies(
        db,
        event_id=event_id,
        date_from=date_from,
        date_to=date_to,
        event_type=event_type,
        copy_type=file_type,
        status=status,
        query=query,
        limit=limit,
    ).items
    items: list[LibrarySearchItem] = [
        LibrarySearchItem(
            entity_type=f"media:{item.source_type}",
            id=item.id,
            event_id=item.event_id,
            event_name=item.event_name,
            title=item.title,
            subtitle=f"{item.media_type} | {item.filename}",
            status=item.status,
            date=item.event_date or item.created_at,
            local_path=item.local_path,
            thumbnail_url=item.thumbnail_url,
        )
        for item in media
    ]
    items.extend(
        LibrarySearchItem(
            entity_type="piece",
            id=item.id,
            event_id=item.event_id,
            event_name=item.event_name,
            title=item.title,
            subtitle=f"{item.piece_type} | {item.target_platform or 'sin plataforma'}",
            status=item.status,
            date=item.event_date or item.updated_at,
            local_path=item.absolute_output_path,
            thumbnail_url=item.thumbnail_url,
        )
        for item in pieces
    )
    items.extend(
        LibrarySearchItem(
            entity_type="copy",
            id=item.id,
            event_id=item.event_id,
            event_name=item.event_name,
            title=item.variant_label or item.copy_type,
            subtitle=f"{item.piece_title} | {item.body_preview}",
            status=item.status,
            date=item.event_date or item.updated_at,
            local_path=item.absolute_output_path,
            thumbnail_url=None,
        )
        for item in copies
    )
    items.sort(key=lambda item: str(item.date or ""), reverse=True)
    return LibrarySearchResponse(items=items[:limit])


def query_original_media(
    db: Session,
    event_id: int | None,
    date_from: date | None,
    date_to: date | None,
    event_type: str | None,
    file_type: str | None,
    status: str | None,
    query: str | None,
    limit: int,
) -> list[OriginalMedia]:
    statement = (
        select(OriginalMedia)
        .join(OriginalMedia.event)
        .where(ContentEvent.status != "deleted")
        .options(selectinload(OriginalMedia.event))
        .order_by(OriginalMedia.imported_at.desc(), OriginalMedia.id.desc())
    )
    statement = apply_event_filters(statement, event_id, date_from, date_to, event_type)
    statement = apply_media_file_type_filter(statement, file_type)
    if status:
        statement = statement.where(OriginalMedia.status == status)
    normalized_query = normalize_filter(query)
    if normalized_query:
        like = f"%{normalized_query}%"
        statement = statement.where(
            or_(
                func.lower(OriginalMedia.filename).like(like),
                func.lower(OriginalMedia.original_path).like(like),
                func.lower(OriginalMedia.relative_path).like(like),
                func.lower(ContentEvent.name).like(like),
            )
        )
    return list(db.scalars(statement.limit(limit)).all())


def query_curated_media(
    db: Session,
    event_id: int | None,
    date_from: date | None,
    date_to: date | None,
    event_type: str | None,
    file_type: str | None,
    status: str | None,
    query: str | None,
    limit: int,
) -> list[CuratedMedia]:
    statement = (
        select(CuratedMedia)
        .join(CuratedMedia.event)
        .join(CuratedMedia.original_media)
        .where(ContentEvent.status != "deleted")
        .options(selectinload(CuratedMedia.event), selectinload(CuratedMedia.original_media))
        .order_by(CuratedMedia.updated_at.desc(), CuratedMedia.id.desc())
    )
    statement = apply_event_filters(statement, event_id, date_from, date_to, event_type)
    statement = apply_media_file_type_filter(statement, file_type)
    if status:
        statement = statement.where(CuratedMedia.selection_status == status)
    normalized_query = normalize_filter(query)
    if normalized_query:
        like = f"%{normalized_query}%"
        statement = statement.where(
            or_(
                func.lower(OriginalMedia.filename).like(like),
                func.lower(OriginalMedia.original_path).like(like),
                func.lower(CuratedMedia.reason).like(like),
                func.lower(ContentEvent.name).like(like),
            )
        )
    return list(db.scalars(statement.limit(limit)).all())


def query_enhanced_media(
    db: Session,
    event_id: int | None,
    date_from: date | None,
    date_to: date | None,
    event_type: str | None,
    file_type: str | None,
    status: str | None,
    query: str | None,
    limit: int,
) -> list[EnhancedMedia]:
    statement = (
        select(EnhancedMedia)
        .join(EnhancedMedia.event)
        .join(EnhancedMedia.original_media)
        .where(ContentEvent.status != "deleted")
        .options(selectinload(EnhancedMedia.event), selectinload(EnhancedMedia.original_media))
        .order_by(EnhancedMedia.created_at.desc(), EnhancedMedia.id.desc())
    )
    statement = apply_event_filters(statement, event_id, date_from, date_to, event_type)
    statement = apply_media_file_type_filter(statement, file_type)
    if status:
        statement = statement.where(EnhancedMedia.status == status)
    normalized_query = normalize_filter(query)
    if normalized_query:
        like = f"%{normalized_query}%"
        statement = statement.where(
            or_(
                func.lower(OriginalMedia.filename).like(like),
                func.lower(EnhancedMedia.output_path).like(like),
                func.lower(EnhancedMedia.enhancement_type).like(like),
                func.lower(ContentEvent.name).like(like),
            )
        )
    return list(db.scalars(statement.limit(limit)).all())


def apply_event_filters(statement, event_id, date_from, date_to, event_type):
    if event_id is not None:
        statement = statement.where(ContentEvent.id == event_id)
    if date_from is not None:
        statement = statement.where(ContentEvent.event_date >= date_from)
    if date_to is not None:
        statement = statement.where(ContentEvent.event_date <= date_to)
    normalized_event_type = normalize_filter(event_type)
    if normalized_event_type:
        statement = statement.where(func.lower(ContentEvent.event_type) == normalized_event_type)
    return statement


def apply_media_file_type_filter(statement, file_type: str | None):
    normalized = normalize_filter(file_type)
    if not normalized:
        return statement
    extension = normalized if normalized.startswith(".") else f".{normalized}"
    return statement.where(
        or_(
            func.lower(OriginalMedia.media_type) == normalized,
            func.lower(OriginalMedia.extension) == extension,
            func.lower(OriginalMedia.extension) == normalized,
        )
    )


def to_original_library_item(media: OriginalMedia) -> LibraryMediaItem:
    return LibraryMediaItem(
        id=media.id,
        source_type="original",
        event_id=media.event_id,
        event_name=media.event.name,
        event_type=media.event.event_type,
        event_date=media.event.event_date,
        title=media.filename,
        filename=media.filename,
        media_type=media.media_type,
        file_type=media.extension or media.media_type,
        status=media.status,
        local_path=media.original_path,
        relative_path=media.relative_path,
        thumbnail_url=original_thumbnail_url(media),
        file_exists=Path(media.original_path).is_file(),
        width=media.width,
        height=media.height,
        duration_seconds=media.duration_seconds,
        original_media_id=media.id,
        curated_media_id=None,
        enhanced_media_id=None,
        created_at=media.imported_at,
    )


def to_curated_library_item(item: CuratedMedia) -> LibraryMediaItem:
    media = item.original_media
    return LibraryMediaItem(
        id=item.id,
        source_type="curated",
        event_id=item.event_id,
        event_name=item.event.name,
        event_type=item.event.event_type,
        event_date=item.event.event_date,
        title=f"Curacion: {media.filename}",
        filename=media.filename,
        media_type=media.media_type,
        file_type=media.extension or media.media_type,
        status=item.selection_status,
        local_path=media.original_path,
        relative_path=media.relative_path,
        thumbnail_url=original_thumbnail_url(media),
        file_exists=Path(media.original_path).is_file(),
        width=media.width,
        height=media.height,
        duration_seconds=media.duration_seconds,
        original_media_id=media.id,
        curated_media_id=item.id,
        enhanced_media_id=None,
        created_at=item.updated_at,
    )


def to_enhanced_library_item(item: EnhancedMedia) -> LibraryMediaItem:
    media = item.original_media
    local_path = absolute_event_file_path(item.event, item.output_path)
    return LibraryMediaItem(
        id=item.id,
        source_type="enhanced",
        event_id=item.event_id,
        event_name=item.event.name,
        event_type=item.event.event_type,
        event_date=item.event.event_date,
        title=f"{item.enhancement_type}: {media.filename}",
        filename=Path(item.output_path).name,
        media_type=media.media_type,
        file_type=Path(item.output_path).suffix or media.extension or media.media_type,
        status=item.status,
        local_path=local_path or item.output_path,
        relative_path=item.output_path,
        thumbnail_url=original_thumbnail_url(media),
        file_exists=Path(local_path).is_file() if local_path else False,
        width=item.width,
        height=item.height,
        duration_seconds=item.duration_seconds,
        original_media_id=media.id,
        curated_media_id=item.curated_media_id,
        enhanced_media_id=item.id,
        created_at=item.created_at,
    )


def to_library_piece_item(piece: ContentPiece) -> LibraryPieceItem:
    copies = list(piece.copies)
    return LibraryPieceItem(
        id=piece.id,
        event_id=piece.event_id,
        event_name=piece.event.name,
        event_type=piece.event.event_type,
        event_date=piece.event.event_date,
        piece_type=piece.piece_type,
        title=piece.title,
        purpose=piece.purpose,
        target_platform=piece.target_platform,
        aspect_ratio=piece.aspect_ratio,
        status=piece.status,
        output_path=piece.output_path,
        absolute_output_path=absolute_event_file_path(piece.event, piece.output_path),
        thumbnail_url=piece_thumbnail_url(piece),
        media_count=len(piece.media_items),
        copy_count=len(copies),
        approved_copy_count=sum(1 for copy in copies if copy.status == "approved"),
        created_at=piece.created_at,
        updated_at=piece.updated_at,
    )


def to_library_copy_item(copy: GeneratedCopy) -> LibraryCopyItem:
    piece = copy.piece
    return LibraryCopyItem(
        id=copy.id,
        piece_id=copy.piece_id,
        event_id=piece.event_id,
        event_name=piece.event.name,
        event_type=piece.event.event_type,
        event_date=piece.event.event_date,
        piece_title=piece.title,
        copy_type=copy.copy_type,
        variant_label=copy.variant_label,
        body_preview=copy.body.strip().replace("\n", " ")[:220],
        status=copy.status,
        output_path=copy.output_path,
        absolute_output_path=absolute_event_file_path(piece.event, copy.output_path),
        created_at=copy.created_at,
        updated_at=copy.updated_at,
    )


def piece_thumbnail_url(piece: ContentPiece) -> str | None:
    media_items = sorted(piece.media_items, key=lambda item: item.position)
    for item in media_items:
        if item.enhanced_media and item.enhanced_media.original_media:
            return original_thumbnail_url(item.enhanced_media.original_media)
    return None


def original_thumbnail_url(media: OriginalMedia) -> str | None:
    return f"/api/media/original/{media.id}/thumbnail" if media.thumbnail_path else None


def absolute_event_file_path(event: ContentEvent, relative_path: str | None) -> str | None:
    if not relative_path:
        return None
    path = Path(relative_path)
    if path.is_absolute():
        return str(path)
    if not event.root_path or not event.folder_name:
        return relative_path
    return str(Path(event.root_path) / event.folder_name / path)


def normalize_filter(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    return normalized or None
