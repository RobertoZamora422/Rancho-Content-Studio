from pathlib import Path
import hashlib

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
            "name": "Exportacion Final",
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_approved_piece_with_copy(
    client: TestClient,
    event_id: int,
    source_root: Path,
) -> tuple[dict, dict, Path, str]:
    source_response = client.post(
        f"/api/events/{event_id}/sources",
        json={"source_path": str(source_root)},
    )
    assert source_response.status_code == 201

    import_response = client.post(f"/api/events/{event_id}/import")
    assert import_response.status_code == 200

    original_media = client.get(f"/api/events/{event_id}/media/original").json()["items"]
    original_path = Path(original_media[0]["original_path"])
    original_hash = sha256_file(original_path)

    curate_response = client.post(f"/api/events/{event_id}/curate-media")
    assert curate_response.status_code == 200
    curated_items = client.get(f"/api/events/{event_id}/curated-media").json()["items"]
    for curated in curated_items:
        patch_response = client.patch(
            f"/api/events/{event_id}/curated-media/{curated['id']}",
            json={
                "selection_status": "user_selected",
                "reason": "Seleccionada para exportacion final.",
            },
        )
        assert patch_response.status_code == 200

    enhancement_response = client.post(
        f"/api/events/{event_id}/enhance-photos",
        json={"preset_slug": "natural_premium"},
    )
    assert enhancement_response.status_code == 200
    assert enhancement_response.json()["enhanced"] == 3

    generation_response = client.post(f"/api/events/{event_id}/generate-pieces")
    assert generation_response.status_code == 200

    pieces = client.get(f"/api/events/{event_id}/content-pieces").json()["items"]
    piece = next(item for item in pieces if item["piece_type"] == "carousel")
    approved_piece_response = client.patch(
        f"/api/events/{event_id}/content-pieces/{piece['id']}",
        json={"status": "approved", "title": "Carrusel final aprobado"},
    )
    assert approved_piece_response.status_code == 200
    approved_piece = approved_piece_response.json()

    copy_response = client.post(
        f"/api/events/{event_id}/content-pieces/{approved_piece['id']}/generate-copy",
        json={"feedback": "mas_calido"},
    )
    assert copy_response.status_code == 200
    generated_copy = copy_response.json()["items"][0]
    approved_copy_response = client.patch(
        f"/api/events/{event_id}/content-pieces/{approved_piece['id']}/copies/{generated_copy['id']}",
        json={
            "body": "Copy final aprobado para publicar.\n\n#RanchoFlorMaria #Eventos",
            "status": "approved",
            "user_feedback": "me_gusta",
        },
    )
    assert approved_copy_response.status_code == 200
    return approved_piece, approved_copy_response.json(), original_path, original_hash


def test_export_package_creates_final_folder_media_copies_and_summary(tmp_path) -> None:
    workspace_root = tmp_path / "workspace"
    source_root = tmp_path / "source"
    workspace_root.mkdir()
    source_root.mkdir()

    for index, fill in enumerate(["#d9aa57", "#b17736", "#7f9a70"], start=1):
        create_photo(source_root / f"foto_export_{index}.jpg", fill)

    with TestClient(app) as client:
        configure_workspace(client, workspace_root)
        event = create_event(client)
        _, _, original_path, original_hash = prepare_approved_piece_with_copy(
            client,
            event["id"],
            source_root,
        )

        export_response = client.post(
            f"/api/events/{event['id']}/export-package",
            json={
                "export_type": "ready_to_publish",
                "include_copies": True,
                "write_event_date_metadata": True,
                "group_by_type": True,
                "include_summary": True,
            },
        )
        assert export_response.status_code == 200
        payload = export_response.json()
        package = payload["package"]
        assert payload["media_exported"] == 3
        assert payload["copies_exported"] == 1
        assert payload["failed_items"] == 0
        assert package["status"] == "generated"

        package_dir = Path(package["absolute_output_path"])
        assert package_dir.is_dir()
        assert package_dir.name.startswith("pkg_")
        assert "09_Listo_Para_Publicar" in package["output_path"]

        item_types = {item["item_type"] for item in package["items"]}
        assert {"media", "copy", "summary"} <= item_types
        for item in package["items"]:
            assert Path(item["absolute_output_path"]).exists()

        media_items = [item for item in package["items"] if item["item_type"] == "media"]
        assert all(item["metadata_written"] for item in media_items)
        assert all(item["metadata_status"].startswith("file_mtime") for item in media_items)

        summary_path = package_dir / "resumen_exportacion.txt"
        summary_text = summary_path.read_text(encoding="utf-8")
        assert "Medios exportados: 3" in summary_text
        assert "Copies exportados: 1" in summary_text
        assert "Carrusel final aprobado" in summary_text

        copy_items = [item for item in package["items"] if item["item_type"] == "copy"]
        copy_text = Path(copy_items[0]["absolute_output_path"]).read_text(encoding="utf-8")
        assert "Copy final aprobado" in copy_text
        assert "#RanchoFlorMaria" in copy_text

        assert original_path.is_file()
        assert sha256_file(original_path) == original_hash
        assert all(path.is_file() for path in source_root.iterdir())

        packages_response = client.get(f"/api/events/{event['id']}/export-packages")
        assert packages_response.status_code == 200
        assert packages_response.json()["items"][0]["id"] == package["id"]

        jobs_response = client.get(f"/api/events/{event['id']}/jobs")
        assert jobs_response.status_code == 200
        assert any(job["job_type"] == "export_package" for job in jobs_response.json()["items"])


def test_export_package_requires_approved_content(tmp_path) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()

    with TestClient(app) as client:
        configure_workspace(client, workspace_root)
        event = create_event(client)
        response = client.post(
            f"/api/events/{event['id']}/export-package",
            json={"export_type": "ready_to_publish"},
        )

        assert response.status_code == 400
        assert "No hay piezas aprobadas" in response.json()["detail"]
