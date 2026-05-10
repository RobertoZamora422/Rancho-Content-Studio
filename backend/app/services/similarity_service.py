from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.media import OriginalMedia, SimilarityGroup, SimilarityGroupItem
from app.schemas.importing import (
    SimilarityDetectionResponse,
    SimilarityGroupItemResponse,
    SimilarityGroupListResponse,
    SimilarityGroupResponse,
)
from app.services.event_service import require_event
from app.services.import_service import to_original_media_response
from app.services.job_service import add_job_log, finish_job, start_job

SIMILARITY_HASH_THRESHOLD = 8
GENERATED_GROUP_TYPES = {"checksum_duplicate", "perceptual_hash"}


@dataclass(frozen=True)
class SimilarityComponent:
    media_items: list[OriginalMedia]
    max_distance: int


def detect_event_similarities(db: Session, event_id: int) -> SimilarityDetectionResponse:
    require_event(db, event_id)
    job = start_job(db, "detect_similarity", event_id)

    media_items = list(
        db.scalars(
            select(OriginalMedia)
            .where(OriginalMedia.event_id == event_id)
            .options(selectinload(OriginalMedia.analysis))
            .order_by(OriginalMedia.imported_at.asc(), OriginalMedia.id.asc())
        ).all()
    )

    clear_generated_groups(db, event_id)
    exact_groups, exact_items = create_checksum_groups(db, event_id, media_items)
    similar_groups, similar_items, skipped_without_hash = create_perceptual_hash_groups(
        db,
        event_id,
        media_items,
    )

    if skipped_without_hash:
        add_job_log(
            db,
            job,
            "warning",
            f"{skipped_without_hash} fotos no tienen hash perceptual; ejecuta Analizar fotos antes de detectar similares.",
        )

    grouped_items = exact_items + similar_items
    add_job_log(
        db,
        job,
        "info",
        f"Deteccion finalizada: {exact_groups} grupos exactos y {similar_groups} grupos similares.",
    )
    finish_job(
        job,
        "completed",
        total_items=len(media_items),
        processed_items=len(media_items),
        failed_items=0,
    )
    db.commit()

    return SimilarityDetectionResponse(
        job_id=job.id,
        total_media=len(media_items),
        exact_groups=exact_groups,
        similar_groups=similar_groups,
        grouped_items=grouped_items,
        skipped_without_hash=skipped_without_hash,
    )


def list_similarity_groups(db: Session, event_id: int) -> SimilarityGroupListResponse:
    require_event(db, event_id)
    groups = db.scalars(
        select(SimilarityGroup)
        .where(SimilarityGroup.event_id == event_id)
        .options(
            selectinload(SimilarityGroup.items)
            .selectinload(SimilarityGroupItem.original_media)
            .selectinload(OriginalMedia.analysis),
            selectinload(SimilarityGroup.representative_media).selectinload(
                OriginalMedia.analysis
            ),
        )
        .order_by(SimilarityGroup.created_at.desc(), SimilarityGroup.id.desc())
    ).all()
    return SimilarityGroupListResponse(items=[to_similarity_group_response(group) for group in groups])


def clear_generated_groups(db: Session, event_id: int) -> None:
    groups = db.scalars(
        select(SimilarityGroup).where(
            SimilarityGroup.event_id == event_id,
            SimilarityGroup.group_type.in_(GENERATED_GROUP_TYPES),
        )
    ).all()
    for group in groups:
        db.delete(group)
    db.flush()


def create_checksum_groups(
    db: Session,
    event_id: int,
    media_items: list[OriginalMedia],
) -> tuple[int, int]:
    by_checksum: dict[str, list[OriginalMedia]] = defaultdict(list)
    for media in media_items:
        if media.checksum_sha256:
            by_checksum[media.checksum_sha256].append(media)

    groups_created = 0
    grouped_items = 0
    for checksum, items in by_checksum.items():
        if len(items) < 2:
            continue
        representative = choose_representative(items)
        group = SimilarityGroup(
            event_id=event_id,
            group_type="checksum_duplicate",
            representative_media_id=representative.id,
            confidence_score=100.0,
            reason=f"Archivos con checksum SHA-256 identico: {checksum[:12]}...",
        )
        db.add(group)
        db.flush()
        for media in sorted(items, key=lambda item: item.id):
            db.add(
                SimilarityGroupItem(
                    group_id=group.id,
                    original_media_id=media.id,
                    distance_score=0.0,
                    role="representative" if media.id == representative.id else "duplicate",
                    reason="Checksum identico.",
                )
            )
        groups_created += 1
        grouped_items += len(items)

    return groups_created, grouped_items


def create_perceptual_hash_groups(
    db: Session,
    event_id: int,
    media_items: list[OriginalMedia],
) -> tuple[int, int, int]:
    candidates = [
        media
        for media in media_items
        if media.media_type == "image" and media.analysis and media.analysis.perceptual_hash
    ]
    skipped_without_hash = len(
        [
            media
            for media in media_items
            if media.media_type == "image"
            and (not media.analysis or not media.analysis.perceptual_hash)
        ]
    )
    components = find_similarity_components(candidates)

    groups_created = 0
    grouped_items = 0
    for component in components:
        representative = choose_representative(component.media_items)
        confidence = round(100 - (component.max_distance / 64) * 100, 2)
        group = SimilarityGroup(
            event_id=event_id,
            group_type="perceptual_hash",
            representative_media_id=representative.id,
            confidence_score=confidence,
            reason=(
                "Fotos con hash perceptual cercano "
                f"(distancia maxima {component.max_distance}, umbral {SIMILARITY_HASH_THRESHOLD})."
            ),
        )
        db.add(group)
        db.flush()
        for media in sorted(component.media_items, key=lambda item: item.id):
            distance = hamming_distance(
                representative.analysis.perceptual_hash if representative.analysis else None,
                media.analysis.perceptual_hash if media.analysis else None,
            )
            db.add(
                SimilarityGroupItem(
                    group_id=group.id,
                    original_media_id=media.id,
                    distance_score=float(distance) if distance is not None else None,
                    role="representative" if media.id == representative.id else "alternative",
                    reason=(
                        "Mejor puntaje de calidad dentro del grupo."
                        if media.id == representative.id
                        else "Hash perceptual cercano al representante."
                    ),
                )
            )
        groups_created += 1
        grouped_items += len(component.media_items)

    return groups_created, grouped_items, skipped_without_hash


def find_similarity_components(candidates: list[OriginalMedia]) -> list[SimilarityComponent]:
    parent = {media.id: media.id for media in candidates}
    max_distance_by_root: dict[int, int] = defaultdict(int)

    def find(media_id: int) -> int:
        while parent[media_id] != media_id:
            parent[media_id] = parent[parent[media_id]]
            media_id = parent[media_id]
        return media_id

    def union(left_id: int, right_id: int, distance: int) -> None:
        left_root = find(left_id)
        right_root = find(right_id)
        if left_root == right_root:
            max_distance_by_root[left_root] = max(max_distance_by_root[left_root], distance)
            return
        keep_root = min(left_root, right_root)
        drop_root = max(left_root, right_root)
        parent[drop_root] = keep_root
        max_distance_by_root[keep_root] = max(
            max_distance_by_root[keep_root],
            max_distance_by_root[drop_root],
            distance,
        )

    for index, left in enumerate(candidates):
        for right in candidates[index + 1 :]:
            distance = hamming_distance(
                left.analysis.perceptual_hash if left.analysis else None,
                right.analysis.perceptual_hash if right.analysis else None,
            )
            if distance is not None and distance <= SIMILARITY_HASH_THRESHOLD:
                union(left.id, right.id, distance)

    grouped: dict[int, list[OriginalMedia]] = defaultdict(list)
    for media in candidates:
        grouped[find(media.id)].append(media)

    components: list[SimilarityComponent] = []
    for root, items in grouped.items():
        if len(items) > 1:
            components.append(
                SimilarityComponent(
                    media_items=items,
                    max_distance=max_distance_by_root[root],
                )
            )
    return components


def choose_representative(items: list[OriginalMedia]) -> OriginalMedia:
    return max(
        items,
        key=lambda media: (
            media.analysis.overall_quality_score if media.analysis else 0,
            media.file_size_bytes or 0,
            -media.id,
        ),
    )


def hamming_distance(left_hash: str | None, right_hash: str | None) -> int | None:
    if not left_hash or not right_hash:
        return None
    try:
        left_value = int(left_hash, 16)
        right_value = int(right_hash, 16)
    except ValueError:
        return None
    return (left_value ^ right_value).bit_count()


def to_similarity_group_response(group: SimilarityGroup) -> SimilarityGroupResponse:
    sorted_items = sorted(
        group.items,
        key=lambda item: (item.role != "representative", item.distance_score or 0, item.id),
    )
    return SimilarityGroupResponse(
        id=group.id,
        event_id=group.event_id,
        group_type=group.group_type,
        representative_media_id=group.representative_media_id,
        confidence_score=group.confidence_score,
        reason=group.reason,
        created_at=group.created_at,
        items=[
            SimilarityGroupItemResponse(
                id=item.id,
                group_id=item.group_id,
                original_media_id=item.original_media_id,
                distance_score=item.distance_score,
                role=item.role,
                reason=item.reason,
                media=to_original_media_response(item.original_media),
            )
            for item in sorted_items
        ],
    )
