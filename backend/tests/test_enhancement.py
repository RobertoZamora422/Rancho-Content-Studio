from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

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
            "name": "Boda Mejora",
            "event_type": "Boda",
            "event_date": "2026-05-10",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_photo(path: Path) -> None:
    image = Image.new("RGB", (220, 160), "#d9aa57")
    draw = ImageDraw.Draw(image)
    draw.rectangle((18, 18, 202, 142), outline="#202722", width=5)
    draw.ellipse((48, 40, 110, 102), fill="#f7f2e9")
    draw.rectangle((130, 42, 178, 116), fill="#6d746d")
    for index in range(0, 220, 20):
        draw.line((index, 0, index, 159), fill="#8f6934", width=1)
    image.save(path, quality=90)


def test_enhance_photos_generates_local_versions_and_manual_decisions(tmp_path) -> None:
    workspace_root = tmp_path / "workspace"
    source_root = tmp_path / "source"
    workspace_root.mkdir()
    source_root.mkdir()

    photo = source_root / "foto_principal.jpg"
    create_photo(photo)
    source_photo_bytes = photo.read_bytes()

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
        assert import_response.json()["imported_files"] == 1

        media_response = client.get(f"/api/events/{event['id']}/media/original")
        media_item = media_response.json()["items"][0]
        imported_original_path = Path(media_item["original_path"])
        imported_original_bytes = imported_original_path.read_bytes()

        assert client.post(f"/api/events/{event['id']}/analyze-photos").status_code == 200
        assert client.post(f"/api/events/{event['id']}/curate-media").status_code == 200

        curated_response = client.get(f"/api/events/{event['id']}/curated-media")
        curated_item = curated_response.json()["items"][0]
        if curated_item["selection_status"] != "selected":
            patch_response = client.patch(
                f"/api/events/{event['id']}/curated-media/{curated_item['id']}",
                json={
                    "selection_status": "user_selected",
                    "reason": "Seleccionada para probar mejora.",
                },
            )
            assert patch_response.status_code == 200

        enhancement_response = client.post(
            f"/api/events/{event['id']}/enhance-photos",
            json={"preset_slug": "calido_elegante"},
        )
        assert enhancement_response.status_code == 200
        enhancement_payload = enhancement_response.json()
        assert enhancement_payload["total_selected"] == 1
        assert enhancement_payload["enhanced"] == 1
        assert enhancement_payload["failed"] == 0
        assert enhancement_payload["preset_slug"] == "calido_elegante"

        enhanced_response = client.get(f"/api/events/{event['id']}/enhanced-media")
        assert enhanced_response.status_code == 200
        enhanced_items = enhanced_response.json()["items"]
        assert len(enhanced_items) == 1

        enhanced_item = enhanced_items[0]
        assert enhanced_item["status"] == "completed"
        assert enhanced_item["preset_slug"] == "calido_elegante"
        assert enhanced_item["output_path"].startswith("04_Mejorados")
        assert enhanced_item["width"] == 220
        assert enhanced_item["height"] == 160

        event_path = Path(event["event_path"])
        output_path = event_path / enhanced_item["output_path"]
        assert output_path.is_file()
        assert output_path.read_bytes() != imported_original_bytes

        file_response = client.get(enhanced_item["output_url"])
        assert file_response.status_code == 200
        assert file_response.headers["content-type"] == "image/jpeg"

        approve_response = client.patch(
            f"/api/events/{event['id']}/enhanced-media/{enhanced_item['id']}",
            json={"status": "approved", "reason": "Lista para piezas."},
        )
        assert approve_response.status_code == 200
        assert approve_response.json()["status"] == "approved"
        assert approve_response.json()["approved_at"] is not None

        jobs_response = client.get(f"/api/events/{event['id']}/jobs")
        assert jobs_response.status_code == 200
        assert any(job["job_type"] == "enhance_photos" for job in jobs_response.json()["items"])

    assert photo.read_bytes() == source_photo_bytes
    assert imported_original_path.read_bytes() == imported_original_bytes
