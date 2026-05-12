from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.calendar import (
    CalendarItemCreate,
    CalendarItemListResponse,
    CalendarItemResponse,
    CalendarItemUpdate,
    CalendarMarkPublishedRequest,
)
from app.services.calendar_service import (
    cancel_calendar_item,
    create_calendar_item,
    list_calendar_items,
    mark_calendar_item_published,
    update_calendar_item,
)

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("", response_model=CalendarItemListResponse)
def read_calendar_items(
    event_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    platform: str | None = None,
    status: str | None = None,
    q: str | None = Query(default=None, max_length=160),
    db: Session = Depends(get_db),
) -> CalendarItemListResponse:
    return list_calendar_items(
        db,
        event_id=event_id,
        date_from=date_from,
        date_to=date_to,
        platform=platform,
        status_filter=status,
        query=q,
    )


@router.post("/items", response_model=CalendarItemResponse, status_code=201)
def create_new_calendar_item(
    payload: CalendarItemCreate,
    db: Session = Depends(get_db),
) -> CalendarItemResponse:
    return create_calendar_item(db, payload)


@router.put("/items/{item_id}", response_model=CalendarItemResponse)
def update_existing_calendar_item(
    item_id: int,
    payload: CalendarItemUpdate,
    db: Session = Depends(get_db),
) -> CalendarItemResponse:
    return update_calendar_item(db, item_id, payload)


@router.post("/items/{item_id}/mark-published", response_model=CalendarItemResponse)
def mark_item_published(
    item_id: int,
    payload: CalendarMarkPublishedRequest | None = None,
    db: Session = Depends(get_db),
) -> CalendarItemResponse:
    return mark_calendar_item_published(db, item_id, payload or CalendarMarkPublishedRequest())


@router.delete("/items/{item_id}", response_model=CalendarItemResponse)
def cancel_existing_calendar_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> CalendarItemResponse:
    return cancel_calendar_item(db, item_id)
