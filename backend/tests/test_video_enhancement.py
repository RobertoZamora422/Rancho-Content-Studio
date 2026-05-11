from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def configure_workspace(client: TestClient, workspace_root: Path, ffmpeg_path: Path) -> None:
    response = client.put(
        "/api/config",
        json={
            "workspace_root": str(workspace_root),
            "ffmpeg_path": str(ffmpeg_path),
            "exiftool_path": None,
        },
    )
    assert response.status_code == 200


def create_event(client: TestClient) -> dict:
    response = client.post(
        "/api/events",
        json={
            "name": "Boda Video",
            "event_type": "Boda",
            "event_date": "2026-05-10",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_enhance_videos_reports_missing_ffmpeg_without_touching_originals(tmp_path) -> None:
    workspace_root = tmp_path / "workspace"
    source_root = tmp_path / "source"
    missing_ffmpeg = tmp_path / "missing_ffmpeg.exe"
    workspace_root.mkdir()
    source_root.mkdir()

    video = source_root / "baile.mp4"
    video.write_bytes(b"fake video bytes for graceful ffmpeg validation")
    source_video_bytes = video.read_bytes()

    with TestClient(app) as client:
        configure_workspace(client, workspace_root, missing_ffmpeg)
        event = create_event(client)

        source_response = client.post(
            f"/api/events/{event['id']}/sources",
            json={"source_path": str(source_root)},
        )
        assert source_response.status_code == 201

        import_response = client.post(f"/api/events/{event['id']}/import")
        assert import_response.status_code == 200
        assert import_response.json()["imported_files"] == 1

        media_response = client.get(f"/api/events/{event['id']}/media/original")
        media_item = media_response.json()["items"][0]
        imported_original_path = Path(media_item["original_path"])
        imported_original_bytes = imported_original_path.read_bytes()

        curate_response = client.post(f"/api/events/{event['id']}/curate-media")
        assert curate_response.status_code == 200

        curated_response = client.get(f"/api/events/{event['id']}/curated-media")
        curated_item = curated_response.json()["items"][0]
        patch_response = client.patch(
            f"/api/events/{event['id']}/curated-media/{curated_item['id']}",
            json={
                "selection_status": "user_selected",
                "reason": "Video seleccionado manualmente para probar Fase 11.",
            },
        )
        assert patch_response.status_code == 200

        enhancement_response = client.post(
            f"/api/events/{event['id']}/enhance-videos",
            json={
                "preset_slug": "natural_premium",
                "processing_mode": "auto",
                "max_full_duration_seconds": 90,
                "clip_duration_seconds": 30,
            },
        )
        assert enhancement_response.status_code == 200
        payload = enhancement_response.json()
        assert payload["ffmpeg_available"] is False
        assert payload["total_selected"] == 1
        assert payload["enhanced"] == 0
        assert payload["failed"] == 1

        enhanced_response = client.get(f"/api/events/{event['id']}/enhanced-media")
        assert enhanced_response.status_code == 200
        assert enhanced_response.json()["items"] == []

        jobs_response = client.get(f"/api/events/{event['id']}/jobs")
        assert jobs_response.status_code == 200
        jobs = jobs_response.json()["items"]
        video_job = next(job for job in jobs if job["job_type"] == "enhance_videos")
        assert video_job["status"] == "completed_with_errors"
        assert video_job["failed_items"] == 1
        assert any("FFmpeg no disponible" in log["message"] for log in video_job["logs"])

    assert video.read_bytes() == source_video_bytes
    assert imported_original_path.read_bytes() == imported_original_bytes
