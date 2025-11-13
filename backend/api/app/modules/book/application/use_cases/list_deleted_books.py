"""ListDeletedBooks UseCase - List soft-deleted books

This use case handles:
- Querying repository for deleted books (with soft_deleted_at set)
- Supporting pagination
- Returning list of Book domain objects
"""

from typing import List, Tuple
from uuid import UUID

from ...domain import Book
from ...application.ports.output import BookRepository
from ...exceptions import BookOperationError


class ListDeletedBooksUseCase:
    """List soft-deleted books"""

    def __init__(self, repository: BookRepository):
        self.repository = repository

    async def execute(
        self,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Book], int]:
        """
        List deleted books with pagination

        Args:
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            Tuple of (list of Book objects, total count)

        Raises:
            BookOperationError: On query error
        """
        try:
            return await self.repository.get_deleted_books(skip, limit)
        except Exception as e:
            raise BookOperationError(f"Failed to list deleted books: {str(e)}")
