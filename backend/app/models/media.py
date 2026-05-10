from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class OriginalMedia(Base):
    __tablename__ = "original_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("content_event.id"), nullable=False, index=True)
    source_id: Mapped[int | None] = mapped_column(
        ForeignKey("local_media_source.id"),
        nullable=True,
        index=True,
    )
    original_path: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    relative_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    extension: Mapped[str | None] = mapped_column(String(32), nullable=True)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    capture_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    date_source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    thumbnail_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="imported")
    original_exists: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    event: Mapped["ContentEvent"] = relationship(back_populates="original_media")
    source: Mapped["LocalMediaSource | None"] = relationship(back_populates="original_media")
    analysis: Mapped["MediaAnalysis | None"] = relationship(
        back_populates="original_media",
        cascade="all, delete-orphan",
    )
    similarity_items: Mapped[list["SimilarityGroupItem"]] = relationship(
        back_populates="original_media"
    )
    curated_entries: Mapped[list["CuratedMedia"]] = relationship(back_populates="original_media")
    enhanced_versions: Mapped[list["EnhancedMedia"]] = relationship(back_populates="original_media")
    piece_links: Mapped[list["ContentPieceMedia"]] = relationship(back_populates="original_media")
    job_logs: Mapped[list["ProcessingJobLog"]] = relationship(back_populates="original_media")


class MediaAnalysis(Base):
    __tablename__ = "media_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    original_media_id: Mapped[int] = mapped_column(
        ForeignKey("original_media.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    sharpness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    brightness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    contrast_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    noise_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    exposure_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    perceptual_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    analysis_version: Mapped[str] = mapped_column(String(80), nullable=False, default="local-basic-v1")
    raw_metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    original_media: Mapped[OriginalMedia] = relationship(back_populates="analysis")


class SimilarityGroup(Base):
    __tablename__ = "similarity_group"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("content_event.id"), nullable=False, index=True)
    group_type: Mapped[str] = mapped_column(String(60), nullable=False, default="perceptual_hash")
    representative_media_id: Mapped[int | None] = mapped_column(
        ForeignKey("original_media.id"),
        nullable=True,
        index=True,
    )
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    event: Mapped["ContentEvent"] = relationship(back_populates="similarity_groups")
    representative_media: Mapped[OriginalMedia | None] = relationship(
        foreign_keys=[representative_media_id]
    )
    items: Mapped[list["SimilarityGroupItem"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )


class SimilarityGroupItem(Base):
    __tablename__ = "similarity_group_item"
    __table_args__ = (
        UniqueConstraint("group_id", "original_media_id", name="uq_similarity_item_group_media"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("similarity_group.id"), nullable=False, index=True)
    original_media_id: Mapped[int] = mapped_column(
        ForeignKey("original_media.id"),
        nullable=False,
        index=True,
    )
    distance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    role: Mapped[str] = mapped_column(String(40), nullable=False, default="alternative")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    group: Mapped[SimilarityGroup] = relationship(back_populates="items")
    original_media: Mapped[OriginalMedia] = relationship(back_populates="similarity_items")


class CuratedMedia(Base):
    __tablename__ = "curated_media"
    __table_args__ = (
        UniqueConstraint("event_id", "original_media_id", name="uq_curated_media_event_media"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("content_event.id"), nullable=False, index=True)
    original_media_id: Mapped[int] = mapped_column(
        ForeignKey("original_media.id"),
        nullable=False,
        index=True,
    )
    selection_status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    selected_by: Mapped[str] = mapped_column(String(40), nullable=False, default="system")
    is_manual_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    event: Mapped["ContentEvent"] = relationship(back_populates="curated_media")
    original_media: Mapped[OriginalMedia] = relationship(back_populates="curated_entries")
    enhanced_versions: Mapped[list["EnhancedMedia"]] = relationship(back_populates="curated_media")


class EnhancedMedia(Base):
    __tablename__ = "enhanced_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("content_event.id"), nullable=False, index=True)
    original_media_id: Mapped[int] = mapped_column(
        ForeignKey("original_media.id"),
        nullable=False,
        index=True,
    )
    curated_media_id: Mapped[int | None] = mapped_column(
        ForeignKey("curated_media.id"),
        nullable=True,
        index=True,
    )
    output_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    enhancement_type: Mapped[str] = mapped_column(String(60), nullable=False, default="basic")
    preset_slug: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="generated")
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    event: Mapped["ContentEvent"] = relationship(back_populates="enhanced_media")
    original_media: Mapped[OriginalMedia] = relationship(back_populates="enhanced_versions")
    curated_media: Mapped[CuratedMedia | None] = relationship(back_populates="enhanced_versions")
    piece_links: Mapped[list["ContentPieceMedia"]] = relationship(back_populates="enhanced_media")
    export_items: Mapped[list["ExportPackageItem"]] = relationship(back_populates="enhanced_media")
