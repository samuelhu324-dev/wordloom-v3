"""
Block Repository - Persistence layer for Block aggregate root

Purpose:
- Interface between Domain and Infrastructure (ORM)
- Handle ORM Model ↔ Domain Model conversion
- Provide business query methods
- Support soft delete filtering
- Implement exception translation

Architecture:
- Abstract interface (BlockRepository)
- Concrete implementation (BlockRepositoryImpl) using SQLAlchemy
- Support for fractional index ordering (Decimal)
- Soft delete filtering (WHERE soft_deleted_at IS NULL)
- Type-safe exception handling
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from api.app.modules.block.domain import Block, BlockContent, BlockType
from api.app.modules.block.models import BlockModel

logger = logging.getLogger(__name__)


class BlockRepository(ABC):
    """Abstract interface for Block persistence"""

    @abstractmethod
    async def save(self, block: Block) -> None:
        """Save Block (create or update)"""
        pass

    @abstractmethod
    async def get_by_id(self, block_id: UUID) -> Optional[Block]:
        """Get Block by ID (with soft-delete filtering)"""
        pass

    @abstractmethod
    async def get_by_book_id(self, book_id: UUID) -> List[Block]:
        """Get all Blocks in a Book, ordered by fractional index"""
        pass

    @abstractmethod
    async def list_paginated(
        self, book_id: UUID, page: int = 1, page_size: int = 20
    ) -> tuple[List[Block], int]:
        """
        Get paginated Blocks in a Book

        Args:
            book_id: Book UUID
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (blocks, total_count)
        """
        pass

    @abstractmethod
    async def get_deleted_blocks(self, book_id: UUID) -> List[Block]:
        """Get soft-deleted Blocks in a Book"""
        pass


class BlockRepositoryImpl(BlockRepository):
    """SQLAlchemy implementation of Block repository"""

    def __init__(self, session):
        self.session = session

    async def save(self, block: Block) -> None:
        """
        Save Block to database

        Handles both INSERT (new block) and UPDATE (existing block)
        Maps Domain Model → ORM Model with type-specific handling

        Note:
        - order field is Decimal (fractional index)
        - No title_text/title_level (now handled by BlockType + heading_level)
        """
        model = await self.session.get(BlockModel, block.id)

        if model is None:
            # INSERT new block
            model = BlockModel(
                id=block.id,
                book_id=block.book_id,
                type=block.type.value,
                content=block.content.value,
                order=block.order,
                heading_level=block.heading_level if block.type == BlockType.HEADING else None,
                created_at=block.created_at,
                updated_at=block.updated_at,
            )
            self.session.add(model)
            logger.debug(f"Inserting new block {block.id}")
        else:
            # UPDATE existing block
            model.type = block.type.value
            model.content = block.content.value
            model.order = block.order
            model.heading_level = block.heading_level if block.type == BlockType.HEADING else None
            model.updated_at = block.updated_at
            logger.debug(f"Updating block {block.id}")

    async def get_by_id(self, block_id: UUID) -> Optional[Block]:
        """
        Get Block by ID

        Filters: soft_deleted_at IS NULL (soft delete pattern)

        Returns:
            Domain Block or None if not found
        """
        from sqlalchemy import select

        stmt = (
            select(BlockModel)
            .where(BlockModel.id == block_id)
            .where(BlockModel.soft_deleted_at.is_(None))  # Soft delete filter
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            logger.debug(f"Block {block_id} not found or deleted")
            return None

        return self._to_domain(model)

    async def get_by_book_id(self, book_id: UUID) -> List[Block]:
        """
        Get all Blocks in a Book

        Ordering: By fractional index (order field)
        Filters: soft_deleted_at IS NULL (soft delete pattern)

        Returns:
            List of Blocks ordered by fractional index
        """
        from sqlalchemy import select

        stmt = (
            select(BlockModel)
            .where(BlockModel.book_id == book_id)
            .where(BlockModel.soft_deleted_at.is_(None))  # Soft delete filter
            .order_by(BlockModel.order.asc())  # Fractional index ordering
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        logger.debug(f"Retrieved {len(models)} blocks for book {book_id}")
        return [self._to_domain(m) for m in models]

    async def list_paginated(
        self, book_id: UUID, page: int = 1, page_size: int = 20
    ) -> tuple[List[Block], int]:
        """
        Get paginated Blocks in a Book with fractional index ordering

        Ordering: By fractional index (order field)
        Filters: soft_deleted_at IS NULL (soft delete pattern)
        Pagination: OFFSET/LIMIT based on page number

        Args:
            book_id: Book UUID
            page: Page number (1-indexed, default 1)
            page_size: Items per page (default 20)

        Returns:
            Tuple of (blocks: List[Block], total_count: int)

        Example:
            blocks, total = await repo.list_paginated(
                book_id=UUID(...), page=2, page_size=10
            )
            has_more = (page - 1) * page_size + len(blocks) < total
        """
        from sqlalchemy import select, func

        # Query 1: Get total count
        count_stmt = (
            select(func.count(BlockModel.id))
            .where(BlockModel.book_id == book_id)
            .where(BlockModel.soft_deleted_at.is_(None))
        )
        count_result = await self.session.execute(count_stmt)
        total_count = count_result.scalar_one()

        # Query 2: Get paginated results
        offset = (page - 1) * page_size
        stmt = (
            select(BlockModel)
            .where(BlockModel.book_id == book_id)
            .where(BlockModel.soft_deleted_at.is_(None))  # Soft delete filter
            .order_by(BlockModel.order.asc())  # Fractional index ordering
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        logger.debug(
            f"Retrieved page {page} (size {page_size}) for book {book_id}: "
            f"{len(models)} items of {total_count} total"
        )
        return ([self._to_domain(m) for m in models], total_count)

    async def get_deleted_blocks(self, book_id: UUID) -> List[Block]:
        """
        Get soft-deleted Blocks in a Book (for recovery)

        Returns:
            List of deleted Blocks that can be restored
        """
        from sqlalchemy import select

        stmt = (
            select(BlockModel)
            .where(BlockModel.book_id == book_id)
            .where(BlockModel.soft_deleted_at.isnot(None))  # Only deleted
            .order_by(BlockModel.soft_deleted_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        logger.debug(f"Retrieved {len(models)} deleted blocks for book {book_id}")
        return [self._to_domain(m) for m in models]

    def _to_domain(self, model: BlockModel) -> Block:
        """
        Convert ORM Model → Domain Model

        Handles type-specific conversions:
        - Decimal order for fractional indexing
        - BlockType enum from string
        - heading_level mapping (only set for HEADING type)
        """
        block_type = BlockType(model.type)
        heading_level = model.heading_level if block_type == BlockType.HEADING else None

        return Block(
            block_id=model.id,
            book_id=model.book_id,
            block_type=block_type,
            content=BlockContent(value=model.content),
            order=Decimal(str(model.order)) if model.order is not None else Decimal("0"),
            heading_level=heading_level,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
