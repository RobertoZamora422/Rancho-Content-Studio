from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from app.utils.tool_validation import resolve_tool_path

IMAGE_THUMBNAIL_SIZE = (480, 480)
VIDEO_THUMBNAIL_SIZE = (480, 270)


@dataclass(frozen=True)
class ThumbnailResult:
    thumbnail_path: Path
    generated_from: str
    warning: str | None = None


def generate_thumbnail(
    source_path: Path,
    output_path: Path,
    media_type: str,
    configured_ffmpeg_path: str | None,
) -> ThumbnailResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if media_type == "image":
        create_image_thumbnail(source_path, output_path)
        return ThumbnailResult(thumbnail_path=output_path, generated_from="image_local")

    if media_type == "video":
        return create_video_thumbnail(source_path, output_path, configured_ffmpeg_path)

    raise ValueError(f"Tipo de medio no soportado para miniatura: {media_type}")


def create_image_thumbnail(source_path: Path, output_path: Path) -> None:
    with Image.open(source_path) as image:
        image = ImageOps.exif_transpose(image)
        image.thumbnail(IMAGE_THUMBNAIL_SIZE)
        save_as_jpeg(image, output_path)


def create_video_thumbnail(
    source_path: Path,
    output_path: Path,
    configured_ffmpeg_path: str | None,
) -> ThumbnailResult:
    ffmpeg_command, resolution_error = resolve_tool_path(configured_ffmpeg_path, "ffmpeg")
    if ffmpeg_command:
        frame_path = output_path.with_suffix(".frame.jpg")
        frame_error = extract_video_frame(ffmpeg_command, source_path, frame_path)
        if frame_error is None:
            try:
                normalize_frame_thumbnail(frame_path, output_path)
                return ThumbnailResult(thumbnail_path=output_path, generated_from="ffmpeg_frame")
            finally:
                frame_path.unlink(missing_ok=True)
        frame_path.unlink(missing_ok=True)
        warning = f"No se pudo extraer frame con FFmpeg: {frame_error}"
    else:
        warning = resolution_error

    create_video_placeholder(output_path)
    return ThumbnailResult(
        thumbnail_path=output_path,
        generated_from="video_placeholder",
        warning=warning,
    )


def extract_video_frame(ffmpeg_command: str, source_path: Path, frame_path: Path) -> str | None:
    try:
        completed = subprocess.run(
            [
                ffmpeg_command,
                "-y",
                "-ss",
                "00:00:01",
                "-i",
                str(source_path),
                "-frames:v",
                "1",
                str(frame_path),
            ],
            capture_output=True,
            check=False,
            text=True,
            timeout=20,
        )
    except OSError as error:
        return str(error)
    except subprocess.TimeoutExpired:
        return "La extraccion de frame excedio el tiempo de espera."

    if completed.returncode != 0:
        return (completed.stderr or completed.stdout).strip() or (
            f"FFmpeg finalizo con codigo {completed.returncode}."
        )
    if not frame_path.is_file() or frame_path.stat().st_size == 0:
        return "FFmpeg no genero una imagen de salida."
    return None


def normalize_frame_thumbnail(frame_path: Path, output_path: Path) -> None:
    with Image.open(frame_path) as image:
        image = ImageOps.exif_transpose(image)
        image.thumbnail(VIDEO_THUMBNAIL_SIZE)
        save_as_jpeg(image, output_path)


def create_video_placeholder(output_path: Path) -> None:
    image = Image.new("RGB", VIDEO_THUMBNAIL_SIZE, "#202722")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, VIDEO_THUMBNAIL_SIZE[0], VIDEO_THUMBNAIL_SIZE[1]), fill="#202722")
    draw.polygon([(205, 96), (205, 174), (280, 135)], fill="#d9aa57")
    draw.text((24, 226), "VIDEO", fill="#f7f2e9")
    image.save(output_path, format="JPEG", quality=82, optimize=True)


def save_as_jpeg(image: Image.Image, output_path: Path) -> None:
    if image.mode in {"RGBA", "LA"}:
        background = Image.new("RGB", image.size, "#f5f3ee")
        alpha = image.getchannel("A")
        background.paste(image.convert("RGBA"), mask=alpha)
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")
    image.save(output_path, format="JPEG", quality=82, optimize=True)
