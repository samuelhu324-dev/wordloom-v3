"""DeleteBlock UseCase - Soft delete a block

This use case handles:
- Validating block exists
- Capturing Paperballs recovery context (deleted_prev_id, deleted_next_id, deleted_section_path)
- Setting soft_deleted_at timestamp
- Preserving block data
- Persisting via repository
"""

import logging

from ...domain import Block
from ...application.ports.output import BlockRepository
from ..ports.input import DeleteBlockRequest
from api.app.modules.book.application.ports.output import BookRepository
from api.app.modules.library.application.ports.output import ILibraryRepository
from ...exceptions import (
    BlockNotFoundError,
    BlockOperationError,
    BlockForbiddenError,
    DomainException,
)

logger = logging.getLogger(__name__)


class DeleteBlockUseCase:
    """Soft delete a block with Paperballs recovery context capture"""

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

    async def _assert_block_owner(self, *, block: Block, request: DeleteBlockRequest) -> None:
        if not getattr(request, "enforce_owner_check", True):
            return
        actor_user_id = getattr(request, "actor_user_id", None)
        if actor_user_id is None:
            return

        book = await self.book_repository.get_by_id(block.book_id)
        if not book:
            raise BlockOperationError(f"Book not found: {block.book_id}")
        library = await self.library_repository.get_by_id(book.library_id)
        if not library:
            raise BlockOperationError(f"Library not found: {book.library_id}")
        if library.user_id != actor_user_id:
            raise BlockForbiddenError(
                "Forbidden: block does not belong to actor",
                actor_user_id=str(actor_user_id),
                library_id=str(book.library_id),
                book_id=str(block.book_id),
                block_id=str(request.block_id),
            )

    async def execute(self, request: DeleteBlockRequest) -> Block:
        """
        Soft delete block and capture Paperballs recovery context

        Enhanced (Nov 14, 2025) to support 3-level recovery strategy:
        - Captures deleted_prev_id (Level 1 recovery)
        - Captures deleted_next_id (Level 2 recovery)
        - Captures deleted_section_path (Level 3 recovery)

                Args:
                        request: DeleteBlockRequest containing:
                            - block_id: Block ID to delete

        Returns:
            Deleted Block domain object with Paperballs context

        Raises:
            BlockNotFoundError: If block not found
            BlockOperationError: On persistence error
        """
        block_id = request.block_id
        block = await self.repository.get_by_id(block_id)
        if not block:
            logger.error(f"Block {block_id} not found for deletion")
            raise BlockNotFoundError(block_id)

        await self._assert_block_owner(block=block, request=request)

        # Resolve book_id from the block to avoid requiring callers to provide it.
        book_id = getattr(block, "book_id", None)
        if not book_id:
            logger.error(f"Block {block_id} has no book_id; cannot capture sibling context")
            raise BlockOperationError(
                block_id=str(block_id),
                operation="delete",
                reason="missing book_id",
            )

        try:
            # === NEW: Capture Paperballs recovery context ===
            logger.info(f"Deleting block {block_id} and capturing Paperballs context")

            # Get previous sibling for Level 1 recovery
            prev_sibling = await self.repository.get_prev_sibling(block_id, book_id)
            # Get next sibling for Level 2 recovery
            next_sibling = await self.repository.get_next_sibling(block_id, book_id)

            # Mark block as deleted with Paperballs context
            block.mark_deleted(
                prev_sibling_id=prev_sibling.id if prev_sibling else None,
                next_sibling_id=next_sibling.id if next_sibling else None,
                section_path=block.section_path if hasattr(block, 'section_path') else None
            )

            logger.debug(
                f"Block {block_id} marked for soft delete with context: "
                f"prev={prev_sibling.id if prev_sibling else None}, "
                f"next={next_sibling.id if next_sibling else None}"
            )

            # Persist deletion
            deleted_block = await self.repository.save(block)

            logger.info(f"Block {block_id} successfully soft-deleted with Paperballs context")
            return deleted_block

        except Exception as e:
            if isinstance(e, DomainException):
                raise
            logger.error(f"Failed to delete block {block_id}: {str(e)}")
            raise BlockOperationError(f"Failed to delete block: {str(e)}")
