from fastapi.testclient import TestClient

from app.main import app


def test_config_roundtrip_and_workspace_validation(tmp_path) -> None:
    workspace_root = tmp_path / "Rancho Content Studio"
    workspace_root.mkdir()

    with TestClient(app) as client:
        update_response = client.put(
            "/api/config",
            json={
                "workspace_root": str(workspace_root),
                "ffmpeg_path": None,
                "exiftool_path": None,
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["workspace_root"] == str(workspace_root)

        read_response = client.get("/api/config")
        assert read_response.status_code == 200
        payload = read_response.json()
        assert payload["workspace_root"] == str(workspace_root)
        assert payload["app_initialized"] is True

        validation_response = client.post("/api/config/validate-tools")
        assert validation_response.status_code == 200
        validation_payload = validation_response.json()
        assert validation_payload["workspace_root_exists"] is True
        assert "available" in validation_payload["ffmpeg"]
        assert "available" in validation_payload["exiftool"]
