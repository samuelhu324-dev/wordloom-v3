"""RestoreBlock UseCase - Restore a soft-deleted block

This use case handles:
- Validating block exists
- Clearing soft_deleted_at timestamp
- Making block active again
- Persisting via repository
"""

from uuid import UUID

from ...domain import Block
from ...application.ports.output import BlockRepository
from ...exceptions import (
    BlockNotFoundError,
    BlockOperationError,
)


class RestoreBlockUseCase:
    """Restore a soft-deleted block"""

    def __init__(self, repository: BlockRepository):
        self.repository = repository

    async def execute(self, block_id: UUID) -> Block:
        """
        Restore block

        Args:
            block_id: Block ID to restore

        Returns:
            Restored Block domain object

        Raises:
            BlockNotFoundError: If block not found
            BlockOperationError: On persistence error
        """
        block = await self.repository.get_by_id(block_id)
        if not block:
            raise BlockNotFoundError(block_id)

        try:
            block.restore()
            restored_block = await self.repository.save(block)
            return restored_block
        except Exception as e:
            raise BlockOperationError(f"Failed to restore block: {str(e)}")
