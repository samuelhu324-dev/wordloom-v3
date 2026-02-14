"""Chronicle Outbox ORM Models

Outbox pattern for propagating chronicle_events changes to a read-optimized
Chronicle projection table (chronicle_entries).

This is intentionally isomorphic to search_outbox_events so we can reuse the
same worker failure-management patterns (lease/retry/failed/replay/metrics).
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import BigInteger, Column, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class ChronicleOutboxEventModel(Base):
    __tablename__ = "chronicle_outbox_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)

    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Currently only "upsert" is used (project event -> entry).
    op = Column(String(20), nullable=False)

    event_version = Column(BigInteger, nullable=False, index=True, default=0)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    status = Column(String(20), nullable=False, index=True, default="pending")
    owner = Column(String(120), nullable=True, index=True)
    lease_until = Column(DateTime(timezone=True), nullable=True, index=True)
    attempts = Column(Integer, nullable=False, default=0)
    next_retry_at = Column(DateTime(timezone=True), nullable=True, index=True)

    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    processed_at = Column(DateTime(timezone=True), nullable=True, index=True)

    processing_started_at = Column(DateTime(timezone=True), nullable=True, index=True)

    error_reason = Column(String(80), nullable=True, index=True)
    error = Column(Text, nullable=True)

    # Optional tracing propagation (W3C Trace Context).
    traceparent = Column(String(512), nullable=True)
    tracestate = Column(Text, nullable=True)

    replay_count = Column(Integer, nullable=False, default=0)
    last_replayed_at = Column(DateTime(timezone=True), nullable=True)
    last_replayed_by = Column(String(120), nullable=True)
    last_replayed_reason = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_chronicle_outbox_entity", "entity_type", "entity_id"),
        Index("idx_chronicle_outbox_processed", "processed_at"),
        Index("idx_chronicle_outbox_claim", "status", "next_retry_at", "lease_until", "event_version"),
        Index("idx_chronicle_outbox_processing_started", "status", "processing_started_at"),
        Index("idx_chronicle_outbox_error_reason", "status", "error_reason"),
    )


__all__ = ["ChronicleOutboxEventModel"]
