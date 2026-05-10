from __future__ import annotations

from pydantic import BaseModel, Field


class AppConfigResponse(BaseModel):
    workspace_root: str | None = None
    ffmpeg_path: str | None = None
    exiftool_path: str | None = None
    app_initialized: bool = True


class AppConfigUpdate(BaseModel):
    workspace_root: str | None = Field(default=None, max_length=1024)
    ffmpeg_path: str | None = Field(default=None, max_length=1024)
    exiftool_path: str | None = Field(default=None, max_length=1024)


class ToolValidationResult(BaseModel):
    configured_path: str | None = None
    resolved_path: str | None = None
    available: bool
    version: str | None = None
    error: str | None = None


class ConfigValidationResponse(BaseModel):
    workspace_root_exists: bool
    workspace_root_error: str | None = None
    ffmpeg: ToolValidationResult
    exiftool: ToolValidationResult
