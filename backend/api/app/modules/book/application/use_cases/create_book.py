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
)


class CreateBookUseCase:
    """Create a new book"""

    def __init__(self, repository: BookRepository, event_bus: Optional[EventBus] = None):
        self.repository = repository
        self.event_bus = event_bus

    async def execute(
        self,
        bookshelf_id: UUID,
        library_id: UUID,
        title: str,
        description: Optional[str] = None,
        cover_icon: Optional[str] = None,
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
            raise BookOperationError(f"Failed to create book: {str(e)}")

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
