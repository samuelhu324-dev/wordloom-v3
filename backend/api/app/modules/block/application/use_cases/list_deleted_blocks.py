"""ListDeletedBlocks UseCase - List soft-deleted blocks in Paperballs

This use case handles:
- Querying repository for deleted blocks
- Including Paperballs recovery metadata (deleted_prev_id, deleted_next_id, deleted_section_path)
- Generating recovery hints for UI
- Supporting pagination
- Returning list of Block domain objects
"""

from typing import List
import logging

from ...domain import Block
from ...application.ports.output import BlockRepository
from api.app.modules.book.application.ports.output import BookRepository
from api.app.modules.library.application.ports.output import ILibraryRepository
from ..ports.input import ListDeletedBlocksRequest, BlockListResponse, BlockResponse
from ...exceptions import DomainException, BlockOperationError, BlockForbiddenError

logger = logging.getLogger(__name__)


class ListDeletedBlocksUseCase:
    """List soft-deleted blocks with recovery metadata"""

    def __init__(
        self,
        repository: BlockRepository,
        *,
        book_repository: BookRepository,
        library_repository: ILibraryRepository,
    ):
        self.repository = repository
        self.book_repository = book_repository
        self.library_repository = library_repository

    async def _assert_book_owner(self, request: ListDeletedBlocksRequest) -> None:
        if not getattr(request, "enforce_owner_check", True):
            return
        actor_user_id = getattr(request, "actor_user_id", None)
        if actor_user_id is None:
            return
        book = await self.book_repository.get_by_id(request.book_id)
        if not book:
            raise BlockOperationError(f"Book not found: {request.book_id}")
        library = await self.library_repository.get_by_id(book.library_id)
        if not library:
            raise BlockOperationError(f"Library not found: {book.library_id}")
        if library.user_id != actor_user_id:
            raise BlockForbiddenError(
                "Forbidden: book does not belong to actor",
                actor_user_id=str(actor_user_id),
                library_id=str(book.library_id),
                book_id=str(request.book_id),
            )

    async def execute(self, request: ListDeletedBlocksRequest) -> BlockListResponse:
        """
        List deleted blocks with Paperballs recovery information

        Enhanced (Nov 14, 2025) to include:
        - deleted_prev_id (Level 1 recovery reference)
        - deleted_next_id (Level 2 recovery reference)
        - deleted_section_path (Level 3 recovery reference)
        - recovery_hint (human-readable recovery strategy)

        Args:
            book_id: Filter by book ID
            skip: Pagination offset
            limit: Pagination limit (max 100)

        Returns:
            Tuple of (list of Block objects with recovery metadata, total count)

        Raises:
            BlockOperationError: On query error
        """
        try:
            await self._assert_book_owner(request)

            logger.info(
                f"Listing deleted blocks for book {request.book_id} (skip={request.skip}, limit={request.limit})"
            )

            all_deleted = await self.repository.get_deleted_blocks(request.book_id)
            total = len(all_deleted)

            start = max(0, request.skip)
            limit = max(1, request.limit)
            slice_ = all_deleted[start : start + limit]

            # Enrich blocks with recovery hints
            for block in slice_:
                block.recovery_hint = self._calculate_recovery_hint(block)

            items = [BlockResponse.from_domain(block) for block in slice_]
            return BlockListResponse(items=items, total=total)

        except Exception as e:
            if isinstance(e, DomainException):
                raise
            logger.error(f"Failed to list deleted blocks: {str(e)}")
            raise BlockOperationError(f"Failed to list deleted blocks: {str(e)}")

    def _calculate_recovery_hint(self, block: Block) -> str:
        """
        Generate human-readable recovery hint based on Paperballs context

        Args:
            block: Block with Paperballs fields

        Returns:
            str - Recovery strategy description
        """
        deleted_prev_id = getattr(block, 'deleted_prev_id', None)
        deleted_next_id = getattr(block, 'deleted_next_id', None)
        deleted_section_path = getattr(block, 'deleted_section_path', None)

        if deleted_prev_id:
            return "Level 1: 在前驱节点之后恢复"
        elif deleted_next_id:
            return "Level 2: 在后继节点之前恢复"
        elif deleted_section_path:
            return f"Level 3: 在 {deleted_section_path} 章节末尾恢复"
        else:
            return "Level 4: 在书籍末尾恢复"
