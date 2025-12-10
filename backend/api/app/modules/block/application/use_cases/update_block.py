"""UpdateBlock UseCase - Update block content

This use case handles:
- Validating block exists
- Updating content
- Updating metadata
- Persisting via repository
"""

from typing import Optional, Dict, Any
from uuid import UUID

from ...domain import Block
from ...application.ports.output import BlockRepository
from ...exceptions import (
    BlockNotFoundError,
    BlockOperationError,
)


class UpdateBlockUseCase:
    """Update block content"""

    def __init__(self, repository: BlockRepository):
        self.repository = repository

    async def execute(
        self,
        block_id: UUID,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Block:
        """
        Update block

        Args:
            block_id: Block ID
            content: New content (optional)
            metadata: New metadata (optional)

        Returns:
            Updated Block domain object

        Raises:
            BlockNotFoundError: If block not found
            BlockOperationError: On persistence error
        """
        block = await self.repository.get_by_id(block_id)
        if not block:
            raise BlockNotFoundError(block_id)

        try:
            if content is not None:
                block.update_content(content)

            if metadata is not None:
                block.update_metadata(metadata)

            updated_block = await self.repository.save(block)
            return updated_block

        except Exception as e:
            if isinstance(e, BlockNotFoundError):
                raise
            raise BlockOperationError(f"Failed to update block: {str(e)}")
