from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.metadata_service import get_thumbnail_path

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/original/{media_id}/thumbnail")
def read_original_media_thumbnail(
    media_id: int,
    db: Session = Depends(get_db),
) -> FileResponse:
    thumbnail_path = get_thumbnail_path(db, media_id)
    return FileResponse(thumbnail_path, media_type="image/jpeg")
