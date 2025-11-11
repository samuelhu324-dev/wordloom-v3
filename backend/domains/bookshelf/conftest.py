"""
Bookshelf Tests - Pytest fixtures and test utilities
"""

import pytest
from uuid import uuid4
from datetime import datetime

from domains.bookshelf.domain import Bookshelf, BookshelfName, BookshelfDescription, BookshelfStatus


@pytest.fixture
def sample_library_id():
    """Sample library ID for testing"""
    return uuid4()


@pytest.fixture
def sample_bookshelf_id():
    """Sample bookshelf ID for testing"""
    return uuid4()


@pytest.fixture
def bookshelf_domain_factory(sample_library_id):
    """Factory fixture for creating Bookshelf domain objects"""
    def _create(
        bookshelf_id=None,
        library_id=None,
        name="Test Bookshelf",
        description=None,
        is_pinned=False,
        is_favorite=False,
        status=BookshelfStatus.ACTIVE,
    ):
        return Bookshelf(
            bookshelf_id=bookshelf_id or uuid4(),
            library_id=library_id or sample_library_id,
            name=BookshelfName(value=name),
            description=BookshelfDescription(value=description),
            is_pinned=is_pinned,
            is_favorite=is_favorite,
            status=status,
        )
    return _create


@pytest.fixture
async def mock_bookshelf_repository():
    """Mock BookshelfRepository for testing"""
    class MockBookshelfRepository:
        def __init__(self):
            self.store = {}

        async def save(self, bookshelf: Bookshelf) -> None:
            self.store[bookshelf.id] = bookshelf

        async def get_by_id(self, bookshelf_id):
            return self.store.get(bookshelf_id)

        async def get_by_library_id(self, library_id):
            return [b for b in self.store.values() if b.library_id == library_id]

        async def delete(self, bookshelf_id) -> None:
            self.store.pop(bookshelf_id, None)

        async def exists(self, bookshelf_id) -> bool:
            return bookshelf_id in self.store

    return MockBookshelfRepository()


@pytest.fixture
async def bookshelf_service(mock_bookshelf_repository):
    """BookshelfService instance with mock repository"""
    from domains.bookshelf.service import BookshelfService
    return BookshelfService(repository=mock_bookshelf_repository)
