"""
UseCase: RestoreLibrary

Purpose:
- Implement the RestoreLibrary input port
- Restore a soft-deleted Library from Basement
- Part of the unified deletion & recovery framework (ADR-038)

Architecture:
- Depends on ILibraryRepository (output port)
- Depends on EventBus (for publishing LibraryRestored event)
- Uses domain method: Library.restore()

Invariants Enforced:
- BASEMENT-001: As root aggregate, Library has no parent dependency check
- Verify library exists before attempting restoration
- Verify library is actually deleted (soft_deleted_at not null)

Related:
- DDD_RULES.yaml: deletion_recovery_framework.basement
- ADR-038: Deletion & Recovery Unified Framework
- Domain: backend/api/app/modules/library/domain/library.py
"""

from datetime import datetime, timezone
from uuid import UUID

from api.app.modules.library.application.ports.input import (
    IRestoreLibraryUseCase,
    RestoreLibraryRequest,
    RestoreLibraryResponse,
)
from api.app.modules.library.application.ports.output import ILibraryRepository
from api.app.shared.events import EventBus
from api.app.shared.exceptions import ResourceNotFoundError, IllegalStateError


class RestoreLibraryUseCase(IRestoreLibraryUseCase):
    """
    Use Case: Restore a soft-deleted Library

    Workflow:
    1. Load Library by ID from repository
    2. Verify library exists (404 if not)
    3. Verify library is deleted (400 if not deleted)
    4. Call Library.restore() to emit LibraryRestored event
    5. Publish events to EventBus
    6. Persist updated library to repository
    7. Return response

    Error Handling:
    - ResourceNotFoundError: Library not found in database
    - IllegalStateError: Library is not deleted (soft_deleted_at is null)
    """

    def __init__(
        self,
        library_repository: ILibraryRepository,
        event_bus: EventBus,
    ):
        """
        Initialize RestoreLibraryUseCase with dependencies

        Args:
            library_repository: Port for Library persistence
            event_bus: Port for event publishing
        """
        self.library_repository = library_repository
        self.event_bus = event_bus

    async def execute(
        self, request: RestoreLibraryRequest
    ) -> RestoreLibraryResponse:
        """
        Execute the RestoreLibrary use case

        Args:
            request: RestoreLibraryRequest containing library_id

        Returns:
            RestoreLibraryResponse with restoration confirmation

        Raises:
            ResourceNotFoundError: If library not found
            IllegalStateError: If library is not deleted
        """
        # Step 1: Load library from repository
        library = await self.library_repository.get_by_id(request.library_id)
        if library is None:
            raise ResourceNotFoundError(
                f"Library {request.library_id} not found",
                resource_type="Library",
                resource_id=str(request.library_id),
            )

        # Step 2: Verify library is deleted
        if not library.is_deleted():
            raise IllegalStateError(
                f"Cannot restore Library {request.library_id}: not deleted "
                f"(soft_deleted_at is None)"
            )

        # Step 3: Call domain method to restore (emits LibraryRestored event)
        library.restore()

        # Step 4: Publish events to EventBus
        for event in library.events:
            await self.event_bus.publish(event)

        # Step 5: Persist updated library to repository
        await self.library_repository.save(library)

        # Step 6: Return response
        now = datetime.now(timezone.utc)
        return RestoreLibraryResponse(
            library_id=library.id,
            restored_at=now,
            message=f"Library '{library.get_name_value()}' has been restored from Basement",
        )
