from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ContentPiece(Base):
    __tablename__ = "content_piece"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("content_event.id"), nullable=False, index=True)
    piece_type: Mapped[str] = mapped_column(String(60), nullable=False)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    purpose: Mapped[str | None] = mapped_column(String(160), nullable=True)
    target_platform: Mapped[str | None] = mapped_column(String(80), nullable=True)
    aspect_ratio: Mapped[str | None] = mapped_column(String(30), nullable=True)
    output_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft")
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    event: Mapped["ContentEvent"] = relationship(back_populates="content_pieces")
    media_items: Mapped[list["ContentPieceMedia"]] = relationship(
        back_populates="piece",
        cascade="all, delete-orphan",
    )
    copies: Mapped[list["GeneratedCopy"]] = relationship(
        back_populates="piece",
        cascade="all, delete-orphan",
    )
    calendar_items: Mapped[list["PublishingCalendarItem"]] = relationship(back_populates="piece")
    export_items: Mapped[list["ExportPackageItem"]] = relationship(back_populates="content_piece")


class ContentPieceMedia(Base):
    __tablename__ = "content_piece_media"
    __table_args__ = (
        UniqueConstraint("piece_id", "position", name="uq_content_piece_media_position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    piece_id: Mapped[int] = mapped_column(ForeignKey("content_piece.id"), nullable=False, index=True)
    original_media_id: Mapped[int | None] = mapped_column(
        ForeignKey("original_media.id"),
        nullable=True,
        index=True,
    )
    enhanced_media_id: Mapped[int | None] = mapped_column(
        ForeignKey("enhanced_media.id"),
        nullable=True,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    role: Mapped[str | None] = mapped_column(String(80), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    piece: Mapped[ContentPiece] = relationship(back_populates="media_items")
    original_media: Mapped["OriginalMedia | None"] = relationship(back_populates="piece_links")
    enhanced_media: Mapped["EnhancedMedia | None"] = relationship(back_populates="piece_links")


class GeneratedCopy(Base):
    __tablename__ = "generated_copy"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    piece_id: Mapped[int] = mapped_column(ForeignKey("content_piece.id"), nullable=False, index=True)
    editorial_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("editorial_profile.id"),
        nullable=True,
        index=True,
    )
    variant_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft")
    generation_mode: Mapped[str] = mapped_column(String(40), nullable=False, default="manual")
    ai_provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    prompt_context: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    piece: Mapped[ContentPiece] = relationship(back_populates="copies")
    editorial_profile: Mapped["EditorialProfile | None"] = relationship(
        back_populates="generated_copies"
    )
    export_items: Mapped[list["ExportPackageItem"]] = relationship(back_populates="generated_copy")


class PublishingCalendarItem(Base):
    __tablename__ = "publishing_calendar_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("content_event.id"),
        nullable=True,
        index=True,
    )
    piece_id: Mapped[int | None] = mapped_column(
        ForeignKey("content_piece.id"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    platform: Mapped[str | None] = mapped_column(String(80), nullable=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="planned")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    event: Mapped["ContentEvent | None"] = relationship(back_populates="calendar_items")
    piece: Mapped[ContentPiece | None] = relationship(back_populates="calendar_items")
