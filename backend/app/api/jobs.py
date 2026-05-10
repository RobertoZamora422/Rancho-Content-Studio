from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.jobs import JobListResponse, JobResponse
from app.services.event_service import require_event
from app.services.job_service import get_job, list_event_jobs

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=JobResponse)
def read_job(job_id: int, db: Session = Depends(get_db)) -> JobResponse:
    return get_job(db, job_id)


@router.get("/events/{event_id}/jobs", response_model=JobListResponse)
def read_event_jobs(event_id: int, db: Session = Depends(get_db)) -> JobListResponse:
    require_event(db, event_id)
    return JobListResponse(items=list_event_jobs(db, event_id))
