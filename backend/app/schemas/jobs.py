from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class JobLogResponse(BaseModel):
    id: int
    job_id: int
    original_media_id: int | None
    level: str
    message: str
    file_path: str | None
    details_json: str | None
    created_at: datetime


class JobResponse(BaseModel):
    id: int
    event_id: int | None
    job_type: str
    status: str
    progress_percent: float
    total_items: int
    processed_items: int
    failed_items: int
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    logs: list[JobLogResponse] = []


class JobListResponse(BaseModel):
    items: list[JobResponse]
