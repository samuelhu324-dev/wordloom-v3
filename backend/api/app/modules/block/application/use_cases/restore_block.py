"""RestoreBlock UseCase - Restore a soft-deleted block

This use case handles:
- Validating block exists in Paperballs (soft-deleted)
- Retrieving Paperballs recovery context (deleted_prev_id, deleted_next_id, deleted_section_path)
- Calling 3-level recovery algorithm via Repository
- Publishing BlockRestored domain event
- Persisting restoration
"""

import logging

from ...application.ports.output import BlockRepository
from api.app.modules.book.application.ports.output import BookRepository
from api.app.modules.library.application.ports.output import ILibraryRepository
from ..ports.input import RestoreBlockRequest
from ...exceptions import (
    BlockNotFoundError,
    BlockOperationError,
    BlockForbiddenError,
    DomainException,
)

logger = logging.getLogger(__name__)


class RestoreBlockUseCase:
    """Restore a soft-deleted block using 3-level Paperballs recovery"""

    def __init__(
        self,
        repository: BlockRepository,
        *,
        book_repository: BookRepository,
        library_repository: ILibraryRepository,
    ):
        self.repository = repository
        self.book_repository = book_repository
        self.library_repository = library_repository

    async def _assert_book_owner(self, *, book_id, request: RestoreBlockRequest) -> None:
        if not getattr(request, "enforce_owner_check", True):
            return
        actor_user_id = getattr(request, "actor_user_id", None)
        if actor_user_id is None:
            return
        book = await self.book_repository.get_by_id(book_id)
        if not book:
            raise BlockOperationError(f"Book not found: {book_id}")
        library = await self.library_repository.get_by_id(book.library_id)
        if not library:
            raise BlockOperationError(f"Library not found: {book.library_id}")
        if library.user_id != actor_user_id:
            raise BlockForbiddenError(
                "Forbidden: block does not belong to actor",
                actor_user_id=str(actor_user_id),
                library_id=str(book.library_id),
                book_id=str(book_id),
                block_id=str(request.block_id),
            )

    async def execute(self, request: RestoreBlockRequest):
        """
        Restore block from Paperballs using 3-level recovery strategy

        Enhanced (Nov 14, 2025) to implement:
        - Level 1: Restore after previous sibling (most accurate)
        - Level 2: Restore before next sibling (second choice)
        - Level 3: Restore at section end (fallback)
        - Level 4: Restore at book end (ultimate fallback)

        Args:
            block_id: Block ID to restore
            book_id: Parent book ID

        Returns:
            Restored Block domain object with new position

        Raises:
            BlockNotFoundError: If block not found or not deleted
            BlockOperationError: On persistence error
        """
        block_id = request.block_id
        try:
            logger.info(f"Starting restoration for block {block_id}")

            block = await self.repository.get_any_by_id(block_id)
            if not block:
                raise BlockNotFoundError(str(block_id))

            if getattr(block, "soft_deleted_at", None) is None:
                raise BlockNotFoundError(f"Block {block_id} is not in Paperballs")

            await self._assert_book_owner(book_id=block.book_id, request=request)

            deleted_prev_id = getattr(block, "deleted_prev_id", None)
            deleted_next_id = getattr(block, "deleted_next_id", None)
            deleted_section_path = getattr(block, "deleted_section_path", None)

            restored_block = await self.repository.restore_from_paperballs(
                block_id=block_id,
                book_id=block.book_id,
                deleted_prev_id=deleted_prev_id,
                deleted_next_id=deleted_next_id,
                deleted_section_path=deleted_section_path,
            )

            logger.info(f"Block {block_id} successfully restored")
            return restored_block

        except Exception as e:
            if isinstance(e, DomainException):
                raise
            logger.error(f"Failed to restore block {block_id}: {str(e)}")
            raise BlockOperationError(f"Failed to restore block: {str(e)}")
