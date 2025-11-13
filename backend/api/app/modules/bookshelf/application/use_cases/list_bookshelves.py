"""ListBookshelves UseCase - List all bookshelves in a library

This use case handles:
- Querying repository for all non-basement bookshelves
- Returning list of Bookshelf domain objects
"""

from typing import List
from uuid import UUID

from ...domain import Bookshelf
from ...application.ports.output import BookshelfRepository
from ...exceptions import BookshelfOperationError


class ListBookshelvesUseCase:
    """List all bookshelves in a library"""

    def __init__(self, repository: BookshelfRepository):
        self.repository = repository

    async def execute(self, library_id: UUID) -> List[Bookshelf]:
        """
        List bookshelves

        Args:
            library_id: Library ID

        Returns:
            List of Bookshelf domain objects

        Raises:
            BookshelfOperationError: On query error
        """
        try:
            return await self.repository.get_by_library_id(library_id)
        except Exception as e:
            raise BookshelfOperationError(f"Failed to list bookshelves: {str(e)}")
