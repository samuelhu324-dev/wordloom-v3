"""ListDeletedBlocks UseCase - List soft-deleted blocks in Paperballs

This use case handles:
- Querying repository for deleted blocks
- Including Paperballs recovery metadata (deleted_prev_id, deleted_next_id, deleted_section_path)
- Generating recovery hints for UI
- Supporting pagination
- Returning list of Block domain objects
"""

from typing import List, Tuple
from uuid import UUID
import logging

from ...domain import Block
from ...application.ports.output import BlockRepository
from ...exceptions import BlockOperationError

logger = logging.getLogger(__name__)


class ListDeletedBlocksUseCase:
    """List soft-deleted blocks with recovery metadata"""

    def __init__(self, repository: BlockRepository):
        self.repository = repository

    async def execute(
        self,
        book_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Block], int]:
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
            logger.info(f"Listing deleted blocks for book {book_id} (skip={skip}, limit={limit})")

            blocks, total = await self.repository.get_deleted_blocks(book_id, skip, limit)

            logger.debug(f"Retrieved {len(blocks)} deleted blocks (total: {total})")

            # === NEW: Enrich blocks with recovery hints ===
            enriched_blocks = []
            for block in blocks:
                # Add recovery hint based on Paperballs context
                recovery_hint = self._calculate_recovery_hint(block)
                block.recovery_hint = recovery_hint
                enriched_blocks.append(block)
                logger.debug(f"Block {block.id}: {recovery_hint}")

            return (enriched_blocks, total)

        except Exception as e:
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
