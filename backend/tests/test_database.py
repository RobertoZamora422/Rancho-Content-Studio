from sqlalchemy import text

from app.core.database import engine, init_database


def test_sqlite_pragmas_are_configured() -> None:
    init_database()

    with engine.connect() as connection:
        journal_mode = connection.execute(text("PRAGMA journal_mode")).scalar_one()
        foreign_keys = connection.execute(text("PRAGMA foreign_keys")).scalar_one()
        synchronous = connection.execute(text("PRAGMA synchronous")).scalar_one()

    assert str(journal_mode).lower() == "wal"
    assert foreign_keys == 1
    assert synchronous == 1
