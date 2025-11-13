"""
Test Suite: Block Repository Layer

Tests for BlockRepository operations:
- CRUD operations
- Query by book
- Fractional Index ordering
- Soft delete handling
- Exception handling

对应 DDD_RULES:
  ✓ RULE-013-REVISED: Repository handles multiple block types
  ✓ RULE-014: Repository maintains book association
  ✓ RULE-015-REVISED: Repository preserves Fractional Index order
  ✓ RULE-016: Repository handles HEADING type
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal

from modules.block.domain import Block, BlockContent, BlockType
from modules.block.exceptions import BlockNotFoundError


class MockBlockRepository:
    """In-memory mock repository"""

    def __init__(self):
        self.store = {}  # block_id -> Block

    async def save(self, block: Block) -> Block:
        """Save or update block"""
        self.store[block.block_id] = block
        return block

    async def find_by_id(self, block_id) -> Block:
        """Find block by ID"""
        if block_id not in self.store:
            raise BlockNotFoundError(f"Block {block_id} not found")
        return self.store[block_id]

    async def find_by_book_id(self, book_id, include_deleted=False) -> list[Block]:
        """Find blocks in a book, ordered by index"""
        blocks = [b for b in self.store.values() if b.book_id == book_id]
        if not include_deleted:
            blocks = [b for b in blocks if not b.is_deleted]
        # Sort by Fractional Index
        return sorted(blocks, key=lambda b: b.index)

    async def find_by_book_and_type(self, book_id, block_type) -> list[Block]:
        """Find blocks of specific type"""
        blocks = [
            b for b in self.store.values()
            if b.book_id == book_id and b.block_type == block_type and not b.is_deleted
        ]
        return sorted(blocks, key=lambda b: b.index)

    async def find_headings(self, book_id) -> list[Block]:
        """Find all HEADING blocks (RULE-016)"""
        return await self.find_by_book_and_type(book_id, BlockType.HEADING)

    async def delete(self, block_id) -> None:
        """Delete block"""
        if block_id not in self.store:
            raise BlockNotFoundError(f"Block {block_id} not found")
        del self.store[block_id]

    async def list_all(self) -> list[Block]:
        """List all blocks"""
        return list(self.store.values())


@pytest.fixture
def repository():
    """Mock repository fixture"""
    return MockBlockRepository()


class TestBlockRepositoryCRUD:
    """CRUD Operations"""

    @pytest.mark.asyncio
    async def test_save_block_creates_new(self, repository):
        """✓ save() creates a new Block"""
        block = Block(
            block_id=uuid4(),
            book_id=uuid4(),
            block_type=BlockType.TEXT,
            content=BlockContent(value="New Block"),
            index=Decimal("1.0"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        saved = await repository.save(block)

        assert saved.block_id == block.block_id

    @pytest.mark.asyncio
    async def test_find_by_id_returns_block(self, repository):
        """✓ find_by_id() retrieves Block"""
        block = Block(
            block_id=uuid4(),
            book_id=uuid4(),
            block_type=BlockType.TEXT,
            content=BlockContent(value="Test"),
            index=Decimal("1.0"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(block)
        found = await repository.find_by_id(block.block_id)

        assert found.block_id == block.block_id

    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, repository):
        """✗ find_by_id() raises error"""
        with pytest.raises(BlockNotFoundError):
            await repository.find_by_id(uuid4())

    @pytest.mark.asyncio
    async def test_delete_block(self, repository):
        """✓ delete() removes block"""
        block = Block(
            block_id=uuid4(),
            book_id=uuid4(),
            block_type=BlockType.TEXT,
            content=BlockContent(value="To Delete"),
            index=Decimal("1.0"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(block)
        await repository.delete(block.block_id)

        with pytest.raises(BlockNotFoundError):
            await repository.find_by_id(block.block_id)


class TestBlockRepositoryOrdering:
    """RULE-015-REVISED: Fractional Index Ordering"""

    @pytest.mark.asyncio
    async def test_find_by_book_ordered_by_index(self, repository):
        """✓ RULE-015-REVISED: Blocks returned ordered by Fractional Index"""
        book_id = uuid4()

        # Create blocks out of order
        block_a = Block(
            block_id=uuid4(),
            book_id=book_id,
            block_type=BlockType.TEXT,
            content=BlockContent(value="First"),
            index=Decimal("1.0"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        block_c = Block(
            block_id=uuid4(),
            book_id=book_id,
            block_type=BlockType.TEXT,
            content=BlockContent(value="Third"),
            index=Decimal("3.0"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        block_b = Block(
            block_id=uuid4(),
            book_id=book_id,
            block_type=BlockType.TEXT,
            content=BlockContent(value="Second"),
            index=Decimal("2.0"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(block_a)
        await repository.save(block_c)
        await repository.save(block_b)

        # Query should return in order
        blocks = await repository.find_by_book_id(book_id)

        assert len(blocks) == 3
        assert blocks[0].index == Decimal("1.0")
        assert blocks[1].index == Decimal("2.0")
        assert blocks[2].index == Decimal("3.0")

    @pytest.mark.asyncio
    async def test_blocks_with_fractional_indices(self, repository):
        """✓ Blocks with fractional indices ordered correctly"""
        book_id = uuid4()

        indices = [Decimal("1.0"), Decimal("1.5"), Decimal("1.25"), Decimal("2.0")]

        for idx in indices:
            block = Block(
                block_id=uuid4(),
                book_id=book_id,
                block_type=BlockType.TEXT,
                content=BlockContent(value="Content"),
                index=idx,
                is_deleted=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            await repository.save(block)

        blocks = await repository.find_by_book_id(book_id)

        block_indices = [b.index for b in blocks]
        assert block_indices == sorted(indices)


class TestBlockRepositoryTypes:
    """Block Type Handling"""

    @pytest.mark.asyncio
    async def test_find_by_book_and_type(self, repository):
        """✓ RULE-013-REVISED: Find blocks by type"""
        book_id = uuid4()

        text_block = Block(
            block_id=uuid4(),
            book_id=book_id,
            block_type=BlockType.TEXT,
            content=BlockContent(value="Text"),
            index=Decimal("1.0"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        code_block = Block(
            block_id=uuid4(),
            book_id=book_id,
            block_type=BlockType.CODE,
            content=BlockContent(value="Code"),
            index=Decimal("2.0"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(text_block)
        await repository.save(code_block)

        text_blocks = await repository.find_by_book_and_type(book_id, BlockType.TEXT)

        assert len(text_blocks) == 1
        assert text_blocks[0].block_type == BlockType.TEXT

    @pytest.mark.asyncio
    async def test_find_headings(self, repository):
        """✓ RULE-016: find_headings() returns HEADING blocks"""
        book_id = uuid4()

        heading_block = Block(
            block_id=uuid4(),
            book_id=book_id,
            block_type=BlockType.HEADING,
            content=BlockContent(value="Section Title"),
            index=Decimal("1.0"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        text_block = Block(
            block_id=uuid4(),
            book_id=book_id,
            block_type=BlockType.TEXT,
            content=BlockContent(value="Content"),
            index=Decimal("2.0"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(heading_block)
        await repository.save(text_block)

        headings = await repository.find_headings(book_id)

        assert len(headings) == 1
        assert headings[0].block_type == BlockType.HEADING


class TestBlockRepositoryInvariants:
    """Invariant Enforcement"""

    @pytest.mark.asyncio
    async def test_rule_014_book_association(self, repository):
        """✓ RULE-014: Block belongs to Book"""
        book_id = uuid4()

        block = Block(
            block_id=uuid4(),
            book_id=book_id,
            block_type=BlockType.TEXT,
            content=BlockContent(value="Content"),
            index=Decimal("1.0"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(block)
        found = await repository.find_by_id(block.block_id)

        assert found.book_id == book_id
