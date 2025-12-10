"""ListBlocks UseCase - List blocks in a book with pagination"""

from ...application.ports.input import (
    BlockListResponse,
    BlockResponse,
    ListBlocksRequest,
)
from ...application.ports.output import BlockRepository
from ...exceptions import BlockOperationError


class ListBlocksUseCase:
    """List blocks in a book"""

    def __init__(self, repository: BlockRepository):
        self.repository = repository

    async def execute(self, request: ListBlocksRequest) -> BlockListResponse:
        """List blocks with pagination and optional soft-delete filtering"""

        try:
            limit = max(1, request.limit)
            page = max(1, (request.skip // limit) + 1)
            blocks, total = await self.repository.list_paginated(
                book_id=request.book_id,
                page=page,
                page_size=limit,
                include_deleted=request.include_deleted,
            )
            items = [BlockResponse.from_domain(block) for block in blocks]
            return BlockListResponse(items=items, total=total)
        except Exception as e:
            raise BlockOperationError(f"Failed to list blocks: {str(e)}")
