from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CopyGenerationRequest(BaseModel):
    feedback: str | None = Field(default=None, max_length=80)


class GeneratedCopyResponse(BaseModel):
    id: int
    piece_id: int
    editorial_profile_id: int | None
    copy_type: str
    variant_label: str | None
    body: str
    hashtags_json: str | None
    cta: str | None
    style_notes: str | None
    status: str
    generation_mode: str
    ai_provider: str | None
    prompt_context: str | None
    user_feedback: str | None
    output_path: str | None
    warnings: list[str]
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None
    rejected_at: datetime | None


class GeneratedCopyListResponse(BaseModel):
    items: list[GeneratedCopyResponse]


class CopyGenerationResponse(BaseModel):
    job_id: int
    piece_id: int
    copies_created: int
    feedback: str | None
    items: list[GeneratedCopyResponse]


class GeneratedCopyUpdate(BaseModel):
    body: str | None = Field(default=None, min_length=1, max_length=5000)
    status: str | None = Field(default=None, min_length=1, max_length=40)
    user_feedback: str | None = Field(default=None, max_length=80)
    variant_label: str | None = Field(default=None, max_length=120)
