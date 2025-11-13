"""UpdateBook UseCase - Update book properties

This use case handles:
- Validating book exists
- Updating title, description, cover image
- Persisting via repository
"""

from typing import Optional
from uuid import UUID

from ...domain import Book
from ...application.ports.output import BookRepository
from ...exceptions import (
    BookNotFoundError,
    BookOperationError,
)


class UpdateBookUseCase:
    """Update book properties"""

    def __init__(self, repository: BookRepository):
        self.repository = repository

    async def execute(
        self,
        book_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        cover_image_url: Optional[str] = None
    ) -> Book:
        """
        Update book

        Args:
            book_id: Book ID
            title: New title (optional)
            description: New description (optional)
            cover_image_url: New cover image URL (optional)

        Returns:
            Updated Book domain object

        Raises:
            BookNotFoundError: If book not found
            BookOperationError: On persistence error
        """
        book = await self.repository.get_by_id(book_id)
        if not book:
            raise BookNotFoundError(book_id)

        try:
            if title is not None:
                book.update_title(title)

            if description is not None:
                book.update_description(description)

            if cover_image_url is not None:
                book.update_cover_image(cover_image_url)

            updated_book = await self.repository.save(book)
            return updated_book

        except Exception as e:
            if isinstance(e, BookNotFoundError):
                raise
            raise BookOperationError(f"Failed to update book: {str(e)}")
