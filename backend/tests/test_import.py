from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def configure_workspace(client: TestClient, workspace_root: Path) -> None:
    response = client.put(
        "/api/config",
        json={
            "workspace_root": str(workspace_root),
            "ffmpeg_path": None,
            "exiftool_path": None,
        },
    )
    assert response.status_code == 200


def create_event(client: TestClient) -> dict:
    response = client.post(
        "/api/events",
        json={
            "name": "Boda Importacion",
            "event_type": "Boda",
            "event_date": "2026-05-10",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_import_media_copies_supported_files_and_keeps_sources(tmp_path) -> None:
    workspace_root = tmp_path / "workspace"
    source_root = tmp_path / "source"
    workspace_root.mkdir()
    source_root.mkdir()

    photo = source_root / "Foto Principal.JPG"
    video = source_root / "baile.MP4"
    unsupported = source_root / "notas.txt"
    photo.write_bytes(b"fake image bytes")
    video.write_bytes(b"fake video bytes")
    unsupported.write_text("no importar", encoding="utf-8")
    original_photo_bytes = photo.read_bytes()

    with TestClient(app) as client:
        configure_workspace(client, workspace_root)
        event = create_event(client)

        source_response = client.post(
            f"/api/events/{event['id']}/sources",
            json={"source_path": str(source_root)},
        )
        assert source_response.status_code == 201
        source = source_response.json()
        assert source["status"] == "registered"

        scan_response = client.post(f"/api/events/{event['id']}/scan")
        assert scan_response.status_code == 200
        scan_payload = scan_response.json()
        assert scan_payload["supported_files"] == 2
        assert scan_payload["unsupported_files"] == 1

        import_response = client.post(f"/api/events/{event['id']}/import")
        assert import_response.status_code == 200
        import_payload = import_response.json()
        assert import_payload["imported_files"] == 2
        assert import_payload["skipped_files"] == 0
        assert import_payload["failed_files"] == 0

        media_response = client.get(f"/api/events/{event['id']}/media/original")
        assert media_response.status_code == 200
        media_items = media_response.json()["items"]
        assert len(media_items) == 2
        assert {item["media_type"] for item in media_items} == {"image", "video"}
        assert all(item["relative_path"].startswith("01_Originales") for item in media_items)

        event_path = Path(event["event_path"])
        assert (event_path / "01_Originales" / "Foto_Principal.jpg").exists()
        assert (event_path / "01_Originales" / "baile.mp4").exists()
        assert not (event_path / "01_Originales" / "notas.txt").exists()
        assert photo.read_bytes() == original_photo_bytes

        second_import_response = client.post(f"/api/events/{event['id']}/import")
        assert second_import_response.status_code == 200
        assert second_import_response.json()["imported_files"] == 0
        assert second_import_response.json()["skipped_files"] == 2

        jobs_response = client.get(f"/api/events/{event['id']}/jobs")
        assert jobs_response.status_code == 200
        jobs = jobs_response.json()["items"]
        assert any(job["job_type"] == "scan_folder" for job in jobs)
        assert any(job["job_type"] == "import_media" for job in jobs)

        job_id = import_payload["job_id"]
        job_response = client.get(f"/api/jobs/{job_id}")
        assert job_response.status_code == 200
        assert job_response.json()["status"] == "completed"


def test_source_inside_event_folder_is_rejected(tmp_path) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()

    with TestClient(app) as client:
        configure_workspace(client, workspace_root)
        event = create_event(client)

        response = client.post(
            f"/api/events/{event['id']}/sources",
            json={"source_path": event["event_path"]},
        )

    assert response.status_code == 400
    assert "fuera de la carpeta del evento" in response.json()["detail"]
