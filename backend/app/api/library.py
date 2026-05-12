from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.library import (
    LibraryCopyListResponse,
    LibraryMediaListResponse,
    LibraryPieceListResponse,
    LibrarySearchResponse,
)
from app.services.library_service import (
    list_library_copies,
    list_library_media,
    list_library_pieces,
    search_library,
)

router = APIRouter(prefix="/library", tags=["library"])


@router.get("/media", response_model=LibraryMediaListResponse)
def read_library_media(
    event_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    event_type: str | None = None,
    file_type: str | None = None,
    status: str | None = None,
    q: str | None = Query(default=None, max_length=160),
    source_type: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=100, ge=1, le=250),
    db: Session = Depends(get_db),
) -> LibraryMediaListResponse:
    return list_library_media(
        db,
        event_id=event_id,
        date_from=date_from,
        date_to=date_to,
        event_type=event_type,
        file_type=file_type,
        status=status,
        query=q,
        source_type=source_type,
        limit=limit,
    )


@router.get("/pieces", response_model=LibraryPieceListResponse)
def read_library_pieces(
    event_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    event_type: str | None = None,
    piece_type: str | None = None,
    status: str | None = None,
    q: str | None = Query(default=None, max_length=160),
    limit: int = Query(default=100, ge=1, le=250),
    db: Session = Depends(get_db),
) -> LibraryPieceListResponse:
    return list_library_pieces(
        db,
        event_id=event_id,
        date_from=date_from,
        date_to=date_to,
        event_type=event_type,
        piece_type=piece_type,
        status=status,
        query=q,
        limit=limit,
    )


@router.get("/copies", response_model=LibraryCopyListResponse)
def read_library_copies(
    event_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    event_type: str | None = None,
    copy_type: str | None = None,
    status: str | None = None,
    q: str | None = Query(default=None, max_length=160),
    limit: int = Query(default=100, ge=1, le=250),
    db: Session = Depends(get_db),
) -> LibraryCopyListResponse:
    return list_library_copies(
        db,
        event_id=event_id,
        date_from=date_from,
        date_to=date_to,
        event_type=event_type,
        copy_type=copy_type,
        status=status,
        query=q,
        limit=limit,
    )


@router.get("/search", response_model=LibrarySearchResponse)
def read_library_search(
    event_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    event_type: str | None = None,
    file_type: str | None = None,
    status: str | None = None,
    q: str | None = Query(default=None, max_length=160),
    limit: int = Query(default=100, ge=1, le=250),
    db: Session = Depends(get_db),
) -> LibrarySearchResponse:
    return search_library(
        db,
        event_id=event_id,
        date_from=date_from,
        date_to=date_to,
        event_type=event_type,
        file_type=file_type,
        status=status,
        query=q,
        limit=limit,
    )
