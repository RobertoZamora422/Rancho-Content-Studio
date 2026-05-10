from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    event_type: str | None = Field(default=None, max_length=80)
    event_date: date
    notes: str | None = None


class EventUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    event_type: str | None = Field(default=None, max_length=80)
    event_date: date | None = None
    notes: str | None = None


class EventResponse(BaseModel):
    id: int
    name: str
    event_type: str | None
    event_date: date | None
    folder_name: str | None
    root_path: str | None
    event_path: str | None
    status: str
    metadata_date_source: str | None
    notes: str | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class EventListResponse(BaseModel):
    items: list[EventResponse]
