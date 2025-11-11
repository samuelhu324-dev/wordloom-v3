"""Block Tests"""
import pytest
from uuid import uuid4
from domains.block.domain import Block, BlockType, BlockContent, BlockTitle

@pytest.fixture
def sample_book_id():
    return uuid4()

@pytest.fixture
def block_domain_factory(sample_book_id):
    def _create(block_id=None, book_id=None, block_type=BlockType.TEXT, content="Test content"):
        return Block(
            block_id=block_id or uuid4(),
            book_id=book_id or sample_book_id,
            block_type=block_type,
            content=BlockContent(value=content),
        )
    return _create

@pytest.fixture
async def mock_block_repository():
    class MockBlockRepository:
        def __init__(self):
            self.store = {}
        async def save(self, block: Block) -> None:
            self.store[block.id] = block
        async def get_by_id(self, block_id):
            return self.store.get(block_id)
        async def get_by_book_id(self, book_id):
            blocks = [b for b in self.store.values() if b.book_id == book_id]
            return sorted(blocks, key=lambda b: b.order)
        async def delete(self, block_id) -> None:
            self.store.pop(block_id, None)
    return MockBlockRepository()
