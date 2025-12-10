"""
Block Repository Output Port

Abstract interface for Block persistence adapter.
Implementation: infra/storage/block_repository_impl.py
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID
from decimal import Decimal

from api.app.modules.block.domain import Block


class BlockRepository(ABC):
    """Abstract repository for Block persistence"""

    @abstractmethod
    async def save(self, block: Block) -> Block:
        """Persist a block"""
        pass

    @abstractmethod
    async def get_by_id(self, block_id: UUID) -> Optional[Block]:
        """Fetch a block by ID"""
        pass

    @abstractmethod
    async def delete(self, block_id: UUID) -> None:
        """Delete a block"""
        pass

    @abstractmethod
    async def list_by_book(self, book_id: UUID) -> List[Block]:
        """Get all blocks in a book"""
        pass

    @abstractmethod
    async def list_paginated(
        self,
        book_id: UUID,
        page: int = 1,
        page_size: int = 20,
        include_deleted: bool = False,
    ) -> Tuple[List[Block], int]:
        """Get paginated blocks for a book with optional soft-delete filtering"""
        pass

    @abstractmethod
    async def count_active_blocks(self, book_id: UUID) -> Tuple[int, int]:
        """Return (block_count, distinct_block_type_count) for active blocks."""
        pass

    # ========== NEW: Paperballs Recovery Interface (Doc 8 Integration) ==========

    @abstractmethod
    async def get_prev_sibling(self, block_id: UUID, book_id: UUID) -> Optional[Block]:
        """
        Get previous sibling block (same section, smaller sort key)

        Purpose: Capture deleted_prev_id during deletion for Level 1 recovery

        Returns: Optional[Block] - Previous sibling or None if not found
        """
        pass

    @abstractmethod
    async def get_next_sibling(self, block_id: UUID, book_id: UUID) -> Optional[Block]:
        """
        Get next sibling block (same section, larger sort key)

        Purpose: Capture deleted_next_id during deletion for Level 2 recovery

        Returns: Optional[Block] - Next sibling or None if not found
        """
        pass

    @abstractmethod
    def new_key_between(
        self,
        prev_sort_key: Optional[Decimal],
        next_sort_key: Optional[Decimal]
    ) -> Decimal:
        """
        Calculate Fractional Index between two sort keys

        Purpose: Compute recovery position for Paperballs restoration

        Algorithm:
            - Both exist: (prev + next) / 2
            - Only prev: prev + 1
            - Only next: next / 2
            - Neither: 1 (default)

        Returns: Decimal - New sort key value (DECIMAL(19,10) precision)
        """
        pass

    @abstractmethod
    async def restore_from_paperballs(
        self,
        block_id: UUID,
        book_id: UUID,
        deleted_prev_id: Optional[UUID],
        deleted_next_id: Optional[UUID],
        deleted_section_path: Optional[str]
    ) -> Block:
        """
        3-Level Recovery Strategy: Restore block from Paperballs

        Implements full recovery algorithm:
            Level 1: After previous sibling (most accurate)
            Level 2: Before next sibling (second choice)
            Level 3: At section end (fallback)
            Level 4: At book end (ultimate fallback)

        Args:
            block_id: ID of block to restore
            book_id: ID of parent book
            deleted_prev_id: Previous sibling ID from deletion context
            deleted_next_id: Next sibling ID from deletion context
            deleted_section_path: Section path from deletion context

        Returns: Block - Restored domain object with new position

        Raises: Exception if restoration fails
        """
        pass
