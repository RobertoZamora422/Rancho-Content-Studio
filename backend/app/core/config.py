from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = BACKEND_ROOT / "data" / "rancho_content_studio.sqlite3"


@dataclass(frozen=True)
class Settings:
    app_name: str = "Rancho Content Studio"
    app_version: str = "0.1.0"
    database_path: Path = DEFAULT_DB_PATH

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path.as_posix()}"


def _resolve_database_path() -> Path:
    configured_path = os.getenv("RANCHO_STUDIO_DB_PATH")
    if not configured_path:
        return DEFAULT_DB_PATH
    return Path(configured_path).expanduser().resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(database_path=_resolve_database_path())
