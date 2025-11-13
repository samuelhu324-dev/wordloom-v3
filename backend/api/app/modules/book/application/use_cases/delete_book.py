"""DeleteBook UseCase - Soft delete a book

This use case handles:
- Validating book exists
- Setting soft_deleted_at timestamp
- Preserving book data (soft delete)
- Persisting via repository

RULE-012: Books support soft delete via soft_deleted_at timestamp
"""

from uuid import UUID

from ...application.ports.output import BookRepository
from ...exceptions import (
    BookNotFoundError,
    BookOperationError,
)


class DeleteBookUseCase:
    """Soft delete a book"""

    def __init__(self, repository: BookRepository):
        self.repository = repository

    async def execute(self, book_id: UUID) -> None:
        """
        Soft delete book

        Args:
            book_id: Book ID to delete

        Raises:
            BookNotFoundError: If book not found
            BookOperationError: On persistence error
        """
        book = await self.repository.get_by_id(book_id)
        if not book:
            raise BookNotFoundError(book_id)

        try:
            await self.repository.delete(book_id)
        except Exception as e:
            raise BookOperationError(f"Failed to delete book: {str(e)}")
