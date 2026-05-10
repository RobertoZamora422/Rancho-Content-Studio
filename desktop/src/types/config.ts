export type AppConfig = {
  workspace_root: string | null;
  ffmpeg_path: string | null;
  exiftool_path: string | null;
  app_initialized: boolean;
};

export type AppConfigUpdate = {
  workspace_root: string | null;
  ffmpeg_path: string | null;
  exiftool_path: string | null;
};

export type ToolValidationResult = {
  configured_path: string | null;
  resolved_path: string | null;
  available: boolean;
  version: string | null;
  error: string | null;
};

export type ConfigValidation = {
  workspace_root_exists: boolean;
  workspace_root_error: string | null;
  ffmpeg: ToolValidationResult;
  exiftool: ToolValidationResult;
};
