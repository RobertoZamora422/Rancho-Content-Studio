import shutil
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app.core.database import SessionLocal
from app.main import app
from app.models.media import OriginalMedia


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
            "name": "Boda Similares",
            "event_type": "Boda",
            "event_date": "2026-05-10",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_similar_photo(path: Path, accent: str) -> None:
    image = Image.new("RGB", (180, 120), "#f7f2e9")
    draw = ImageDraw.Draw(image)
    draw.rectangle((24, 20, 156, 100), outline="#202722", width=4)
    draw.ellipse((52, 30, 92, 70), fill=accent)
    draw.rectangle((104, 42, 140, 88), fill="#d9aa57")
    image.save(path, quality=88)


def add_checksum_duplicate(media_payload: dict) -> None:
    original_path = Path(media_payload["original_path"])
    duplicate_path = original_path.with_name(f"{original_path.stem}_manual_copy{original_path.suffix}")
    shutil.copy2(original_path, duplicate_path)

    capture_datetime = media_payload["capture_datetime"]
    if capture_datetime:
        capture_datetime = datetime.fromisoformat(capture_datetime)

    with SessionLocal() as db:
        db.add(
            OriginalMedia(
                event_id=media_payload["event_id"],
                source_id=media_payload["source_id"],
                original_path=str(duplicate_path),
                relative_path=str(Path(media_payload["relative_path"]).with_name(duplicate_path.name)),
                filename=duplicate_path.name,
                extension=duplicate_path.suffix.lower(),
                media_type=media_payload["media_type"],
                mime_type=media_payload["mime_type"],
                file_size_bytes=duplicate_path.stat().st_size,
                checksum_sha256=media_payload["checksum_sha256"],
                capture_datetime=capture_datetime,
                date_source=media_payload["date_source"],
                width=media_payload["width"],
                height=media_payload["height"],
                thumbnail_path=None,
                metadata_json=media_payload["metadata_json"],
                status="imported",
                original_exists=True,
            )
        )
        db.commit()


def test_detect_similarity_creates_visual_and_checksum_groups(tmp_path) -> None:
    workspace_root = tmp_path / "workspace"
    source_root = tmp_path / "source"
    workspace_root.mkdir()
    source_root.mkdir()

    first_photo = source_root / "momento_1.jpg"
    second_photo = source_root / "momento_2.jpg"
    create_similar_photo(first_photo, "#9a6a14")
    create_similar_photo(second_photo, "#9f6f18")
    original_photo_bytes = first_photo.read_bytes()

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

        analysis_response = client.post(f"/api/events/{event['id']}/analyze-photos")
        assert analysis_response.status_code == 200
        assert analysis_response.json()["analyzed_photos"] == 2

        media_response = client.get(f"/api/events/{event['id']}/media/original")
        assert media_response.status_code == 200
        media_items = media_response.json()["items"]
        assert len(media_items) == 2
        add_checksum_duplicate(media_items[0])

        detection_response = client.post(f"/api/events/{event['id']}/detect-similarity")
        assert detection_response.status_code == 200
        detection_payload = detection_response.json()
        assert detection_payload["exact_groups"] == 1
        assert detection_payload["similar_groups"] >= 1
        assert detection_payload["grouped_items"] >= 4

        groups_response = client.get(f"/api/events/{event['id']}/similarity-groups")
        assert groups_response.status_code == 200
        groups = groups_response.json()["items"]
        assert any(group["group_type"] == "checksum_duplicate" for group in groups)
        assert any(group["group_type"] == "perceptual_hash" for group in groups)
        assert all(len(group["items"]) >= 2 for group in groups)
        assert any(
            item["role"] == "representative"
            for group in groups
            for item in group["items"]
        )

        rerun_response = client.post(f"/api/events/{event['id']}/detect-similarity")
        assert rerun_response.status_code == 200
        rerun_groups = client.get(f"/api/events/{event['id']}/similarity-groups").json()["items"]
        assert len(rerun_groups) == len(groups)

        jobs_response = client.get(f"/api/events/{event['id']}/jobs")
        assert jobs_response.status_code == 200
        assert any(job["job_type"] == "detect_similarity" for job in jobs_response.json()["items"])

    assert first_photo.read_bytes() == original_photo_bytes
