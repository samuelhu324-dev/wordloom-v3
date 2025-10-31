from __future__ import annotations
import uuid, datetime
from sqlalchemy import String, Text, Integer, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from app.database_orbit import OrbitBase

class Bookmark(OrbitBase):
    __tablename__ = "bookmarks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    tags = mapped_column(ARRAY(String), nullable=False, server_default="{}")
    links = mapped_column(ARRAY(String), nullable=False, server_default="{}")
    urgency: Mapped[int] = mapped_column(Integer, default=3)
    daily: Mapped[int] = mapped_column(Integer, default=3)
    status: Mapped[str] = mapped_column(String(20), default="active")
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    image_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    next_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    blocked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    done_at = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at = mapped_column(DateTime(timezone=True), nullable=True)
