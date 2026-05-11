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
            "name": "Boda Piezas",
            "event_type": "Boda",
            "event_date": "2026-05-10",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_photo(path: Path, fill: str) -> None:
    image = Image.new("RGB", (180, 130), fill)
    draw = ImageDraw.Draw(image)
    draw.rectangle((18, 18, 162, 112), outline="#202722", width=4)
    draw.ellipse((48, 36, 92, 80), fill="#f7f2e9")
    draw.rectangle((110, 42, 145, 92), fill="#6d746d")
    image.save(path, quality=90)


def test_generate_content_pieces_from_enhanced_media_and_edit_order(tmp_path) -> None:
    workspace_root = tmp_path / "workspace"
    source_root = tmp_path / "source"
    workspace_root.mkdir()
    source_root.mkdir()

    for index, fill in enumerate(["#d9aa57", "#b17736", "#7f9a70", "#9a6a14"], start=1):
        create_photo(source_root / f"foto_{index}.jpg", fill)

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
        assert import_response.json()["imported_files"] == 4

        curate_response = client.post(f"/api/events/{event['id']}/curate-media")
        assert curate_response.status_code == 200

        curated_items = client.get(f"/api/events/{event['id']}/curated-media").json()["items"]
        assert len(curated_items) == 4
        for curated in curated_items:
            patch_response = client.patch(
                f"/api/events/{event['id']}/curated-media/{curated['id']}",
                json={
                    "selection_status": "user_selected",
                    "reason": "Foto seleccionada para piezas.",
                },
            )
            assert patch_response.status_code == 200

        enhancement_response = client.post(
            f"/api/events/{event['id']}/enhance-photos",
            json={"preset_slug": "natural_premium"},
        )
        assert enhancement_response.status_code == 200
        assert enhancement_response.json()["enhanced"] == 4

        generation_response = client.post(f"/api/events/{event['id']}/generate-pieces")
        assert generation_response.status_code == 200
        generation_payload = generation_response.json()
        assert generation_payload["total_available_media"] == 4
        assert generation_payload["pieces_created"] >= 3

        pieces_response = client.get(f"/api/events/{event['id']}/content-pieces")
        assert pieces_response.status_code == 200
        pieces = pieces_response.json()["items"]
        piece_types = {piece["piece_type"] for piece in pieces}
        assert {"carousel", "story", "single_post"} <= piece_types
        assert all(piece["media_items"] for piece in pieces)

        carousel = next(piece for piece in pieces if piece["piece_type"] == "carousel")
        original_order = [item["id"] for item in carousel["media_items"]]
        reordered = list(reversed(original_order))
        update_response = client.patch(
            f"/api/events/{event['id']}/content-pieces/{carousel['id']}",
            json={
                "media_item_order": reordered,
                "status": "approved",
                "title": "Carrusel principal aprobado",
            },
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["status"] == "approved"
        assert updated["approved_at"] is not None
        assert [item["id"] for item in updated["media_items"]] == reordered
        assert updated["media_items"][0]["role"] == "cover"
        assert all(item["role"] == "sequence" for item in updated["media_items"][1:])

        second_generation_response = client.post(f"/api/events/{event['id']}/generate-pieces")
        assert second_generation_response.status_code == 200
        assert second_generation_response.json()["pieces_created"] == 0
        assert second_generation_response.json()["pieces_skipped"] >= 3

        jobs_response = client.get(f"/api/events/{event['id']}/jobs")
        assert jobs_response.status_code == 200
        assert any(job["job_type"] == "generate_pieces" for job in jobs_response.json()["items"])
