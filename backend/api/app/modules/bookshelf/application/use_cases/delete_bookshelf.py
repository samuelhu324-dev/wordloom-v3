"""DeleteBookshelf UseCase - Soft delete (mark as DELETED) a Bookshelf

Responsibilities:
- Load bookshelf from repository by ID
- Validate not Basement type (RULE-010)
- Call bookshelf.mark_deleted() to change status
- Persist updated bookshelf to repository
- Publish BookshelfDeletedEvent via domain events
- Return response

RULE-010: Basement bookshelf cannot be deleted (it's the recycle bin)
RULE-005: Deletion is soft (status → DELETED, not removed from database)

Design Pattern: UseCase (Application Layer)
- Orchestrates domain behavior with persistence
- Handles business rule validation (no Basement deletion)
- Coordinates event publication
"""
from uuid import UUID

from api.app.modules.bookshelf.application.ports.input import (
    DeleteBookshelfRequest,
    DeleteBookshelfResponse,
    IDeleteBookshelfUseCase,
)
from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository
from api.app.modules.bookshelf.exceptions import (
    BasementOperationError,
    BookshelfForbiddenError,
    BookshelfLibraryAssociationError,
    BookshelfNotFoundError,
    BookshelfOperationError,
)
from api.app.modules.library.application.ports.output import ILibraryRepository


class DeleteBookshelfUseCase(IDeleteBookshelfUseCase):
    """Implementation of DeleteBookshelf UseCase

    Orchestrates:
    1. Load bookshelf from repository
    2. Validate not Basement type
    3. Call domain method: bookshelf.mark_deleted()
    4. Persist updated bookshelf
    5. Return response with updated status
    """

    def __init__(
        self,
        repository: IBookshelfRepository,
        *,
        library_repository: ILibraryRepository | None = None,
    ):
        """
        Initialize DeleteBookshelfUseCase

        Args:
            repository: IBookshelfRepository implementation for persistence
        """
        self.repository = repository
        self.library_repository = library_repository

    async def execute(self, request: DeleteBookshelfRequest) -> DeleteBookshelfResponse:
        """
        Execute bookshelf deletion (soft delete)

        Args:
            request: DeleteBookshelfRequest with bookshelf_id

        Returns:
            DeleteBookshelfResponse with updated bookshelf status

        Raises:
            ValueError: If bookshelf not found or if Basement type
            Exception: On unexpected repository errors
        """

        # Step 1: Load bookshelf from repository
        bookshelf = await self.repository.get_by_id(request.bookshelf_id)

        # Step 2: Validate existence
        if not bookshelf:
            raise BookshelfNotFoundError(str(request.bookshelf_id))

        await self._enforce_library_owner(bookshelf.library_id, request)

        # Step 3: Validate not Basement (RULE-010)
        if bookshelf.is_basement:
            raise BasementOperationError(
                bookshelf_id=str(request.bookshelf_id),
                operation="delete",
                reason="Basement bookshelf cannot be deleted",
            )

        # Step 4: Call domain method to mark as deleted
        # This changes status to DELETED and publishes BookshelfDeletedEvent
        bookshelf.mark_deleted()

        # Step 5: Persist updated bookshelf
        await self.repository.save(bookshelf)

        # Step 6: Return response with updated status
        return DeleteBookshelfResponse(
            id=bookshelf.id,
            status=bookshelf.status.value,
            deleted_at=bookshelf.updated_at.isoformat() if bookshelf.updated_at else "",
        )

    async def _enforce_library_owner(self, library_id: UUID, request: DeleteBookshelfRequest) -> None:
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
