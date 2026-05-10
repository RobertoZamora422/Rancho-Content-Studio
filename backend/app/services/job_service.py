from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.jobs import ProcessingJob, ProcessingJobLog
from app.schemas.jobs import JobLogResponse, JobResponse


def start_job(db: Session, job_type: str, event_id: int | None = None) -> ProcessingJob:
    job = ProcessingJob(
        event_id=event_id,
        job_type=job_type,
        status="running",
        progress_percent=0,
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    db.flush()
    return job


def add_job_log(
    db: Session,
    job: ProcessingJob,
    level: str,
    message: str,
    file_path: str | None = None,
    original_media_id: int | None = None,
    details_json: str | None = None,
) -> None:
    db.add(
        ProcessingJobLog(
            job_id=job.id,
            original_media_id=original_media_id,
            level=level,
            message=message,
            file_path=file_path,
            details_json=details_json,
        )
    )


def finish_job(
    job: ProcessingJob,
    status_value: str,
    total_items: int,
    processed_items: int,
    failed_items: int,
    error_message: str | None = None,
) -> None:
    job.status = status_value
    job.total_items = total_items
    job.processed_items = processed_items
    job.failed_items = failed_items
    job.progress_percent = 100 if total_items == 0 else round(
        ((processed_items + failed_items) / total_items) * 100,
        2,
    )
    job.finished_at = datetime.now(timezone.utc)
    job.error_message = error_message


def get_job(db: Session, job_id: int) -> JobResponse:
    job = db.scalar(
        select(ProcessingJob)
        .where(ProcessingJob.id == job_id)
        .options(selectinload(ProcessingJob.logs))
    )
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job no encontrado.")
    return to_job_response(job)


def list_event_jobs(db: Session, event_id: int) -> list[JobResponse]:
    jobs = db.scalars(
        select(ProcessingJob)
        .where(ProcessingJob.event_id == event_id)
        .options(selectinload(ProcessingJob.logs))
        .order_by(ProcessingJob.created_at.desc())
    ).all()
    return [to_job_response(job) for job in jobs]


def to_job_response(job: ProcessingJob) -> JobResponse:
    return JobResponse(
        id=job.id,
        event_id=job.event_id,
        job_type=job.job_type,
        status=job.status,
        progress_percent=job.progress_percent,
        total_items=job.total_items,
        processed_items=job.processed_items,
        failed_items=job.failed_items,
        started_at=job.started_at,
        finished_at=job.finished_at,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        logs=[
            JobLogResponse(
                id=log.id,
                job_id=log.job_id,
                original_media_id=log.original_media_id,
                level=log.level,
                message=log.message,
                file_path=log.file_path,
                details_json=log.details_json,
                created_at=log.created_at,
            )
            for log in sorted(job.logs, key=lambda item: item.created_at)
        ],
    )
