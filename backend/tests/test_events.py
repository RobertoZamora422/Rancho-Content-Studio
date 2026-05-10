from pathlib import Path

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.schemas.config import AppConfigUpdate
from app.services.config_service import update_app_config
from app.utils.event_folders import EVENT_SUBDIRECTORIES


def reset_workspace_root() -> None:
    with SessionLocal() as db:
        update_app_config(
            db,
            AppConfigUpdate(workspace_root=None, ffmpeg_path=None, exiftool_path=None),
        )


def set_workspace_root(path: Path) -> None:
    with SessionLocal() as db:
        update_app_config(
            db,
            AppConfigUpdate(workspace_root=str(path), ffmpeg_path=None, exiftool_path=None),
        )


def test_create_event_requires_configured_workspace_root() -> None:
    with TestClient(app) as client:
        reset_workspace_root()
        response = client.post(
            "/api/events",
            json={
                "name": "Boda Ana y Luis",
                "event_type": "Boda",
                "event_date": "2026-05-10",
            },
        )

    assert response.status_code == 400
    assert "carpeta raiz local" in response.json()["detail"]


def test_event_lifecycle_creates_folders_without_deleting_them(tmp_path) -> None:
    set_workspace_root(tmp_path)

    with TestClient(app) as client:
        create_response = client.post(
            "/api/events",
            json={
                "name": "Boda Ana y Luis",
                "event_type": "Boda",
                "event_date": "2026-05-10",
                "notes": "Evento de prueba",
            },
        )
        assert create_response.status_code == 201
        event = create_response.json()

        event_path = Path(event["event_path"])
        assert event["folder_name"] == "2026-05-10_Boda_Ana_y_Luis"
        assert event["status"] == "active"
        assert event_path.is_dir()
        for subdirectory in EVENT_SUBDIRECTORIES:
            assert (event_path / subdirectory).is_dir()

        list_response = client.get("/api/events")
        assert list_response.status_code == 200
        assert any(item["id"] == event["id"] for item in list_response.json()["items"])

        update_response = client.put(
            f"/api/events/{event['id']}",
            json={"name": "Boda Ana y Luis - Recepcion", "notes": "Actualizado"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Boda Ana y Luis - Recepcion"
        assert update_response.json()["folder_name"] == "2026-05-10_Boda_Ana_y_Luis"

        archive_response = client.post(f"/api/events/{event['id']}/archive")
        assert archive_response.status_code == 200
        assert archive_response.json()["status"] == "archived"

        archived_list_response = client.get("/api/events?include_archived=true")
        assert archived_list_response.status_code == 200
        assert any(
            item["id"] == event["id"] for item in archived_list_response.json()["items"]
        )

        delete_response = client.delete(f"/api/events/{event['id']}")
        assert delete_response.status_code == 200
        assert delete_response.json()["status"] == "deleted"
        assert event_path.is_dir()

        missing_response = client.get(f"/api/events/{event['id']}")
        assert missing_response.status_code == 404

    reset_workspace_root()
