from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFilter

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
            "name": "Boda Analisis",
            "event_type": "Boda",
            "event_date": "2026-05-10",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_sharp_sample(path: Path) -> None:
    image = Image.new("RGB", (160, 120), "#d9aa57")
    draw = ImageDraw.Draw(image)
    for x in range(0, 160, 16):
        draw.line((x, 0, x, 119), fill="#202722", width=2)
    for y in range(0, 120, 16):
        draw.line((0, y, 159, y), fill="#f7f2e9", width=2)
    image.save(path)


def test_analyze_photos_creates_media_analysis_and_skips_videos(tmp_path) -> None:
    workspace_root = tmp_path / "workspace"
    source_root = tmp_path / "source"
    workspace_root.mkdir()
    source_root.mkdir()

    sharp_photo = source_root / "foto_nitida.jpg"
    blurry_photo = source_root / "foto_borrosa.jpg"
    video = source_root / "clip.mp4"
    create_sharp_sample(sharp_photo)
    Image.open(sharp_photo).filter(ImageFilter.GaussianBlur(radius=5)).save(blurry_photo)
    video.write_bytes(b"fake video")
    original_photo_bytes = sharp_photo.read_bytes()

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
        assert import_response.json()["imported_files"] == 3

        analysis_response = client.post(f"/api/events/{event['id']}/analyze-photos")
        assert analysis_response.status_code == 200
        analysis_payload = analysis_response.json()
        assert analysis_payload["total_photos"] == 2
        assert analysis_payload["analyzed_photos"] == 2
        assert analysis_payload["failed_photos"] == 0
        assert analysis_payload["skipped_non_images"] == 1

        media_response = client.get(f"/api/events/{event['id']}/media/original")
        assert media_response.status_code == 200
        media_items = media_response.json()["items"]
        photos = [item for item in media_items if item["media_type"] == "image"]
        assert len(photos) == 2
        assert all(item["analysis"] for item in photos)
        assert all(item["analysis"]["perceptual_hash"] for item in photos)
        assert all(
            0 <= item["analysis"]["overall_quality_score"] <= 100
            for item in photos
        )

        sharp_item = next(item for item in photos if item["filename"].startswith("foto_nitida"))
        blurry_item = next(item for item in photos if item["filename"].startswith("foto_borrosa"))
        assert sharp_item["analysis"]["sharpness_score"] > blurry_item["analysis"]["sharpness_score"]

        video_item = next(item for item in media_items if item["media_type"] == "video")
        assert video_item["analysis"] is None

        jobs_response = client.get(f"/api/events/{event['id']}/jobs")
        assert jobs_response.status_code == 200
        assert any(job["job_type"] == "analyze_media" for job in jobs_response.json()["items"])

    assert sharp_photo.read_bytes() == original_photo_bytes
