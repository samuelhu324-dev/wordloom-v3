"""
DeleteLibrary UseCase

Purpose:
- Delete/soft-delete a Library
- Emit LibraryDeleted event (triggers cascade delete)
- Handle not found cases

Cross-Reference:
- HEXAGONAL_RULES.yaml: step_5_usecase_splitting (Line ~600-650)
- DDD_RULES.yaml: library.soft_delete_strategy
"""

from uuid import UUID
import logging

from api.app.modules.library.exceptions import (
    LibraryNotFoundError,
    LibraryAlreadyDeletedError,
    LibraryForbiddenError,
)
from api.app.modules.library.application.ports.input import (
    DeleteLibraryRequest,
    DeleteLibraryResponse,
    IDeleteLibraryUseCase,
)
from api.app.modules.library.application.ports.output import ILibraryRepository

logger = logging.getLogger(__name__)


class DeleteLibraryUseCase(IDeleteLibraryUseCase):
    """
    UseCase: Delete a Library (soft delete)

    Business Flow:
    1. Verify library exists
    2. Verify not already deleted
    3. Mark library as deleted (Domain.mark_deleted())
    4. Emit LibraryDeleted event (triggers cascade)
    5. Persist soft_deleted_at timestamp

    Event Handlers will cascade:
    - Delete Bookshelves (including Books and Blocks)
    - Delete associated Media
    - Delete associated Tags
    - Cleanup Chronicle sessions

    Failure Cases:
    - Library not found (404)
    - Already deleted (409)
    """

    def __init__(
        self,
        repository: ILibraryRepository,
        event_bus,  # IEventBus
    ):
        """Initialize with Repository and EventBus dependencies"""
        self.repository = repository
        self.event_bus = event_bus

    async def execute(self, request: DeleteLibraryRequest) -> None:
        """
        Execute DeleteLibrary business operation

        Args:
            request: DeleteLibraryRequest with library_id

        Raises:
            LibraryNotFoundError: If library not found
            LibraryAlreadyDeletedError: If already deleted
        """
        library_id = request.library_id
        logger.info(f"DeleteLibrary starting: {library_id}")

        # ================================================================
        # Step 1: Retrieve library
        # ================================================================
        library = await self.repository.get_by_id(library_id)
        if not library:
            logger.warning(f"Library not found: {library_id}")
            raise LibraryNotFoundError(f"Library {library_id} not found")

        # Authorization (skeleton): allow router to pass actor_user_id for ownership checks.
        if getattr(request, "enforce_owner_check", True) and getattr(request, "actor_user_id", None) is not None:
            if library.user_id != request.actor_user_id:
                raise LibraryForbiddenError(
                    library_id=str(library.id),
                    actor_user_id=str(request.actor_user_id),
                )

        # ================================================================
        # Step 2: Check if already deleted
        # ================================================================
        if library.is_deleted():
            logger.warning(f"Library already deleted: {library_id}")
            raise LibraryAlreadyDeletedError(f"Library {library_id} is already deleted")

        # ================================================================
        # Step 3: [DOMAIN] Mark as deleted
        # ================================================================
        try:
            library.mark_deleted()  # Emits LibraryDeleted event
            logger.debug(f"Library marked as deleted: {library_id}")
        except Exception as e:
            logger.error(f"Failed to mark library as deleted: {e}", exc_info=True)
            raise

        # ================================================================
        # Step 4: [REPOSITORY] Persist soft delete
        # ================================================================
        try:
            await self.repository.save(library)
            logger.info(f"Library soft delete persisted: {library_id}")
        except Exception as e:
            logger.error(f"Failed to persist soft delete: {e}", exc_info=True)
            raise

        # ================================================================
        # Step 5: [EVENTBUS] Publish LibraryDeleted event
        # ================================================================
        try:
            for event in library.events:
                await self.event_bus.publish(event)
                logger.debug(f"Event published: {event.__class__.__name__}")
            logger.info(f"DeleteLibrary events published: {library_id}")
        except Exception as e:
            logger.error(f"Failed to publish events: {e}", exc_info=True)
            raise

        logger.info(f"DeleteLibrary completed successfully: {library_id}")
