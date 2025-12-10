"""ListBasementBooksUseCase implementation."""
from __future__ import annotations

from typing import Tuple

from api.app.modules.book.exceptions import BookOperationError

from ...application.ports.output import BasementRepository
from ...domain.entities import BasementBookSnapshot
from ..dtos import ListBasementBooksQuery


class ListBasementBooksUseCase:
    """Return paginated Basement snapshots for a library."""

    def __init__(self, repository: BasementRepository):
        self._repository = repository

    async def execute(self, query: ListBasementBooksQuery) -> Tuple[list[BasementBookSnapshot], int]:
        try:
            entries, total = await self._repository.list_by_library(
                library_id=query.library_id,
                skip=query.skip,
                limit=query.limit,
            )
            snapshots = [self._entry_to_snapshot(entry) for entry in entries]
            return snapshots, total
        except Exception as exc:  # pragma: no cover - defensive guard
            raise BookOperationError(f"Failed to list Basement books: {exc}") from exc

    @staticmethod
    def _entry_to_snapshot(entry) -> BasementBookSnapshot:
        """Convert a BasementEntry to a BasementBookSnapshot for router consumption."""
        return BasementBookSnapshot(
            id=entry.book_id,
            library_id=entry.library_id,
            bookshelf_id=entry.bookshelf_id,
            previous_bookshelf_id=entry.previous_bookshelf_id,
            title=entry.title_snapshot,
            summary=entry.summary_snapshot,
            status=entry.status_snapshot,
            block_count=entry.block_count_snapshot,
            moved_to_basement_at=entry.moved_at,
            soft_deleted_at=entry.moved_at,
            created_at=entry.created_at,
            updated_at=entry.created_at,
        )
