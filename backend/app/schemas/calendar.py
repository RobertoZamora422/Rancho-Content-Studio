from __future__ import annotations

from datetime import date, datetime, time

from pydantic import BaseModel, Field


class CalendarItemCreate(BaseModel):
    piece_id: int
    scheduled_date: date | None = None
    scheduled_time: time | None = None
    platform: str = Field(min_length=1, max_length=80)
    status: str = Field(default="scheduled", min_length=1, max_length=40)
    title: str | None = Field(default=None, max_length=220)
    published_url: str | None = Field(default=None, max_length=1024)
    notes: str | None = Field(default=None, max_length=2000)


class CalendarItemUpdate(BaseModel):
    piece_id: int | None = None
    scheduled_date: date | None = None
    scheduled_time: time | None = None
    platform: str | None = Field(default=None, max_length=80)
    status: str | None = Field(default=None, max_length=40)
    title: str | None = Field(default=None, max_length=220)
    published_url: str | None = Field(default=None, max_length=1024)
    notes: str | None = Field(default=None, max_length=2000)


class CalendarMarkPublishedRequest(BaseModel):
    published_url: str | None = Field(default=None, max_length=1024)
    notes: str | None = Field(default=None, max_length=2000)


class CalendarPieceSummary(BaseModel):
    id: int
    title: str
    piece_type: str
    target_platform: str | None
    status: str
    thumbnail_url: str | None


class CalendarEventSummary(BaseModel):
    id: int
    name: str
    event_type: str | None
    event_date: date | None


class CalendarItemResponse(BaseModel):
    id: int
    event_id: int | None
    piece_id: int | None
    title: str
    platform: str | None
    scheduled_for: datetime | None
    scheduled_date: date | None
    scheduled_time: str | None
    status: str
    published_at: datetime | None
    published_url: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    event: CalendarEventSummary | None
    piece: CalendarPieceSummary | None


class CalendarItemListResponse(BaseModel):
    items: list[CalendarItemResponse]
