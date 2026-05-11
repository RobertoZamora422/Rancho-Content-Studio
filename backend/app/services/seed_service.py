from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.identity import Brand, EditorialProfile, User, VisualStylePreset

VISUAL_STYLE_PRESETS: tuple[tuple[str, str, str], ...] = (
    (
        "natural_premium",
        "Natural premium",
        "Ajustes limpios y naturales con acabado cuidado para eventos sociales.",
    ),
    (
        "calido_elegante",
        "Calido elegante",
        "Tono calido, contraste moderado y apariencia refinada.",
    ),
    (
        "color_vivo_fiesta",
        "Color vivo fiesta",
        "Color mas expresivo para celebraciones con luces, baile y ambiente.",
    ),
    (
        "suave_bodas",
        "Suave bodas",
        "Tratamiento suave para bodas, detalles romanticos y tonos delicados.",
    ),
    (
        "brillante_xv",
        "Brillante XV",
        "Look luminoso para quinceaneras y escenas festivas.",
    ),
    (
        "sobrio_corporativo",
        "Sobrio corporativo",
        "Edicion discreta y profesional para eventos empresariales.",
    ),
)


def seed_reference_data(db: Session) -> None:
    admin = db.scalar(select(User).where(User.username == "admin"))
    if admin is None:
        admin = User(username="admin", full_name="Roberto Zamora")
        db.add(admin)

    admin.full_name = "Roberto Zamora"
    admin.email = "roberto.zamora@local.rancho-content-studio"
    admin.role = "admin"
    admin.is_active = True

    brand = db.scalar(select(Brand).where(Brand.name == "Rancho Flor Maria"))
    if brand is None:
        brand = Brand(name="Rancho Flor Maria")
        db.add(brand)

    brand.description = "Marca principal para eventos sociales de Rancho Flor Maria."
    brand.base_hashtags = "#RanchoFlorMaria #MomentosEspeciales #Eventos"
    brand.preferred_phrases = "celebrar en familia; momentos memorables; detalles que se sienten"
    brand.avoided_words = "exagerado; viral obligatorio; promesas irreales"

    db.flush()

    profile = db.scalar(
        select(EditorialProfile).where(
            EditorialProfile.brand_id == brand.id,
            EditorialProfile.name == "Perfil editorial base",
        )
    )
    if profile is None:
        profile = EditorialProfile(
            brand_id=brand.id,
            name="Perfil editorial base",
            tone="calido, natural, cercano, profesional",
        )
        db.add(profile)

    profile.tone = "calido, natural, cercano, profesional"
    profile.emotional_level = "moderado"
    profile.formality_level = "semi_formal"
    profile.emoji_style = "sutil"
    profile.description = (
        "Comunicacion cercana y cuidada para eventos sociales, con enfoque humano "
        "y promocional sin sentirse generica."
    )
    profile.emoji_policy = "emojis sutiles"
    profile.hashtags_base = brand.base_hashtags
    profile.preferred_phrases = brand.preferred_phrases
    profile.words_to_avoid = brand.avoided_words
    profile.approved_examples = "Gracias por confiar en Rancho Flor Maria para celebrar momentos memorables."
    profile.rejected_examples = "Hazlo viral obligatorio; el evento mas exagerado de todos."
    profile.copy_rules = "Evitar promesas irreales. Mantener un tono humano, claro y calido."
    profile.is_default = True

    for slug, name, description in VISUAL_STYLE_PRESETS:
        preset = db.scalar(select(VisualStylePreset).where(VisualStylePreset.slug == slug))
        if preset is None:
            preset = VisualStylePreset(slug=slug, name=name)
            db.add(preset)

        preset.brand_id = brand.id
        preset.name = name
        preset.description = description
        preset.settings_json = "{}"
        preset.is_active = True

    db.commit()
