"""DeleteBook UseCase - Soft delete a book

This use case handles:
- Validating book exists
- Calling domain.move_to_basement() for soft delete
- Publishing BookMovedToBasement event
- Preserving book data (soft delete via soft_deleted_at)
- Persisting via repository

RULE-012: Books support soft delete via soft_deleted_at timestamp
"""

from uuid import UUID

from ...domain import Book
from ...application.ports.output import BookRepository
from ...exceptions import (
    BookNotFoundError,
    BookOperationError,
)


class DeleteBookUseCase:
    """Soft delete a book via Basement pattern"""

    def __init__(self, repository: BookRepository):
        self.repository = repository

    async def execute(self, request) -> None:
        """
        Soft delete book by moving to Basement

        Args:
            request: DeleteBookRequest with book_id and basement_bookshelf_id

        Raises:
            BookNotFoundError: If book not found
            BookOperationError: On persistence error
        """
        book = await self.repository.get_by_id(request.book_id)
        if not book:
            raise BookNotFoundError(request.book_id)

        try:
            # Call domain method to trigger BookMovedToBasement event
            book.move_to_basement(request.basement_bookshelf_id)
            # Persist with soft_deleted_at set by domain method
            await self.repository.save(book)
        except Exception as e:
            raise BookOperationError(f"Failed to delete book: {str(e)}")
