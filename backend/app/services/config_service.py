from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.local_app_config import LocalAppConfig
from app.schemas.config import (
    AppConfigResponse,
    AppConfigUpdate,
    ConfigValidationResponse,
    ToolValidationResult,
)
from app.utils.tool_validation import (
    normalize_optional_path,
    read_tool_version,
    resolve_tool_path,
)


DEFAULT_CONFIG: tuple[tuple[str, str | None, str], ...] = (
    ("app.initialized", "true", "Marca que la base local fue inicializada."),
    ("workspace.root", None, "Carpeta raiz local elegida por el usuario."),
    ("tools.ffmpeg_path", None, "Ruta local a FFmpeg, pendiente de configurar."),
    ("tools.exiftool_path", None, "Ruta local a ExifTool, pendiente de configurar."),
)


def upsert_default_config(db: Session) -> None:
    for key, value, description in DEFAULT_CONFIG:
        existing = db.scalar(
            select(LocalAppConfig).where(LocalAppConfig.key == key)
        )
        if existing is None:
            db.add(
                LocalAppConfig(
                    key=key,
                    value=value,
                    description=description,
                )
            )
    db.commit()


def get_config_value(db: Session, key: str) -> str | None:
    config = db.scalar(select(LocalAppConfig).where(LocalAppConfig.key == key))
    return config.value if config else None


def set_config_value(db: Session, key: str, value: str | None, description: str) -> None:
    config = db.scalar(select(LocalAppConfig).where(LocalAppConfig.key == key))
    normalized_value = normalize_optional_path(value)
    if config is None:
        db.add(LocalAppConfig(key=key, value=normalized_value, description=description))
        return

    config.value = normalized_value
    config.description = description


def get_app_config(db: Session) -> AppConfigResponse:
    return AppConfigResponse(
        workspace_root=get_config_value(db, "workspace.root"),
        ffmpeg_path=get_config_value(db, "tools.ffmpeg_path"),
        exiftool_path=get_config_value(db, "tools.exiftool_path"),
        app_initialized=get_config_value(db, "app.initialized") == "true",
    )


def update_app_config(db: Session, payload: AppConfigUpdate) -> AppConfigResponse:
    set_config_value(
        db,
        "workspace.root",
        payload.workspace_root,
        "Carpeta raiz local elegida por el usuario.",
    )
    set_config_value(
        db,
        "tools.ffmpeg_path",
        payload.ffmpeg_path,
        "Ruta local a FFmpeg, pendiente de configurar.",
    )
    set_config_value(
        db,
        "tools.exiftool_path",
        payload.exiftool_path,
        "Ruta local a ExifTool, pendiente de configurar.",
    )
    db.commit()
    return get_app_config(db)


def validate_current_config(db: Session) -> ConfigValidationResponse:
    config = get_app_config(db)
    workspace_root_error: str | None = None
    workspace_root_exists = False

    if config.workspace_root:
        workspace_path = Path(config.workspace_root).expanduser()
        workspace_root_exists = workspace_path.is_dir()
        if not workspace_root_exists:
            workspace_root_error = f"No existe la carpeta raiz local: {config.workspace_root}"
    else:
        workspace_root_error = "No se ha configurado una carpeta raiz local."

    ffmpeg = validate_tool(config.ffmpeg_path, "ffmpeg", ["-version"])
    exiftool = validate_tool(config.exiftool_path, "exiftool", ["-ver"])

    return ConfigValidationResponse(
        workspace_root_exists=workspace_root_exists,
        workspace_root_error=workspace_root_error,
        ffmpeg=ffmpeg,
        exiftool=exiftool,
    )


def validate_tool(
    configured_path: str | None,
    executable_name: str,
    version_args: list[str],
) -> ToolValidationResult:
    resolved_path, resolution_error = resolve_tool_path(configured_path, executable_name)
    if not resolved_path:
        return ToolValidationResult(
            configured_path=normalize_optional_path(configured_path),
            resolved_path=None,
            available=False,
            version=None,
            error=resolution_error,
        )

    version, version_error = read_tool_version(resolved_path, version_args)
    return ToolValidationResult(
        configured_path=normalize_optional_path(configured_path),
        resolved_path=resolved_path,
        available=version_error is None,
        version=version,
        error=version_error,
    )
