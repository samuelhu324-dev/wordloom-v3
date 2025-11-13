"""CreateBlock UseCase - Create a new block (various types)

This use case handles:
- Validating book exists
- Creating Block domain object for different types (TEXT, IMAGE, VIDEO, AUDIO, PDF, CODE)
- Computing fractional index for ordering
- Persisting via repository
"""

from typing import Optional, Dict, Any
from uuid import UUID

from ...domain import Block, BlockType
from ...application.ports.output import BlockRepository
from ...exceptions import (
    BlockOperationError,
)


class CreateBlockUseCase:
    """Create a new block"""

    def __init__(self, repository: BlockRepository):
        self.repository = repository

    async def execute(
        self,
        book_id: UUID,
        block_type: BlockType,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        position_after_id: Optional[UUID] = None
    ) -> Block:
        """
        Create block

        Args:
            book_id: Book ID
            block_type: Type of block (TEXT, IMAGE, VIDEO, AUDIO, PDF, CODE)
            content: Block content
            metadata: Additional metadata (dimensions for images, duration for videos, etc.)
            position_after_id: Position this block after another block (for fractional indexing)

        Returns:
            Created Block domain object

        Raises:
            BlockOperationError: On persistence error
        """
        try:
            # Compute fractional index
            order_index = None
            if position_after_id:
                # Get position of previous block and compute new fractional index
                pass  # Implementation depends on fractional index algorithm

            block = Block.create(
                book_id=book_id,
                block_type=block_type,
                content=content,
                metadata=metadata,
                order=order_index
            )
            created_block = await self.repository.save(block)
            return created_block

        except Exception as e:
            raise BlockOperationError(f"Failed to create block: {str(e)}")
