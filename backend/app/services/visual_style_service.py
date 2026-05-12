from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.identity import VisualStylePreset


def list_visual_style_presets(
    db: Session,
    *,
    include_inactive: bool = False,
) -> list[VisualStylePreset]:
    statement = select(VisualStylePreset).order_by(VisualStylePreset.name)
    if not include_inactive:
        statement = statement.where(VisualStylePreset.is_active.is_(True))
    return list(db.scalars(statement).all())
