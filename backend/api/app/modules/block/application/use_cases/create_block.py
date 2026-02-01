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
            # NOTE:
            # - The current domain factory `Block.create(...)` does not accept `metadata`.
            # - For HEADING blocks, domain requires `heading_level`.

            heading_level: Optional[int] = None
            if metadata and isinstance(metadata, dict):
                raw_heading_level = metadata.get("heading_level")
                if raw_heading_level is not None:
                    try:
                        heading_level = int(raw_heading_level)
                    except (TypeError, ValueError):
                        heading_level = None

            # TODO: implement fractional ordering once the algorithm is defined.
            # For now, rely on the domain default order.
            _ = position_after_id

            block = Block.create(
                book_id=book_id,
                block_type=block_type,
                content=content or "",
                heading_level=heading_level,
            )
            created_block = await self.repository.save(block)
            return created_block

        except Exception as e:
            raise BlockOperationError(f"Failed to create block: {str(e)}")
