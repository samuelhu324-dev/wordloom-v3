"""GetBlock UseCase - Get a block by ID

This use case handles:
- Validating block exists
- Returning Block domain object
"""

from uuid import UUID

from ...domain import Block
from ...application.ports.output import BlockRepository
from ...exceptions import (
    BlockNotFoundError,
    BlockOperationError,
)


class GetBlockUseCase:
    """Get a block by ID"""

    def __init__(self, repository: BlockRepository):
        self.repository = repository

    async def execute(self, block_id: UUID) -> Block:
        """
        Get block

        Args:
            block_id: Block ID

        Returns:
            Block domain object

        Raises:
            BlockNotFoundError: If block not found
            BlockOperationError: On query error
        """
        try:
            block = await self.repository.get_by_id(block_id)
            if not block:
                raise BlockNotFoundError(block_id)
            return block
        except Exception as e:
            if isinstance(e, BlockNotFoundError):
                raise
            raise BlockOperationError(f"Failed to get block: {str(e)}")
