"""
Bookshelf Tests - Pytest fixtures and test utilities

Provides:
- Fixtures for Bookshelf domain testing
- Mock objects
- Test data factories
- Database integration fixtures for round-trip testing
"""

import pytest
from uuid import uuid4
from datetime import datetime

from modules.bookshelf.domain import Bookshelf, BookshelfName, BookshelfDescription, BookshelfStatus
from modules.bookshelf.models import BookshelfModel


# ============================================================================
# Constants
# ============================================================================

@pytest.fixture
def sample_library_id():
    """Sample library ID for testing (fixed constant)"""
    return uuid4()


@pytest.fixture
def sample_bookshelf_name():
    """Sample bookshelf name"""
    return "Test Bookshelf"


# ============================================================================
# Domain Factories
# ============================================================================

@pytest.fixture
def bookshelf_domain_factory(sample_library_id):
    """
    Factory fixture for creating Bookshelf domain objects

    Usage:
        bookshelf = bookshelf_domain_factory(name="Custom Name")
    """
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
            description=BookshelfDescription(value=description) if description else None,
            is_pinned=is_pinned,
            is_favorite=is_favorite,
            status=status,
        )

    return _create


@pytest.fixture
def bookshelf_model_factory(sample_library_id):
    """
    Factory fixture for creating Bookshelf ORM models

    Usage:
        model = bookshelf_model_factory(name="Custom Name")
    """
    def _create(
        bookshelf_id=None,
        library_id=None,
        name="Test Bookshelf",
        is_basement=False,
        **kwargs
    ):
        return BookshelfModel(
            id=bookshelf_id or uuid4(),
            library_id=library_id or sample_library_id,
            name=name,
            is_basement=is_basement,
            description=kwargs.get("description"),
            is_pinned=kwargs.get("is_pinned", False),
            pinned_at=kwargs.get("pinned_at"),
            is_favorite=kwargs.get("is_favorite", False),
            status=kwargs.get("status", "active"),
            book_count=kwargs.get("book_count", 0),
            created_at=kwargs.get("created_at", datetime.utcnow()),
            updated_at=kwargs.get("updated_at", datetime.utcnow()),
        )

    return _create


# ============================================================================
# Mock Repository
# ============================================================================

@pytest.fixture
async def mock_bookshelf_repository():
    """
    Mock BookshelfRepository for unit testing (no database)

    Implements:
    - RULE-006: name uniqueness within library (enforced in mock)
    - RULE-010: basement bookshelf support
    """
    class MockBookshelfRepository:
        def __init__(self):
            self.store = {}  # bookshelf_id → Bookshelf

        async def save(self, bookshelf: Bookshelf) -> None:
            # ✅ RULE-006: Check name uniqueness within library
            for existing in self.store.values():
                if (existing.library_id == bookshelf.library_id and
                    str(existing.name) == str(bookshelf.name) and
                    existing.id != bookshelf.id):  # Allow update with same ID
                    raise BookshelfAlreadyExistsError(
                        f"Bookshelf name '{bookshelf.name}' already exists in library {bookshelf.library_id}"
                    )
            self.store[bookshelf.id] = bookshelf

        async def get_by_id(self, bookshelf_id):
            return self.store.get(bookshelf_id)

        async def get_by_library_id(self, library_id):
            return [b for b in self.store.values() if b.library_id == library_id]

        async def get_basement_by_library_id(self, library_id):
            """✅ RULE-010: Support basement bookshelf lookup"""
            for b in self.store.values():
                if b.library_id == library_id and getattr(b, 'is_basement', False):
                    return b
            return None

        async def delete(self, bookshelf_id) -> None:
            self.store.pop(bookshelf_id, None)

        async def exists(self, bookshelf_id) -> bool:
            return bookshelf_id in self.store

    return MockBookshelfRepository()


# ============================================================================
# Service Instance
# ============================================================================

@pytest.fixture
async def bookshelf_service(mock_bookshelf_repository):
    """
    BookshelfService instance with mock repository

    Usage:
        bookshelf = await bookshelf_service.create_bookshelf(library_id, "My Shelf")
    """
    from modules.bookshelf.service import BookshelfService

    return BookshelfService(repository=mock_bookshelf_repository)


# ============================================================================
# Helper Exceptions
# ============================================================================

class BookshelfAlreadyExistsError(Exception):
    """Raised when bookshelf name already exists in library (RULE-006)"""
    pass
