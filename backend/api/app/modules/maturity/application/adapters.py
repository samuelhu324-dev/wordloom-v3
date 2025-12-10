"""Default adapters bridging the book aggregate to the maturity module."""
from __future__ import annotations

import logging
from uuid import UUID

from api.app.modules.book.application.ports.output import BookRepository
from api.app.modules.block.application.ports.output import BlockRepository
from api.app.modules.book.domain import BookMaturity
from api.app.modules.tag.application.ports.output import TagRepository
from api.app.modules.tag.domain import EntityType as TagEntityType

from ..domain import BookProfileSnapshot, MaturityStage
from .ports import MaturityDataProvider
from ..exceptions import BookMaturitySourceNotFound

logger = logging.getLogger(__name__)


class BookAggregateMaturityDataProvider(MaturityDataProvider):
    """Reads the Book aggregate and derives normalized maturity facts."""

    def __init__(
        self,
        book_repository: BookRepository,
        block_repository: BlockRepository | None = None,
        tag_repository: TagRepository | None = None,
    ) -> None:
        self._book_repository = book_repository
        self._block_repository = block_repository
        self._tag_repository = tag_repository

    async def load_book_profile(self, book_id: UUID) -> BookProfileSnapshot:
        book = await self._book_repository.get_by_id(book_id)
        if not book:
            raise BookMaturitySourceNotFound(book_id)

        maturity_value = getattr(book, "maturity", None)
        maturity_stage = None
        try:
            if isinstance(maturity_value, BookMaturity):
                maturity_stage = MaturityStage(maturity_value.value)
            elif maturity_value is not None:
                maturity_stage = MaturityStage(str(maturity_value))
        except ValueError:
            maturity_stage = None

        tag_count_snapshot = await self._resolve_tag_count(book)
        block_count, block_type_count = await self._resolve_block_metrics(book)

        return BookProfileSnapshot(
            book_id=book.id,
            library_id=book.library_id,
            bookshelf_id=book.bookshelf_id,
            title=getattr(book.title, "value", None),
            summary=getattr(book.summary, "value", None),
            cover_icon=getattr(book, "cover_icon", None),
            maturity=maturity_stage,
            maturity_score=getattr(book, "maturity_score", 0) or 0,
            tag_count_snapshot=tag_count_snapshot,
            block_type_count=block_type_count,
            block_count=block_count,
            open_todo_snapshot=getattr(book, "open_todo_snapshot", 0) or 0,
            operations_bonus=getattr(book, "operations_bonus", 0) or 0,
            visit_count_90d=getattr(book, "visit_count_90d", 0) or 0,
            last_visit_at=getattr(book, "last_visited_at", None),
            last_event_at=getattr(book, "last_content_edit_at", getattr(book, "updated_at", None)),
            book=book,
        )

    async def _resolve_tag_count(self, book) -> int:
        snapshot_value = getattr(book, "tag_count_snapshot", 0) or 0
        if snapshot_value or not self._tag_repository:
            return snapshot_value

        try:
            tags = await self._tag_repository.find_by_entity(TagEntityType.BOOK, book.id)
        except Exception as exc:  # pragma: no cover - defensive logging only
            logger.warning(
                "Fallback tag lookup failed; using snapshot value",
                extra={"book_id": str(getattr(book, "id", None)), "error": str(exc)},
            )
            return snapshot_value

        live_count = len(tags)
        return live_count or snapshot_value

    async def _resolve_block_metrics(self, book) -> tuple[int, int]:
        count_snapshot = getattr(book, "block_count", 0) or 0
        type_snapshot = getattr(book, "block_type_count", 0) or 0

        if not self._block_repository:
            return count_snapshot, type_snapshot

        needs_count = count_snapshot <= 0
        needs_type = type_snapshot <= 0
        if not needs_count and not needs_type:
            return count_snapshot, type_snapshot

        try:
            live_count, live_type = await self._block_repository.count_active_blocks(book.id)
        except Exception as exc:  # pragma: no cover - defensive logging only
            logger.warning(
                "Fallback block metric lookup failed; using snapshot values",
                extra={"book_id": str(getattr(book, "id", None)), "error": str(exc)},
            )
            return count_snapshot, type_snapshot

        resolved_count = live_count if needs_count else count_snapshot
        resolved_types = live_type if needs_type else type_snapshot
        return resolved_count, resolved_types
