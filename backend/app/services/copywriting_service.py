from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.content import ContentPiece, ContentPieceMedia, GeneratedCopy
from app.models.events import ContentEvent
from app.models.identity import EditorialProfile
from app.models.jobs import DecisionLog
from app.models.media import EnhancedMedia
from app.schemas.copywriting import (
    CopyGenerationRequest,
    CopyGenerationResponse,
    GeneratedCopyListResponse,
    GeneratedCopyResponse,
    GeneratedCopyUpdate,
)
from app.services.editorial_profile_service import require_default_editorial_profile
from app.services.event_service import require_event
from app.services.import_service import get_event_path
from app.services.job_service import add_job_log, finish_job, start_job
from app.utils.event_folders import safe_windows_name

VALID_COPY_STATUSES = {"generated", "edited", "approved", "rejected", "regenerated", "archived"}
VALID_FEEDBACK = {
    "me_gusta",
    "no_me_gusta",
    "mas_humano",
    "mas_corto",
    "menos_cursi",
    "mas_calido",
    "mas_comercial",
    "mas_natural",
}


@dataclass(frozen=True)
class CopyVariant:
    copy_type: str
    variant_label: str
    body: str
    hashtags: list[str]
    cta: str | None
    style_notes: str


def generate_piece_copy(
    db: Session,
    event_id: int,
    piece_id: int,
    payload: CopyGenerationRequest,
) -> CopyGenerationResponse:
    event = require_event(db, event_id)
    piece = require_piece_for_copy(db, event_id, piece_id)
    if piece.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aprueba la pieza antes de generar copy.",
        )

    profile = require_default_editorial_profile(db)
    feedback = normalize_feedback(payload.feedback)
    existing_count = db.scalar(
        select(func.count()).select_from(GeneratedCopy).where(GeneratedCopy.piece_id == piece.id)
    )
    next_status = "regenerated" if existing_count else "generated"
    job = start_job(db, "generate_copy", event.id)
    variants = build_copy_variants(event, piece, profile, feedback)
    created: list[GeneratedCopy] = []

    for variant in variants:
        body = remove_avoided_terms(variant.body, profile)
        if not body.strip():
            add_job_log(db, job, "error", f"Copy vacio omitido: {variant.variant_label}.")
            continue

        generated = GeneratedCopy(
            piece_id=piece.id,
            editorial_profile_id=profile.id,
            variant_label=variant.variant_label,
            copy_type=variant.copy_type,
            body=body,
            hashtags_json=json.dumps(variant.hashtags, ensure_ascii=True),
            cta=variant.cta,
            style_notes=variant.style_notes,
            status=next_status,
            generation_mode="local_template",
            ai_provider=None,
            prompt_context=json.dumps(
                build_prompt_context(event, piece, profile, feedback, variant),
                ensure_ascii=True,
            ),
            user_feedback=feedback,
        )
        db.add(generated)
        db.flush()
        export_copy_markdown(event, piece, generated)
        db.add(
            DecisionLog(
                event_id=event.id,
                entity_type="generated_copy",
                entity_id=generated.id,
                decision_type="copy_generated",
                reason=f"Variante {variant.variant_label} creada con motor local.",
                actor="system",
            )
        )
        add_job_log(
            db,
            job,
            "info",
            f"Copy generado: {variant.variant_label}.",
            file_path=generated.output_path,
        )
        created.append(generated)

    failed = len(variants) - len(created)
    finish_job(
        job,
        "completed" if failed == 0 else "completed_with_errors",
        total_items=len(variants),
        processed_items=len(created),
        failed_items=failed,
    )
    db.commit()

    refreshed = [
        require_copy(db, event_id, piece_id, generated.id)
        for generated in created
    ]
    return CopyGenerationResponse(
        job_id=job.id,
        piece_id=piece.id,
        copies_created=len(refreshed),
        feedback=feedback,
        items=[to_generated_copy_response(item, profile) for item in refreshed],
    )


def list_piece_copies(
    db: Session,
    event_id: int,
    piece_id: int,
) -> GeneratedCopyListResponse:
    profile = require_default_editorial_profile(db)
    require_piece_for_copy(db, event_id, piece_id)
    copies = db.scalars(
        select(GeneratedCopy)
        .where(GeneratedCopy.piece_id == piece_id)
        .order_by(GeneratedCopy.created_at.desc(), GeneratedCopy.id.desc())
    ).all()
    return GeneratedCopyListResponse(
        items=[to_generated_copy_response(item, profile) for item in copies]
    )


def update_piece_copy(
    db: Session,
    event_id: int,
    piece_id: int,
    copy_id: int,
    payload: GeneratedCopyUpdate,
) -> GeneratedCopyResponse:
    event = require_event(db, event_id)
    piece = require_piece_for_copy(db, event_id, piece_id)
    profile = require_default_editorial_profile(db)
    generated = require_copy(db, event_id, piece_id, copy_id)

    if payload.body is not None:
        generated.body = payload.body.strip()
        generated.status = "edited" if payload.status is None else generated.status
    if payload.variant_label is not None:
        generated.variant_label = payload.variant_label.strip() or generated.variant_label
    if payload.user_feedback is not None:
        generated.user_feedback = normalize_feedback(payload.user_feedback)
    if payload.status is not None:
        next_status = payload.status.strip()
        if next_status not in VALID_COPY_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estado de copy no permitido.",
            )
        if next_status == "approved":
            validate_copy_can_be_approved(generated, profile)
            generated.approved_at = datetime.now(timezone.utc)
            generated.rejected_at = None
            append_profile_example(profile, "approved_examples", generated.body)
        elif next_status == "rejected":
            generated.rejected_at = datetime.now(timezone.utc)
            generated.approved_at = None
            append_profile_example(profile, "rejected_examples", generated.body)
        generated.status = next_status

    if not generated.body.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El copy no puede estar vacio.",
        )

    generated.updated_at = datetime.now(timezone.utc)
    export_copy_markdown(event, piece, generated)
    db.add(
        DecisionLog(
            event_id=event.id,
            entity_type="generated_copy",
            entity_id=generated.id,
            decision_type="copy_manual_update",
            reason=f"Copy actualizado a estado {generated.status}.",
            actor="user",
        )
    )
    db.commit()
    db.refresh(generated)
    return to_generated_copy_response(generated, profile)


def require_piece_for_copy(db: Session, event_id: int, piece_id: int) -> ContentPiece:
    piece = db.scalar(
        select(ContentPiece)
        .where(ContentPiece.event_id == event_id, ContentPiece.id == piece_id)
        .options(
            selectinload(ContentPiece.media_items)
            .selectinload(ContentPieceMedia.enhanced_media)
            .selectinload(EnhancedMedia.original_media)
        )
    )
    if piece is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pieza no encontrada.")
    if not piece.media_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La pieza no tiene medios asociados.",
        )
    return piece


def require_copy(
    db: Session,
    event_id: int,
    piece_id: int,
    copy_id: int,
) -> GeneratedCopy:
    require_piece_for_copy(db, event_id, piece_id)
    generated = db.get(GeneratedCopy, copy_id)
    if generated is None or generated.piece_id != piece_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Copy no encontrado.")
    return generated


def build_copy_variants(
    event: ContentEvent,
    piece: ContentPiece,
    profile: EditorialProfile,
    feedback: str | None,
) -> list[CopyVariant]:
    event_type = event.event_type or "evento"
    purpose = humanize(piece.purpose or piece.piece_type)
    platform = piece.target_platform or "redes sociales"
    hashtags = normalize_hashtags(profile.hashtags_base)
    if not hashtags:
        hashtags = ["#RanchoFlorMaria", "#MomentosEspeciales", "#Eventos"]
    preferred = first_phrase(profile.preferred_phrases) or "momentos memorables"
    warmth = warmth_line(feedback, profile)
    cta = cta_for_feedback(feedback)
    tone_note = (
        f"Tono: {profile.tone}. Nivel emocional: {profile.emotional_level}. "
        f"Formalidad: {profile.formality_level}. Emojis: {profile.emoji_style}."
    )

    caption = (
        f"{piece.title} para {event.name}.\n\n"
        f"Un {event_type.lower()} con {preferred}, pensado para compartir {purpose} "
        f"en {platform}. {warmth}\n\n"
        f"{cta}\n\n"
        f"{' '.join(hashtags)}"
    )
    short = (
        f"{event.name}: {purpose} con el sello calido de Rancho Flor Maria.\n\n"
        f"{' '.join(hashtags[:4])}"
    )
    cover = f"{event.name}\n{humanize(piece.title)}"
    story = (
        f"Detalles de {event.name} para recordar y compartir.\n"
        f"{warmth}\n\n{' '.join(hashtags[:3])}"
    )
    hashtag_body = " ".join(hashtags)

    if feedback == "mas_corto":
        caption = f"{event.name}: {purpose} en Rancho Flor Maria.\n\n{' '.join(hashtags[:3])}"
        story = f"{event.name} en momentos para recordar."
    elif feedback == "mas_comercial":
        caption = (
            f"{event.name} muestra como cada detalle puede convertirse en contenido listo "
            f"para compartir. {cta}\n\n{' '.join(hashtags)}"
        )
    elif feedback == "menos_cursi":
        caption = (
            f"Resumen de {event.name}: medios seleccionados, mejorados y organizados "
            f"para publicar con claridad.\n\n{' '.join(hashtags[:4])}"
        )

    label_suffix = f" - {feedback.replace('_', ' ')}" if feedback else ""
    return [
        CopyVariant("caption", f"Caption principal{label_suffix}", caption, hashtags, cta, tone_note),
        CopyVariant("reel_short_copy", f"Copy breve{label_suffix}", short, hashtags[:4], None, tone_note),
        CopyVariant("cover_text", f"Texto de portada{label_suffix}", cover, [], None, tone_note),
        CopyVariant("story_text", f"Historia{label_suffix}", story, hashtags[:3], None, tone_note),
        CopyVariant("hashtags", f"Hashtags{label_suffix}", hashtag_body, hashtags, None, tone_note),
    ]


def build_prompt_context(
    event: ContentEvent,
    piece: ContentPiece,
    profile: EditorialProfile,
    feedback: str | None,
    variant: CopyVariant,
) -> dict[str, object]:
    media_names = [
        item.enhanced_media.original_media.filename
        for item in sorted(piece.media_items, key=lambda item: item.position)
        if item.enhanced_media and item.enhanced_media.original_media
    ]
    return {
        "generator": "phase13_local_template_v1",
        "feedback": feedback,
        "event": {
            "id": event.id,
            "name": event.name,
            "type": event.event_type,
            "date": event.event_date.isoformat(),
        },
        "piece": {
            "id": piece.id,
            "type": piece.piece_type,
            "title": piece.title,
            "purpose": piece.purpose,
            "platform": piece.target_platform,
        },
        "profile": {
            "id": profile.id,
            "tone": profile.tone,
            "emotional_level": profile.emotional_level,
            "formality_level": profile.formality_level,
            "emoji_style": profile.emoji_style,
            "copy_rules": profile.copy_rules,
        },
        "media_names": media_names,
        "variant": variant.copy_type,
    }


def export_copy_markdown(
    event: ContentEvent,
    piece: ContentPiece,
    generated: GeneratedCopy,
) -> None:
    event_path = get_event_path(event)
    copies_dir = event_path / "08_Copies"
    copies_dir.mkdir(parents=True, exist_ok=True)
    variant = safe_windows_name(generated.variant_label or generated.copy_type, fallback="copy")
    piece_name = safe_windows_name(piece.title, fallback="pieza")
    output_path = copies_dir / f"pieza_{piece.id:04d}_copy_{generated.id:04d}_{variant}.md"
    output_path.write_text(
        "\n".join(
            [
                f"# {piece.title}",
                "",
                f"Estado: {generated.status}",
                f"Tipo: {generated.copy_type}",
                f"Variante: {generated.variant_label or generated.copy_type}",
                f"Plataforma: {piece.target_platform or 'Sin plataforma'}",
                f"Pieza: {piece_name}",
                "",
                generated.body,
                "",
            ]
        ),
        encoding="utf-8",
    )
    generated.output_path = str(output_path.relative_to(event_path))


def to_generated_copy_response(
    generated: GeneratedCopy,
    profile: EditorialProfile,
) -> GeneratedCopyResponse:
    return GeneratedCopyResponse(
        id=generated.id,
        piece_id=generated.piece_id,
        editorial_profile_id=generated.editorial_profile_id,
        copy_type=generated.copy_type,
        variant_label=generated.variant_label,
        body=generated.body,
        hashtags_json=generated.hashtags_json,
        cta=generated.cta,
        style_notes=generated.style_notes,
        status=generated.status,
        generation_mode=generated.generation_mode,
        ai_provider=generated.ai_provider,
        prompt_context=generated.prompt_context,
        user_feedback=generated.user_feedback,
        output_path=generated.output_path,
        warnings=copy_warnings(generated.body, profile),
        created_at=generated.created_at,
        updated_at=generated.updated_at,
        approved_at=generated.approved_at,
        rejected_at=generated.rejected_at,
    )


def copy_warnings(body: str, profile: EditorialProfile) -> list[str]:
    warnings: list[str] = []
    if not body.strip():
        warnings.append("copy_vacio")
    if len(body) > 2200:
        warnings.append("copy_largo")
    if not any(part.startswith("#") for part in body.split()):
        warnings.append("sin_hashtags")
    if contains_avoided_terms(body, profile):
        warnings.append("contiene_palabras_a_evitar")
    return warnings


def validate_copy_can_be_approved(generated: GeneratedCopy, profile: EditorialProfile) -> None:
    if not generated.body.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede aprobar un copy vacio.",
        )
    if contains_avoided_terms(generated.body, profile):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El copy contiene palabras o frases a evitar del perfil editorial.",
        )


def append_profile_example(profile: EditorialProfile, field_name: str, body: str) -> None:
    current = getattr(profile, field_name) or ""
    snippets = [part.strip() for part in current.split("\n---\n") if part.strip()]
    snippet = body.strip()[:800]
    if snippet and snippet not in snippets:
        snippets.append(snippet)
    setattr(profile, field_name, "\n---\n".join(snippets[-10:]))


def normalize_feedback(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if normalized not in VALID_FEEDBACK:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback de copy no permitido.",
        )
    return normalized


def normalize_hashtags(value: str | None) -> list[str]:
    if not value:
        return []
    normalized = value.replace(",", " ").replace(";", " ").replace("\n", " ")
    tags: list[str] = []
    for item in normalized.split():
        tag = item.strip()
        if not tag:
            continue
        if not tag.startswith("#"):
            tag = f"#{tag}"
        if tag not in tags:
            tags.append(tag)
    return tags


def split_profile_terms(value: str | None) -> list[str]:
    if not value:
        return []
    normalized = value.replace(",", ";").replace("\n", ";")
    return [term.strip() for term in normalized.split(";") if term.strip()]


def contains_avoided_terms(body: str, profile: EditorialProfile) -> bool:
    lower_body = body.casefold()
    return any(term.casefold() in lower_body for term in split_profile_terms(profile.words_to_avoid))


def remove_avoided_terms(body: str, profile: EditorialProfile) -> str:
    cleaned = body
    for term in split_profile_terms(profile.words_to_avoid):
        cleaned = cleaned.replace(term, "")
        cleaned = cleaned.replace(term.capitalize(), "")
    return "\n".join(" ".join(line.split()) for line in cleaned.splitlines()).strip()


def first_phrase(value: str | None) -> str | None:
    terms = split_profile_terms(value)
    return terms[0] if terms else None


def warmth_line(feedback: str | None, profile: EditorialProfile) -> str:
    if feedback == "mas_humano":
        return "La idea es que el texto se sienta cercano, como una memoria real del dia."
    if feedback == "mas_calido":
        return "Mantiene una sensacion calida, familiar y cuidada."
    if feedback == "mas_natural":
        return "El mensaje se mantiene directo, natural y sin sonar forzado."
    if feedback == "menos_cursi":
        return "El tono se mantiene sobrio, claro y sin exageraciones."
    if profile.emotional_level == "alto":
        return "El texto puede sentirse emotivo, sin perder claridad."
    return "El tono se mantiene cercano y profesional."


def cta_for_feedback(feedback: str | None) -> str:
    if feedback == "mas_comercial":
        return "Agenda tu fecha y prepara tu evento con nosotros."
    return "Guarda este recuerdo y compartelo con quienes fueron parte del momento."


def humanize(value: str) -> str:
    return value.replace("_", " ").strip().capitalize()
