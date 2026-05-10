from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DecisionLog(Base):
    __tablename__ = "decision_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("content_event.id"),
        nullable=True,
        index=True,
    )
    original_media_id: Mapped[int | None] = mapped_column(
        ForeignKey("original_media.id"),
        nullable=True,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    decision_type: Mapped[str] = mapped_column(String(80), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor: Mapped[str] = mapped_column(String(80), nullable=False, default="system")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    event: Mapped["ContentEvent | None"] = relationship(back_populates="decisions")
    original_media: Mapped["OriginalMedia | None"] = relationship()


class ProcessingJob(Base):
    __tablename__ = "processing_job"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("content_event.id"),
        nullable=True,
        index=True,
    )
    job_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="queued")
    progress_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    event: Mapped["ContentEvent | None"] = relationship(back_populates="processing_jobs")
    logs: Mapped[list["ProcessingJobLog"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )


class ProcessingJobLog(Base):
    __tablename__ = "processing_job_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("processing_job.id"), nullable=False, index=True)
    original_media_id: Mapped[int | None] = mapped_column(
        ForeignKey("original_media.id"),
        nullable=True,
        index=True,
    )
    level: Mapped[str] = mapped_column(String(40), nullable=False, default="info")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    job: Mapped[ProcessingJob] = relationship(back_populates="logs")
    original_media: Mapped["OriginalMedia | None"] = relationship(back_populates="job_logs")


class ExportPackage(Base):
    __tablename__ = "export_package"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("content_event.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(220), nullable=False)
    output_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft")
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
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    event: Mapped["ContentEvent"] = relationship(back_populates="export_packages")
    items: Mapped[list["ExportPackageItem"]] = relationship(
        back_populates="package",
        cascade="all, delete-orphan",
    )


class ExportPackageItem(Base):
    __tablename__ = "export_package_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("export_package.id"), nullable=False, index=True)
    content_piece_id: Mapped[int | None] = mapped_column(
        ForeignKey("content_piece.id"),
        nullable=True,
        index=True,
    )
    generated_copy_id: Mapped[int | None] = mapped_column(
        ForeignKey("generated_copy.id"),
        nullable=True,
        index=True,
    )
    enhanced_media_id: Mapped[int | None] = mapped_column(
        ForeignKey("enhanced_media.id"),
        nullable=True,
        index=True,
    )
    item_type: Mapped[str] = mapped_column(String(60), nullable=False)
    output_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    metadata_written: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_status: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    package: Mapped[ExportPackage] = relationship(back_populates="items")
    content_piece: Mapped["ContentPiece | None"] = relationship(back_populates="export_items")
    generated_copy: Mapped["GeneratedCopy | None"] = relationship(back_populates="export_items")
    enhanced_media: Mapped["EnhancedMedia | None"] = relationship(back_populates="export_items")
