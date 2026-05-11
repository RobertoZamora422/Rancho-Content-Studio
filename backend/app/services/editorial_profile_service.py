from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.identity import EditorialProfile
from app.models.jobs import DecisionLog
from app.schemas.editorial import EditorialProfileResponse, EditorialProfileUpdate

VALID_EMOTIONAL_LEVELS = {"bajo", "moderado", "alto"}
VALID_FORMALITY_LEVELS = {"casual", "semi_formal", "formal"}
VALID_EMOJI_STYLES = {"sin_emojis", "sutil", "moderado", "expresivo"}


def get_default_editorial_profile(db: Session) -> EditorialProfileResponse:
    return to_editorial_profile_response(require_default_editorial_profile(db))


def update_default_editorial_profile(
    db: Session,
    payload: EditorialProfileUpdate,
) -> EditorialProfileResponse:
    profile = require_default_editorial_profile(db)

    if payload.name is not None:
        profile.name = require_text(payload.name, "El nombre del perfil no puede estar vacio.")
    if payload.tone is not None:
        profile.tone = require_text(payload.tone, "El tono editorial no puede estar vacio.")
    if payload.emotional_level is not None:
        profile.emotional_level = validate_choice(
            payload.emotional_level,
            VALID_EMOTIONAL_LEVELS,
            "Nivel emocional no permitido.",
        )
    if payload.formality_level is not None:
        profile.formality_level = validate_choice(
            payload.formality_level,
            VALID_FORMALITY_LEVELS,
            "Nivel de formalidad no permitido.",
        )
    if payload.emoji_style is not None:
        profile.emoji_style = validate_choice(
            payload.emoji_style,
            VALID_EMOJI_STYLES,
            "Estilo de emojis no permitido.",
        )
        profile.emoji_policy = f"emojis {profile.emoji_style}"

    for field_name in (
        "description",
        "emoji_policy",
        "hashtags_base",
        "preferred_phrases",
        "words_to_avoid",
        "approved_examples",
        "rejected_examples",
        "copy_rules",
    ):
        value = getattr(payload, field_name)
        if value is not None:
            setattr(profile, field_name, normalize_optional_text(value))

    profile.updated_at = datetime.now(timezone.utc)
    db.add(
        DecisionLog(
            event_id=None,
            entity_type="editorial_profile",
            entity_id=profile.id,
            decision_type="editorial_profile_updated",
            reason="Perfil editorial actualizado manualmente.",
            actor="user",
        )
    )
    db.commit()
    db.refresh(profile)
    return to_editorial_profile_response(profile)


def require_default_editorial_profile(db: Session) -> EditorialProfile:
    profile = db.scalar(
        select(EditorialProfile).order_by(EditorialProfile.is_default.desc(), EditorialProfile.id.asc())
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay perfil editorial configurado.",
        )
    return profile


def to_editorial_profile_response(profile: EditorialProfile) -> EditorialProfileResponse:
    return EditorialProfileResponse(
        id=profile.id,
        brand_id=profile.brand_id,
        name=profile.name,
        tone=profile.tone,
        emotional_level=profile.emotional_level,
        formality_level=profile.formality_level,
        emoji_style=profile.emoji_style,
        description=profile.description,
        emoji_policy=profile.emoji_policy,
        hashtags_base=profile.hashtags_base,
        preferred_phrases=profile.preferred_phrases,
        words_to_avoid=profile.words_to_avoid,
        approved_examples=profile.approved_examples,
        rejected_examples=profile.rejected_examples,
        copy_rules=profile.copy_rules,
        is_default=profile.is_default,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def validate_choice(value: str, allowed: set[str], message: str) -> str:
    normalized = value.strip()
    if normalized not in allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return normalized


def require_text(value: str, message: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return normalized


def normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None
