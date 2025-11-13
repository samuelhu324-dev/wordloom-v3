"""GetBook UseCase - Get a book by ID

This use case handles:
- Validating book exists (not soft-deleted)
- Returning Book domain object
"""

from uuid import UUID

from ...domain import Book
from ...application.ports.output import BookRepository
from ...exceptions import (
    BookNotFoundError,
    BookOperationError,
)


class GetBookUseCase:
    """Get a book by ID"""

    def __init__(self, repository: BookRepository):
        self.repository = repository

    async def execute(self, book_id: UUID) -> Book:
        """
        Get book

        Args:
            book_id: Book ID

        Returns:
            Book domain object

        Raises:
            BookNotFoundError: If book not found or is soft-deleted
            BookOperationError: On query error
        """
        try:
            book = await self.repository.get_by_id(book_id)
            if not book:
                raise BookNotFoundError(book_id)
            return book
        except Exception as e:
            if isinstance(e, BookNotFoundError):
                raise
            raise BookOperationError(f"Failed to get book: {str(e)}")
