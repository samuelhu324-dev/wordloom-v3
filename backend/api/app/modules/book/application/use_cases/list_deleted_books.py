"""ListDeletedBooks UseCase - List soft-deleted books from Basement

Implements RULE-012: Basement View Query

This use case handles:
- Querying repository for soft-deleted books (soft_deleted_at IS NOT NULL)
- Supporting optional filtering by bookshelf or library
- Supporting pagination
- Returning paginated list grouped by bookshelf
"""

from typing import List, Optional
from uuid import UUID
import logging

from ...domain import Book
from ..ports.input import (
    ListDeletedBooksRequest,
    BookListResponse,
    BookResponse,
)
from ..ports.output import BookRepository
from ...exceptions import BookOperationError

logger = logging.getLogger(__name__)


class ListDeletedBooksUseCase:
    """List soft-deleted books from Basement (RULE-012)"""

    def __init__(self, repository: BookRepository):
        self.repository = repository

    async def execute(self, request: ListDeletedBooksRequest) -> BookListResponse:
        """
        List deleted books with optional filtering and pagination

        RULE-012: Basement view - shows all soft-deleted books grouped by bookshelf.

        Args:
            request: ListDeletedBooksRequest containing:
                - bookshelf_id: Optional UUID (filter by original bookshelf)
                - library_id: Optional UUID (permission context)
                - skip: int (pagination offset)
                - limit: int (page size, 1-100)

        Returns:
            BookListResponse with paginated list of soft-deleted books

        Raises:
            BookOperationError: On query error
        """
        try:
            logger.debug(f"ListDeletedBooksUseCase: Querying deleted books, skip={request.skip}, limit={request.limit}")

            # Query repository for deleted books with filters
            deleted_books, total_count = await self.repository.get_deleted_books(
                skip=request.skip,
                limit=request.limit,
                bookshelf_id=request.bookshelf_id,
                library_id=request.library_id
            )

            logger.debug(f"ListDeletedBooksUseCase: Found {len(deleted_books)} deleted books (total: {total_count})")

            # Convert domain objects to response DTOs
            response_items = [BookResponse.from_domain(book) for book in deleted_books]

            return BookListResponse(
                items=response_items,
                total=total_count
            )

        except Exception as e:
            logger.error(f"Failed to list deleted books: {e}", exc_info=True)
            raise BookOperationError(f"Failed to list deleted books: {str(e)}")
