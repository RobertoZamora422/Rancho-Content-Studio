from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.editorial import EditorialProfileResponse, EditorialProfileUpdate
from app.services.editorial_profile_service import (
    get_default_editorial_profile,
    update_default_editorial_profile,
)

router = APIRouter(prefix="/editorial-profile", tags=["editorial-profile"])


@router.get("/default", response_model=EditorialProfileResponse)
def read_default_editorial_profile(db: Session = Depends(get_db)) -> EditorialProfileResponse:
    return get_default_editorial_profile(db)


@router.put("/default", response_model=EditorialProfileResponse)
def update_default_profile(
    payload: EditorialProfileUpdate,
    db: Session = Depends(get_db),
) -> EditorialProfileResponse:
    return update_default_editorial_profile(db, payload)
