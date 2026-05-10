from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.events import EventCreate, EventListResponse, EventResponse, EventUpdate
from app.schemas.importing import (
    ImportResponse,
    MetadataProcessResponse,
    OriginalMediaListResponse,
    ScanResponse,
    SourceCreate,
    SourceResponse,
    VisualAnalysisProcessResponse,
)
from app.services.event_service import (
    archive_event,
    create_event,
    get_event,
    list_events,
    logically_delete_event,
    update_event,
)
from app.services.import_service import (
    add_source,
    import_event_media,
    list_original_media,
    list_sources,
    scan_event_sources,
)
from app.services.metadata_service import process_event_metadata_and_thumbnails
from app.services.visual_analysis_service import analyze_event_photos

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=EventListResponse)
def read_events(
    include_archived: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> EventListResponse:
    return EventListResponse(items=list_events(db, include_archived=include_archived))


@router.post("", response_model=EventResponse, status_code=201)
def create_new_event(payload: EventCreate, db: Session = Depends(get_db)) -> EventResponse:
    return create_event(db, payload)


@router.get("/{event_id}", response_model=EventResponse)
def read_event(event_id: int, db: Session = Depends(get_db)) -> EventResponse:
    return get_event(db, event_id)


@router.put("/{event_id}", response_model=EventResponse)
def update_existing_event(
    event_id: int,
    payload: EventUpdate,
    db: Session = Depends(get_db),
) -> EventResponse:
    return update_event(db, event_id, payload)


@router.delete("/{event_id}", response_model=EventResponse)
def delete_existing_event(event_id: int, db: Session = Depends(get_db)) -> EventResponse:
    return logically_delete_event(db, event_id)


@router.post("/{event_id}/archive", response_model=EventResponse)
def archive_existing_event(event_id: int, db: Session = Depends(get_db)) -> EventResponse:
    return archive_event(db, event_id)


@router.get("/{event_id}/sources", response_model=list[SourceResponse])
def read_event_sources(event_id: int, db: Session = Depends(get_db)) -> list[SourceResponse]:
    return list_sources(db, event_id)


@router.post("/{event_id}/sources", response_model=SourceResponse, status_code=201)
def create_event_source(
    event_id: int,
    payload: SourceCreate,
    db: Session = Depends(get_db),
) -> SourceResponse:
    return add_source(db, event_id, payload)


@router.post("/{event_id}/scan", response_model=ScanResponse)
def scan_event(event_id: int, db: Session = Depends(get_db)) -> ScanResponse:
    return scan_event_sources(db, event_id)


@router.post("/{event_id}/import", response_model=ImportResponse)
def import_media(event_id: int, db: Session = Depends(get_db)) -> ImportResponse:
    return import_event_media(db, event_id)


@router.post("/{event_id}/process-metadata", response_model=MetadataProcessResponse)
def process_metadata(
    event_id: int,
    db: Session = Depends(get_db),
) -> MetadataProcessResponse:
    return process_event_metadata_and_thumbnails(db, event_id)


@router.post("/{event_id}/analyze-photos", response_model=VisualAnalysisProcessResponse)
def analyze_photos(
    event_id: int,
    db: Session = Depends(get_db),
) -> VisualAnalysisProcessResponse:
    return analyze_event_photos(db, event_id)


@router.get("/{event_id}/media/original", response_model=OriginalMediaListResponse)
def read_original_media(
    event_id: int,
    db: Session = Depends(get_db),
) -> OriginalMediaListResponse:
    return OriginalMediaListResponse(items=list_original_media(db, event_id))
