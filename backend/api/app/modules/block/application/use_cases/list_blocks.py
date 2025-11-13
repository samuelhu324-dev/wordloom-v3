"""ListBlocks UseCase - List blocks in a book

This use case handles:
- Querying repository for active blocks (not soft-deleted)
- Ordering by fractional index
- Supporting pagination
- Returning list of Block domain objects
"""

from typing import List, Tuple
from uuid import UUID

from ...domain import Block
from ...application.ports.output import BlockRepository
from ...exceptions import BlockOperationError


class ListBlocksUseCase:
    """List blocks in a book"""

    def __init__(self, repository: BlockRepository):
        self.repository = repository

    async def execute(
        self,
        book_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Block], int]:
        """
        List blocks with pagination

        Args:
            book_id: Book ID
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            Tuple of (list of Block objects, total count)

        Raises:
            BlockOperationError: On query error
        """
        try:
            return await self.repository.get_by_book_id(book_id, skip, limit)
        except Exception as e:
            raise BlockOperationError(f"Failed to list blocks: {str(e)}")
