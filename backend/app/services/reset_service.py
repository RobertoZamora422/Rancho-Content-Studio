from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.seed import seed_initial_config
from app.models.content import (
    ContentPiece,
    ContentPieceMedia,
    GeneratedCopy,
    PublishingCalendarItem,
)
from app.models.events import ContentEvent, LocalMediaSource
from app.models.jobs import (
    DecisionLog,
    ExportPackage,
    ExportPackageItem,
    ProcessingJob,
    ProcessingJobLog,
)
from app.models.media import (
    CuratedMedia,
    EnhancedMedia,
    MediaAnalysis,
    OriginalMedia,
    SimilarityGroup,
    SimilarityGroupItem,
)


RESET_MODEL_ORDER = (
    ProcessingJobLog,
    ExportPackageItem,
    PublishingCalendarItem,
    GeneratedCopy,
    ContentPieceMedia,
    ContentPiece,
    ExportPackage,
    EnhancedMedia,
    CuratedMedia,
    SimilarityGroupItem,
    SimilarityGroup,
    MediaAnalysis,
    DecisionLog,
    OriginalMedia,
    LocalMediaSource,
    ProcessingJob,
    ContentEvent,
)


@dataclass(frozen=True)
class ResetResult:
    deleted_counts: dict[str, int]
    dry_run: bool


def reset_operational_data(db: Session, *, dry_run: bool = True) -> ResetResult:
    deleted_counts: dict[str, int] = {}

    for model in RESET_MODEL_ORDER:
        table_name = model.__tablename__
        count = db.scalar(select(func.count()).select_from(model)) or 0
        deleted_counts[table_name] = int(count)
        if not dry_run and count:
            db.execute(delete(model))

    if dry_run:
        db.rollback()
    else:
        seed_initial_config(db)
        db.commit()

    return ResetResult(deleted_counts=deleted_counts, dry_run=dry_run)
