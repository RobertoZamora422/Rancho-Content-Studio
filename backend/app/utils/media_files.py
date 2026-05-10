from __future__ import annotations

import hashlib
import mimetypes
import shutil
from datetime import datetime, timezone
from pathlib import Path

from app.utils.event_folders import safe_windows_name

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".tif",
    ".tiff",
    ".heic",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".m4v",
    ".avi",
    ".mkv",
    ".webm",
    ".mts",
    ".m2ts",
}

SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


def iter_files(source_path: Path) -> list[Path]:
    return sorted(path for path in source_path.rglob("*") if path.is_file())


def is_supported_media(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def media_type_for_path(path: Path) -> str:
    extension = path.suffix.lower()
    if extension in IMAGE_EXTENSIONS:
        return "image"
    if extension in VIDEO_EXTENSIONS:
        return "video"
    return "unknown"


def mime_type_for_path(path: Path) -> str | None:
    mime_type, _ = mimetypes.guess_type(path.name)
    return mime_type


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_modified_datetime(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def safe_media_filename(path: Path) -> str:
    stem = safe_windows_name(path.stem, fallback="media")
    extension = path.suffix.lower()
    return f"{stem}{extension}"


def unique_destination(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    for index in range(2, 10000):
        next_candidate = directory / f"{stem}_{index:03d}{suffix}"
        if not next_candidate.exists():
            return next_candidate

    raise RuntimeError("No se pudo generar un nombre unico para el archivo importado.")


def copy_media_file(source: Path, destination: Path) -> None:
    shutil.copy2(source, destination)
