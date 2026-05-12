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
            "name": "Biblioteca Calendario",
            "event_type": "Boda",
            "event_date": "2026-05-15",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_photo(path: Path, fill: str) -> None:
    image = Image.new("RGB", (180, 130), fill)
    draw = ImageDraw.Draw(image)
    draw.rectangle((18, 18, 162, 112), outline="#202722", width=4)
    draw.ellipse((50, 36, 92, 80), fill="#f7f2e9")
    draw.rectangle((112, 42, 145, 92), fill="#6d746d")
    image.save(path, quality=90)


def prepare_content(client: TestClient, event_id: int, source_root: Path) -> tuple[dict, dict, dict]:
    source_response = client.post(
        f"/api/events/{event_id}/sources",
        json={"source_path": str(source_root)},
    )
    assert source_response.status_code == 201

    import_response = client.post(f"/api/events/{event_id}/import")
    assert import_response.status_code == 200
    assert import_response.json()["imported_files"] == 1

    metadata_response = client.post(f"/api/events/{event_id}/process-metadata")
    assert metadata_response.status_code == 200
    assert metadata_response.json()["thumbnails_generated"] == 1

    curate_response = client.post(f"/api/events/{event_id}/curate-media")
    assert curate_response.status_code == 200
    curated_items = client.get(f"/api/events/{event_id}/curated-media").json()["items"]
    assert len(curated_items) == 1
    selected_response = client.patch(
        f"/api/events/{event_id}/curated-media/{curated_items[0]['id']}",
        json={
            "selection_status": "user_selected",
            "reason": "Seleccionada para biblioteca y calendario.",
        },
    )
    assert selected_response.status_code == 200

    enhancement_response = client.post(
        f"/api/events/{event_id}/enhance-photos",
        json={"preset_slug": "natural_premium"},
    )
    assert enhancement_response.status_code == 200
    assert enhancement_response.json()["enhanced"] == 1

    generation_response = client.post(f"/api/events/{event_id}/generate-pieces")
    assert generation_response.status_code == 200
    pieces = client.get(f"/api/events/{event_id}/content-pieces").json()["items"]
    assert len(pieces) >= 2
    approved_piece = next(piece for piece in pieces if piece["piece_type"] == "single_post")
    unapproved_piece = next(piece for piece in pieces if piece["id"] != approved_piece["id"])
    approved_response = client.patch(
        f"/api/events/{event_id}/content-pieces/{approved_piece['id']}",
        json={"status": "approved", "title": "Post aprobado de biblioteca"},
    )
    assert approved_response.status_code == 200
    approved_piece = approved_response.json()

    copy_response = client.post(
        f"/api/events/{event_id}/content-pieces/{approved_piece['id']}/generate-copy",
        json={"feedback": "mas_calido"},
    )
    assert copy_response.status_code == 200
    generated_copy = copy_response.json()["items"][0]
    approved_copy_response = client.patch(
        f"/api/events/{event_id}/content-pieces/{approved_piece['id']}/copies/{generated_copy['id']}",
        json={
            "body": "Copy final aprobado para biblioteca.\n\n#RanchoFlorMaria #Eventos",
            "status": "approved",
            "user_feedback": "me_gusta",
        },
    )
    assert approved_copy_response.status_code == 200
    return approved_piece, unapproved_piece, approved_copy_response.json()


def test_library_endpoints_filter_historical_media_pieces_and_copies(tmp_path) -> None:
    workspace_root = tmp_path / "workspace"
    source_root = tmp_path / "source"
    workspace_root.mkdir()
    source_root.mkdir()
    create_photo(source_root / "foto_biblioteca.jpg", "#d9aa57")

    with TestClient(app) as client:
        configure_workspace(client, workspace_root)
        event = create_event(client)
        approved_piece, _, approved_copy = prepare_content(client, event["id"], source_root)

        media_response = client.get(f"/api/library/media?event_id={event['id']}")
        assert media_response.status_code == 200
        media_items = media_response.json()["items"]
        assert {"original", "curated", "enhanced"} <= {item["source_type"] for item in media_items}
        assert all("output_url" not in item for item in media_items)
        assert any(item["thumbnail_url"] for item in media_items)
        assert all(item["local_path"] for item in media_items)

        enhanced_response = client.get(
            f"/api/library/media?event_id={event['id']}&source_type=enhanced&file_type=image"
        )
        assert enhanced_response.status_code == 200
        assert enhanced_response.json()["items"][0]["source_type"] == "enhanced"

        pieces_response = client.get(f"/api/library/pieces?event_id={event['id']}&status=approved")
        assert pieces_response.status_code == 200
        pieces = pieces_response.json()["items"]
        assert pieces[0]["id"] == approved_piece["id"]
        assert pieces[0]["media_count"] == 1
        assert pieces[0]["approved_copy_count"] == 1

        copies_response = client.get(f"/api/library/copies?event_id={event['id']}&q=biblioteca")
        assert copies_response.status_code == 200
        copies = copies_response.json()["items"]
        assert copies[0]["id"] == approved_copy["id"]
        assert "Copy final aprobado" in copies[0]["body_preview"]

        search_response = client.get(f"/api/library/search?event_id={event['id']}&q=Biblioteca")
        assert search_response.status_code == 200
        entity_types = {item["entity_type"] for item in search_response.json()["items"]}
        assert "piece" in entity_types
        assert "copy" in entity_types


def test_calendar_schedules_updates_publishes_and_cancels_manually(tmp_path) -> None:
    workspace_root = tmp_path / "workspace"
    source_root = tmp_path / "source"
    workspace_root.mkdir()
    source_root.mkdir()
    create_photo(source_root / "foto_calendario.jpg", "#7f9a70")

    with TestClient(app) as client:
        configure_workspace(client, workspace_root)
        event = create_event(client)
        approved_piece, unapproved_piece, _ = prepare_content(client, event["id"], source_root)

        rejected_response = client.post(
            "/api/calendar/items",
            json={
                "piece_id": unapproved_piece["id"],
                "scheduled_date": "2026-05-20",
                "platform": "instagram",
                "status": "scheduled",
            },
        )
        assert rejected_response.status_code == 400
        assert "piezas aprobadas" in rejected_response.json()["detail"]

        create_response = client.post(
            "/api/calendar/items",
            json={
                "piece_id": approved_piece["id"],
                "scheduled_date": "2026-05-20",
                "scheduled_time": "10:30",
                "platform": "instagram",
                "status": "scheduled",
                "notes": "Publicar manualmente.",
            },
        )
        assert create_response.status_code == 201
        item = create_response.json()
        assert item["event"]["id"] == event["id"]
        assert item["piece"]["id"] == approved_piece["id"]
        assert item["scheduled_date"] == "2026-05-20"
        assert item["scheduled_time"] == "10:30"
        assert item["status"] == "scheduled"

        list_response = client.get(f"/api/calendar?event_id={event['id']}&status=scheduled")
        assert list_response.status_code == 200
        assert list_response.json()["items"][0]["id"] == item["id"]

        update_response = client.put(
            f"/api/calendar/items/{item['id']}",
            json={
                "status": "ready_to_publish",
                "scheduled_date": "2026-05-21",
                "scheduled_time": "11:00",
                "platform": "facebook",
                "notes": "Lista para publicar.",
            },
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["status"] == "ready_to_publish"
        assert updated["platform"] == "facebook"
        assert updated["scheduled_date"] == "2026-05-21"

        published_response = client.post(
            f"/api/calendar/items/{item['id']}/mark-published",
            json={
                "published_url": "https://example.com/publicacion",
                "notes": "Publicada manualmente.",
            },
        )
        assert published_response.status_code == 200
        published = published_response.json()
        assert published["status"] == "published"
        assert published["published_at"] is not None
        assert published["published_url"] == "https://example.com/publicacion"

        cancelled_response = client.delete(f"/api/calendar/items/{item['id']}")
        assert cancelled_response.status_code == 200
        assert cancelled_response.json()["status"] == "cancelled"
