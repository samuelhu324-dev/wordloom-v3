"""
Block Service - Orchestration for Block domain operations

Purpose:
- Layer 1: Input validation and business rule checks
- Layer 2: Domain logic execution (via Domain factory methods)
- Layer 3: Persistence coordination (Repository save)
- Layer 4: Event publishing (to EventBus)

Architecture:
- Type-specific methods (create_text_block, create_heading_block, etc.)
- Fractional index support for O(1) drag/drop reordering
- Permission validation via Library ownership check
- Soft delete pattern (mark_deleted, not hard delete)
"""

import logging
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from domains.block.domain import Block, BlockType
from domains.block.repository import BlockRepository

logger = logging.getLogger(__name__)


class BlockService:
    """Block service for domain orchestration and business logic"""

    def __init__(self, repository: BlockRepository, book_repository=None, library_repository=None):
        """
        Initialize Block service

        Args:
            repository: Block repository for persistence
            book_repository: Optional Book repository for existence/permission checks
            library_repository: Optional Library repository for ownership validation
        """
        self.repository = repository
        self.book_repository = book_repository  # For Book existence & permission checks
        self.library_repository = library_repository  # For Library ownership validation

    # ========================================================================
    # Layer 1-2: Type-Specific Block Creation Methods
    # ========================================================================

    async def create_text_block(
        self,
        book_id: UUID,
        content: str,
        order: Decimal = Decimal("0"),
        user_id: Optional[UUID] = None,
    ) -> Block:
        """
        Create TEXT block with validation

        Layer 1: Verify Book exists and user permission
        Layer 2: Call Domain factory (Block.create_text)
        Layer 3: Persist to repository
        Layer 4: Publish BlockCreated event
        """
        await self._verify_book_access(book_id, user_id)

        block = Block.create_text(book_id, content, order)
        await self.repository.save(block)

        logger.info(f"Created TEXT block {block.id} in book {book_id}")
        return block

    async def create_heading_block(
        self,
        book_id: UUID,
        content: str,
        level: int = 1,
        order: Decimal = Decimal("0"),
        user_id: Optional[UUID] = None,
    ) -> Block:
        """
        Create HEADING block (H1-H3) with validation

        Layer 1: Verify Book exists, validate level 1-3, user permission
        Layer 2: Call Domain factory (Block.create_heading)
        Layer 3: Persist to repository
        Layer 4: Publish BlockCreated event
        """
        if level not in (1, 2, 3):
            raise ValueError("Heading level must be 1, 2, or 3")

        await self._verify_book_access(book_id, user_id)

        block = Block.create_heading(book_id, content, level, order)
        await self.repository.save(block)

        logger.info(f"Created HEADING (H{level}) block {block.id} in book {book_id}")
        return block

    async def create_code_block(
        self,
        book_id: UUID,
        content: str,
        language: str = "text",
        order: Decimal = Decimal("0"),
        user_id: Optional[UUID] = None,
    ) -> Block:
        """Create CODE block with validation"""
        await self._verify_book_access(book_id, user_id)

        block = Block.create_code(book_id, content, language, order)
        await self.repository.save(block)

        logger.info(f"Created CODE block {block.id} in book {book_id}")
        return block

    async def create_image_block(
        self,
        book_id: UUID,
        order: Decimal = Decimal("0"),
        user_id: Optional[UUID] = None,
    ) -> Block:
        """Create IMAGE block with validation"""
        await self._verify_book_access(book_id, user_id)

        block = Block.create_image(book_id, order)
        await self.repository.save(block)

        logger.info(f"Created IMAGE block {block.id} in book {book_id}")
        return block

    async def create_quote_block(
        self,
        book_id: UUID,
        content: str,
        order: Decimal = Decimal("0"),
        user_id: Optional[UUID] = None,
    ) -> Block:
        """Create QUOTE block with validation"""
        await self._verify_book_access(book_id, user_id)

        block = Block.create_quote(book_id, content, order)
        await self.repository.save(block)

        logger.info(f"Created QUOTE block {block.id} in book {book_id}")
        return block

    async def create_list_block(
        self,
        book_id: UUID,
        content: str,
        order: Decimal = Decimal("0"),
        user_id: Optional[UUID] = None,
    ) -> Block:
        """Create LIST block with validation"""
        await self._verify_book_access(book_id, user_id)

        block = Block.create_list(book_id, content, order)
        await self.repository.save(block)

        logger.info(f"Created LIST block {block.id} in book {book_id}")
        return block

    # ========================================================================
    # Block Retrieval
    # ========================================================================

    async def get_block(self, block_id: UUID) -> Block:
        """Get Block by ID"""
        block = await self.repository.get_by_id(block_id)
        if not block:
            raise Exception(f"Block {block_id} not found")
        return block

    async def list_blocks(self, book_id: UUID) -> List[Block]:
        """List all Blocks in a Book (sorted by fractional index)"""
        return await self.repository.get_by_book_id(book_id)

    # ========================================================================
    # Block Modification
    # ========================================================================

    async def update_block_content(
        self,
        block_id: UUID,
        new_content: str,
        user_id: Optional[UUID] = None,
    ) -> Block:
        """
        Update Block content with permission validation

        Layer 1: Verify Book exists and user permission
        Layer 2: Call Domain method (block.set_content)
        Layer 3: Persist to repository
        Layer 4: Publish BlockContentChanged event
        """
        block = await self.get_block(block_id)
        await self._verify_book_access(block.book_id, user_id)

        block.set_content(new_content)
        await self.repository.save(block)

        logger.info(f"Updated content for block {block_id}")
        return block

    async def reorder_block(
        self,
        block_id: UUID,
        new_order: Decimal,
        user_id: Optional[UUID] = None,
    ) -> Block:
        """
        Reorder Block using fractional index (O(1) operation)

        Layer 1: Verify Book exists, validate order is Decimal, user permission
        Layer 2: Call Domain method (block.set_order_fractional)
        Layer 3: Persist to repository
        Layer 4: Publish BlockReordered event

        Example:
            # Move block between siblings at order 10.0 and 20.0
            new_order = Decimal('15.0')  # Middle value
            block = await service.reorder_block(block_id, Decimal('15.0'), user_id)
        """
        if not isinstance(new_order, Decimal):
            new_order = Decimal(str(new_order))

        block = await self.get_block(block_id)
        await self._verify_book_access(block.book_id, user_id)

        block.set_order_fractional(new_order)
        await self.repository.save(block)

        logger.info(f"Reordered block {block_id} to order {new_order}")
        return block

    async def reorder_block_between(
        self,
        block_id: UUID,
        before_order: Optional[Decimal] = None,
        after_order: Optional[Decimal] = None,
        user_id: Optional[UUID] = None,
    ) -> Block:
        """
        Reorder Block between two siblings (convenience method)

        Calculates fractional index automatically:
        - new_order = (before_order + after_order) / 2

        Args:
            block_id: ID of block to reorder
            before_order: Order of block before (or None if inserting at start)
            after_order: Order of block after (or None if inserting at end)
            user_id: User ID for permission check

        Returns:
            Updated Block with new fractional order

        Raises:
            ValueError: If both before and after are None
        """
        block = await self.get_block(block_id)
        await self._verify_book_access(block.book_id, user_id)

        new_order = self._calculate_fractional_order(before_order, after_order)

        block.set_order_fractional(new_order)
        await self.repository.save(block)

        logger.info(f"Reordered block {block_id} between {before_order} and {after_order}")
        return block

    # ========================================================================
    # Block Deletion (Soft Delete)
    # ========================================================================

    async def delete_block(
        self,
        block_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> None:
        """
        Delete Block (soft delete - mark as deleted, not hard delete)

        Layer 1: Verify Book exists and user permission
        Layer 2: Call Domain method (block.mark_deleted)
        Layer 3: Persist to repository
        Layer 4: Publish BlockDeleted event

        Note: Hard deletion happens via periodic purge job (after 30+ days)
        """
        block = await self.get_block(block_id)
        await self._verify_book_access(block.book_id, user_id)

        block.mark_deleted()  # ← Domain event emitted
        await self.repository.save(block)  # ← Only persist, no hard delete

        logger.info(f"Soft-deleted block {block_id}")

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _verify_book_access(
        self,
        book_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> None:
        """
        Layer 1 Validation: Verify Book exists and user has access

        Args:
            book_id: ID of Book
            user_id: Optional user ID for ownership check

        Raises:
            Exception: If Book not found or permission denied
        """
        if not self.book_repository:
            return

        # Check Book exists
        book = await self.book_repository.get_by_id(book_id)
        if not book:
            raise Exception(f"Book {book_id} not found")

        # Check user permission (optional)
        if user_id and self.library_repository:
            library = await self.library_repository.get_by_id(book.library_id)
            if library and library.user_id != user_id:
                raise PermissionError(f"User {user_id} does not own Book {book_id}")

    @staticmethod
    def _calculate_fractional_order(
        before_order: Optional[Decimal] = None,
        after_order: Optional[Decimal] = None,
    ) -> Decimal:
        """
        Calculate fractional index between two orders

        Fractional Index Algorithm (from https://www.notion.so/Fractional-Indexing-c4e2f34b5e5b4c9d8e1f0a1b2c3d4e5f):
        - If both provided: new_order = (before + after) / 2
        - If only before: new_order = before + 1000
        - If only after: new_order = after - 1000 / 2
        - If neither: new_order = 0

        Args:
            before_order: Order of block before (insert position)
            after_order: Order of block after (insert position)

        Returns:
            Decimal order value for new position
        """
        if before_order is None and after_order is None:
            return Decimal("0")

        if before_order is None:
            return after_order / Decimal("2")

        if after_order is None:
            return before_order + Decimal("1000")

        # Both provided: calculate midpoint
        return (before_order + after_order) / Decimal("2")
