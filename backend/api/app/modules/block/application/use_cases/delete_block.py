"""DeleteBlock UseCase - Soft delete a block

This use case handles:
- Validating block exists
- Capturing Paperballs recovery context (deleted_prev_id, deleted_next_id, deleted_section_path)
- Setting soft_deleted_at timestamp
- Preserving block data
- Persisting via repository
"""

from uuid import UUID
import logging

from ...domain import Block
from ...application.ports.output import BlockRepository
from ...exceptions import (
    BlockNotFoundError,
    BlockOperationError,
)

logger = logging.getLogger(__name__)


class DeleteBlockUseCase:
    """Soft delete a block with Paperballs recovery context capture"""

    def __init__(self, repository: BlockRepository):
        self.repository = repository

    async def execute(self, block_id: UUID, book_id: UUID) -> Block:
        """
        Soft delete block and capture Paperballs recovery context

        Enhanced (Nov 14, 2025) to support 3-level recovery strategy:
        - Captures deleted_prev_id (Level 1 recovery)
        - Captures deleted_next_id (Level 2 recovery)
        - Captures deleted_section_path (Level 3 recovery)

        Args:
            block_id: Block ID to delete
            book_id: Parent book ID

        Returns:
            Deleted Block domain object with Paperballs context

        Raises:
            BlockNotFoundError: If block not found
            BlockOperationError: On persistence error
        """
        block = await self.repository.get_by_id(block_id)
        if not block:
            logger.error(f"Block {block_id} not found for deletion")
            raise BlockNotFoundError(block_id)

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

        except BlockNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete block {block_id}: {str(e)}")
            raise BlockOperationError(f"Failed to delete block: {str(e)}")
