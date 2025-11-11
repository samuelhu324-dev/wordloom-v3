"""Block Service"""
from typing import List
from uuid import UUID
from domains.block.domain import Block, BlockType
from domains.block.repository import BlockRepository

class BlockService:
    def __init__(self, repository: BlockRepository):
        self.repository = repository

    async def create_block(self, book_id: UUID, block_type: str, content: str, order: int = 0) -> Block:
        bt = BlockType(block_type)
        block = Block.create(book_id, bt, content, order)
        await self.repository.save(block)
        return block

    async def get_block(self, block_id: UUID) -> Block:
        block = await self.repository.get_by_id(block_id)
        if not block: raise Exception(f"Block {block_id} not found")
        return block

    async def list_blocks(self, book_id: UUID) -> List[Block]:
        return await self.repository.get_by_book_id(book_id)

    async def update_block_content(self, block_id: UUID, new_content: str) -> Block:
        block = await self.get_block(block_id)
        block.set_content(new_content)
        await self.repository.save(block)
        return block

    async def reorder_block(self, block_id: UUID, new_order: int) -> Block:
        block = await self.get_block(block_id)
        block.set_order(new_order)
        await self.repository.save(block)
        return block

    async def delete_block(self, block_id: UUID) -> None:
        block = await self.get_block(block_id)
        block.mark_deleted()
        await self.repository.save(block)
        await self.repository.delete(block_id)
