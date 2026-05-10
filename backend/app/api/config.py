from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.config import AppConfigResponse, AppConfigUpdate, ConfigValidationResponse
from app.services.config_service import get_app_config, update_app_config, validate_current_config

router = APIRouter(prefix="/config", tags=["config"])


@router.get("", response_model=AppConfigResponse)
def read_config(db: Session = Depends(get_db)) -> AppConfigResponse:
    return get_app_config(db)


@router.put("", response_model=AppConfigResponse)
def write_config(
    payload: AppConfigUpdate,
    db: Session = Depends(get_db),
) -> AppConfigResponse:
    return update_app_config(db, payload)


@router.post("/validate-tools", response_model=ConfigValidationResponse)
def validate_tools(db: Session = Depends(get_db)) -> ConfigValidationResponse:
    return validate_current_config(db)
