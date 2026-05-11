from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(160), unique=True, nullable=True)
    role: Mapped[str] = mapped_column(String(40), nullable=False, default="admin")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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

    events: Mapped[list["ContentEvent"]] = relationship(back_populates="created_by")


class Brand(Base):
    __tablename__ = "brand"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_hashtags: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_phrases: Mapped[str | None] = mapped_column(Text, nullable=True)
    avoided_words: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    editorial_profiles: Mapped[list["EditorialProfile"]] = relationship(
        back_populates="brand",
        cascade="all, delete-orphan",
    )
    visual_style_presets: Mapped[list["VisualStylePreset"]] = relationship(
        back_populates="brand",
        cascade="all, delete-orphan",
    )
    events: Mapped[list["ContentEvent"]] = relationship(back_populates="brand")


class EditorialProfile(Base):
    __tablename__ = "editorial_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brand.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    tone: Mapped[str] = mapped_column(String(255), nullable=False)
    emotional_level: Mapped[str] = mapped_column(String(40), nullable=False, default="moderado")
    formality_level: Mapped[str] = mapped_column(String(40), nullable=False, default="semi_formal")
    emoji_style: Mapped[str] = mapped_column(String(40), nullable=False, default="sutil")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    emoji_policy: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hashtags_base: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_phrases: Mapped[str | None] = mapped_column(Text, nullable=True)
    words_to_avoid: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_examples: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejected_examples: Mapped[str | None] = mapped_column(Text, nullable=True)
    copy_rules: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
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

    brand: Mapped[Brand] = relationship(back_populates="editorial_profiles")
    generated_copies: Mapped[list["GeneratedCopy"]] = relationship(
        back_populates="editorial_profile"
    )


class VisualStylePreset(Base):
    __tablename__ = "visual_style_preset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[int | None] = mapped_column(
        ForeignKey("brand.id"),
        nullable=True,
        index=True,
    )
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    settings_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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

    brand: Mapped[Brand | None] = relationship(back_populates="visual_style_presets")
