"""CreateBook UseCase - Create a new book

This use case handles:
- Validating bookshelf exists
- Creating Book domain object
- Persisting via repository
- Publishing domain events via EventBus

Books support soft delete via soft_deleted_at timestamp
"""

from typing import Optional
from uuid import UUID

from api.app.shared.events import EventBus

from ...domain import Book
from ...application.ports.output import BookRepository
from ...exceptions import (
    BookOperationError,
    BookForbiddenError,
    BookLibraryAssociationError,
    DomainException,
)
from api.app.modules.library.application.ports.output import ILibraryRepository


class CreateBookUseCase:
    """Create a new book"""

    def __init__(
        self,
        repository: BookRepository,
        event_bus: Optional[EventBus] = None,
        *,
        library_repository: Optional[ILibraryRepository] = None,
    ):
        self.repository = repository
        self.event_bus = event_bus
        self.library_repository = library_repository

    async def execute(
        self,
        bookshelf_id: UUID,
        library_id: UUID,
        title: str,
        description: Optional[str] = None,
        cover_icon: Optional[str] = None,
        *,
        actor_user_id: Optional[UUID] = None,
        enforce_owner_check: bool = True,
    ) -> Book:
        """
        Create book

        Args:
            bookshelf_id: Bookshelf ID
            library_id: Library ID (for permission checks)
            title: Book title
            description: Optional description

        Returns:
            Created Book domain object

        Raises:
            BookOperationError: On persistence error
        """
        try:
            await self._enforce_library_owner(
                library_id,
                actor_user_id=actor_user_id,
                enforce_owner_check=enforce_owner_check,
            )
            book = Book.create(
                bookshelf_id=bookshelf_id,
                library_id=library_id,
                title=title,
                summary=description,
                cover_icon=cover_icon,
            )
            created_book = await self.repository.save(book)
            await self._publish_events(created_book)
            return created_book

        except Exception as e:
            if isinstance(e, DomainException):
                raise
            raise BookOperationError(f"Failed to create book: {str(e)}")

    async def _enforce_library_owner(
        self,
        library_id: UUID,
        *,
        actor_user_id: Optional[UUID],
        enforce_owner_check: bool,
    ) -> None:
        if not enforce_owner_check or actor_user_id is None:
            return
        if self.library_repository is None:
            raise BookOperationError("library_repository is required when enforcing owner checks")

        library = await self.library_repository.get_by_id(library_id)
        if not library:
            raise BookLibraryAssociationError(library_id=str(library_id), reason="Library not found")
        if getattr(library, "user_id", None) != actor_user_id:
            raise BookForbiddenError(
                library_id=str(library_id),
                actor_user_id=str(actor_user_id),
                reason="Actor does not own this library",
            )

    async def _publish_events(self, book: Book) -> None:
        """Publish domain events captured on the aggregate"""
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
