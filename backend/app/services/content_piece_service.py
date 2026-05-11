from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.content import ContentPiece, ContentPieceMedia
from app.models.jobs import DecisionLog
from app.models.media import EnhancedMedia, OriginalMedia
from app.schemas.pieces import (
    ContentPieceListResponse,
    ContentPieceMediaResponse,
    ContentPieceResponse,
    ContentPieceUpdate,
    PieceGenerationResponse,
)
from app.services.enhancement_service import to_enhanced_media_response
from app.services.event_service import require_event
from app.services.import_service import get_event_path
from app.services.job_service import add_job_log, finish_job, start_job

AVAILABLE_ENHANCED_STATUSES = {"completed", "approved"}
VALID_PIECE_STATUSES = {"draft", "generated", "in_review", "approved", "rejected"}


@dataclass(frozen=True)
class PieceProposal:
    piece_type: str
    title: str
    purpose: str
    target_platform: str
    aspect_ratio: str
    media: list[EnhancedMedia]
    reason: str


def generate_event_pieces(db: Session, event_id: int) -> PieceGenerationResponse:
    event = require_event(db, event_id)
    event_path = get_event_path(event)
    job = start_job(db, "generate_pieces", event.id)
    media_items = list_available_enhanced_media(db, event.id, event_path)

    if not media_items:
        add_job_log(
            db,
            job,
            "warning",
            "No hay medios mejorados completados o aprobados para generar piezas.",
        )
        finish_job(job, "completed", total_items=0, processed_items=0, failed_items=0)
        db.commit()
        return PieceGenerationResponse(
            job_id=job.id,
            total_available_media=0,
            pieces_created=0,
            pieces_skipped=0,
        )

    proposals = build_piece_proposals(media_items)
    existing_signatures = load_existing_piece_signatures(db, event.id)
    pieces_created = 0
    pieces_skipped = 0

    for proposal in proposals:
        signature = proposal_signature(proposal)
        if signature in existing_signatures:
            pieces_skipped += 1
            add_job_log(
                db,
                job,
                "info",
                f"Pieza omitida por firma existente: {proposal.title}.",
                details_json=json.dumps({"signature": list(signature)}, ensure_ascii=True),
            )
            continue

        piece = ContentPiece(
            event_id=event.id,
            piece_type=proposal.piece_type,
            title=proposal.title,
            purpose=proposal.purpose,
            target_platform=proposal.target_platform,
            aspect_ratio=proposal.aspect_ratio,
            status="generated",
            metadata_json=json.dumps(
                {
                    "generated_by": "phase12_rules_v1",
                    "recommendation_reason": proposal.reason,
                    "media_signature": list(signature),
                },
                ensure_ascii=True,
            ),
        )
        db.add(piece)
        db.flush()
        for index, enhanced in enumerate(proposal.media, start=1):
            db.add(
                ContentPieceMedia(
                    piece_id=piece.id,
                    original_media_id=enhanced.original_media_id,
                    enhanced_media_id=enhanced.id,
                    position=index,
                    role="cover" if index == 1 else "sequence",
                    notes=proposal.reason if index == 1 else None,
                )
            )

        db.flush()
        db.add(
            DecisionLog(
                event_id=event.id,
                entity_type="content_piece",
                entity_id=piece.id,
                decision_type="piece_generated",
                reason=proposal.reason,
                actor="system",
            )
        )
        pieces_created += 1
        existing_signatures.add(signature)
        add_job_log(db, job, "info", f"Pieza generada: {proposal.title}.")

    finish_job(
        job,
        "completed",
        total_items=len(proposals),
        processed_items=pieces_created + pieces_skipped,
        failed_items=0,
    )
    db.commit()

    return PieceGenerationResponse(
        job_id=job.id,
        total_available_media=len(media_items),
        pieces_created=pieces_created,
        pieces_skipped=pieces_skipped,
    )


def list_event_content_pieces(db: Session, event_id: int) -> ContentPieceListResponse:
    require_event(db, event_id)
    pieces = db.scalars(
        select(ContentPiece)
        .where(ContentPiece.event_id == event_id)
        .options(piece_load_options())
        .order_by(ContentPiece.created_at.desc(), ContentPiece.id.desc())
    ).all()
    return ContentPieceListResponse(items=[to_content_piece_response(piece) for piece in pieces])


def update_content_piece(
    db: Session,
    event_id: int,
    piece_id: int,
    payload: ContentPieceUpdate,
) -> ContentPieceResponse:
    require_event(db, event_id)
    piece = db.scalar(
        select(ContentPiece)
        .where(ContentPiece.event_id == event_id, ContentPiece.id == piece_id)
        .options(piece_load_options())
    )
    if piece is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pieza no encontrada.")

    previous_status = piece.status
    if payload.title is not None:
        next_title = payload.title.strip()
        if not next_title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El titulo de la pieza no puede estar vacio.",
            )
        piece.title = next_title
    if payload.purpose is not None:
        piece.purpose = payload.purpose.strip() or None
    if payload.target_platform is not None:
        piece.target_platform = payload.target_platform.strip() or None
    if payload.aspect_ratio is not None:
        piece.aspect_ratio = payload.aspect_ratio.strip() or None

    if payload.media_item_order is not None:
        apply_media_item_order(db, piece, payload.media_item_order)

    if payload.status is not None:
        next_status = payload.status.strip()
        if next_status not in VALID_PIECE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estado de pieza no permitido.",
            )
        if next_status == "approved" and not piece.media_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede aprobar una pieza sin medios.",
            )
        piece.status = next_status
        now = datetime.now(timezone.utc)
        if next_status == "approved":
            piece.approved_at = now
            piece.rejected_at = None
        elif next_status == "rejected":
            piece.rejected_at = now
            piece.approved_at = None

    piece.updated_at = datetime.now(timezone.utc)
    db.add(
        DecisionLog(
            event_id=event_id,
            entity_type="content_piece",
            entity_id=piece.id,
            decision_type="piece_manual_update",
            reason=f"{previous_status} -> {piece.status}.",
            actor="user",
        )
    )
    db.commit()
    db.refresh(piece)
    piece = db.scalar(
        select(ContentPiece)
        .where(ContentPiece.event_id == event_id, ContentPiece.id == piece_id)
        .options(piece_load_options())
    )
    if piece is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pieza no encontrada.")
    return to_content_piece_response(piece)


def list_available_enhanced_media(
    db: Session,
    event_id: int,
    event_path: Path,
) -> list[EnhancedMedia]:
    candidates = db.scalars(
        select(EnhancedMedia)
        .where(
            EnhancedMedia.event_id == event_id,
            EnhancedMedia.status.in_(AVAILABLE_ENHANCED_STATUSES),
        )
        .options(selectinload(EnhancedMedia.original_media).selectinload(OriginalMedia.analysis))
        .order_by(EnhancedMedia.status.asc(), EnhancedMedia.created_at.asc(), EnhancedMedia.id.asc())
    ).all()
    available: list[EnhancedMedia] = []
    for item in candidates:
        output_path = Path(item.output_path)
        if not output_path.is_absolute():
            output_path = event_path / output_path
        if output_path.is_file():
            available.append(item)
    return available


def build_piece_proposals(media_items: list[EnhancedMedia]) -> list[PieceProposal]:
    photos = [item for item in media_items if item.original_media.media_type == "image"]
    videos = [item for item in media_items if item.original_media.media_type == "video"]
    proposals: list[PieceProposal] = []

    if videos:
        reel_media = videos[:5]
        proposals.append(
            PieceProposal(
                piece_type="reel",
                title="Reel de ambiente",
                purpose="ambiente",
                target_platform="Instagram/TikTok",
                aspect_ratio="mantener_original",
                media=reel_media,
                reason="Videos mejorados seleccionados para una pieza dinamica sin forzar verticalidad.",
            )
        )

    if len(photos) >= 3:
        carousel_media = photos[:10]
        proposals.append(
            PieceProposal(
                piece_type="carousel",
                title="Carrusel principal",
                purpose="resumen_evento",
                target_platform="Instagram/Facebook",
                aspect_ratio="4:5 recomendado",
                media=carousel_media,
                reason="Fotos mejoradas suficientes para una narrativa visual del evento.",
            )
        )

    story_media = [*videos[:2], *photos[:4]]
    if story_media:
        proposals.append(
            PieceProposal(
                piece_type="story",
                title="Historias destacadas",
                purpose="momentos_destacados",
                target_platform="Instagram/Facebook Stories",
                aspect_ratio="mantener_original",
                media=story_media[:6],
                reason="Seleccion corta de medios para historias revisables.",
            )
        )

    if photos:
        proposals.append(
            PieceProposal(
                piece_type="single_post",
                title="Publicacion individual destacada",
                purpose="felicitacion",
                target_platform="Instagram/Facebook",
                aspect_ratio="4:5 recomendado",
                media=photos[:1],
                reason="Mejor foto disponible para una publicacion individual.",
            )
        )

    if videos and photos:
        proposals.append(
            PieceProposal(
                piece_type="promo_piece",
                title="Pieza promocional del evento",
                purpose="promocional",
                target_platform="Instagram/Facebook",
                aspect_ratio="mantener_original",
                media=[*videos[:1], *photos[:3]],
                reason="Combinacion de video y fotos para una pieza promocional ligera.",
            )
        )

    return [proposal for proposal in proposals if proposal.media]


def load_existing_piece_signatures(db: Session, event_id: int) -> set[tuple[str, tuple[int, ...]]]:
    pieces = db.scalars(
        select(ContentPiece)
        .where(ContentPiece.event_id == event_id)
        .options(selectinload(ContentPiece.media_items))
    ).all()
    signatures: set[tuple[str, tuple[int, ...]]] = set()
    for piece in pieces:
        enhanced_ids = tuple(
            sorted(
                item.enhanced_media_id
                for item in piece.media_items
                if item.enhanced_media_id is not None
            )
        )
        if enhanced_ids:
            signatures.add((piece.piece_type, enhanced_ids))

    return signatures


def proposal_signature(proposal: PieceProposal) -> tuple[str, tuple[int, ...]]:
    return proposal.piece_type, tuple(sorted(item.id for item in proposal.media))


def apply_media_item_order(
    db: Session,
    piece: ContentPiece,
    media_item_order: list[int],
) -> None:
    current_ids = {item.id for item in piece.media_items}
    next_ids = set(media_item_order)
    if current_ids != next_ids or len(media_item_order) != len(current_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El orden enviado debe incluir exactamente los medios actuales de la pieza.",
        )
    by_id = {item.id: item for item in piece.media_items}
    for offset, item in enumerate(piece.media_items, start=1):
        item.position = -offset
    db.flush()
    for position, item_id in enumerate(media_item_order, start=1):
        item = by_id[item_id]
        item.position = position
        item.role = "cover" if position == 1 else "sequence"


def piece_load_options():
    return selectinload(ContentPiece.media_items).selectinload(
        ContentPieceMedia.enhanced_media
    ).selectinload(EnhancedMedia.original_media).selectinload(OriginalMedia.analysis)


def to_content_piece_response(piece: ContentPiece) -> ContentPieceResponse:
    media_items = sorted(piece.media_items, key=lambda item: item.position)
    return ContentPieceResponse(
        id=piece.id,
        event_id=piece.event_id,
        piece_type=piece.piece_type,
        title=piece.title,
        purpose=piece.purpose,
        target_platform=piece.target_platform,
        aspect_ratio=piece.aspect_ratio,
        output_path=piece.output_path,
        status=piece.status,
        metadata_json=piece.metadata_json,
        created_at=piece.created_at,
        updated_at=piece.updated_at,
        approved_at=piece.approved_at,
        rejected_at=piece.rejected_at,
        media_items=[
            ContentPieceMediaResponse(
                id=item.id,
                piece_id=item.piece_id,
                original_media_id=item.original_media_id,
                enhanced_media_id=item.enhanced_media_id,
                position=item.position,
                role=item.role,
                notes=item.notes,
                enhanced_media=(
                    to_enhanced_media_response(item.enhanced_media)
                    if item.enhanced_media
                    else None
                ),
            )
            for item in media_items
        ],
    )
