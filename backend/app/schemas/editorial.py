from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class EditorialProfileResponse(BaseModel):
    id: int
    brand_id: int
    name: str
    tone: str
    emotional_level: str
    formality_level: str
    emoji_style: str
    description: str | None
    emoji_policy: str | None
    hashtags_base: str | None
    preferred_phrases: str | None
    words_to_avoid: str | None
    approved_examples: str | None
    rejected_examples: str | None
    copy_rules: str | None
    is_default: bool
    created_at: datetime
    updated_at: datetime


class EditorialProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    tone: str | None = Field(default=None, min_length=1, max_length=255)
    emotional_level: str | None = Field(default=None, min_length=1, max_length=40)
    formality_level: str | None = Field(default=None, min_length=1, max_length=40)
    emoji_style: str | None = Field(default=None, min_length=1, max_length=40)
    description: str | None = Field(default=None, max_length=2000)
    emoji_policy: str | None = Field(default=None, max_length=255)
    hashtags_base: str | None = Field(default=None, max_length=1000)
    preferred_phrases: str | None = Field(default=None, max_length=2000)
    words_to_avoid: str | None = Field(default=None, max_length=2000)
    approved_examples: str | None = Field(default=None, max_length=5000)
    rejected_examples: str | None = Field(default=None, max_length=5000)
    copy_rules: str | None = Field(default=None, max_length=3000)
