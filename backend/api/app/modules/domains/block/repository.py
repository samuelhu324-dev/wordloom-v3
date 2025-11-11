"""Block Repository"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from domains.block.domain import Block, BlockContent, BlockType, BlockTitle
from domains.block.models import BlockModel

class BlockRepository(ABC):
    @abstractmethod
    async def save(self, block: Block) -> None: pass
    @abstractmethod
    async def get_by_id(self, block_id: UUID) -> Optional[Block]: pass
    @abstractmethod
    async def get_by_book_id(self, book_id: UUID) -> List[Block]: pass
    @abstractmethod
    async def delete(self, block_id: UUID) -> None: pass

class BlockRepositoryImpl(BlockRepository):
    def __init__(self, session):
        self.session = session

    async def save(self, block: Block) -> None:
        model = BlockModel(
            id=block.id,
            book_id=block.book_id,
            block_type=block.block_type.value,
            content=block.content.value,
            order=block.order,
            title_level=block.title.level if block.title else None,
            title_text=block.title.text if block.title else None,
            created_at=block.created_at,
            updated_at=block.updated_at,
        )
        self.session.add(model)

    async def get_by_id(self, block_id: UUID) -> Optional[Block]:
        model = await self.session.get(BlockModel, block_id)
        if not model: return None
        return self._to_domain(model)

    async def get_by_book_id(self, book_id: UUID) -> List[Block]:
        from sqlalchemy import select
        stmt = select(BlockModel).where(BlockModel.book_id == book_id).order_by(BlockModel.order)
        result = await self.session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def delete(self, block_id: UUID) -> None:
        model = await self.session.get(BlockModel, block_id)
        if model: await self.session.delete(model)

    def _to_domain(self, model: BlockModel) -> Block:
        title = None
        if model.title_text and model.title_level:
            title = BlockTitle(text=model.title_text, level=model.title_level)
        return Block(
            block_id=model.id,
            book_id=model.book_id,
            block_type=BlockType(model.block_type),
            content=BlockContent(value=model.content),
            order=model.order,
            title=title,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
