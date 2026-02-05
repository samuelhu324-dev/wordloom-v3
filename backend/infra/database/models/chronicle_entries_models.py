"""Chronicle Entries ORM Models

Read-optimized projection derived from chronicle_events.

Design goals:
- One entry per chronicle_event (idempotent upsert by event id).
- Optimized for timeline queries and filtering.
- Summary/derived fields can evolve; keep raw payload for reference.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import Base


class ChronicleEntryModel(Base):
    __tablename__ = "chronicle_entries"

    # Idempotency key: 1 entry per chronicle_event
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)

    event_type = Column(String(64), nullable=False, index=True)

    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    block_id = Column(UUID(as_uuid=True), ForeignKey("blocks.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)

    payload = Column(JSONB, nullable=False, server_default="{}")

    # Human-ish summary for UI; rules may evolve.
    summary = Column(Text, nullable=True)

    projection_version = Column(Integer, nullable=False, default=1)

    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


Index("ix_chronicle_entries_book_time", ChronicleEntryModel.book_id, ChronicleEntryModel.occurred_at.desc())
Index("ix_chronicle_entries_type_time", ChronicleEntryModel.event_type, ChronicleEntryModel.occurred_at.desc())
Index("ix_chronicle_entries_created", ChronicleEntryModel.created_at.desc())


__all__ = ["ChronicleEntryModel"]
