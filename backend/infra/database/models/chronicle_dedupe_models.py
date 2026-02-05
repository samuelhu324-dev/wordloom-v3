"""Chronicle event dedupe/rate-limit state.

Purpose
-------
Chronicle includes some high-frequency facts (e.g. block_updated) that can
overwhelm Postgres at scale.

We implement multi-instance consistent dedupe via a small state table and
Postgres "upsert with conditional update":

- One row per (event_type, book_id, block_id, actor_id, window_seconds)
- A monotonic last_bucket (time bucket index)
- Writers attempt to advance last_bucket; only the first writer per bucket wins

This avoids unbounded growth (unlike storing one row per bucket) and is safe
under concurrent writes from multiple app instances.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, Integer, String, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class ChronicleEventDedupeStateModel(Base):
    __tablename__ = "chronicle_event_dedupe_state"

    event_type = Column(String(64), primary_key=True, nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    block_id = Column(UUID(as_uuid=True), ForeignKey("blocks.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    actor_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    window_seconds = Column(Integer, primary_key=True, nullable=False)

    last_bucket = Column(BigInteger, nullable=False)

    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


Index(
    "ix_chronicle_event_dedupe_state_updated",
    ChronicleEventDedupeStateModel.updated_at.desc(),
)


__all__ = ["ChronicleEventDedupeStateModel"]
