from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.main import app
from app import models  # noqa: F401
from app.models.events import ContentEvent
from app.services.reset_service import reset_operational_data


def test_visual_styles_endpoint_returns_seed_presets() -> None:
    with TestClient(app) as client:
        response = client.get("/api/visual-styles")

    assert response.status_code == 200
    payload = response.json()
    slugs = {item["slug"] for item in payload["items"]}
    assert "natural_premium" in slugs
    assert "sobrio_corporativo" in slugs


def test_reset_operational_data_is_dry_run_by_default() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)

    with TestingSession() as db:
        db.add(ContentEvent(name="Evento temporal reset", event_type="Prueba"))
        db.commit()

        dry_run = reset_operational_data(db)
        assert dry_run.dry_run is True
        assert dry_run.deleted_counts["content_event"] >= 1
        assert db.scalar(select(ContentEvent).where(ContentEvent.name == "Evento temporal reset"))

        applied = reset_operational_data(db, dry_run=False)
        assert applied.dry_run is False
        assert db.scalar(select(ContentEvent).where(ContentEvent.name == "Evento temporal reset")) is None
