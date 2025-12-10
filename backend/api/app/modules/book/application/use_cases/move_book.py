"""
MoveBook UseCase - Transfer a book to another bookshelf

Implements RULE-011: Book Transfer Operation

This use case handles:
- Validating source book exists
- Validating target bookshelf exists
- Performing cross-bookshelf transfer
- Emitting BookMovedToBookshelf event
- Persisting changes via repository
"""

from typing import Optional
import logging

from api.app.shared.events import EventBus

from ...domain import Book
from ..ports.input import MoveBookRequest
from ..ports.output import BookRepository
from ...exceptions import (
    BookNotFoundError,
    InvalidBookMoveError,
)

logger = logging.getLogger(__name__)


class MoveBookUseCase:
    """Transfer a book to another bookshelf (RULE-011)"""

    def __init__(self, repository: BookRepository, event_bus: Optional[EventBus] = None):
        self.repository = repository
        self.event_bus = event_bus

    async def execute(self, request: MoveBookRequest) -> Book:
        """
        Move a book to a different bookshelf

        RULE-011: Books can move across bookshelves.
        Domain method: move_to_bookshelf()

        Args:
            request: MoveBookRequest containing:
                - book_id: UUID (the book to move)
                - target_bookshelf_id: UUID (destination bookshelf)
                - reason: Optional[str] (audit trail)

        Returns:
            BookResponse with updated bookshelf_id

        Raises:
            BookNotFoundError: If book doesn't exist
            InvalidBookMoveError: If move is invalid (same shelf, etc.)
        """
        try:
            # Fetch the book
            logger.debug(f"MoveBookUseCase: Fetching book {request.book_id}")
            book = await self.repository.get_by_id(request.book_id)
            if not book:
                logger.warning(f"Book not found: {request.book_id}")
                raise BookNotFoundError(f"Book {request.book_id} not found")

            # Validate move (throws ValueError if invalid)
            logger.info(
                "MoveBookUseCase: Moving book %s from %s to %s",
                book.id,
                book.bookshelf_id,
                request.target_bookshelf_id,
            )

            book.move_to_bookshelf(request.target_bookshelf_id)

            # Persist the changes
            updated_book = await self.repository.save(book)
            await self._publish_events(updated_book)
            logger.info(f"MoveBookUseCase: Book moved successfully: {updated_book.id}")

            return updated_book

        except BookNotFoundError:
            raise
        except ValueError as e:
            logger.warning(f"Invalid move operation: {e}")
            raise InvalidBookMoveError(str(e))
        except InvalidBookMoveError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in MoveBookUseCase: {e}", exc_info=True)
            raise InvalidBookMoveError(f"Failed to move book: {str(e)}")

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
            raise InvalidBookMoveError(f"Failed to publish move events: {str(exc)}")
        else:
            clear = getattr(book, "clear_events", None)
            if callable(clear):
                clear()
