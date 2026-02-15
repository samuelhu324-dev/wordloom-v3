"""Search Outbox ORM Models

Outbox pattern for propagating search_index changes to external systems (Elasticsearch).

Each write to search_index enqueues a row here in the same DB transaction.
A separate worker process reads unprocessed rows and updates ES.

We keep payload minimal and derive full document from search_index when needed.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, BigInteger, Text, Index, Integer
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class SearchOutboxEventModel(Base):
    """Outbox row for search_index → Elasticsearch synchronization.

    Columns:
      - id: Primary key
      - entity_type: "block", "tag", etc.
      - entity_id: UUID of the entity
      - op: operation type ("upsert" or "delete")
      - event_version: same monotonic version as search_index.event_version
      - created_at: enqueue time
      - processed_at: when successfully processed by worker
      - error: last error message if processing failed
            - status: pending|processing|done|failed
            - owner: worker id holding the lease
            - lease_until: lease expiration timestamp
            - attempts: retry attempts so far
            - next_retry_at: do not retry before this time
            - updated_at: last state transition timestamp
    """

    __tablename__ = "search_outbox_events"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # "upsert" | "delete"
    op = Column(String(20), nullable=False)

    event_version = Column(BigInteger, nullable=False, index=True, default=0)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    status = Column(String(20), nullable=False, index=True, default="pending")
    owner = Column(String(120), nullable=True, index=True)
    lease_until = Column(DateTime(timezone=True), nullable=True, index=True)
    attempts = Column(Integer, nullable=False, default=0)
    next_retry_at = Column(DateTime(timezone=True), nullable=True, index=True)

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    processed_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # When the current processing attempt began (set on claim). Used to detect
    # stuck events even if leases are being renewed.
    processing_started_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Coarse, low-cardinality reason for the last error (e.g., es_429, es_4xx).
    # Keep separate from `error` so we can query/aggregate without parsing text.
    error_reason = Column(String(80), nullable=True, index=True)

    error = Column(Text, nullable=True)

    # Optional tracing propagation (W3C Trace Context).
    # When present, workers should continue this trace.
    traceparent = Column(String(512), nullable=True)
    tracestate = Column(Text, nullable=True)

    # Manual replay audit (explicit ops path): failed -> pending.
    replay_count = Column(Integer, nullable=False, default=0)
    last_replayed_at = Column(DateTime(timezone=True), nullable=True)
    last_replayed_by = Column(String(120), nullable=True)
    last_replayed_reason = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_search_outbox_entity", "entity_type", "entity_id"),
        Index("idx_search_outbox_processed", "processed_at"),
        Index("idx_search_outbox_claim", "status", "next_retry_at", "lease_until", "event_version"),
        Index("idx_search_outbox_processing_started", "status", "processing_started_at"),
        Index("idx_search_outbox_error_reason", "status", "error_reason"),
    )


__all__ = ["SearchOutboxEventModel"]
