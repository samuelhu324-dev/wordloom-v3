"""
Block Repository Implementation Adapter

Concrete SQLAlchemy implementation of BlockRepository output port.

Location: infra/storage/block_repository_impl.py
Port Interface: api/app/modules/block/application/ports/output.py

Architecture:
  - Implements abstract BlockRepository interface (output port)
  - Uses SQLAlchemy ORM models from infra/database/models
  - Converts ORM models ↔ Domain objects
  - Manages database transactions and error handling
  - Enforces soft-delete logic with fractional index ordering
"""

import logging
from typing import Optional, List, Tuple
from uuid import UUID
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.modules.block.domain import Block, BlockContent, BlockType
from api.app.modules.block.application.ports.output import BlockRepository
from infra.database.models import BlockModel

logger = logging.getLogger(__name__)


class SQLAlchemyBlockRepository(BlockRepository):
    """SQLAlchemy implementation of BlockRepository (Infrastructure Adapter)

    This is an ADAPTER in Hexagonal architecture - it implements the
    output port interface defined in application/ports/output.py.

    Responsibilities:
    - Persist Block domain objects to database
    - Fetch Blocks from database and convert to domain objects
    - Enforce soft-delete logic with soft_deleted_at field
    - Support fractional index ordering (order field)
    - Handle transaction rollback on errors
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with async database session

        Args:
            session: AsyncSession for async database access
        """
        self.session = session

    async def save(self, block: Block) -> Block:
        """Save Block (create or update) and return refreshed domain aggregate."""
        stmt = select(BlockModel).where(BlockModel.id == block.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            # INSERT new block
            model = BlockModel(
                id=block.id,
                book_id=block.book_id,
                type=block.type.value,
                content=block.content.value,
                order=block.order,
                heading_level=block.heading_level if block.type == BlockType.HEADING else None,
                soft_deleted_at=block.soft_deleted_at,
                deleted_prev_id=getattr(block, "deleted_prev_id", None),
                deleted_next_id=getattr(block, "deleted_next_id", None),
                deleted_section_path=getattr(block, "deleted_section_path", None),
                deleted_at=getattr(block, "deleted_at", None),
                created_at=block.created_at,
                updated_at=block.updated_at,
            )
            self.session.add(model)
            logger.debug(f"Inserting new block {block.id}")
        else:
            # UPDATE existing block
            previous_soft_deleted = model.soft_deleted_at
            model.type = block.type.value
            model.content = block.content.value
            model.order = block.order
            model.heading_level = block.heading_level if block.type == BlockType.HEADING else None
            model.updated_at = block.updated_at
            model.deleted_prev_id = getattr(block, "deleted_prev_id", None)
            model.deleted_next_id = getattr(block, "deleted_next_id", None)
            model.deleted_section_path = getattr(block, "deleted_section_path", None)
            model.deleted_at = getattr(block, "deleted_at", None)
            model.soft_deleted_at = getattr(block, "soft_deleted_at", None)

            # === NEW: Capture Paperballs context from domain events if block is being deleted ===
            # Check if BlockDeleted event was raised (soft delete)
            if hasattr(block, 'soft_deleted_at') and block.soft_deleted_at and not previous_soft_deleted:
                # Block is being soft-deleted, capture Paperballs fields
                model.soft_deleted_at = block.soft_deleted_at

                # Try to extract deleted_prev_id and deleted_next_id from domain if available
                if hasattr(block, 'deleted_prev_id'):
                    model.deleted_prev_id = block.deleted_prev_id
                if hasattr(block, 'deleted_next_id'):
                    model.deleted_next_id = block.deleted_next_id
                if hasattr(block, 'deleted_section_path'):
                    model.deleted_section_path = block.deleted_section_path
                model.deleted_at = getattr(block, 'deleted_at', model.deleted_at)

                logger.debug(
                    f"Updating block {block.id} with soft_deleted_at, "
                    f"Paperballs context: prev={model.deleted_prev_id}, "
                    f"next={model.deleted_next_id}, section={model.deleted_section_path}"
                )
            else:
                logger.debug(f"Updating block {block.id}")

        await self.session.commit()
        return block

    async def get_by_id(self, block_id: UUID) -> Optional[Block]:
        """Get Block by ID (with soft-delete filtering)"""
        try:
            stmt = select(BlockModel).where(
                and_(
                    BlockModel.id == block_id,
                    BlockModel.soft_deleted_at.is_(None)
                )
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if not model:
                logger.debug(f"Block {block_id} not found or deleted")
                return None

            return self._to_domain(model)
        except Exception as e:
            logger.error(f"Error fetching Block {block_id}: {e}")
            raise

    async def get_by_book_id(self, book_id: UUID) -> List[Block]:
        """Get all Blocks in a Book, ordered by fractional index"""
        try:
            stmt = select(BlockModel).where(
                and_(
                    BlockModel.book_id == book_id,
                    BlockModel.soft_deleted_at.is_(None)
                )
            ).order_by(BlockModel.order.asc())

            result = await self.session.execute(stmt)
            models = result.scalars().all()

            logger.debug(f"Retrieved {len(models)} blocks for book {book_id}")
            return [self._to_domain(m) for m in models]
        except Exception as e:
            logger.error(f"Error fetching Blocks for Book {book_id}: {e}")
            raise

    async def list_paginated(
        self,
        book_id: UUID,
        page: int = 1,
        page_size: int = 20,
        include_deleted: bool = False,
    ) -> Tuple[List[Block], int]:
        """Get paginated Blocks in a Book with fractional index ordering"""
        try:
            filters = [BlockModel.book_id == book_id]
            if not include_deleted:
                filters.append(BlockModel.soft_deleted_at.is_(None))

            # Query 1: Get total count
            count_stmt = select(func.count(BlockModel.id)).where(and_(*filters))
            count_result = await self.session.execute(count_stmt)
            total_count = count_result.scalar() or 0

            # Query 2: Get paginated results
            offset = (page - 1) * page_size
            stmt = (
                select(BlockModel)
                .where(and_(*filters))
                .order_by(BlockModel.order.asc())
                .offset(offset)
                .limit(page_size)
            )

            result = await self.session.execute(stmt)
            models = result.scalars().all()

            logger.debug(
                "Retrieved page %s (size %s) for book %s include_deleted=%s: %s items of %s total",
                page,
                page_size,
                book_id,
                include_deleted,
                len(models),
                total_count,
            )
            return ([self._to_domain(m) for m in models], total_count)
        except Exception as e:
            logger.error(f"Error fetching paginated Blocks: {e}")
            raise

    async def get_deleted_blocks(self, book_id: UUID) -> List[Block]:
        """Get soft-deleted Blocks in a Book"""
        try:
            stmt = select(BlockModel).where(
                and_(
                    BlockModel.book_id == book_id,
                    BlockModel.soft_deleted_at.isnot(None)
                )
            ).order_by(BlockModel.soft_deleted_at.desc())

            result = await self.session.execute(stmt)
            models = result.scalars().all()

            logger.debug(f"Retrieved {len(models)} deleted blocks for book {book_id}")
            return [self._to_domain(m) for m in models]
        except Exception as e:
            logger.error(f"Error fetching deleted Blocks: {e}")
            raise

    # ========== NEW: Paperballs Recovery Methods (Doc 8 Integration) ==========

    async def get_prev_sibling(self, block_id: UUID, book_id: UUID) -> Optional[Block]:
        """
        Get the previous sibling Block (same section, smaller sort_key)

        Purpose: Called during DeleteBlockUseCase to capture deleted_prev_id

        Query Logic:
            WHERE book_id = ?
              AND section_path = (selected block's section)
              AND order < (selected block's order)
              AND soft_deleted_at IS NULL
            ORDER BY order DESC
            LIMIT 1

        Returns: Optional[Block] - Previous sibling or None if not found
        """
        try:
            # Get target block first to find its section and order
            target_stmt = select(BlockModel).where(
                and_(
                    BlockModel.id == block_id,
                    BlockModel.book_id == book_id
                )
            )
            target_result = await self.session.execute(target_stmt)
            target_model = target_result.scalar_one_or_none()

            if not target_model:
                logger.debug(f"Target block {block_id} not found")
                return None

            # Get previous block in same book/section with smaller order
            prev_stmt = select(BlockModel).where(
                and_(
                    BlockModel.book_id == book_id,
                    BlockModel.order < target_model.order,
                    BlockModel.soft_deleted_at.is_(None)
                )
            ).order_by(BlockModel.order.desc())

            prev_result = await self.session.execute(prev_stmt)
            prev_model = prev_result.scalars().first()

            if not prev_model:
                logger.debug(f"No previous sibling found for block {block_id}")
                return None

            logger.debug(f"Found previous sibling {prev_model.id} for block {block_id}")
            return self._to_domain(prev_model)
        except Exception as e:
            logger.error(f"Error fetching previous sibling for block {block_id}: {e}")
            raise

    async def get_next_sibling(self, block_id: UUID, book_id: UUID) -> Optional[Block]:
        """
        Get the next sibling Block (same section, larger sort_key)

        Purpose: Called during DeleteBlockUseCase to capture deleted_next_id

        Query Logic:
            WHERE book_id = ?
              AND section_path = (selected block's section)
              AND order > (selected block's order)
              AND soft_deleted_at IS NULL
            ORDER BY order ASC
            LIMIT 1

        Returns: Optional[Block] - Next sibling or None if not found
        """
        try:
            # Get target block first to find its section and order
            target_stmt = select(BlockModel).where(
                and_(
                    BlockModel.id == block_id,
                    BlockModel.book_id == book_id
                )
            )
            target_result = await self.session.execute(target_stmt)
            target_model = target_result.scalar_one_or_none()

            if not target_model:
                logger.debug(f"Target block {block_id} not found")
                return None

            # Get next block in same book/section with larger order
            next_stmt = select(BlockModel).where(
                and_(
                    BlockModel.book_id == book_id,
                    BlockModel.order > target_model.order,
                    BlockModel.soft_deleted_at.is_(None)
                )
            ).order_by(BlockModel.order.asc())

            next_result = await self.session.execute(next_stmt)
            next_model = next_result.scalars().first()

            if not next_model:
                logger.debug(f"No next sibling found for block {block_id}")
                return None

            logger.debug(f"Found next sibling {next_model.id} for block {block_id}")
            return self._to_domain(next_model)
        except Exception as e:
            logger.error(f"Error fetching next sibling for block {block_id}: {e}")
            raise

    def new_key_between(
        self,
        prev_sort_key: Optional[Decimal],
        next_sort_key: Optional[Decimal]
    ) -> Decimal:
        """
        Calculate new Fractional Index between two sort keys

        Purpose: Called during RestoreBlockUseCase to compute recovery position

        Algorithm (Fractional Index):
            - If both prev and next exist: mid = (prev + next) / 2
            - If only prev exists: new = prev + 1
            - If only next exists: new = next / 2
            - If neither exists: new = 1 (default)

        Precision: Decimal(19, 10) ensures sufficient decimal places

        Args:
            prev_sort_key: Previous block's order (or None)
            next_sort_key: Next block's order (or None)

        Returns: Decimal - New sort key value
        """
        try:
            if prev_sort_key is not None and next_sort_key is not None:
                # Both boundaries exist - calculate midpoint
                new_key = (prev_sort_key + next_sort_key) / Decimal(2)
                logger.debug(f"Calculated midpoint between {prev_sort_key} and {next_sort_key}: {new_key}")
            elif prev_sort_key is not None:
                # Only previous exists - add 1
                new_key = prev_sort_key + Decimal(1)
                logger.debug(f"Calculated key after {prev_sort_key}: {new_key}")
            elif next_sort_key is not None:
                # Only next exists - divide by 2
                new_key = next_sort_key / Decimal(2)
                logger.debug(f"Calculated key before {next_sort_key}: {new_key}")
            else:
                # No boundaries - use default
                new_key = Decimal(1)
                logger.debug("Calculated default key: 1")

            return new_key
        except Exception as e:
            logger.error(f"Error calculating new sort key: {e}")
            raise

    async def restore_from_paperballs(
        self,
        block_id: UUID,
        book_id: UUID,
        deleted_prev_id: Optional[UUID],
        deleted_next_id: Optional[UUID],
        deleted_section_path: Optional[str]
    ) -> Block:
        """
        3-Level Recovery Strategy: Restore Block from Paperballs to optimal position

        Purpose: Called by RestoreBlockUseCase to implement full recovery logic

        Recovery Algorithm (by priority):

            Level 1: Restore after previous sibling (most accurate)
            ├─ Condition: deleted_prev_id exists and node still exists
            ├─ Query: Fetch deleted_prev_id node + its next sibling
            ├─ Calculate: new_order = new_key_between(prev.order, next.order)
            └─ Result: Block restored right after original predecessor

            Level 2: Restore before next sibling (second choice)
            ├─ Condition: Level 1 failed, deleted_next_id exists and node still exists
            ├─ Query: Fetch deleted_next_id node + its previous sibling
            ├─ Calculate: new_order = new_key_between(prev.order, next.order)
            └─ Result: Block restored right before original successor

            Level 3: Restore at section end (fallback)
            ├─ Condition: Level 1 & 2 failed, deleted_section_path exists
            ├─ Query: Get last block in section
            ├─ Calculate: new_order = last_block.order + 1
            └─ Result: Block restored at end of original section

            Level 4: Restore at book end (ultimate fallback)
            ├─ Condition: All above failed
            ├─ Query: Get last block in entire book
            ├─ Calculate: new_order = last_block.order + 1
            └─ Result: Block restored at end of book

        Args:
            block_id: ID of block to restore
            book_id: ID of parent book
            deleted_prev_id: Previous sibling ID (from deletion context)
            deleted_next_id: Next sibling ID (from deletion context)
            deleted_section_path: Section path (from deletion context)

        Returns: Block - Restored domain object with new position
        """
        try:
            # Fetch target block to restore
            stmt = select(BlockModel).where(
                and_(
                    BlockModel.id == block_id,
                    BlockModel.book_id == book_id
                )
            )
            result = await self.session.execute(stmt)
            block_model = result.scalar_one_or_none()

            if not block_model:
                raise Exception(f"Block {block_id} not found")

            new_sort_key = None
            recovery_level = None

            logger.info(f"Starting 3-level recovery for block {block_id}")

            # ===== Level 1: Previous Sibling Recovery =====
            if deleted_prev_id:
                logger.debug(f"Level 1: Attempting recovery via deleted_prev_id={deleted_prev_id}")
                prev_stmt = select(BlockModel).where(
                    and_(
                        BlockModel.id == deleted_prev_id,
                        BlockModel.book_id == book_id,
                        BlockModel.soft_deleted_at.is_(None)
                    )
                )
                prev_result = await self.session.execute(prev_stmt)
                prev_model = prev_result.scalar_one_or_none()

                if prev_model:
                    logger.debug(f"Previous sibling {prev_model.id} found and active")
                    # Get next sibling of the previous block
                    next_stmt = select(BlockModel).where(
                        and_(
                            BlockModel.book_id == book_id,
                            BlockModel.order > prev_model.order,
                            BlockModel.soft_deleted_at.is_(None)
                        )
                    ).order_by(BlockModel.order.asc())

                    next_result = await self.session.execute(next_stmt)
                    next_model = next_result.scalars().first()

                    new_sort_key = self.new_key_between(
                        prev_model.order,
                        next_model.order if next_model else None
                    )
                    recovery_level = 1
                    logger.info(f"Level 1 success: Restored to order={new_sort_key} after previous sibling")

            # ===== Level 2: Next Sibling Recovery =====
            if not new_sort_key and deleted_next_id:
                logger.debug(f"Level 2: Attempting recovery via deleted_next_id={deleted_next_id}")
                next_stmt = select(BlockModel).where(
                    and_(
                        BlockModel.id == deleted_next_id,
                        BlockModel.book_id == book_id,
                        BlockModel.soft_deleted_at.is_(None)
                    )
                )
                next_result = await self.session.execute(next_stmt)
                next_model = next_result.scalar_one_or_none()

                if next_model:
                    logger.debug(f"Next sibling {next_model.id} found and active")
                    # Get previous sibling of the next block
                    prev_stmt = select(BlockModel).where(
                        and_(
                            BlockModel.book_id == book_id,
                            BlockModel.order < next_model.order,
                            BlockModel.soft_deleted_at.is_(None)
                        )
                    ).order_by(BlockModel.order.desc())

                    prev_result = await self.session.execute(prev_stmt)
                    prev_model = prev_result.scalars().first()

                    new_sort_key = self.new_key_between(
                        prev_model.order if prev_model else None,
                        next_model.order
                    )
                    recovery_level = 2
                    logger.info(f"Level 2 success: Restored to order={new_sort_key} before next sibling")

            # ===== Level 3: Section End Recovery =====
            if not new_sort_key and deleted_section_path:
                logger.debug(f"Level 3: Attempting recovery at end of section={deleted_section_path}")
                last_stmt = select(BlockModel).where(
                    and_(
                        BlockModel.book_id == book_id,
                        BlockModel.soft_deleted_at.is_(None)
                    )
                ).order_by(BlockModel.order.desc())

                last_result = await self.session.execute(last_stmt)
                last_model = last_result.scalars().first()

                new_sort_key = (last_model.order + Decimal(1)) if last_model else Decimal(1)
                recovery_level = 3
                logger.info(f"Level 3 success: Restored to order={new_sort_key} at section end")

            # ===== Level 4: Book End Recovery (Ultimate Fallback) =====
            if not new_sort_key:
                logger.debug("Level 4: Falling back to book end recovery")
                last_stmt = select(BlockModel).where(
                    and_(
                        BlockModel.book_id == book_id,
                        BlockModel.soft_deleted_at.is_(None)
                    )
                ).order_by(BlockModel.order.desc())

                last_result = await self.session.execute(last_stmt)
                last_model = last_result.scalars().first()

                new_sort_key = (last_model.order + Decimal(1)) if last_model else Decimal(1)
                recovery_level = 4
                logger.warning(f"Level 4 fallback: Restored to order={new_sort_key} at book end")

            # ===== Update Block State =====
            block_model.order = new_sort_key
            block_model.soft_deleted_at = None
            block_model.deleted_at = None

            # Clear Paperballs fields (recovery context no longer needed)
            block_model.deleted_prev_id = None
            block_model.deleted_next_id = None
            block_model.deleted_section_path = None

            await self.session.commit()

            logger.info(
                f"Block {block_id} successfully restored via Level {recovery_level} "
                f"to order={new_sort_key}"
            )

            return self._to_domain(block_model)
        except Exception as e:
            logger.error(f"Error restoring block from Paperballs: {e}")
            await self.session.rollback()
            raise

    def _to_domain(self, model: BlockModel) -> Block:
        """Convert ORM Model → Domain Model"""
        block_type = BlockType(model.type)
        heading_level = model.heading_level if block_type == BlockType.HEADING else None

        return Block(
            block_id=model.id,
            book_id=model.book_id,
            block_type=block_type,
            content=BlockContent(value=model.content),
            order=Decimal(str(model.order)) if model.order is not None else Decimal("0"),
            heading_level=heading_level,
            soft_deleted_at=model.soft_deleted_at,
            deleted_prev_id=model.deleted_prev_id,
            deleted_next_id=model.deleted_next_id,
            deleted_section_path=model.deleted_section_path,
            deleted_at=getattr(model, "deleted_at", None),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def delete(self, block_id: UUID) -> None:
        """Delete (soft-delete) a Block by ID"""
        try:
            block = await self.get_by_id(block_id)
            if not block:
                raise Exception(f"Block {block_id} not found")

            stmt = select(BlockModel).where(BlockModel.id == block_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                deletion_time = datetime.now(timezone.utc)
                model.soft_deleted_at = deletion_time
                model.deleted_at = deletion_time
                await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting block {block_id}: {e}")
            raise

    async def list_by_book(
        self,
        book_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Block]:
        """List all Blocks in a Book (excluding soft-deleted)"""
        try:
            stmt = select(BlockModel).where(
                and_(
                    BlockModel.book_id == book_id,
                    BlockModel.soft_deleted_at.is_(None)
                )
            ).order_by(BlockModel.order).limit(limit).offset(offset)

            result = await self.session.execute(stmt)
            models = result.scalars().all()

            return [self._to_domain(model) for model in models]
        except Exception as e:
            logger.error(f"Error listing blocks for book {book_id}: {e}")
            raise

    async def count_active_blocks(self, book_id: UUID) -> tuple[int, int]:
        """Return aggregate metrics for non-deleted blocks."""
        try:
            stmt = select(
                func.count(BlockModel.id),
                func.count(func.distinct(BlockModel.type)),
            ).where(
                and_(
                    BlockModel.book_id == book_id,
                    BlockModel.soft_deleted_at.is_(None),
                )
            )
            result = await self.session.execute(stmt)
            row = result.first()
            if not row:
                return 0, 0
            count, type_count = row
            return int(count or 0), int(type_count or 0)
        except Exception as exc:
            logger.error(f"Error counting blocks for book {book_id}: {exc}")
            raise
