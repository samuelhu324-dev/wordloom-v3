"""ListBooks UseCase - List books in a bookshelf

This use case handles:
- Querying repository for active books (not soft-deleted)
- Supporting pagination
- Returning list of Book domain objects
"""

from typing import List, Tuple
from uuid import UUID

from ...domain import Book
from ...application.ports.output import BookRepository
from ...exceptions import BookOperationError


class ListBooksUseCase:
    """List books in a bookshelf"""

    def __init__(self, repository: BookRepository):
        self.repository = repository

    async def execute(
        self,
        bookshelf_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Book], int]:
        """
        List books with pagination

        Args:
            bookshelf_id: Bookshelf ID
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            Tuple of (list of Book objects, total count)

        Raises:
            BookOperationError: On query error
        """
        try:
            return await self.repository.get_by_bookshelf_id(bookshelf_id, skip, limit)
        except Exception as e:
            raise BookOperationError(f"Failed to list books: {str(e)}")
