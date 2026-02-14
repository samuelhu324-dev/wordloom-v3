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
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.modules.block.domain.events import BlockCreated, BlockUpdated
from api.app.modules.book.domain.events import BookCreated, BookRenamed
from api.app.modules.tag.domain.events import TagCreated, TagRenamed
from infra.database.models.search_index_models import SearchIndexModel
from infra.database.models.search_outbox_models import SearchOutboxEventModel
from infra.observability.tracing import inject_trace_context
from infra.database.models.book_models import BookModel
from infra.observability.outbox_metrics import outbox_produced_total
from infra.search.search_outbox_repository import SearchOutboxRepository

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

    async def index_book_created(self, event: BookCreated) -> None: ...

    async def index_book_renamed(self, event: BookRenamed) -> None: ...

    async def delete_book(self, *, book_id: UUID) -> None: ...

    async def index_tag_created(self, event: TagCreated) -> None: ...

    async def index_tag_renamed(self, event: TagRenamed) -> None: ...

    async def delete_tag(self, *, tag_id: UUID) -> None: ...


class PostgresSearchIndexer:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._outbox = SearchOutboxRepository(db)

    async def _get_library_id_for_book(self, book_id: UUID) -> UUID | None:
        return (
            await self._db.execute(
                select(BookModel.library_id).where(BookModel.id == book_id)
            )
        ).scalar_one_or_none()

    async def index_block_created(self, event: BlockCreated) -> None:
        occurred_at = event.occurred_at
        version = _event_version(occurred_at)
        library_id = await self._get_library_id_for_book(event.book_id)
        stmt = (
            pg_insert(SearchIndexModel)
            .values(
                entity_type="block",
                library_id=library_id,
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

        await self._outbox.enqueue(
            entity_type="block",
            entity_id=event.block_id,
            op="upsert",
            event_version=version,
        )
        outbox_produced_total.labels(event_type="block.created", entity_type="block").inc()
        logger.info("Search index: inserted block %s (outbox enqueued)", event.block_id)

    async def index_block_updated(self, event: BlockUpdated) -> None:
        occurred_at = event.occurred_at
        version = _event_version(occurred_at)
        library_id = await self._get_library_id_for_book(event.book_id)
        stmt = pg_insert(SearchIndexModel).values(
            entity_type="block",
            library_id=library_id,
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

        await self._outbox.enqueue(
            entity_type="block",
            entity_id=event.block_id,
            op="upsert",
            event_version=version,
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
        await self._outbox.enqueue(
            entity_type="block",
            entity_id=block_id,
            op="delete",
            event_version=version,
        )
        outbox_produced_total.labels(event_type="block.deleted", entity_type="block").inc()
        logger.info("Search index: deleted block %s (outbox enqueued)", block_id)

    async def index_book_created(self, event: BookCreated) -> None:
        occurred_at = event.occurred_at
        version = _event_version(occurred_at)
        library_id = await self._get_library_id_for_book(event.book_id)
        stmt = (
            pg_insert(SearchIndexModel)
            .values(
                entity_type="book",
                library_id=library_id,
                entity_id=event.book_id,
                text=event.title or "",
                snippet=(event.title or "")[:200],
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

        await self._outbox.enqueue(
            entity_type="book",
            entity_id=event.book_id,
            op="upsert",
            event_version=version,
        )
        outbox_produced_total.labels(event_type="book.created", entity_type="book").inc()
        logger.info("Search index: inserted book %s (outbox enqueued)", event.book_id)

    async def index_book_renamed(self, event: BookRenamed) -> None:
        occurred_at = event.occurred_at
        version = _event_version(occurred_at)
        library_id = await self._get_library_id_for_book(event.book_id)

        stmt = pg_insert(SearchIndexModel).values(
            entity_type="book",
            library_id=library_id,
            entity_id=event.book_id,
            text=event.new_title or "",
            snippet=(event.new_title or "")[:200],
            rank_score=0.0,
            created_at=occurred_at,
            updated_at=occurred_at,
            event_version=version,
        )
        excluded = stmt.excluded
        stmt = stmt.on_conflict_do_update(
            index_elements=[SearchIndexModel.entity_type, SearchIndexModel.entity_id],
            set_={
                "library_id": excluded.library_id,
                "text": excluded.text,
                "snippet": excluded.snippet,
                "updated_at": excluded.updated_at,
                "event_version": excluded.event_version,
            },
            where=SearchIndexModel.event_version <= excluded.event_version,
        )
        await self._db.execute(stmt)

        await self._outbox.enqueue(
            entity_type="book",
            entity_id=event.book_id,
            op="upsert",
            event_version=version,
        )
        outbox_produced_total.labels(event_type="book.renamed", entity_type="book").inc()
        logger.info("Search index: updated book %s (outbox enqueued)", event.book_id)

    async def delete_book(self, *, book_id: UUID) -> None:
        stmt = delete(SearchIndexModel).where(
            SearchIndexModel.entity_type == "book",
            SearchIndexModel.entity_id == book_id,
        )
        await self._db.execute(stmt)

        version = _event_version(datetime.utcnow())
        await self._outbox.enqueue(
            entity_type="book",
            entity_id=book_id,
            op="delete",
            event_version=version,
        )
        outbox_produced_total.labels(event_type="book.deleted", entity_type="book").inc()
        logger.info("Search index: deleted book %s (outbox enqueued)", book_id)

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

        traceparent, tracestate = inject_trace_context()
        await self._db.execute(
            pg_insert(SearchOutboxEventModel).values(
                entity_type="tag",
                entity_id=event.tag_id,
                op="upsert",
                event_version=version,
                traceparent=traceparent,
                tracestate=tracestate,
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

        traceparent, tracestate = inject_trace_context()
        await self._db.execute(
            pg_insert(SearchOutboxEventModel).values(
                entity_type="tag",
                entity_id=event.tag_id,
                op="upsert",
                event_version=version,
                traceparent=traceparent,
                tracestate=tracestate,
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
        traceparent, tracestate = inject_trace_context()
        await self._db.execute(
            pg_insert(SearchOutboxEventModel).values(
                entity_type="tag",
                entity_id=tag_id,
                op="delete",
                event_version=version,
                traceparent=traceparent,
                tracestate=tracestate,
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
