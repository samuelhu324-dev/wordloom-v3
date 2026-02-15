"""GetBookshelf UseCase - Retrieve a Bookshelf by ID

Responsibilities:
- Query bookshelf from repository by ID
- Handle not-found case (raise exception or return empty)
- Return response DTO with bookshelf data

Design Pattern: UseCase (Application Layer)
- Read-only operation (Query)
- No state changes, no events published
- Simple pass-through from repository to Router
"""
from uuid import UUID

from api.app.modules.bookshelf.application.ports.input import (
    GetBookshelfRequest,
    GetBookshelfResponse,
    IGetBookshelfUseCase,
)
from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository
from api.app.modules.bookshelf.exceptions import (
    BookshelfForbiddenError,
    BookshelfLibraryAssociationError,
    BookshelfNotFoundError,
    BookshelfOperationError,
)
from api.app.modules.library.application.ports.output import ILibraryRepository


class GetBookshelfUseCase(IGetBookshelfUseCase):
    """Implementation of GetBookshelf UseCase

    Orchestrates:
    1. Query repository by ID
    2. Validate result (not None)
    3. Convert domain object to response DTO
    """

    def __init__(
        self,
        repository: IBookshelfRepository,
        *,
        library_repository: ILibraryRepository | None = None,
    ):
        """
        Initialize GetBookshelfUseCase

        Args:
            repository: IBookshelfRepository implementation for queries
        """
        self.repository = repository
        self.library_repository = library_repository

    async def execute(self, request: GetBookshelfRequest) -> GetBookshelfResponse:
        """
        Execute bookshelf retrieval

        Args:
            request: GetBookshelfRequest with bookshelf_id

        Returns:
            GetBookshelfResponse with bookshelf data

        Raises:
            ValueError: If bookshelf not found
            Exception: On unexpected repository errors
        """

        # Step 1: Query repository by ID
        bookshelf = await self.repository.get_by_id(request.bookshelf_id)

        # Step 2: Validate existence
        if not bookshelf:
            raise BookshelfNotFoundError(str(request.bookshelf_id))

        await self._enforce_library_owner(bookshelf.library_id, request)

        # Step 3: Convert to response DTO and return
        return GetBookshelfResponse.from_domain(bookshelf)

    async def _enforce_library_owner(self, library_id: UUID, request: GetBookshelfRequest) -> None:
        if not request.enforce_owner_check or request.actor_user_id is None:
            return
        if self.library_repository is None:
            raise BookshelfOperationError(
                bookshelf_id=str(request.bookshelf_id),
                operation="authorize",
                reason="library_repository is required when enforcing owner checks",
            )

        library = await self.library_repository.get_by_id(library_id)
        if not library:
            raise BookshelfLibraryAssociationError(
                bookshelf_id=str(request.bookshelf_id),
                library_id=str(library_id),
                reason="Library not found",
            )
        if getattr(library, "user_id", None) != request.actor_user_id:
            raise BookshelfForbiddenError(
                bookshelf_id=str(request.bookshelf_id),
                library_id=str(library_id),
                actor_user_id=str(request.actor_user_id),
                reason="Actor does not own this library",
            )
