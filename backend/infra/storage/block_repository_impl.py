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
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

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

    def __init__(self, session: Session):
        """Initialize repository with database session

        Args:
            session: SQLAlchemy session for database access
        """
        self.session = session

    async def save(self, block: Block) -> None:
        """Save Block (create or update)"""
        model = self.session.query(BlockModel).filter(
            BlockModel.id == block.id
        ).first()

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

        self.session.commit()

    async def get_by_id(self, block_id: UUID) -> Optional[Block]:
        """Get Block by ID (with soft-delete filtering)"""
        try:
            model = self.session.query(BlockModel).filter(
                and_(
                    BlockModel.id == block_id,
                    BlockModel.soft_deleted_at.is_(None)
                )
            ).first()

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
            models = self.session.query(BlockModel).filter(
                and_(
                    BlockModel.book_id == book_id,
                    BlockModel.soft_deleted_at.is_(None)
                )
            ).order_by(BlockModel.order.asc()).all()

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
    ) -> Tuple[List[Block], int]:
        """Get paginated Blocks in a Book with fractional index ordering"""
        try:
            # Query 1: Get total count
            total_count = self.session.query(func.count(BlockModel.id)).filter(
                and_(
                    BlockModel.book_id == book_id,
                    BlockModel.soft_deleted_at.is_(None)
                )
            ).scalar() or 0

            # Query 2: Get paginated results
            offset = (page - 1) * page_size
            models = self.session.query(BlockModel).filter(
                and_(
                    BlockModel.book_id == book_id,
                    BlockModel.soft_deleted_at.is_(None)
                )
            ).order_by(BlockModel.order.asc()).offset(offset).limit(page_size).all()

            logger.debug(
                f"Retrieved page {page} (size {page_size}) for book {book_id}: "
                f"{len(models)} items of {total_count} total"
            )
            return ([self._to_domain(m) for m in models], total_count)
        except Exception as e:
            logger.error(f"Error fetching paginated Blocks: {e}")
            raise

    async def get_deleted_blocks(self, book_id: UUID) -> List[Block]:
        """Get soft-deleted Blocks in a Book"""
        try:
            models = self.session.query(BlockModel).filter(
                and_(
                    BlockModel.book_id == book_id,
                    BlockModel.soft_deleted_at.isnot(None)
                )
            ).order_by(BlockModel.soft_deleted_at.desc()).all()

            logger.debug(f"Retrieved {len(models)} deleted blocks for book {book_id}")
            return [self._to_domain(m) for m in models]
        except Exception as e:
            logger.error(f"Error fetching deleted Blocks: {e}")
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
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
