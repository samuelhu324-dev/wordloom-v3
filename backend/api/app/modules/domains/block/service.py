"""Block Service"""
from typing import List
from uuid import UUID
from domains.block.domain import Block, BlockType
from domains.block.repository import BlockRepository

class BlockService:
    def __init__(self, repository: BlockRepository, book_repository=None, library_repository=None):
        self.repository = repository
        self.book_repository = book_repository  # For Book existence & permission checks
        self.library_repository = library_repository  # For Library ownership validation

    async def create_block(self, book_id: UUID, block_type: str, content: str, order: int = 0, user_id: UUID = None) -> Block:
        """Create Block with Book existence and permission validation"""
        # Step 1: Verify Book exists
        if self.book_repository:
            book = await self.book_repository.get_by_id(book_id)
            if not book:
                raise Exception(f"Book {book_id} not found")

            # Step 2: Optional - verify user permission (ownership)
            if user_id and self.library_repository:
                library = await self.library_repository.get_by_id(book.library_id)
                if library and library.user_id != user_id:
                    raise PermissionError(f"User {user_id} does not own Book {book_id}")

        # Step 3: Create Block
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

    async def update_block_content(self, block_id: UUID, new_content: str, user_id: UUID = None) -> Block:
        """Update Block content with permission validation"""
        block = await self.get_block(block_id)

        # Optional: Verify Book exists and user has permission
        if self.book_repository and user_id and self.library_repository:
            book = await self.book_repository.get_by_id(block.book_id)
            if not book:
                raise Exception(f"Book {block.book_id} not found")
            library = await self.library_repository.get_by_id(book.library_id)
            if library and library.user_id != user_id:
                raise PermissionError(f"User {user_id} does not own Book {block.book_id}")

        block.set_content(new_content)
        await self.repository.save(block)
        return block

    async def reorder_block(self, block_id: UUID, new_order: int, user_id: UUID = None) -> Block:
        """Reorder Block with permission validation"""
        block = await self.get_block(block_id)

        # Optional: Verify Book exists and user has permission
        if self.book_repository and user_id and self.library_repository:
            book = await self.book_repository.get_by_id(block.book_id)
            if not book:
                raise Exception(f"Book {block.book_id} not found")
            library = await self.library_repository.get_by_id(book.library_id)
            if library and library.user_id != user_id:
                raise PermissionError(f"User {user_id} does not own Book {block.book_id}")

        block.set_order(new_order)
        await self.repository.save(block)
        return block

    async def delete_block(self, block_id: UUID, user_id: UUID = None) -> None:
        """Delete Block (soft delete - mark as deleted) with permission validation"""
        block = await self.get_block(block_id)

        # Optional: Verify Book exists and user has permission
        if self.book_repository and user_id and self.library_repository:
            book = await self.book_repository.get_by_id(block.book_id)
            if not book:
                raise Exception(f"Book {block.book_id} not found")
            library = await self.library_repository.get_by_id(book.library_id)
            if library and library.user_id != user_id:
                raise PermissionError(f"User {user_id} does not own Book {block.book_id}")

        block.mark_deleted()  # ← Domain event emitted
        await self.repository.save(block)  # ← Only persist, no hard delete
        # Hard deletion via purge job (after 30+ days)
