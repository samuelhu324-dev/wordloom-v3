"""RestoreBook UseCase - Restore a soft-deleted book

This use case handles:
- Validating book exists
- Clearing soft_deleted_at timestamp
- Making book active again
- Persisting via repository
"""

from uuid import UUID

from ...domain import Book
from ...application.ports.output import BookRepository
from ...exceptions import (
    BookNotFoundError,
    BookOperationError,
)


class RestoreBookUseCase:
    """Restore a soft-deleted book"""

    def __init__(self, repository: BookRepository):
        self.repository = repository

    async def execute(self, book_id: UUID) -> Book:
        """
        Restore book

        Args:
            book_id: Book ID to restore

        Returns:
            Restored Book domain object

        Raises:
            BookNotFoundError: If book not found
            BookOperationError: On persistence error
        """
        book = await self.repository.get_by_id(book_id)
        if not book:
            raise BookNotFoundError(book_id)

        try:
            book.restore()
            restored_book = await self.repository.save(book)
            return restored_book
        except Exception as e:
            raise BookOperationError(f"Failed to restore book: {str(e)}")
