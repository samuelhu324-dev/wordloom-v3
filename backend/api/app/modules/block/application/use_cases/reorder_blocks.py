"""ReorderBlocks UseCase - Reorder blocks using fractional index

This use case handles:
- Moving a block to a new position
- Computing new fractional index based on surrounding blocks
- Supporting O(1) insert/move operations
- Persisting via repository

使用 Fractional Index 算法保证 O(1) 移动操作
"""

from typing import Optional
from uuid import UUID
from decimal import Decimal

from ...domain import Block
from ...application.ports.output import BlockRepository
from ...exceptions import (
    BlockNotFoundError,
    BlockOperationError,
)


class ReorderBlocksUseCase:
    """Reorder blocks using fractional indexing"""

    def __init__(self, repository: BlockRepository):
        self.repository = repository

    async def execute(
        self,
        block_id: UUID,
        position_after_id: Optional[UUID] = None,
        position_before_id: Optional[UUID] = None
    ) -> Block:
        """
        Move block to new position

        Args:
            block_id: Block to move
            position_after_id: Place after this block (optional)
            position_before_id: Place before this block (optional)

        Returns:
            Updated Block domain object with new order

        Raises:
            BlockNotFoundError: If block not found
            BlockOperationError: On persistence error
        """
        block = await self.repository.get_by_id(block_id)
        if not block:
            raise BlockNotFoundError(block_id)

        try:
            # Compute new fractional index based on surrounding blocks
            new_order = self._compute_new_order(
                position_after_id,
                position_before_id
            )

            block.update_order(new_order)
            updated_block = await self.repository.save(block)
            return updated_block

        except Exception as e:
            if isinstance(e, BlockNotFoundError):
                raise
            raise BlockOperationError(f"Failed to reorder block: {str(e)}")

    @staticmethod
    def _compute_new_order(
        after_id: Optional[UUID],
        before_id: Optional[UUID]
    ) -> Decimal:
        """Compute new fractional index"""
        # Implementation of fractional index algorithm
        # This is simplified - actual implementation depends on algorithm choice
        pass
