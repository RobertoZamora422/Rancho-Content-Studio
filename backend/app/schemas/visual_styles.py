from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class VisualStylePresetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    description: str | None
    is_active: bool


class VisualStylePresetListResponse(BaseModel):
    items: list[VisualStylePresetResponse]
