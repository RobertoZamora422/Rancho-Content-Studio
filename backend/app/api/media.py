from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.enhancement_service import get_enhanced_media_file_path
from app.services.metadata_service import get_thumbnail_path

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/original/{media_id}/thumbnail")
def read_original_media_thumbnail(
    media_id: int,
    db: Session = Depends(get_db),
) -> FileResponse:
    thumbnail_path = get_thumbnail_path(db, media_id)
    return FileResponse(thumbnail_path, media_type="image/jpeg")


@router.get("/enhanced/{enhanced_id}/file")
def read_enhanced_media_file(
    enhanced_id: int,
    db: Session = Depends(get_db),
) -> FileResponse:
    output_path = get_enhanced_media_file_path(db, enhanced_id)
    return FileResponse(output_path, media_type="image/jpeg")
