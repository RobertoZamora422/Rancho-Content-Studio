from __future__ import annotations

from datetime import date, datetime, time, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.content import ContentPiece, ContentPieceMedia, PublishingCalendarItem
from app.models.events import ContentEvent
from app.models.jobs import DecisionLog
from app.models.media import EnhancedMedia
from app.schemas.calendar import (
    CalendarEventSummary,
    CalendarItemCreate,
    CalendarItemListResponse,
    CalendarItemResponse,
    CalendarItemUpdate,
    CalendarMarkPublishedRequest,
    CalendarPieceSummary,
)

ALLOWED_PLATFORMS = {
    "instagram",
    "facebook",
    "tiktok",
    "whatsapp_business",
    "google_photos",
    "multiple",
    "other",
}
ALLOWED_STATUSES = {
    "not_scheduled",
    "scheduled",
    "ready_to_publish",
    "published",
    "cancelled",
}


def list_calendar_items(
    db: Session,
    event_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    platform: str | None = None,
    status_filter: str | None = None,
    query: str | None = None,
) -> CalendarItemListResponse:
    statement = (
        select(PublishingCalendarItem)
        .outerjoin(PublishingCalendarItem.event)
        .outerjoin(PublishingCalendarItem.piece)
        .where(or_(ContentEvent.id.is_(None), ContentEvent.status != "deleted"))
        .options(*calendar_load_options())
        .order_by(
            PublishingCalendarItem.scheduled_for.is_(None),
            PublishingCalendarItem.scheduled_for.asc(),
            PublishingCalendarItem.created_at.desc(),
        )
    )
    if event_id is not None:
        statement = statement.where(PublishingCalendarItem.event_id == event_id)
    if date_from is not None:
        statement = statement.where(func.date(PublishingCalendarItem.scheduled_for) >= date_from.isoformat())
    if date_to is not None:
        statement = statement.where(func.date(PublishingCalendarItem.scheduled_for) <= date_to.isoformat())
    normalized_platform = normalize_key(platform)
    if normalized_platform:
        validate_platform(normalized_platform)
        statement = statement.where(PublishingCalendarItem.platform == normalized_platform)
    normalized_status = normalize_key(status_filter)
    if normalized_status:
        validate_status(normalized_status)
        statement = statement.where(PublishingCalendarItem.status == normalized_status)
    normalized_query = normalize_key(query)
    if normalized_query:
        like = f"%{normalized_query}%"
        statement = statement.where(
            or_(
                func.lower(PublishingCalendarItem.title).like(like),
                func.lower(PublishingCalendarItem.notes).like(like),
                func.lower(ContentPiece.title).like(like),
                func.lower(ContentEvent.name).like(like),
            )
        )

    items = db.scalars(statement).all()
    return CalendarItemListResponse(items=[to_calendar_item_response(item) for item in items])


def create_calendar_item(db: Session, payload: CalendarItemCreate) -> CalendarItemResponse:
    piece = require_schedulable_piece(db, payload.piece_id)
    next_status = normalize_status(payload.status)
    scheduled_for = build_scheduled_for(payload.scheduled_date, payload.scheduled_time, next_status)
    platform = normalize_platform(payload.platform)
    title = normalize_title(payload.title) or piece.title

    item = PublishingCalendarItem(
        event_id=piece.event_id,
        piece_id=piece.id,
        title=title,
        platform=platform,
        scheduled_for=scheduled_for,
        status=next_status,
        published_url=normalize_text(payload.published_url),
        notes=normalize_text(payload.notes),
    )
    if next_status == "published":
        item.published_at = datetime.now(timezone.utc)
    db.add(item)
    db.flush()
    db.add(
        DecisionLog(
            event_id=piece.event_id,
            entity_type="calendar_item",
            entity_id=item.id,
            decision_type="calendar_scheduled",
            reason=f"Pieza #{piece.id} planificada en {platform}.",
            actor="user",
        )
    )
    db.commit()
    return get_calendar_item_response(db, item.id)


def update_calendar_item(
    db: Session,
    item_id: int,
    payload: CalendarItemUpdate,
) -> CalendarItemResponse:
    item = require_calendar_item(db, item_id)
    previous_status = item.status
    fields_set = payload.model_fields_set

    if payload.piece_id is not None and payload.piece_id != item.piece_id:
        piece = require_schedulable_piece(db, payload.piece_id)
        item.piece_id = piece.id
        item.event_id = piece.event_id
        item.title = item.title or piece.title

    if "title" in fields_set:
        item.title = normalize_title(payload.title) or item.title
    if payload.platform is not None:
        item.platform = normalize_platform(payload.platform)
    if payload.status is not None:
        item.status = normalize_status(payload.status)
    if "published_url" in fields_set:
        item.published_url = normalize_text(payload.published_url)
    if "notes" in fields_set:
        item.notes = normalize_text(payload.notes)
    if "scheduled_date" in fields_set or "scheduled_time" in fields_set or payload.status is not None:
        next_date = (
            payload.scheduled_date
            if "scheduled_date" in fields_set
            else item.scheduled_for.date()
            if item.scheduled_for
            else None
        )
        next_time = (
            payload.scheduled_time
            if "scheduled_time" in fields_set
            else item.scheduled_for.time().replace(second=0, microsecond=0)
            if item.scheduled_for
            else None
        )
        item.scheduled_for = build_scheduled_for(next_date, next_time, item.status)

    if item.status == "published" and item.published_at is None:
        item.published_at = datetime.now(timezone.utc)
    if item.status != "published":
        item.published_at = None

    item.updated_at = datetime.now(timezone.utc)
    db.add(
        DecisionLog(
            event_id=item.event_id,
            entity_type="calendar_item",
            entity_id=item.id,
            decision_type="calendar_updated",
            reason=f"{previous_status} -> {item.status}.",
            actor="user",
        )
    )
    db.commit()
    return get_calendar_item_response(db, item.id)


def mark_calendar_item_published(
    db: Session,
    item_id: int,
    payload: CalendarMarkPublishedRequest,
) -> CalendarItemResponse:
    item = require_calendar_item(db, item_id)
    item.status = "published"
    item.published_at = datetime.now(timezone.utc)
    if payload.published_url is not None:
        item.published_url = normalize_text(payload.published_url)
    if payload.notes is not None:
        item.notes = normalize_text(payload.notes)
    item.updated_at = datetime.now(timezone.utc)
    db.add(
        DecisionLog(
            event_id=item.event_id,
            entity_type="calendar_item",
            entity_id=item.id,
            decision_type="calendar_published",
            reason="Publicacion marcada manualmente como publicada.",
            actor="user",
        )
    )
    db.commit()
    return get_calendar_item_response(db, item.id)


def cancel_calendar_item(db: Session, item_id: int) -> CalendarItemResponse:
    item = require_calendar_item(db, item_id)
    item.status = "cancelled"
    item.updated_at = datetime.now(timezone.utc)
    db.add(
        DecisionLog(
            event_id=item.event_id,
            entity_type="calendar_item",
            entity_id=item.id,
            decision_type="calendar_cancelled",
            reason="Programacion cancelada logicamente; no se elimina contenido.",
            actor="user",
        )
    )
    db.commit()
    return get_calendar_item_response(db, item.id)


def require_calendar_item(db: Session, item_id: int) -> PublishingCalendarItem:
    item = db.scalar(
        select(PublishingCalendarItem)
        .where(PublishingCalendarItem.id == item_id)
        .options(*calendar_load_options())
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item de calendario no encontrado.")
    return item


def require_schedulable_piece(db: Session, piece_id: int) -> ContentPiece:
    piece = db.scalar(
        select(ContentPiece)
        .where(ContentPiece.id == piece_id)
        .options(
            selectinload(ContentPiece.event),
            selectinload(ContentPiece.media_items)
            .selectinload(ContentPieceMedia.enhanced_media)
            .selectinload(EnhancedMedia.original_media),
        )
    )
    if piece is None or piece.event.status == "deleted":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pieza no encontrada.")
    if piece.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden planificar piezas aprobadas.",
        )
    return piece


def get_calendar_item_response(db: Session, item_id: int) -> CalendarItemResponse:
    item = require_calendar_item(db, item_id)
    return to_calendar_item_response(item)


def calendar_load_options():
    return (
        selectinload(PublishingCalendarItem.event),
        selectinload(PublishingCalendarItem.piece).selectinload(ContentPiece.event),
        selectinload(PublishingCalendarItem.piece)
        .selectinload(ContentPiece.media_items)
        .selectinload(ContentPieceMedia.enhanced_media)
        .selectinload(EnhancedMedia.original_media),
    )


def to_calendar_item_response(item: PublishingCalendarItem) -> CalendarItemResponse:
    scheduled_date = item.scheduled_for.date() if item.scheduled_for else None
    scheduled_time = item.scheduled_for.strftime("%H:%M") if item.scheduled_for else None
    event = item.event or (item.piece.event if item.piece else None)
    return CalendarItemResponse(
        id=item.id,
        event_id=item.event_id,
        piece_id=item.piece_id,
        title=item.title,
        platform=item.platform,
        scheduled_for=item.scheduled_for,
        scheduled_date=scheduled_date,
        scheduled_time=scheduled_time,
        status=item.status,
        published_at=item.published_at,
        published_url=item.published_url,
        notes=item.notes,
        created_at=item.created_at,
        updated_at=item.updated_at,
        event=(
            CalendarEventSummary(
                id=event.id,
                name=event.name,
                event_type=event.event_type,
                event_date=event.event_date,
            )
            if event
            else None
        ),
        piece=(
            CalendarPieceSummary(
                id=item.piece.id,
                title=item.piece.title,
                piece_type=item.piece.piece_type,
                target_platform=item.piece.target_platform,
                status=item.piece.status,
                thumbnail_url=piece_thumbnail_url(item.piece),
            )
            if item.piece
            else None
        ),
    )


def build_scheduled_for(
    scheduled_date: date | None,
    scheduled_time: time | None,
    status_value: str,
) -> datetime | None:
    if status_value in {"scheduled", "ready_to_publish"} and scheduled_date is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha programada es obligatoria para este estado.",
        )
    if scheduled_date is None:
        return None
    normalized_time = scheduled_time or time(hour=9, minute=0)
    return datetime.combine(
        scheduled_date,
        normalized_time.replace(second=0, microsecond=0),
        tzinfo=timezone.utc,
    )


def piece_thumbnail_url(piece: ContentPiece) -> str | None:
    for media_item in sorted(piece.media_items, key=lambda item: item.position):
        media = media_item.enhanced_media.original_media if media_item.enhanced_media else None
        if media and media.thumbnail_path:
            return f"/api/media/original/{media.id}/thumbnail"
    return None


def normalize_platform(value: str) -> str:
    normalized = normalize_key(value)
    if normalized is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La plataforma es obligatoria.")
    validate_platform(normalized)
    return normalized


def validate_platform(value: str) -> None:
    if value not in ALLOWED_PLATFORMS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plataforma no permitida.")


def normalize_status(value: str) -> str:
    normalized = normalize_key(value) or "not_scheduled"
    if normalized == "planned":
        normalized = "not_scheduled"
    validate_status(normalized)
    return normalized


def validate_status(value: str) -> None:
    if value not in ALLOWED_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Estado de publicacion no permitido.")


def normalize_title(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def normalize_key(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    return normalized or None


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None
