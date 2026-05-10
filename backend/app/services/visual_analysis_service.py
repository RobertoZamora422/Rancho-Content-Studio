from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.media import MediaAnalysis, OriginalMedia
from app.schemas.importing import VisualAnalysisProcessResponse
from app.services.event_service import require_event
from app.services.job_service import add_job_log, finish_job, start_job, update_job_progress

ANALYSIS_VERSION = "local-pillow-basic-v1"
ANALYSIS_MAX_SIZE = (1024, 1024)
HASH_SIZE = 8


@dataclass(frozen=True)
class ImageAnalysisResult:
    sharpness_score: float
    brightness_score: float
    contrast_score: float
    noise_score: float
    exposure_score: float
    overall_quality_score: float
    perceptual_hash: str
    raw_metrics_json: str


def analyze_event_photos(db: Session, event_id: int) -> VisualAnalysisProcessResponse:
    require_event(db, event_id)
    job = start_job(db, "analyze_media", event_id)
    media_items = list(
        db.scalars(
            select(OriginalMedia)
            .where(OriginalMedia.event_id == event_id)
            .order_by(OriginalMedia.imported_at.asc(), OriginalMedia.id.asc())
        ).all()
    )
    photos = [media for media in media_items if media.media_type == "image"]
    skipped_non_images = len(media_items) - len(photos)

    analyzed = 0
    failed = 0
    for media in photos:
        try:
            source_path = require_existing_image(media)
            result = analyze_image(source_path)
            upsert_analysis(db, media, result)
            analyzed += 1
            add_job_log(
                db,
                job,
                "info",
                f"Foto analizada con puntaje global {result.overall_quality_score:.1f}.",
                file_path=str(source_path),
                original_media_id=media.id,
            )
        except Exception as error:  # noqa: BLE001 - per-file errors must not stop the job.
            failed += 1
            add_job_log(
                db,
                job,
                "error",
                str(error),
                file_path=media.original_path,
                original_media_id=media.id,
            )
        update_job_progress(job, len(photos), analyzed, failed)
        db.flush()

    if skipped_non_images:
        add_job_log(
            db,
            job,
            "info",
            f"{skipped_non_images} medios no imagen fueron omitidos en Fase 7.",
        )

    finish_job(
        job,
        "completed" if failed == 0 else "completed_with_errors",
        total_items=len(photos),
        processed_items=analyzed,
        failed_items=failed,
    )
    db.commit()

    return VisualAnalysisProcessResponse(
        job_id=job.id,
        total_photos=len(photos),
        analyzed_photos=analyzed,
        failed_photos=failed,
        skipped_non_images=skipped_non_images,
    )


def analyze_image(source_path: Path) -> ImageAnalysisResult:
    try:
        with Image.open(source_path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.thumbnail(ANALYSIS_MAX_SIZE)
            grayscale = ImageOps.grayscale(image)
            gray_stats = ImageStat.Stat(grayscale)
            brightness_raw = float(gray_stats.mean[0])
            contrast_raw = float(gray_stats.stddev[0])
            sharpness_raw = estimate_sharpness(grayscale)
            noise_raw = estimate_noise(grayscale)
            dark_ratio, bright_ratio = clipped_ratios(grayscale)
            perceptual_hash = average_hash(grayscale)
    except (OSError, UnidentifiedImageError) as error:
        raise ValueError(f"No se pudo analizar la imagen: {error}") from error

    brightness_score = clamp_score((brightness_raw / 255) * 100)
    contrast_score = clamp_score((contrast_raw / 64) * 100)
    sharpness_score = clamp_score((sharpness_raw / 36) * 100)
    noise_score = clamp_score(100 - (noise_raw / 32) * 100)
    exposure_score = estimate_exposure_score(brightness_score, dark_ratio, bright_ratio)
    overall_quality_score = weighted_quality(
        sharpness_score=sharpness_score,
        exposure_score=exposure_score,
        contrast_score=contrast_score,
        noise_score=noise_score,
    )

    raw_metrics = {
        "brightness_raw": round(brightness_raw, 4),
        "contrast_raw": round(contrast_raw, 4),
        "sharpness_raw": round(sharpness_raw, 4),
        "noise_raw": round(noise_raw, 4),
        "dark_pixel_ratio": round(dark_ratio, 6),
        "bright_pixel_ratio": round(bright_ratio, 6),
        "method": ANALYSIS_VERSION,
    }

    return ImageAnalysisResult(
        sharpness_score=round(sharpness_score, 2),
        brightness_score=round(brightness_score, 2),
        contrast_score=round(contrast_score, 2),
        noise_score=round(noise_score, 2),
        exposure_score=round(exposure_score, 2),
        overall_quality_score=round(overall_quality_score, 2),
        perceptual_hash=perceptual_hash,
        raw_metrics_json=json.dumps(raw_metrics, ensure_ascii=True),
    )


def upsert_analysis(db: Session, media: OriginalMedia, result: ImageAnalysisResult) -> None:
    analysis = db.scalar(
        select(MediaAnalysis).where(MediaAnalysis.original_media_id == media.id)
    )
    if analysis is None:
        analysis = MediaAnalysis(original_media_id=media.id)
        db.add(analysis)

    analysis.sharpness_score = result.sharpness_score
    analysis.brightness_score = result.brightness_score
    analysis.contrast_score = result.contrast_score
    analysis.noise_score = result.noise_score
    analysis.exposure_score = result.exposure_score
    analysis.overall_quality_score = result.overall_quality_score
    analysis.perceptual_hash = result.perceptual_hash
    analysis.analysis_version = ANALYSIS_VERSION
    analysis.raw_metrics_json = result.raw_metrics_json
    analysis.analyzed_at = datetime.now(timezone.utc)


def require_existing_image(media: OriginalMedia) -> Path:
    path = Path(media.original_path)
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo original importado: {media.original_path}")
    return path


def estimate_sharpness(grayscale: Image.Image) -> float:
    edges = grayscale.filter(ImageFilter.FIND_EDGES)
    return float(ImageStat.Stat(edges).stddev[0])


def estimate_noise(grayscale: Image.Image) -> float:
    blurred = grayscale.filter(ImageFilter.GaussianBlur(radius=1.0))
    residual = ImageChops.difference(grayscale, blurred)
    return float(ImageStat.Stat(residual).mean[0])


def clipped_ratios(grayscale: Image.Image) -> tuple[float, float]:
    histogram = grayscale.histogram()
    total_pixels = max(sum(histogram), 1)
    dark_pixels = sum(histogram[:16])
    bright_pixels = sum(histogram[240:])
    return dark_pixels / total_pixels, bright_pixels / total_pixels


def average_hash(grayscale: Image.Image) -> str:
    resized = grayscale.resize((HASH_SIZE, HASH_SIZE), Image.Resampling.LANCZOS)
    pixels = list(resized.getdata())
    average = sum(pixels) / len(pixels)
    bits = "".join("1" if pixel >= average else "0" for pixel in pixels)
    return f"{int(bits, 2):016x}"


def estimate_exposure_score(
    brightness_score: float,
    dark_ratio: float,
    bright_ratio: float,
) -> float:
    centered_score = 100 - min(abs(brightness_score - 52) * 2.2, 100)
    clipping_penalty = min((dark_ratio + bright_ratio) * 160, 45)
    return clamp_score(centered_score - clipping_penalty)


def weighted_quality(
    sharpness_score: float,
    exposure_score: float,
    contrast_score: float,
    noise_score: float,
) -> float:
    return clamp_score(
        sharpness_score * 0.35
        + exposure_score * 0.30
        + contrast_score * 0.20
        + noise_score * 0.15
    )


def clamp_score(value: float) -> float:
    return max(0.0, min(100.0, float(value)))
