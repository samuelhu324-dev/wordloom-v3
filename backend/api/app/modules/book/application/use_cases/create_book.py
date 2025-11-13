"""CreateBook UseCase - Create a new book

This use case handles:
- Validating bookshelf exists
- Creating Book domain object
- Persisting via repository

Books support soft delete via soft_deleted_at timestamp
"""

from typing import Optional
from uuid import UUID

from ...domain import Book
from ...application.ports.output import BookRepository
from ...exceptions import (
    BookOperationError,
)


class CreateBookUseCase:
    """Create a new book"""

    def __init__(self, repository: BookRepository):
        self.repository = repository

    async def execute(
        self,
        bookshelf_id: UUID,
        title: str,
        description: Optional[str] = None,
        cover_image_url: Optional[str] = None
    ) -> Book:
        """
        Create book

        Args:
            bookshelf_id: Bookshelf ID
            title: Book title
            description: Optional description
            cover_image_url: Optional cover image URL

        Returns:
            Created Book domain object

        Raises:
            BookOperationError: On persistence error
        """
        try:
            book = Book.create(
                bookshelf_id=bookshelf_id,
                title=title,
                description=description,
                cover_image_url=cover_image_url
            )
            created_book = await self.repository.save(book)
            return created_book

        except Exception as e:
            raise BookOperationError(f"Failed to create book: {str(e)}")
