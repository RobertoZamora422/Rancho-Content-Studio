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
            "name": "XV Copy",
            "event_type": "XV",
            "event_date": "2026-05-10",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_photo(path: Path, fill: str) -> None:
    image = Image.new("RGB", (180, 130), fill)
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 160, 110), outline="#202722", width=4)
    draw.ellipse((50, 36, 94, 80), fill="#f7f2e9")
    draw.rectangle((110, 42, 145, 92), fill="#6d746d")
    image.save(path, quality=90)


def prepare_approved_piece(client: TestClient, event_id: int, source_root: Path) -> dict:
    source_response = client.post(
        f"/api/events/{event_id}/sources",
        json={"source_path": str(source_root)},
    )
    assert source_response.status_code == 201

    import_response = client.post(f"/api/events/{event_id}/import")
    assert import_response.status_code == 200

    curate_response = client.post(f"/api/events/{event_id}/curate-media")
    assert curate_response.status_code == 200
    curated_items = client.get(f"/api/events/{event_id}/curated-media").json()["items"]
    for curated in curated_items:
        patch_response = client.patch(
            f"/api/events/{event_id}/curated-media/{curated['id']}",
            json={
                "selection_status": "user_selected",
                "reason": "Foto seleccionada para copy.",
            },
        )
        assert patch_response.status_code == 200

    enhancement_response = client.post(
        f"/api/events/{event_id}/enhance-photos",
        json={"preset_slug": "natural_premium"},
    )
    assert enhancement_response.status_code == 200

    generation_response = client.post(f"/api/events/{event_id}/generate-pieces")
    assert generation_response.status_code == 200
    pieces = client.get(f"/api/events/{event_id}/content-pieces").json()["items"]
    piece = next(item for item in pieces if item["piece_type"] in {"carousel", "single_post"})
    update_response = client.patch(
        f"/api/events/{event_id}/content-pieces/{piece['id']}",
        json={"status": "approved"},
    )
    assert update_response.status_code == 200
    return update_response.json()


def test_generate_edit_approve_and_export_copy(tmp_path) -> None:
    workspace_root = tmp_path / "workspace"
    source_root = tmp_path / "source"
    workspace_root.mkdir()
    source_root.mkdir()

    for index, fill in enumerate(["#d9aa57", "#b17736", "#7f9a70"], start=1):
        create_photo(source_root / f"foto_copy_{index}.jpg", fill)

    with TestClient(app) as client:
        configure_workspace(client, workspace_root)
        profile_response = client.put(
            "/api/editorial-profile/default",
            json={
                "tone": "calido, natural, cercano, profesional",
                "emotional_level": "moderado",
                "formality_level": "semi_formal",
                "emoji_style": "sutil",
                "hashtags_base": "#RanchoFlorMaria #Eventos",
                "preferred_phrases": "momentos memorables; celebrar en familia",
                "words_to_avoid": "viral obligatorio; exagerado",
                "copy_rules": "Evitar promesas irreales y mantener tono humano.",
            },
        )
        assert profile_response.status_code == 200
        assert profile_response.json()["tone"].startswith("calido")

        event = create_event(client)
        piece = prepare_approved_piece(client, event["id"], source_root)

        generation_response = client.post(
            f"/api/events/{event['id']}/content-pieces/{piece['id']}/generate-copy",
            json={"feedback": "mas_calido"},
        )
        assert generation_response.status_code == 200
        payload = generation_response.json()
        assert payload["copies_created"] >= 4
        assert payload["feedback"] == "mas_calido"
        assert any(item["copy_type"] == "caption" for item in payload["items"])
        assert all(item["output_path"] for item in payload["items"])

        first_copy = payload["items"][0]
        output_path = workspace_root / event["folder_name"] / first_copy["output_path"]
        assert output_path.is_file()

        approval_response = client.patch(
            f"/api/events/{event['id']}/content-pieces/{piece['id']}/copies/{first_copy['id']}",
            json={
                "body": "Un recuerdo calido de Rancho Flor Maria.\n\n#RanchoFlorMaria #Eventos",
                "status": "approved",
                "user_feedback": "me_gusta",
            },
        )
        assert approval_response.status_code == 200
        approved = approval_response.json()
        assert approved["status"] == "approved"
        assert approved["approved_at"] is not None
        assert "Un recuerdo calido" in output_path.read_text(encoding="utf-8")

        profile_after = client.get("/api/editorial-profile/default").json()
        assert "Un recuerdo calido" in profile_after["approved_examples"]

        rejected_response = client.patch(
            f"/api/events/{event['id']}/content-pieces/{piece['id']}/copies/{first_copy['id']}",
            json={
                "body": "Este evento sera viral obligatorio.\n\n#RanchoFlorMaria",
                "status": "approved",
            },
        )
        assert rejected_response.status_code == 400

        copies_response = client.get(
            f"/api/events/{event['id']}/content-pieces/{piece['id']}/copies"
        )
        assert copies_response.status_code == 200
        assert len(copies_response.json()["items"]) == payload["copies_created"]

        jobs_response = client.get(f"/api/events/{event['id']}/jobs")
        assert jobs_response.status_code == 200
        assert any(job["job_type"] == "generate_copy" for job in jobs_response.json()["items"])
