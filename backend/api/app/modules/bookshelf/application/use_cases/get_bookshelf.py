"""GetBookshelf UseCase - Get a bookshelf by ID

This use case handles:
- Validating bookshelf exists
- Returning Bookshelf domain object
"""

from uuid import UUID

from ...domain import Bookshelf
from ...application.ports.output import BookshelfRepository
from ...exceptions import (
    BookshelfNotFoundError,
    BookshelfOperationError,
)


class GetBookshelfUseCase:
    """Get a bookshelf by ID"""

    def __init__(self, repository: BookshelfRepository):
        self.repository = repository

    async def execute(self, bookshelf_id: UUID) -> Bookshelf:
        """
        Get bookshelf

        Args:
            bookshelf_id: Bookshelf ID

        Returns:
            Bookshelf domain object

        Raises:
            BookshelfNotFoundError: If bookshelf not found
            BookshelfOperationError: On query error
        """
        try:
            bookshelf = await self.repository.get_by_id(bookshelf_id)
            if not bookshelf:
                raise BookshelfNotFoundError(bookshelf_id)
            return bookshelf
        except Exception as e:
            if isinstance(e, BookshelfNotFoundError):
                raise
            raise BookshelfOperationError(f"Failed to get bookshelf: {str(e)}")
