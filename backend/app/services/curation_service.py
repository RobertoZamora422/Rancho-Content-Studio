from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.jobs import DecisionLog
from app.models.media import CuratedMedia, OriginalMedia, SimilarityGroup, SimilarityGroupItem
from app.schemas.importing import (
    CuratedMediaListResponse,
    CuratedMediaResponse,
    CuratedMediaUpdate,
    CurationProcessResponse,
)
from app.services.event_service import require_event
from app.services.import_service import to_original_media_response
from app.services.job_service import add_job_log, finish_job, start_job, update_job_progress

AUTO_ACTOR = "system"
MANUAL_ACTOR = "user"
VALID_MANUAL_STATUSES = {
    "user_selected",
    "user_rejected",
    "selected",
    "alternative",
    "manual_review",
}
REJECTED_STATUSES = {
    "rejected_duplicate",
    "rejected_similar",
    "rejected_low_quality",
    "rejected_blurry",
    "rejected_dark",
    "user_rejected",
}


@dataclass(frozen=True)
class CurationDecision:
    status: str
    reason: str
    score: float | None


@dataclass(frozen=True)
class SimilarityContext:
    group_id: int
    group_type: str
    role: str
    representative_media_id: int | None


def curate_event_media(db: Session, event_id: int) -> CurationProcessResponse:
    require_event(db, event_id)
    job = start_job(db, "curate_media", event_id)
    media_items = list(
        db.scalars(
            select(OriginalMedia)
            .where(OriginalMedia.event_id == event_id)
            .options(selectinload(OriginalMedia.analysis))
            .order_by(OriginalMedia.imported_at.asc(), OriginalMedia.id.asc())
        ).all()
    )
    existing_by_media_id = {
        item.original_media_id: item
        for item in db.scalars(
            select(CuratedMedia).where(CuratedMedia.event_id == event_id)
        ).all()
    }
    similarity_context = build_similarity_context(db, event_id)

    selected = 0
    alternative = 0
    rejected = 0
    manual_review = 0
    preserved_manual_overrides = 0

    for media in media_items:
        existing = existing_by_media_id.get(media.id)
        if existing and existing.is_manual_override:
            preserved_manual_overrides += 1
            selected, alternative, rejected, manual_review = count_status(
                existing.selection_status,
                selected,
                alternative,
                rejected,
                manual_review,
            )
            continue

        previous_status = existing.selection_status if existing else None
        previous_reason = existing.reason if existing else None
        decision = decide_media(media, similarity_context.get(media.id))
        curated = upsert_curated_media(db, event_id, media, decision, existing)
        log_decision_if_changed(
            db,
            event_id,
            media.id,
            previous_status,
            previous_reason,
            curated,
        )
        selected, alternative, rejected, manual_review = count_status(
            curated.selection_status,
            selected,
            alternative,
            rejected,
            manual_review,
        )
        add_job_log(
            db,
            job,
            "info",
            f"{media.filename}: {curated.selection_status}. {curated.reason}",
            file_path=media.original_path,
            original_media_id=media.id,
        )
        update_job_progress(job, len(media_items), selected + alternative + rejected + manual_review, 0)
        db.flush()

    if selected == 0 and media_items:
        add_job_log(
            db,
            job,
            "warning",
            "La curacion no dejo medios seleccionados; revisa manualmente los estados.",
        )

    finish_job(
        job,
        "completed",
        total_items=len(media_items),
        processed_items=len(media_items),
        failed_items=0,
    )
    db.commit()

    return CurationProcessResponse(
        job_id=job.id,
        total_media=len(media_items),
        selected=selected,
        alternative=alternative,
        rejected=rejected,
        manual_review=manual_review,
        preserved_manual_overrides=preserved_manual_overrides,
    )


def list_curated_media(db: Session, event_id: int) -> CuratedMediaListResponse:
    require_event(db, event_id)
    items = db.scalars(
        select(CuratedMedia)
        .where(CuratedMedia.event_id == event_id)
        .options(
            selectinload(CuratedMedia.original_media).selectinload(OriginalMedia.analysis),
        )
        .order_by(CuratedMedia.selection_status.asc(), CuratedMedia.score.desc(), CuratedMedia.id.asc())
    ).all()
    return CuratedMediaListResponse(items=[to_curated_media_response(item) for item in items])


def update_curated_media(
    db: Session,
    event_id: int,
    curated_id: int,
    payload: CuratedMediaUpdate,
) -> CuratedMediaResponse:
    require_event(db, event_id)
    status_value = payload.selection_status.strip()
    if status_value not in VALID_MANUAL_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado manual de curacion no permitido.",
        )

    curated = db.scalar(
        select(CuratedMedia)
        .where(CuratedMedia.id == curated_id, CuratedMedia.event_id == event_id)
        .options(selectinload(CuratedMedia.original_media).selectinload(OriginalMedia.analysis))
    )
    if curated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curacion no encontrada.")
    if not curated.original_media.original_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede seleccionar un archivo original marcado como faltante.",
        )

    previous_status = curated.selection_status
    curated.selection_status = status_value
    curated.reason = payload.reason or manual_reason(status_value)
    curated.selected_by = MANUAL_ACTOR
    curated.is_manual_override = True
    curated.updated_at = datetime.now(timezone.utc)
    db.add(
        DecisionLog(
            event_id=event_id,
            original_media_id=curated.original_media_id,
            entity_type="curated_media",
            entity_id=curated.id,
            decision_type="curation_manual",
            reason=f"{previous_status} -> {status_value}. {curated.reason}",
            actor=MANUAL_ACTOR,
        )
    )
    db.commit()
    db.refresh(curated)
    return to_curated_media_response(curated)


def build_similarity_context(db: Session, event_id: int) -> dict[int, SimilarityContext]:
    groups = db.scalars(
        select(SimilarityGroup)
        .where(SimilarityGroup.event_id == event_id)
        .options(selectinload(SimilarityGroup.items))
    ).all()
    contexts: dict[int, SimilarityContext] = {}
    for group in groups:
        for item in group.items:
            current = contexts.get(item.original_media_id)
            next_context = SimilarityContext(
                group_id=group.id,
                group_type=group.group_type,
                role=item.role,
                representative_media_id=group.representative_media_id,
            )
            if current is None or priority(next_context) > priority(current):
                contexts[item.original_media_id] = next_context
    return contexts


def priority(context: SimilarityContext) -> int:
    if context.group_type == "checksum_duplicate":
        return 3
    if context.group_type == "perceptual_hash":
        return 2
    return 1


def decide_media(media: OriginalMedia, context: SimilarityContext | None) -> CurationDecision:
    quality = media.analysis.overall_quality_score if media.analysis else None
    sharpness = media.analysis.sharpness_score if media.analysis else None
    exposure = media.analysis.exposure_score if media.analysis else None
    brightness = media.analysis.brightness_score if media.analysis else None

    if not media.original_exists:
        return CurationDecision("manual_review", "Archivo original faltante; requiere revision.", quality)
    if media.media_type != "image":
        return CurationDecision("manual_review", "Video pendiente de analisis avanzado en fase posterior.", quality)
    if media.analysis is None:
        return CurationDecision("manual_review", "Foto sin analisis visual; ejecuta Analizar fotos.", quality)

    if context and context.group_type == "checksum_duplicate" and context.role != "representative":
        return CurationDecision(
            "rejected_duplicate",
            f"Duplicado exacto del grupo #{context.group_id}; descarte logico reversible.",
            quality,
        )

    if context and context.group_type == "perceptual_hash" and context.role != "representative":
        return CurationDecision(
            "alternative",
            f"Alternativa visual del grupo #{context.group_id}; se conserva para revision.",
            quality,
        )

    if context and context.role == "representative":
        return CurationDecision(
            "selected",
            f"Representante sugerido del grupo #{context.group_id} por mejor calidad.",
            quality,
        )

    if sharpness is not None and sharpness < 30:
        return CurationDecision("rejected_blurry", "Nitidez baja; descarte logico reversible.", quality)
    if (exposure is not None and exposure < 30) or (brightness is not None and brightness < 18):
        return CurationDecision("rejected_dark", "Exposicion o brillo bajo; descarte logico reversible.", quality)
    if quality is not None and quality < 35:
        return CurationDecision("rejected_low_quality", "Puntaje global bajo; descarte logico reversible.", quality)
    if quality is not None and quality < 45:
        return CurationDecision("manual_review", "Calidad media-baja; requiere revision humana.", quality)

    return CurationDecision("selected", "Foto con calidad suficiente para seleccion inicial.", quality)


def upsert_curated_media(
    db: Session,
    event_id: int,
    media: OriginalMedia,
    decision: CurationDecision,
    existing: CuratedMedia | None,
) -> CuratedMedia:
    curated = existing or CuratedMedia(event_id=event_id, original_media_id=media.id)
    curated.selection_status = decision.status
    curated.reason = decision.reason
    curated.score = decision.score
    curated.selected_by = AUTO_ACTOR
    curated.is_manual_override = False
    curated.updated_at = datetime.now(timezone.utc)
    db.add(curated)
    db.flush()
    return curated


def log_decision_if_changed(
    db: Session,
    event_id: int,
    media_id: int,
    previous_status: str | None,
    previous_reason: str | None,
    current: CuratedMedia,
) -> None:
    if previous_status == current.selection_status and previous_reason == current.reason:
        return
    db.add(
        DecisionLog(
            event_id=event_id,
            original_media_id=media_id,
            entity_type="curated_media",
            entity_id=current.id,
            decision_type="curation_auto",
            reason=f"{current.selection_status}. {current.reason}",
            actor=AUTO_ACTOR,
        )
    )


def count_status(
    status_value: str,
    selected: int,
    alternative: int,
    rejected: int,
    manual_review: int,
) -> tuple[int, int, int, int]:
    if status_value in {"selected", "user_selected"}:
        selected += 1
    elif status_value == "alternative":
        alternative += 1
    elif status_value in REJECTED_STATUSES:
        rejected += 1
    else:
        manual_review += 1
    return selected, alternative, rejected, manual_review


def manual_reason(status_value: str) -> str:
    labels = {
        "user_selected": "Seleccionado manualmente por el usuario.",
        "user_rejected": "Rechazado manualmente por el usuario.",
        "selected": "Marcado como seleccionado por el usuario.",
        "alternative": "Marcado como alternativa por el usuario.",
        "manual_review": "Enviado a revision manual por el usuario.",
    }
    return labels[status_value]


def to_curated_media_response(item: CuratedMedia) -> CuratedMediaResponse:
    return CuratedMediaResponse(
        id=item.id,
        event_id=item.event_id,
        original_media_id=item.original_media_id,
        selection_status=item.selection_status,
        reason=item.reason,
        score=item.score,
        selected_by=item.selected_by,
        is_manual_override=item.is_manual_override,
        created_at=item.created_at,
        updated_at=item.updated_at,
        media=to_original_media_response(item.original_media),
    )
