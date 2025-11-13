"""DeleteBookshelf UseCase - Delete a bookshelf

This use case handles:
- Validating bookshelf exists
- Preventing deletion of Basement bookshelf
- Soft or hard delete
- Handling cascading deletion

RULE-010: Basement bookshelf cannot be deleted
"""

from uuid import UUID

from ...domain import Bookshelf
from ...application.ports.output import BookshelfRepository
from ...exceptions import (
    BookshelfNotFoundError,
    BookshelfOperationError,
)


class DeleteBookshelfUseCase:
    """Delete a bookshelf"""

    def __init__(self, repository: BookshelfRepository):
        self.repository = repository

    async def execute(self, bookshelf_id: UUID) -> None:
        """
        Delete bookshelf

        Args:
            bookshelf_id: Bookshelf ID to delete

        Raises:
            BookshelfNotFoundError: If bookshelf not found
            BookshelfOperationError: If basement or on persistence error
        """
        bookshelf = await self.repository.get_by_id(bookshelf_id)
        if not bookshelf:
            raise BookshelfNotFoundError(bookshelf_id)

        # Check if basement (RULE-010)
        if bookshelf.is_basement():
            raise BookshelfOperationError("Cannot delete Basement bookshelf")

        try:
            await self.repository.delete(bookshelf_id)
        except Exception as e:
            raise BookshelfOperationError(f"Failed to delete bookshelf: {str(e)}")
