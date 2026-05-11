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
            "name": "Boda Curacion",
            "event_type": "Boda",
            "event_date": "2026-05-10",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_similar_photo(path: Path, accent: str) -> None:
    image = Image.new("RGB", (180, 120), "#f7f2e9")
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 18, 160, 102), outline="#202722", width=4)
    draw.ellipse((48, 32, 92, 76), fill=accent)
    draw.rectangle((108, 38, 144, 86), fill="#d9aa57")
    for x in range(0, 180, 18):
        draw.line((x, 0, x, 119), fill="#202722", width=1)
    for y in range(0, 120, 18):
        draw.line((0, y, 179, y), fill="#6d746d", width=1)
    image.save(path, quality=88)


def test_curate_media_creates_explainable_states_and_preserves_manual_override(tmp_path) -> None:
    workspace_root = tmp_path / "workspace"
    source_root = tmp_path / "source"
    workspace_root.mkdir()
    source_root.mkdir()

    first_photo = source_root / "seleccion_1.jpg"
    second_photo = source_root / "seleccion_2.jpg"
    dark_photo = source_root / "oscura.jpg"
    create_similar_photo(first_photo, "#9a6a14")
    create_similar_photo(second_photo, "#9f6f18")
    Image.new("RGB", (180, 120), "#111111").save(dark_photo)
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
        assert import_response.json()["imported_files"] == 3

        assert client.post(f"/api/events/{event['id']}/analyze-photos").status_code == 200
        assert client.post(f"/api/events/{event['id']}/detect-similarity").status_code == 200

        curate_response = client.post(f"/api/events/{event['id']}/curate-media")
        assert curate_response.status_code == 200
        curate_payload = curate_response.json()
        assert curate_payload["total_media"] == 3
        assert curate_payload["selected"] >= 1
        assert curate_payload["alternative"] >= 1
        assert curate_payload["rejected"] >= 1

        curated_response = client.get(f"/api/events/{event['id']}/curated-media")
        assert curated_response.status_code == 200
        curated_items = curated_response.json()["items"]
        assert len(curated_items) == 3
        assert all(item["reason"] for item in curated_items)
        assert any(item["selection_status"] == "selected" for item in curated_items)
        assert any(item["selection_status"] == "alternative" for item in curated_items)
        assert any(item["selection_status"].startswith("rejected_") for item in curated_items)

        alternative = next(item for item in curated_items if item["selection_status"] == "alternative")
        patch_response = client.patch(
            f"/api/events/{event['id']}/curated-media/{alternative['id']}",
            json={
                "selection_status": "user_selected",
                "reason": "Elegida manualmente para conservar variedad.",
            },
        )
        assert patch_response.status_code == 200
        patched = patch_response.json()
        assert patched["selection_status"] == "user_selected"
        assert patched["is_manual_override"] is True

        rerun_response = client.post(f"/api/events/{event['id']}/curate-media")
        assert rerun_response.status_code == 200
        assert rerun_response.json()["preserved_manual_overrides"] == 1

        rerun_items = client.get(f"/api/events/{event['id']}/curated-media").json()["items"]
        preserved = next(item for item in rerun_items if item["id"] == alternative["id"])
        assert preserved["selection_status"] == "user_selected"
        assert preserved["is_manual_override"] is True

        jobs_response = client.get(f"/api/events/{event['id']}/jobs")
        assert jobs_response.status_code == 200
        assert any(job["job_type"] == "curate_media" for job in jobs_response.json()["items"])

    assert first_photo.read_bytes() == original_photo_bytes
