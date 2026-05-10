from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ContentEvent(Base):
    __tablename__ = "content_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[int | None] = mapped_column(ForeignKey("brand.id"), nullable=True, index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    event_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    folder_name: Mapped[str | None] = mapped_column(String(220), nullable=True)
    root_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft")
    metadata_date_source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    brand: Mapped["Brand | None"] = relationship(back_populates="events")
    created_by: Mapped["User | None"] = relationship(back_populates="events")
    sources: Mapped[list["LocalMediaSource"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )
    original_media: Mapped[list["OriginalMedia"]] = relationship(back_populates="event")
    similarity_groups: Mapped[list["SimilarityGroup"]] = relationship(back_populates="event")
    curated_media: Mapped[list["CuratedMedia"]] = relationship(back_populates="event")
    enhanced_media: Mapped[list["EnhancedMedia"]] = relationship(back_populates="event")
    content_pieces: Mapped[list["ContentPiece"]] = relationship(back_populates="event")
    calendar_items: Mapped[list["PublishingCalendarItem"]] = relationship(back_populates="event")
    processing_jobs: Mapped[list["ProcessingJob"]] = relationship(back_populates="event")
    export_packages: Mapped[list["ExportPackage"]] = relationship(back_populates="event")
    decisions: Mapped[list["DecisionLog"]] = relationship(back_populates="event")


class LocalMediaSource(Base):
    __tablename__ = "local_media_source"
    __table_args__ = (
        UniqueConstraint("event_id", "source_path", name="uq_local_media_source_event_path"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("content_event.id"), nullable=False, index=True)
    source_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False, default="local_folder")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="registered")
    file_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scanned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    event: Mapped[ContentEvent] = relationship(back_populates="sources")
    original_media: Mapped[list["OriginalMedia"]] = relationship(back_populates="source")
