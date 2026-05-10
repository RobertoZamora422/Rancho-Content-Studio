from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.events import EventCreate, EventListResponse, EventResponse, EventUpdate
from app.services.event_service import (
    archive_event,
    create_event,
    get_event,
    list_events,
    logically_delete_event,
    update_event,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=EventListResponse)
def read_events(
    include_archived: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> EventListResponse:
    return EventListResponse(items=list_events(db, include_archived=include_archived))


@router.post("", response_model=EventResponse, status_code=201)
def create_new_event(payload: EventCreate, db: Session = Depends(get_db)) -> EventResponse:
    return create_event(db, payload)


@router.get("/{event_id}", response_model=EventResponse)
def read_event(event_id: int, db: Session = Depends(get_db)) -> EventResponse:
    return get_event(db, event_id)


@router.put("/{event_id}", response_model=EventResponse)
def update_existing_event(
    event_id: int,
    payload: EventUpdate,
    db: Session = Depends(get_db),
) -> EventResponse:
    return update_event(db, event_id, payload)


@router.delete("/{event_id}", response_model=EventResponse)
def delete_existing_event(event_id: int, db: Session = Depends(get_db)) -> EventResponse:
    return logically_delete_event(db, event_id)


@router.post("/{event_id}/archive", response_model=EventResponse)
def archive_existing_event(event_id: int, db: Session = Depends(get_db)) -> EventResponse:
    return archive_event(db, event_id)
