"""DeleteBook UseCase - Soft delete a book with Basement guard."""

from typing import Optional
from uuid import UUID

from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository
from api.app.modules.bookshelf.domain import BookshelfType
from api.app.shared.events import EventBus

from ..ports.input import DeleteBookRequest
from ..services import BookBasementBridge
from ...domain import Book
from ...application.ports.output import BookRepository
from ...exceptions import (
    BookNotFoundError,
    BookshelfNotFoundError,
    BookOperationError,
    InvalidBookMoveError,
)


class DeleteBookUseCase:
    """Soft delete a book via Basement pattern"""

    def __init__(
        self,
        repository: BookRepository,
        bookshelf_repository: IBookshelfRepository,
        event_bus: Optional[EventBus] = None,
        *,
        basement_bridge: Optional[BookBasementBridge] = None,
    ):
        self.repository = repository
        self.bookshelf_repository = bookshelf_repository
        self.event_bus = event_bus
        self._basement_bridge = basement_bridge

    async def execute(self, request: DeleteBookRequest) -> None:
        """
        Soft delete book by moving to Basement

        Args:
            request: DeleteBookRequest with book_id and basement_bookshelf_id

        Raises:
            BookNotFoundError: If book not found
            BookOperationError: On persistence error
        """
        book = await self.repository.get_by_id(request.book_id)
        if not book:
            raise BookNotFoundError(str(request.book_id))

        await self._validate_basement_target(book, request.basement_bookshelf_id)

        if self._basement_bridge:
            await self._delegate_to_basement_bridge(request)
            return

        try:
            # Call domain method to trigger BookMovedToBasement event
            book.move_to_basement(request.basement_bookshelf_id)
            # Persist with soft_deleted_at set by domain method
            await self.repository.save(book)
            await self._publish_events(book)
        except BookOperationError:
            raise
        except Exception as e:
            raise BookOperationError(f"Failed to delete book: {str(e)}")

    async def _publish_events(self, book: Book) -> None:
        if not self.event_bus:
            return

        events = getattr(book, "get_events", lambda: [])()
        if not events:
            return

        try:
            for event in events:
                await self.event_bus.publish(event)
        except Exception as exc:
            raise BookOperationError(f"Failed to publish book events: {str(exc)}")
        else:
            clear = getattr(book, "clear_events", None)
            if callable(clear):
                clear()

    async def _delegate_to_basement_bridge(self, request: DeleteBookRequest) -> None:
        await self._basement_bridge.move_book_to_basement(
            book_id=request.book_id,
            basement_bookshelf_id=request.basement_bookshelf_id,
        )

    async def _validate_basement_target(self, book: Book, basement_bookshelf_id: UUID) -> None:
        target = await self.bookshelf_repository.get_by_id(basement_bookshelf_id)
        if not target:
            raise BookshelfNotFoundError(
                bookshelf_id=str(basement_bookshelf_id),
                book_id=str(book.id),
            )

        if target.library_id != book.library_id:
            raise InvalidBookMoveError(
                book_id=str(book.id),
                source_bookshelf_id=str(book.bookshelf_id),
                target_bookshelf_id=str(basement_bookshelf_id),
                reason="Basement bookshelf does not belong to the same library",
            )

        if target.type != BookshelfType.BASEMENT:
            raise InvalidBookMoveError(
                book_id=str(book.id),
                source_bookshelf_id=str(book.bookshelf_id),
                target_bookshelf_id=str(basement_bookshelf_id),
                reason="Target bookshelf is not marked as Basement",
            )
