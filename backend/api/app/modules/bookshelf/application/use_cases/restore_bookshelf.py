"""
UseCase: RestoreBookshelf

Purpose:
- Implement the RestoreBookshelf input port
- Restore a soft-deleted Bookshelf from Basement
- Part of the unified deletion & recovery framework (ADR-038)

Architecture:
- Depends on IBookshelfRepository (output port)
- Depends on ILibraryRepository (output port) - for BASEMENT-001 validation
- Depends on EventBus (for publishing events)
- Uses domain method: Bookshelf.restore()

Invariants Enforced:
- BASEMENT-001: Cannot restore if parent Library is deleted
- BASEMENT-002: Restoration doesn't move data, just updates status
- Verify bookshelf exists and is in DELETED status

Related:
- DDD_RULES.yaml: deletion_recovery_framework.basement.recovery_rules
- ADR-038: Deletion & Recovery Unified Framework
- Domain: backend/api/app/modules/bookshelf/domain/bookshelf.py
"""

from datetime import datetime, timezone
from uuid import UUID

from api.app.modules.bookshelf.application.ports.input import (
    IRestoreBookshelfUseCase,
    RestoreBookshelfRequest,
    RestoreBookshelfResponse,
)
from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository
from api.app.modules.library.application.ports.output import ILibraryRepository


class RestoreBookshelfUseCase(IRestoreBookshelfUseCase):
    """
    Use Case: Restore a soft-deleted Bookshelf

    Workflow:
    1. Load Bookshelf by ID from repository
    2. Verify bookshelf exists
    3. Verify bookshelf is in DELETED status
    4. Load parent Library to verify not deleted (BASEMENT-001 invariant)
    5. Call Bookshelf.restore() to change status back to ACTIVE
    6. Persist updated bookshelf to repository
    7. Return response

    Error Handling:
    - ValueError: Bookshelf not found or invalid state
    """

    def __init__(
        self,
        bookshelf_repository: IBookshelfRepository,
        library_repository: ILibraryRepository,
    ):
        """
        Initialize RestoreBookshelfUseCase with dependencies

        Args:
            bookshelf_repository: Port for Bookshelf persistence
            library_repository: Port for Library validation (BASEMENT-001 check)
        """
        self.bookshelf_repository = bookshelf_repository
        self.library_repository = library_repository

    async def execute(
        self, request: RestoreBookshelfRequest
    ) -> RestoreBookshelfResponse:
        """
        Execute the RestoreBookshelf use case

        Args:
            request: RestoreBookshelfRequest containing bookshelf_id and cascade flag

        Returns:
            RestoreBookshelfResponse with restoration confirmation

        Raises:
            ValueError: If bookshelf not found, not deleted, or parent Library is deleted
        """
        # Step 1: Load bookshelf from repository
        bookshelf = await self.bookshelf_repository.get_by_id(request.bookshelf_id)
        if bookshelf is None:
            raise ValueError(f"Bookshelf {request.bookshelf_id} not found")

        # Step 2: Verify bookshelf is in DELETED status
        if not bookshelf.is_deleted:
            raise ValueError(
                f"Cannot restore Bookshelf {request.bookshelf_id}: status is "
                f"{bookshelf.status.value}, not DELETED"
            )

        # Step 3: Verify parent Library is not deleted (BASEMENT-001 invariant)
        library = await self.library_repository.get_by_id(bookshelf.library_id)
        if library is None or library.is_deleted():
            raise ValueError(
                f"Cannot restore Bookshelf {request.bookshelf_id}: parent Library "
                f"{bookshelf.library_id} is deleted or not found (BASEMENT-001 invariant)"
            )

        # Step 4: Call domain method to restore (emits BookshelfStatusChanged event)
        bookshelf.restore()

        # Step 5: Persist updated bookshelf to repository
        await self.bookshelf_repository.save(bookshelf)

        # Step 6: Return response
        now = datetime.now(timezone.utc)
        return RestoreBookshelfResponse(
            id=bookshelf.id,
            status=bookshelf.status.value,
            restored_at=now.isoformat(),
            restored_books_count=0,  # TODO: implement cascade restore
            message=f"Bookshelf '{bookshelf.name.value}' has been restored from Basement",
        )
