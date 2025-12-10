"""Maturity snapshot ORM models."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import Base


class MaturitySnapshotModel(Base):
    __tablename__ = "maturity_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    book_id = Column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage = Column(String(16), nullable=False)
    score = Column(Integer, nullable=False, default=0)
    components = Column(JSONB, nullable=False, server_default="[]")
    tasks = Column(JSONB, nullable=False, server_default="[]")
    signals = Column(JSONB, nullable=False, server_default="{}")
    manual_override = Column(Boolean, nullable=False, default=False)
    manual_reason = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


Index("ix_maturity_snapshots_book_time", MaturitySnapshotModel.book_id, MaturitySnapshotModel.created_at.desc())
