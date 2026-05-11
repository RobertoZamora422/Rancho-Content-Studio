from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.events import EventCreate, EventListResponse, EventResponse, EventUpdate
from app.schemas.importing import (
    CuratedMediaListResponse,
    CuratedMediaResponse,
    CuratedMediaUpdate,
    CurationProcessResponse,
    EnhancedMediaListResponse,
    EnhancedMediaResponse,
    EnhancedMediaUpdate,
    ImportResponse,
    MetadataProcessResponse,
    OriginalMediaListResponse,
    PhotoEnhancementRequest,
    PhotoEnhancementResponse,
    ScanResponse,
    SimilarityDetectionResponse,
    SimilarityGroupListResponse,
    SourceCreate,
    SourceResponse,
    VideoEnhancementRequest,
    VideoEnhancementResponse,
    VisualAnalysisProcessResponse,
)
from app.schemas.pieces import (
    ContentPieceListResponse,
    ContentPieceResponse,
    ContentPieceUpdate,
    PieceGenerationResponse,
)
from app.services.content_piece_service import (
    generate_event_pieces,
    list_event_content_pieces,
    update_content_piece,
)
from app.services.curation_service import curate_event_media, list_curated_media, update_curated_media
from app.services.enhancement_service import (
    enhance_event_photos,
    enhance_event_videos,
    list_enhanced_media,
    update_enhanced_media_status,
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
from app.services.similarity_service import detect_event_similarities, list_similarity_groups
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


@router.post("/{event_id}/detect-similarity", response_model=SimilarityDetectionResponse)
def detect_similarity(
    event_id: int,
    db: Session = Depends(get_db),
) -> SimilarityDetectionResponse:
    return detect_event_similarities(db, event_id)


@router.post("/{event_id}/curate-media", response_model=CurationProcessResponse)
def curate_media(
    event_id: int,
    db: Session = Depends(get_db),
) -> CurationProcessResponse:
    return curate_event_media(db, event_id)


@router.get("/{event_id}/curated-media", response_model=CuratedMediaListResponse)
def read_curated_media(
    event_id: int,
    db: Session = Depends(get_db),
) -> CuratedMediaListResponse:
    return list_curated_media(db, event_id)


@router.patch(
    "/{event_id}/curated-media/{curated_id}",
    response_model=CuratedMediaResponse,
)
def update_curated_media_decision(
    event_id: int,
    curated_id: int,
    payload: CuratedMediaUpdate,
    db: Session = Depends(get_db),
) -> CuratedMediaResponse:
    return update_curated_media(db, event_id, curated_id, payload)


@router.post("/{event_id}/enhance-photos", response_model=PhotoEnhancementResponse)
def enhance_photos(
    event_id: int,
    payload: PhotoEnhancementRequest,
    db: Session = Depends(get_db),
) -> PhotoEnhancementResponse:
    return enhance_event_photos(db, event_id, payload)


@router.post("/{event_id}/enhance-videos", response_model=VideoEnhancementResponse)
def enhance_videos(
    event_id: int,
    payload: VideoEnhancementRequest,
    db: Session = Depends(get_db),
) -> VideoEnhancementResponse:
    return enhance_event_videos(db, event_id, payload)


@router.get("/{event_id}/enhanced-media", response_model=EnhancedMediaListResponse)
def read_enhanced_media(
    event_id: int,
    db: Session = Depends(get_db),
) -> EnhancedMediaListResponse:
    return list_enhanced_media(db, event_id)


@router.patch(
    "/{event_id}/enhanced-media/{enhanced_id}",
    response_model=EnhancedMediaResponse,
)
def update_enhanced_media_decision(
    event_id: int,
    enhanced_id: int,
    payload: EnhancedMediaUpdate,
    db: Session = Depends(get_db),
) -> EnhancedMediaResponse:
    return update_enhanced_media_status(db, event_id, enhanced_id, payload)


@router.post("/{event_id}/generate-pieces", response_model=PieceGenerationResponse)
def generate_pieces(
    event_id: int,
    db: Session = Depends(get_db),
) -> PieceGenerationResponse:
    return generate_event_pieces(db, event_id)


@router.get("/{event_id}/content-pieces", response_model=ContentPieceListResponse)
def read_content_pieces(
    event_id: int,
    db: Session = Depends(get_db),
) -> ContentPieceListResponse:
    return list_event_content_pieces(db, event_id)


@router.patch(
    "/{event_id}/content-pieces/{piece_id}",
    response_model=ContentPieceResponse,
)
def update_piece(
    event_id: int,
    piece_id: int,
    payload: ContentPieceUpdate,
    db: Session = Depends(get_db),
) -> ContentPieceResponse:
    return update_content_piece(db, event_id, piece_id, payload)


@router.get("/{event_id}/similarity-groups", response_model=SimilarityGroupListResponse)
def read_similarity_groups(
    event_id: int,
    db: Session = Depends(get_db),
) -> SimilarityGroupListResponse:
    return list_similarity_groups(db, event_id)


@router.get("/{event_id}/media/original", response_model=OriginalMediaListResponse)
def read_original_media(
    event_id: int,
    db: Session = Depends(get_db),
) -> OriginalMediaListResponse:
    return OriginalMediaListResponse(items=list_original_media(db, event_id))
