from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.visual_styles import VisualStylePresetListResponse
from app.services.visual_style_service import list_visual_style_presets

router = APIRouter(prefix="/visual-styles", tags=["visual-styles"])


@router.get("", response_model=VisualStylePresetListResponse)
def read_visual_style_presets(
    include_inactive: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> VisualStylePresetListResponse:
    return VisualStylePresetListResponse(
        items=list_visual_style_presets(db, include_inactive=include_inactive)
    )
