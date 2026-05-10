from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SourceCreate(BaseModel):
    source_path: str = Field(min_length=1, max_length=1024)


class SourceResponse(BaseModel):
    id: int
    event_id: int
    source_path: str
    source_type: str
    status: str
    file_count: int
    scanned_at: datetime | None
    imported_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ScanSourceSummary(BaseModel):
    source_id: int
    source_path: str
    supported_files: int
    unsupported_files: int
    failed_files: int


class ScanResponse(BaseModel):
    job_id: int
    total_sources: int
    supported_files: int
    unsupported_files: int
    failed_files: int
    sources: list[ScanSourceSummary]


class ImportResponse(BaseModel):
    job_id: int
    imported_files: int
    skipped_files: int
    failed_files: int
    total_files: int


class MetadataProcessResponse(BaseModel):
    metadata_job_id: int
    thumbnail_job_id: int
    total_files: int
    metadata_updated: int
    metadata_failed: int
    thumbnails_generated: int
    thumbnail_failed: int


class VisualAnalysisProcessResponse(BaseModel):
    job_id: int
    total_photos: int
    analyzed_photos: int
    failed_photos: int
    skipped_non_images: int


class MediaAnalysisResponse(BaseModel):
    sharpness_score: float | None
    brightness_score: float | None
    contrast_score: float | None
    noise_score: float | None
    exposure_score: float | None
    overall_quality_score: float | None
    perceptual_hash: str | None
    analysis_version: str
    raw_metrics_json: str | None
    analyzed_at: datetime


class OriginalMediaResponse(BaseModel):
    id: int
    event_id: int
    source_id: int | None
    original_path: str
    relative_path: str | None
    filename: str
    extension: str | None
    media_type: str
    mime_type: str | None
    file_size_bytes: int | None
    checksum_sha256: str | None
    capture_datetime: datetime | None
    date_source: str | None
    width: int | None
    height: int | None
    duration_seconds: float | None
    thumbnail_path: str | None
    thumbnail_url: str | None
    metadata_json: str | None
    analysis: MediaAnalysisResponse | None
    status: str
    original_exists: bool
    imported_at: datetime


class OriginalMediaListResponse(BaseModel):
    items: list[OriginalMediaResponse]
