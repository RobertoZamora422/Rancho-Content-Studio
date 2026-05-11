from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.importing import EnhancedMediaResponse


class PieceGenerationResponse(BaseModel):
    job_id: int
    total_available_media: int
    pieces_created: int
    pieces_skipped: int


class ContentPieceMediaResponse(BaseModel):
    id: int
    piece_id: int
    original_media_id: int | None
    enhanced_media_id: int | None
    position: int
    role: str | None
    notes: str | None
    enhanced_media: EnhancedMediaResponse | None


class ContentPieceResponse(BaseModel):
    id: int
    event_id: int
    piece_type: str
    title: str
    purpose: str | None
    target_platform: str | None
    aspect_ratio: str | None
    output_path: str | None
    status: str
    metadata_json: str | None
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None
    rejected_at: datetime | None
    media_items: list[ContentPieceMediaResponse]


class ContentPieceListResponse(BaseModel):
    items: list[ContentPieceResponse]


class ContentPieceUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=220)
    purpose: str | None = Field(default=None, max_length=160)
    target_platform: str | None = Field(default=None, max_length=80)
    aspect_ratio: str | None = Field(default=None, max_length=30)
    status: str | None = Field(default=None, min_length=1, max_length=40)
    media_item_order: list[int] | None = None
