"""Search outbox repository.

This is an infra-only helper to encapsulate writes into `search_outbox_events`.
The worker/daemon can remain script-driven; this repo is mainly used by
projection writers to enqueue events within the same DB transaction.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from infra.database.models.search_outbox_models import SearchOutboxEventModel
from infra.observability.tracing import inject_trace_context


class SearchOutboxRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def enqueue(
        self,
        *,
        entity_type: str,
        entity_id: UUID,
        op: str,
        event_version: int,
    ) -> None:
        traceparent, tracestate = inject_trace_context()
        await self._db.execute(
            pg_insert(SearchOutboxEventModel).values(
                entity_type=entity_type,
                entity_id=entity_id,
                op=op,
                event_version=event_version,
                traceparent=traceparent,
                tracestate=tracestate,
            )
        )


__all__ = ["SearchOutboxRepository"]
