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
from ...exceptions import (
    BookshelfException,
    BookshelfForbiddenError,
    BookshelfLibraryAssociationError,
    BookshelfOperationError,
    BookshelfPersistenceError,
)
from api.app.modules.library.application.ports.output import ILibraryRepository


class ListBookshelvesUseCase:
    """List all bookshelves in a library"""

    def __init__(
        self,
        repository: IBookshelfRepository,
        *,
        library_repository: ILibraryRepository | None = None,
    ):
        self.repository = repository
        self.library_repository = library_repository

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
            await self._enforce_library_owner(request)
            return await self.repository.get_by_library_id(request.library_id)
        except BookshelfException:
            raise
        except Exception as e:
            raise BookshelfPersistenceError(
                operation="list_bookshelves",
                reason=f"Failed to query bookshelves for library {request.library_id}",
                original_error=e
            )

    async def _enforce_library_owner(self, request: ListBookshelvesRequest) -> None:
        if not request.enforce_owner_check or request.actor_user_id is None:
            return
        if self.library_repository is None:
            raise BookshelfOperationError(
                bookshelf_id="<unknown>",
                operation="authorize",
                reason="library_repository is required when enforcing owner checks",
            )

        library = await self.library_repository.get_by_id(request.library_id)
        if not library:
            raise BookshelfLibraryAssociationError(
                bookshelf_id="<unknown>",
                library_id=str(request.library_id),
                reason="Library not found",
            )
        if getattr(library, "user_id", None) != request.actor_user_id:
            raise BookshelfForbiddenError(
                library_id=str(request.library_id),
                actor_user_id=str(request.actor_user_id),
                reason="Actor does not own this library",
            )
