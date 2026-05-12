from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class LibraryMediaItem(BaseModel):
    id: int
    source_type: str
    event_id: int
    event_name: str
    event_type: str | None
    event_date: date | None
    title: str
    filename: str
    media_type: str
    file_type: str | None
    status: str
    local_path: str
    relative_path: str | None
    thumbnail_url: str | None
    file_exists: bool
    width: int | None
    height: int | None
    duration_seconds: float | None
    original_media_id: int | None
    curated_media_id: int | None
    enhanced_media_id: int | None
    created_at: datetime


class LibraryMediaListResponse(BaseModel):
    items: list[LibraryMediaItem]


class LibraryPieceItem(BaseModel):
    id: int
    event_id: int
    event_name: str
    event_type: str | None
    event_date: date | None
    piece_type: str
    title: str
    purpose: str | None
    target_platform: str | None
    aspect_ratio: str | None
    status: str
    output_path: str | None
    absolute_output_path: str | None
    thumbnail_url: str | None
    media_count: int
    copy_count: int
    approved_copy_count: int
    created_at: datetime
    updated_at: datetime


class LibraryPieceListResponse(BaseModel):
    items: list[LibraryPieceItem]


class LibraryCopyItem(BaseModel):
    id: int
    piece_id: int
    event_id: int
    event_name: str
    event_type: str | None
    event_date: date | None
    piece_title: str
    copy_type: str
    variant_label: str | None
    body_preview: str
    status: str
    output_path: str | None
    absolute_output_path: str | None
    created_at: datetime
    updated_at: datetime


class LibraryCopyListResponse(BaseModel):
    items: list[LibraryCopyItem]


class LibrarySearchItem(BaseModel):
    entity_type: str
    id: int
    event_id: int
    event_name: str
    title: str
    subtitle: str | None
    status: str
    date: date | datetime | None
    local_path: str | None
    thumbnail_url: str | None


class LibrarySearchResponse(BaseModel):
    items: list[LibrarySearchItem]
