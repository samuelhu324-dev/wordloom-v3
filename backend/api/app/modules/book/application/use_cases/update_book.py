"""UpdateBook UseCase - Update book properties

This use case handles:
- Validating book exists
- Updating title, summary, maturity lifecycle
- Persisting via repository and publishing domain events
"""

from typing import Optional, Iterable, List
from uuid import UUID

from ...domain import Book, BookMaturity
from ...application.ports.output import BookRepository
from ...application.ports.input import UpdateBookRequest
from ...exceptions import (
    BookNotFoundError,
    BookOperationError,
    DomainException,
    BookForbiddenError,
    BookLibraryAssociationError,
)
from ...domain.exceptions import InvalidBookDataError
from api.app.shared.events import EventBus
from ..services import BookTagSyncService
from api.app.modules.library.application.ports.output import ILibraryRepository


class UpdateBookUseCase:
    """Update book properties"""

    def __init__(
        self,
        repository: BookRepository,
        event_bus: Optional[EventBus] = None,
        tag_sync_service: Optional[BookTagSyncService] = None,
        *,
        library_repository: Optional[ILibraryRepository] = None,
    ):
        self.repository = repository
        self.event_bus = event_bus
        self.tag_sync_service = tag_sync_service
        self.library_repository = library_repository

    async def execute(self, request: UpdateBookRequest) -> Book:
        """
        Update book

        Args:
            request: UpdateBookRequest containing fields to mutate

        Returns:
            Updated Book domain object

        Raises:
            BookNotFoundError: If book not found
            BookOperationError: On persistence error
        """
        book_id = getattr(request, "book_id", None)
        if book_id is None:
            raise InvalidBookDataError("Book ID is required for update")

        book = await self.repository.get_by_id(book_id)
        if not book:
            raise BookNotFoundError(book_id)

        await self._enforce_library_owner(getattr(book, "library_id", None), request)

        try:
            title = getattr(request, "title", None)
            if title is not None:
                book.update_title(title)

            description = getattr(request, "summary", None)
            if description is not None:
                book.update_description(description)

            maturity = getattr(request, "maturity", None)
            if maturity is not None:
                try:
                    new_maturity = (
                        maturity
                        if isinstance(maturity, BookMaturity)
                        else BookMaturity(str(maturity))
                    )
                except ValueError as conversion_error:
                    raise InvalidBookDataError(str(conversion_error)) from conversion_error
                book.change_maturity(new_maturity)

            is_pinned = getattr(request, "is_pinned", None)
            if is_pinned is not None:
                book.set_pinned(bool(is_pinned))

            if getattr(request, "cover_icon_provided", False):
                book.update_cover_icon(getattr(request, "cover_icon", None))

            if getattr(request, "cover_media_id_provided", False):
                book.set_cover_media(getattr(request, "cover_media_id", None))

            pending_tags_summary: Optional[List[str]] = None
            if request.tag_ids is not None:
                if not self.tag_sync_service:
                    raise InvalidBookDataError("Tag synchronization service is not configured")
                pending_tags_summary = await self.tag_sync_service.sync_tags(book_id, request.tag_ids)

            updated_book = await self.repository.save(book)
            if pending_tags_summary is not None:
                setattr(updated_book, "tags_summary", pending_tags_summary)
            await self._publish_events(updated_book)
            return updated_book

        except DomainException:
            raise
        except Exception as e:
            raise BookOperationError(f"Failed to update book: {str(e)}")

    async def _enforce_library_owner(self, library_id: Optional[UUID], request: UpdateBookRequest) -> None:
        if not getattr(request, "enforce_owner_check", True) or getattr(request, "actor_user_id", None) is None:
            return
        if self.library_repository is None:
            raise BookOperationError("library_repository is required when enforcing owner checks")
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
        """Publish any queued domain events via the event bus"""
        if not self.event_bus:
            return

        pending_events: Iterable = getattr(book, "get_events", lambda: [])()
        for event in pending_events:
            await self.event_bus.publish(event)

        clear = getattr(book, "clear_events", None)
        if callable(clear):
            clear()
