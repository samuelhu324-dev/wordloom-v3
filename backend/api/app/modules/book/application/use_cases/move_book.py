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
from uuid import UUID
import logging

from api.app.shared.events import EventBus

from ...domain import Book
from ..ports.input import MoveBookRequest
from ..ports.output import BookRepository
from ...exceptions import (
    BookNotFoundError,
    InvalidBookMoveError,
    BookForbiddenError,
    BookLibraryAssociationError,
    DomainException,
    BookshelfNotFoundError,
)
from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository
from api.app.modules.library.application.ports.output import ILibraryRepository

logger = logging.getLogger(__name__)


class MoveBookUseCase:
    """Transfer a book to another bookshelf (RULE-011)"""

    def __init__(
        self,
        repository: BookRepository,
        event_bus: Optional[EventBus] = None,
        *,
        bookshelf_repository: Optional[IBookshelfRepository] = None,
        library_repository: Optional[ILibraryRepository] = None,
    ):
        self.repository = repository
        self.event_bus = event_bus
        self.bookshelf_repository = bookshelf_repository
        self.library_repository = library_repository

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
                raise BookNotFoundError(str(request.book_id))

            await self._enforce_library_owner(getattr(book, "library_id", None), request)
            await self._validate_target_bookshelf(book, request.target_bookshelf_id)

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
            raise InvalidBookMoveError(
                book_id=str(getattr(request, "book_id", "")),
                source_bookshelf_id=str(getattr(book, "bookshelf_id", "")),
                target_bookshelf_id=str(getattr(request, "target_bookshelf_id", "")),
                reason=str(e),
            )
        except InvalidBookMoveError:
            raise
        except Exception as e:
            if isinstance(e, DomainException):
                raise
            logger.error(f"Unexpected error in MoveBookUseCase: {e}", exc_info=True)
            raise InvalidBookMoveError(
                book_id=str(getattr(request, "book_id", "")),
                source_bookshelf_id=str(getattr(book, "bookshelf_id", "")),
                target_bookshelf_id=str(getattr(request, "target_bookshelf_id", "")),
                reason=f"Failed to move book: {str(e)}",
            )

    async def _validate_target_bookshelf(self, book: Book, target_bookshelf_id: UUID) -> None:
        if self.bookshelf_repository is None:
            # We can still move within domain rules, but we can't enforce same-library invariant safely.
            return
        target = await self.bookshelf_repository.get_by_id(target_bookshelf_id)
        if not target:
            raise BookshelfNotFoundError(bookshelf_id=str(target_bookshelf_id), book_id=str(getattr(book, "id", "")))
        if getattr(target, "library_id", None) != getattr(book, "library_id", None):
            raise InvalidBookMoveError(
                book_id=str(getattr(book, "id", "")),
                source_bookshelf_id=str(getattr(book, "bookshelf_id", "")),
                target_bookshelf_id=str(target_bookshelf_id),
                reason="Target bookshelf does not belong to the same library",
            )

    async def _enforce_library_owner(self, library_id: Optional[UUID], request: MoveBookRequest) -> None:
        if not getattr(request, "enforce_owner_check", True) or getattr(request, "actor_user_id", None) is None:
            return
        if self.library_repository is None:
            raise InvalidBookMoveError(
                book_id=str(getattr(request, "book_id", "")),
                source_bookshelf_id="(unknown)",
                target_bookshelf_id=str(getattr(request, "target_bookshelf_id", "")),
                reason="library_repository is required when enforcing owner checks",
            )
        if library_id is None:
            raise BookLibraryAssociationError(library_id="(missing)", book_id=str(getattr(request, "book_id", "")), reason="Book has no library_id")

        library = await self.library_repository.get_by_id(library_id)
        if not library:
            raise BookLibraryAssociationError(library_id=str(library_id), book_id=str(getattr(request, "book_id", "")), reason="Library not found")
        if getattr(library, "user_id", None) != request.actor_user_id:
            raise BookForbiddenError(
                book_id=str(getattr(request, "book_id", "")),
                library_id=str(library_id),
                actor_user_id=str(request.actor_user_id),
                reason="Actor does not own this library",
            )

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
