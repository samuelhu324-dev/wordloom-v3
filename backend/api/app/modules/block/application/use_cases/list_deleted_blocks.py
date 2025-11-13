"""ListDeletedBlocks UseCase - List soft-deleted blocks

This use case handles:
- Querying repository for deleted blocks
- Supporting pagination
- Returning list of Block domain objects
"""

from typing import List, Tuple
from uuid import UUID

from ...domain import Block
from ...application.ports.output import BlockRepository
from ...exceptions import BlockOperationError


class ListDeletedBlocksUseCase:
    """List soft-deleted blocks"""

    def __init__(self, repository: BlockRepository):
        self.repository = repository

    async def execute(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Block], int]:
        """
        List deleted blocks with pagination

        Args:
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            Tuple of (list of Block objects, total count)

        Raises:
            BlockOperationError: On query error
        """
        try:
            return await self.repository.get_deleted_blocks(skip, limit)
        except Exception as e:
            raise BlockOperationError(f"Failed to list deleted blocks: {str(e)}")
