"""Search indexer abstraction + PostgreSQL implementation.

Goal: make EventBus handlers depend on an interface (Protocol) rather than
hardcoding DB write logic inline.

This is an infra-side abstraction (not the application SearchPort).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.modules.block.domain.events import BlockCreated, BlockUpdated
from api.app.modules.tag.domain.events import TagCreated, TagRenamed
from infra.database.models.search_index_models import SearchIndexModel
from infra.database.models.search_outbox_models import SearchOutboxEventModel
from infra.observability.outbox_metrics import outbox_produced_total

logger = logging.getLogger(__name__)


def _event_version(occurred_at: datetime) -> int:
    """Derive a monotonic, comparable integer version from occurred_at.

    Block/Tag events currently don't carry an explicit version, so we use microsecond
    timestamps to implement the same "newer wins" ordering guard.
    """

    return int(occurred_at.timestamp() * 1_000_000)


class SearchIndexer(Protocol):
    async def index_block_created(self, event: BlockCreated) -> None: ...

    async def index_block_updated(self, event: BlockUpdated) -> None: ...

    async def delete_block(self, *, block_id: UUID) -> None: ...

    async def index_tag_created(self, event: TagCreated) -> None: ...

    async def index_tag_renamed(self, event: TagRenamed) -> None: ...

    async def delete_tag(self, *, tag_id: UUID) -> None: ...


class PostgresSearchIndexer:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def index_block_created(self, event: BlockCreated) -> None:
        occurred_at = event.occurred_at
        version = _event_version(occurred_at)
        stmt = (
            pg_insert(SearchIndexModel)
            .values(
                entity_type="block",
                entity_id=event.block_id,
                text=event.content or "",
                snippet=(event.content or "")[:200],
                rank_score=0.0,
                created_at=occurred_at,
                updated_at=occurred_at,
                event_version=version,
            )
            .on_conflict_do_nothing(
                index_elements=[SearchIndexModel.entity_type, SearchIndexModel.entity_id]
            )
        )
        await self._db.execute(stmt)

        # Enqueue outbox entry for ES synchronization (upsert document).
        await self._db.execute(
            pg_insert(SearchOutboxEventModel).values(
                entity_type="block",
                entity_id=event.block_id,
                op="upsert",
                event_version=version,
            )
        )
        outbox_produced_total.labels(event_type="block.created", entity_type="block").inc()
        logger.info("Search index: inserted block %s (outbox enqueued)", event.block_id)

    async def index_block_updated(self, event: BlockUpdated) -> None:
        occurred_at = event.occurred_at
        version = _event_version(occurred_at)
        stmt = pg_insert(SearchIndexModel).values(
            entity_type="block",
            entity_id=event.block_id,
            text=event.content or "",
            snippet=(event.content or "")[:200],
            rank_score=0.0,
            created_at=occurred_at,
            updated_at=occurred_at,
            event_version=version,
        )
        excluded = stmt.excluded
        stmt = stmt.on_conflict_do_update(
            index_elements=[SearchIndexModel.entity_type, SearchIndexModel.entity_id],
            set_={
                "text": excluded.text,
                "snippet": excluded.snippet,
                "updated_at": excluded.updated_at,
                "event_version": excluded.event_version,
            },
            # Anti-regression: ignore out-of-order older events.
            where=SearchIndexModel.event_version <= excluded.event_version,
        )
        await self._db.execute(stmt)

        await self._db.execute(
            pg_insert(SearchOutboxEventModel).values(
                entity_type="block",
                entity_id=event.block_id,
                op="upsert",
                event_version=version,
            )
        )
        outbox_produced_total.labels(event_type="block.updated", entity_type="block").inc()
        logger.info("Search index: updated block %s (outbox enqueued)", event.block_id)

    async def delete_block(self, *, block_id: UUID) -> None:
        stmt = delete(SearchIndexModel).where(
            SearchIndexModel.entity_type == "block",
            SearchIndexModel.entity_id == block_id,
        )
        await self._db.execute(stmt)

        # Use a synthetic version based on current time. For deletes we only need
        # monotonicity relative to previous writes for the same entity.
        version = _event_version(datetime.utcnow())
        await self._db.execute(
            pg_insert(SearchOutboxEventModel).values(
                entity_type="block",
                entity_id=block_id,
                op="delete",
                event_version=version,
            )
        )
        outbox_produced_total.labels(event_type="block.deleted", entity_type="block").inc()
        logger.info("Search index: deleted block %s (outbox enqueued)", block_id)

    async def index_tag_created(self, event: TagCreated) -> None:
        occurred_at = event.occurred_at
        version = _event_version(occurred_at)
        stmt = (
            pg_insert(SearchIndexModel)
            .values(
                entity_type="tag",
                entity_id=event.tag_id,
                text=event.name or "",
                snippet=event.name or "",
                rank_score=0.0,
                created_at=occurred_at,
                updated_at=occurred_at,
                event_version=version,
            )
            .on_conflict_do_nothing(
                index_elements=[SearchIndexModel.entity_type, SearchIndexModel.entity_id]
            )
        )
        await self._db.execute(stmt)

        await self._db.execute(
            pg_insert(SearchOutboxEventModel).values(
                entity_type="tag",
                entity_id=event.tag_id,
                op="upsert",
                event_version=version,
            )
        )
        outbox_produced_total.labels(event_type="tag.created", entity_type="tag").inc()
        logger.info("Search index: inserted tag %s (outbox enqueued)", event.tag_id)

    async def index_tag_renamed(self, event: TagRenamed) -> None:
        occurred_at = event.occurred_at
        version = _event_version(occurred_at)
        stmt = pg_insert(SearchIndexModel).values(
            entity_type="tag",
            entity_id=event.tag_id,
            text=event.new_name or "",
            snippet=event.new_name or "",
            rank_score=0.0,
            created_at=occurred_at,
            updated_at=occurred_at,
            event_version=version,
        )
        excluded = stmt.excluded
        stmt = stmt.on_conflict_do_update(
            index_elements=[SearchIndexModel.entity_type, SearchIndexModel.entity_id],
            set_={
                "text": excluded.text,
                "snippet": excluded.snippet,
                "updated_at": excluded.updated_at,
                "event_version": excluded.event_version,
            },
            # Anti-regression: ignore out-of-order older events.
            where=SearchIndexModel.event_version <= excluded.event_version,
        )
        await self._db.execute(stmt)

        await self._db.execute(
            pg_insert(SearchOutboxEventModel).values(
                entity_type="tag",
                entity_id=event.tag_id,
                op="upsert",
                event_version=version,
            )
        )
        outbox_produced_total.labels(event_type="tag.renamed", entity_type="tag").inc()
        logger.info("Search index: updated tag %s (outbox enqueued)", event.tag_id)

    async def delete_tag(self, *, tag_id: UUID) -> None:
        stmt = delete(SearchIndexModel).where(
            SearchIndexModel.entity_type == "tag",
            SearchIndexModel.entity_id == tag_id,
        )
        await self._db.execute(stmt)

        version = _event_version(datetime.utcnow())
        await self._db.execute(
            pg_insert(SearchOutboxEventModel).values(
                entity_type="tag",
                entity_id=tag_id,
                op="delete",
                event_version=version,
            )
        )
        outbox_produced_total.labels(event_type="tag.deleted", entity_type="tag").inc()
        logger.info("Search index: deleted tag %s (outbox enqueued)", tag_id)


def get_search_indexer(db: AsyncSession) -> SearchIndexer:
    """Factory for EventBus handlers.

    Keeping this as a function makes it easy to swap implementations in tests
    (e.g., a fake indexer) without changing handler signatures.
    """

    return PostgresSearchIndexer(db)


__all__ = [
    "SearchIndexer",
    "PostgresSearchIndexer",
    "get_search_indexer",
]
