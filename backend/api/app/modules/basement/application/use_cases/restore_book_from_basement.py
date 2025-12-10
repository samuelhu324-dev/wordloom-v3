"""RestoreBookFromBasementUseCase implementation."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from api.app.modules.book.application.ports.output import BookRepository
from api.app.modules.book.domain import Book
from api.app.modules.book.exceptions import (
    BookNotFoundError,
    BookNotInBasementError,
    BookOperationError,
)
from api.app.shared.events import EventBus

from ...application.ports.output import BasementRepository
from ...domain.entities import BasementBookSnapshot
from ..dtos import RestoreBookFromBasementCommand


class RestoreBookFromBasementUseCase:
    """Restore previously soft-deleted books back to an active bookshelf."""

    def __init__(
        self,
        book_repository: BookRepository,
        basement_repository: BasementRepository,
        event_bus: Optional[EventBus] = None,
    ):
        self._book_repository = book_repository
        self._basement_repository = basement_repository
        # EventBus kept optional per Plan173E; re-enable by injecting DI event_bus
        self._event_bus = event_bus

    async def execute(self, command: RestoreBookFromBasementCommand) -> BasementBookSnapshot:
        book = await self._book_repository.get_by_id(command.book_id)
        if not book:
            book = await self._get_deleted_book(command.book_id)
        if not book:
            raise BookNotFoundError(str(command.book_id))
        if not book.is_in_basement:
            raise BookNotInBasementError(str(command.book_id))

        try:
            book.restore_from_basement(command.target_bookshelf_id)
            saved = await self._book_repository.save(book)
            await self._publish_events(saved)

            # Remove BasementEntry since book is no longer in Basement
            await self._basement_repository.delete_by_book_id(command.book_id)

            return BasementBookSnapshot.from_domain(saved)
        except BookNotInBasementError:
            raise
        except BookOperationError:
            raise
        except Exception as exc:  # pragma: no cover - defensive guard
            raise BookOperationError(f"Failed to restore book from Basement: {exc}") from exc

    async def _get_deleted_book(self, book_id: UUID) -> Optional[Book]:
        deleted, _ = await self._book_repository.get_deleted_books(
            skip=0,
            limit=1,
            book_id=book_id,
        )
        return deleted[0] if deleted else None

    async def _publish_events(self, book: Book) -> None:
        if not self._event_bus:
            return
        events = getattr(book, "get_events", lambda: [])()
        for event in events:
            await self._event_bus.publish(event)
        clear = getattr(book, "clear_events", None)
        if callable(clear):
            clear()
