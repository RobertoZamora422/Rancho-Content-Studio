from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
settings.database_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    future=True,
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragmas(dbapi_connection, _) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)


def init_database() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_incremental_schema()


def ensure_incremental_schema() -> None:
    """Apply small additive schema changes until Alembic is introduced."""
    with engine.begin() as connection:
        media_columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(original_media)")).all()
        }
        if "metadata_json" not in media_columns:
            connection.execute(text("ALTER TABLE original_media ADD COLUMN metadata_json TEXT"))

        editorial_columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(editorial_profile)")).all()
        }
        editorial_additions = {
            "emotional_level": "TEXT NOT NULL DEFAULT 'moderado'",
            "formality_level": "TEXT NOT NULL DEFAULT 'semi_formal'",
            "emoji_style": "TEXT NOT NULL DEFAULT 'sutil'",
            "approved_examples": "TEXT",
            "rejected_examples": "TEXT",
            "copy_rules": "TEXT",
        }
        for column, definition in editorial_additions.items():
            if column not in editorial_columns:
                connection.execute(
                    text(f"ALTER TABLE editorial_profile ADD COLUMN {column} {definition}")
                )

        copy_columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(generated_copy)")).all()
        }
        copy_additions = {
            "copy_type": "TEXT NOT NULL DEFAULT 'caption'",
            "hashtags_json": "TEXT",
            "cta": "TEXT",
            "style_notes": "TEXT",
            "user_feedback": "TEXT",
            "output_path": "TEXT",
        }
        for column, definition in copy_additions.items():
            if column not in copy_columns:
                connection.execute(
                    text(f"ALTER TABLE generated_copy ADD COLUMN {column} {definition}")
                )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
