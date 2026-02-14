"""RestoreBook UseCase - Restore a soft-deleted book from Basement

This use case handles:
- Delegating to BookBasementBridge when available
- Fallback: Validating book exists and is in Basement
- Calling domain.restore_from_basement() to clear soft_deleted_at
- Publishing BookRestoredFromBasement event
- Making book active again
- Persisting via repository

RULE-013: Restore soft-deleted books from Basement to target bookshelf
"""

from typing import Optional
from uuid import UUID

from api.app.shared.events import EventBus

from ..ports.input import RestoreBookRequest
from ..services import BookBasementBridge
from ...domain import Book
from ...application.ports.output import BookRepository
from ...exceptions import (
    BookNotFoundError,
    BookOperationError,
    BookNotInBasementError,
    BookForbiddenError,
    BookLibraryAssociationError,
    DomainException,
    BookshelfNotFoundError,
    InvalidBookMoveError,
)
from api.app.modules.library.application.ports.output import ILibraryRepository
from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository


class RestoreBookUseCase:
    """Restore a soft-deleted book from Basement"""

    def __init__(
        self,
        repository: BookRepository,
        event_bus: Optional[EventBus] = None,
        *,
        basement_bridge: Optional[BookBasementBridge] = None,
        library_repository: Optional[ILibraryRepository] = None,
        bookshelf_repository: Optional[IBookshelfRepository] = None,
    ):
        self.repository = repository
        self.event_bus = event_bus
        self._basement_bridge = basement_bridge
        self.library_repository = library_repository
        self.bookshelf_repository = bookshelf_repository

    async def execute(self, request: RestoreBookRequest) -> Book:
        """
        Restore book from Basement

        Args:
            request: RestoreBookRequest with book_id and target_bookshelf_id

        Returns:
            Restored Book domain object

        Raises:
            BookNotFoundError: If book not found
            BookNotInBasementError: If book is not soft-deleted
            BookOperationError: On persistence error
        """
        if self._basement_bridge:
            await self._basement_bridge.restore_book_from_basement(
                book_id=request.book_id,
                target_bookshelf_id=request.target_bookshelf_id,
            )
            book = await self.repository.get_by_id(request.book_id)
            if not book:
                raise BookOperationError(f"Restored book {request.book_id} not found in repository")
            return book

        book = await self.repository.get_by_id(request.book_id)
        if not book:
            raise BookNotFoundError(str(request.book_id))

        await self._enforce_library_owner(getattr(book, "library_id", None), request)
        await self._validate_target_bookshelf(book, request.target_bookshelf_id)

        # Validate book is in Basement (soft_deleted_at is not None)
        if book.soft_deleted_at is None:
            raise BookNotInBasementError(request.book_id)

        try:
            # Call domain method to trigger BookRestoredFromBasement event
            book.restore_from_basement(request.target_bookshelf_id)
            # Persist with soft_deleted_at cleared by domain method
            restored_book = await self.repository.save(book)
            await self._publish_events(restored_book)
            return restored_book
        except BookOperationError:
            raise
        except Exception as e:
            if isinstance(e, DomainException):
                raise
            raise BookOperationError(f"Failed to restore book: {str(e)}")

    async def _validate_target_bookshelf(self, book: Book, target_bookshelf_id: UUID) -> None:
        if self.bookshelf_repository is None:
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

    async def _enforce_library_owner(self, library_id: Optional[UUID], request: RestoreBookRequest) -> None:
        if not getattr(request, "enforce_owner_check", True) or getattr(request, "actor_user_id", None) is None:
            return
        if self.library_repository is None:
            raise BookOperationError("library_repository is required when enforcing owner checks")
        if library_id is None:
            raise BookLibraryAssociationError(library_id="(missing)", book_id=str(request.book_id), reason="Book has no library_id")

        library = await self.library_repository.get_by_id(library_id)
        if not library:
            raise BookLibraryAssociationError(library_id=str(library_id), book_id=str(request.book_id), reason="Library not found")
        if getattr(library, "user_id", None) != request.actor_user_id:
            raise BookForbiddenError(
                book_id=str(request.book_id),
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
            raise BookOperationError(f"Failed to publish book events: {str(exc)}")
        else:
            clear = getattr(book, "clear_events", None)
            if callable(clear):
                clear()
