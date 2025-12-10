"""ListBookshelves UseCase - List all bookshelves in a library

This use case handles:
- Querying repository for all non-basement bookshelves
- Returning list of Bookshelf domain objects
"""

from typing import List
from uuid import UUID

from ...domain import Bookshelf
from ...application.ports.output import IBookshelfRepository
from ...application.ports.input import ListBookshelvesRequest
from ...exceptions import BookshelfException, BookshelfPersistenceError


class ListBookshelvesUseCase:
    """List all bookshelves in a library"""

    def __init__(self, repository: IBookshelfRepository):
        self.repository = repository

    async def execute(self, request: ListBookshelvesRequest) -> List[Bookshelf]:
        """
        List bookshelves

        Args:
            request: ListBookshelvesRequest with library_id, skip, limit

        Returns:
            List of Bookshelf domain objects

        Raises:
            BookshelfOperationError: On query error
        """
        try:
            return await self.repository.get_by_library_id(request.library_id)
        except BookshelfException:
            raise
        except Exception as e:
            raise BookshelfPersistenceError(
                operation="list_bookshelves",
                reason=f"Failed to query bookshelves for library {request.library_id}",
                original_error=e
            )
