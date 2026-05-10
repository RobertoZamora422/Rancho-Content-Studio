from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.events import ContentEvent
from app.models.identity import Brand, User
from app.schemas.events import EventCreate, EventResponse, EventUpdate
from app.services.config_service import get_app_config
from app.utils.event_folders import build_event_folder_name, create_event_directory_tree


def list_events(db: Session, include_archived: bool = False) -> list[EventResponse]:
    statement = select(ContentEvent).where(ContentEvent.status != "deleted")
    if not include_archived:
        statement = statement.where(ContentEvent.status != "archived")
    statement = statement.order_by(ContentEvent.event_date.desc(), ContentEvent.created_at.desc())

    return [to_event_response(event) for event in db.scalars(statement).all()]


def create_event(db: Session, payload: EventCreate) -> EventResponse:
    workspace_root = resolve_workspace_root(db)
    folder_name = build_event_folder_name(payload.event_date, payload.name)
    event_path = create_event_directory_tree(workspace_root, folder_name)

    event = ContentEvent(
        brand_id=get_default_brand_id(db),
        created_by_user_id=get_admin_user_id(db),
        name=payload.name.strip(),
        event_type=normalize_optional_text(payload.event_type),
        event_date=payload.event_date,
        folder_name=event_path.name,
        root_path=str(workspace_root),
        status="active",
        metadata_date_source="event_date",
        notes=normalize_optional_text(payload.notes),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return to_event_response(event)


def get_event(db: Session, event_id: int) -> EventResponse:
    return to_event_response(require_event(db, event_id))


def update_event(db: Session, event_id: int, payload: EventUpdate) -> EventResponse:
    event = require_event(db, event_id)
    if event.status == "deleted":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado.")

    if payload.name is not None:
        event.name = payload.name.strip()
    if payload.event_type is not None:
        event.event_type = normalize_optional_text(payload.event_type)
    if payload.event_date is not None:
        event.event_date = payload.event_date
        event.metadata_date_source = "event_date"
    if payload.notes is not None:
        event.notes = normalize_optional_text(payload.notes)

    db.commit()
    db.refresh(event)
    return to_event_response(event)


def archive_event(db: Session, event_id: int) -> EventResponse:
    event = require_event(db, event_id)
    event.status = "archived"
    event.archived_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(event)
    return to_event_response(event)


def logically_delete_event(db: Session, event_id: int) -> EventResponse:
    event = require_event(db, event_id)
    event.status = "deleted"
    event.archived_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(event)
    return to_event_response(event)


def require_event(db: Session, event_id: int) -> ContentEvent:
    event = db.get(ContentEvent, event_id)
    if event is None or event.status == "deleted":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado.")
    return event


def resolve_workspace_root(db: Session) -> Path:
    config = get_app_config(db)
    if not config.workspace_root:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configura una carpeta raiz local antes de crear eventos.",
        )

    root_path = Path(config.workspace_root).expanduser()
    if not root_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No existe la carpeta raiz local: {config.workspace_root}",
        )

    return root_path.resolve()


def normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def get_default_brand_id(db: Session) -> int | None:
    brand = db.scalar(select(Brand).where(Brand.name == "Rancho Flor Maria"))
    return brand.id if brand else None


def get_admin_user_id(db: Session) -> int | None:
    user = db.scalar(select(User).where(User.username == "admin"))
    return user.id if user else None


def to_event_response(event: ContentEvent) -> EventResponse:
    event_path = None
    if event.root_path and event.folder_name:
        event_path = str(Path(event.root_path) / event.folder_name)

    return EventResponse(
        id=event.id,
        name=event.name,
        event_type=event.event_type,
        event_date=event.event_date,
        folder_name=event.folder_name,
        root_path=event.root_path,
        event_path=event_path,
        status=event.status,
        metadata_date_source=event.metadata_date_source,
        notes=event.notes,
        archived_at=event.archived_at,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )
