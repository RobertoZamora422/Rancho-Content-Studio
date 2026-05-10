from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

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
            "name": "Boda Metadata",
            "event_type": "Boda",
            "event_date": "2026-05-10",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_process_metadata_and_thumbnails_uses_local_fallbacks(tmp_path) -> None:
    workspace_root = tmp_path / "workspace"
    source_root = tmp_path / "source"
    workspace_root.mkdir()
    source_root.mkdir()

    photo = source_root / "foto.jpg"
    Image.new("RGB", (64, 48), "#d9aa57").save(photo)
    video = source_root / "clip.mp4"
    video.write_bytes(b"not a real video, used to verify local placeholder fallback")
    original_photo_bytes = photo.read_bytes()
    original_video_bytes = video.read_bytes()

    with TestClient(app) as client:
        configure_workspace(client, workspace_root)
        event = create_event(client)

        source_response = client.post(
            f"/api/events/{event['id']}/sources",
            json={"source_path": str(source_root)},
        )
        assert source_response.status_code == 201

        import_response = client.post(f"/api/events/{event['id']}/import")
        assert import_response.status_code == 200
        assert import_response.json()["imported_files"] == 2

        process_response = client.post(f"/api/events/{event['id']}/process-metadata")
        assert process_response.status_code == 200
        process_payload = process_response.json()
        assert process_payload["metadata_updated"] == 2
        assert process_payload["metadata_failed"] == 0
        assert process_payload["thumbnails_generated"] == 2
        assert process_payload["thumbnail_failed"] == 0

        media_response = client.get(f"/api/events/{event['id']}/media/original")
        assert media_response.status_code == 200
        media_items = media_response.json()["items"]
        assert len(media_items) == 2
        assert all(item["capture_datetime"] for item in media_items)
        assert all(item["date_source"] == "file_modified_time" for item in media_items)
        assert all(item["thumbnail_path"] for item in media_items)
        assert all(item["thumbnail_url"] for item in media_items)
        assert all(item["metadata_json"] for item in media_items)

        photo_item = next(item for item in media_items if item["media_type"] == "image")
        assert photo_item["width"] == 64
        assert photo_item["height"] == 48

        event_path = Path(event["event_path"])
        for item in media_items:
            thumbnail_path = event_path / item["thumbnail_path"]
            assert thumbnail_path.is_file()
            thumbnail_response = client.get(item["thumbnail_url"])
            assert thumbnail_response.status_code == 200
            assert thumbnail_response.headers["content-type"] == "image/jpeg"

        jobs_response = client.get(f"/api/events/{event['id']}/jobs")
        assert jobs_response.status_code == 200
        job_types = {job["job_type"] for job in jobs_response.json()["items"]}
        assert {"write_metadata", "generate_thumbnails"} <= job_types

    assert photo.read_bytes() == original_photo_bytes
    assert video.read_bytes() == original_video_bytes
