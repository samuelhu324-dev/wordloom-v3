"""DeleteBlock UseCase - Soft delete a block

This use case handles:
- Validating block exists
- Setting soft_deleted_at timestamp
- Preserving block data
- Persisting via repository
"""

from uuid import UUID

from ...application.ports.output import BlockRepository
from ...exceptions import (
    BlockNotFoundError,
    BlockOperationError,
)


class DeleteBlockUseCase:
    """Soft delete a block"""

    def __init__(self, repository: BlockRepository):
        self.repository = repository

    async def execute(self, block_id: UUID) -> None:
        """
        Soft delete block

        Args:
            block_id: Block ID to delete

        Raises:
            BlockNotFoundError: If block not found
            BlockOperationError: On persistence error
        """
        block = await self.repository.get_by_id(block_id)
        if not block:
            raise BlockNotFoundError(block_id)

        try:
            await self.repository.delete(block_id)
        except Exception as e:
            raise BlockOperationError(f"Failed to delete block: {str(e)}")
