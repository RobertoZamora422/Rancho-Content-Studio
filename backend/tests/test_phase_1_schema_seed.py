from sqlalchemy import func, inspect, select

from app.core.database import SessionLocal, engine, init_database
from app.core.seed import seed_initial_config
from app.models.identity import Brand, EditorialProfile, User, VisualStylePreset


EXPECTED_PHASE_1_TABLES = {
    "local_app_config",
    "user",
    "brand",
    "editorial_profile",
    "visual_style_preset",
    "content_event",
    "local_media_source",
    "original_media",
    "media_analysis",
    "similarity_group",
    "similarity_group_item",
    "curated_media",
    "enhanced_media",
    "content_piece",
    "content_piece_media",
    "generated_copy",
    "publishing_calendar_item",
    "decision_log",
    "processing_job",
    "processing_job_log",
    "export_package",
    "export_package_item",
}

EXPECTED_PRESETS = {
    "natural_premium",
    "calido_elegante",
    "color_vivo_fiesta",
    "suave_bodas",
    "brillante_xv",
    "sobrio_corporativo",
}


def test_phase_1_tables_are_created() -> None:
    init_database()

    table_names = set(inspect(engine).get_table_names())

    assert EXPECTED_PHASE_1_TABLES <= table_names


def test_phase_1_seed_data_is_present_and_idempotent() -> None:
    init_database()

    with SessionLocal() as db:
        seed_initial_config(db)
        seed_initial_config(db)

        admin = db.scalar(select(User).where(User.username == "admin"))
        brand = db.scalar(select(Brand).where(Brand.name == "Rancho Flor Maria"))

        assert admin is not None
        assert admin.full_name == "Roberto Zamora"
        assert admin.role == "admin"
        assert brand is not None

        profile = db.scalar(
            select(EditorialProfile).where(
                EditorialProfile.brand_id == brand.id,
                EditorialProfile.name == "Perfil editorial base",
            )
        )
        assert profile is not None
        assert profile.is_default is True
        assert "calido" in profile.tone
        assert "profesional" in profile.tone

        preset_slugs = set(db.scalars(select(VisualStylePreset.slug)).all())
        assert EXPECTED_PRESETS <= preset_slugs

        assert (
            db.scalar(select(func.count()).select_from(User).where(User.username == "admin"))
            == 1
        )
        assert (
            db.scalar(
                select(func.count()).select_from(Brand).where(Brand.name == "Rancho Flor Maria")
            )
            == 1
        )
        for slug in EXPECTED_PRESETS:
            assert (
                db.scalar(
                    select(func.count())
                    .select_from(VisualStylePreset)
                    .where(VisualStylePreset.slug == slug)
                )
                == 1
            )
