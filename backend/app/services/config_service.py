from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.local_app_config import LocalAppConfig


DEFAULT_CONFIG: tuple[tuple[str, str | None, str], ...] = (
    ("app.initialized", "true", "Marca que la base local fue inicializada."),
    ("workspace.root", None, "Carpeta raiz local elegida por el usuario."),
    ("tools.ffmpeg_path", None, "Ruta local a FFmpeg, pendiente de configurar."),
    ("tools.exiftool_path", None, "Ruta local a ExifTool, pendiente de configurar."),
)


def upsert_default_config(db: Session) -> None:
    for key, value, description in DEFAULT_CONFIG:
        existing = db.scalar(
            select(LocalAppConfig).where(LocalAppConfig.key == key)
        )
        if existing is None:
            db.add(
                LocalAppConfig(
                    key=key,
                    value=value,
                    description=description,
                )
            )
    db.commit()
