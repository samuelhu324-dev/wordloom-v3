"""Projection status ORM model.

Used for operational visibility (rebuild bookkeeping) and metrics export.

This table is intentionally low-cardinality:
- One row per projection.
- Not per library/tenant (avoid high-cardinality metrics).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, String, Text

from .base import Base


class ProjectionStatusModel(Base):
    __tablename__ = "projection_status"

    projection_name = Column(String(100), primary_key=True, nullable=False)

    last_rebuild_started_at = Column(DateTime(timezone=True), nullable=True)
    last_rebuild_finished_at = Column(DateTime(timezone=True), nullable=True)
    last_rebuild_duration_seconds = Column(Float, nullable=True)
    last_rebuild_success = Column(Boolean, nullable=True)
    last_rebuild_error = Column(Text, nullable=True)

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


__all__ = ["ProjectionStatusModel"]
