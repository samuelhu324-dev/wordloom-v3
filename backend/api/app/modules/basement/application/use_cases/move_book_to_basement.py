"""MoveBookToBasementUseCase implementation."""
from __future__ import annotations

from typing import Optional

from api.app.modules.book.application.ports.output import BookRepository
from api.app.modules.book.domain import Book
from api.app.modules.book.exceptions import (
    BookAlreadyDeletedError,
    BookNotFoundError,
    BookOperationError,
)
from api.app.shared.events import EventBus

from ...application.ports.output import BasementRepository
from ...domain.basement_entry import BasementEntry
from ...domain.entities import BasementBookSnapshot
from ..dtos import MoveBookToBasementCommand


class MoveBookToBasementUseCase:
    """Soft delete a book by moving it into the Basement bookshelf."""

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

    async def execute(self, command: MoveBookToBasementCommand) -> BasementBookSnapshot:
        book = await self._book_repository.get_by_id(command.book_id)
        if not book:
            raise BookNotFoundError(str(command.book_id))
        if book.is_in_basement:
            raise BookAlreadyDeletedError(str(command.book_id))

        try:
            book.move_to_basement(command.basement_bookshelf_id)
            saved_book = await self._book_repository.save(book)
            await self._publish_events(saved_book)

            # Persist BasementEntry for dedicated query view
            entry = BasementEntry.from_book(saved_book, moved_at=saved_book.moved_to_basement_at)
            await self._basement_repository.save(entry)

            return BasementBookSnapshot.from_domain(saved_book)
        except BookOperationError:
            raise
        except Exception as exc:  # pragma: no cover - defensive guard
            raise BookOperationError(f"Failed to move book to Basement: {exc}") from exc

    async def _publish_events(self, book: Book) -> None:
        if not self._event_bus:
            return
        events = getattr(book, "get_events", lambda: [])()
        for event in events:
            await self._event_bus.publish(event)
        clear = getattr(book, "clear_events", None)
        if callable(clear):
            clear()
