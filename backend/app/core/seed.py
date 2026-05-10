from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.config_service import upsert_default_config
from app.services.seed_service import seed_reference_data


def seed_initial_config(db: Session) -> None:
    upsert_default_config(db)
    seed_reference_data(db)
