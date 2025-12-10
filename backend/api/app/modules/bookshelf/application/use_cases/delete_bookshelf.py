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

from api.app.modules.bookshelf.application.ports.input import (
    DeleteBookshelfRequest,
    DeleteBookshelfResponse,
    IDeleteBookshelfUseCase,
)
from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository


class DeleteBookshelfUseCase(IDeleteBookshelfUseCase):
    """Implementation of DeleteBookshelf UseCase

    Orchestrates:
    1. Load bookshelf from repository
    2. Validate not Basement type
    3. Call domain method: bookshelf.mark_deleted()
    4. Persist updated bookshelf
    5. Return response with updated status
    """

    def __init__(self, repository: IBookshelfRepository):
        """
        Initialize DeleteBookshelfUseCase

        Args:
            repository: IBookshelfRepository implementation for persistence
        """
        self.repository = repository

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
            raise ValueError(f"Bookshelf {request.bookshelf_id} not found")

        # Step 3: Validate not Basement (RULE-010)
        if bookshelf.is_basement:
            raise ValueError(
                f"Cannot delete Basement bookshelf {request.bookshelf_id} - it serves as recycle bin"
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
