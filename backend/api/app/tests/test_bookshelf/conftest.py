"""
Bookshelf Test Fixtures - Shared across all test files

Provides:
- Domain object factories
- Mock repositories
- Request DTOs
- Common test data
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from typing import List, Optional
from unittest.mock import AsyncMock

from api.app.modules.bookshelf.domain import (
    Bookshelf,
    BookshelfName,
    BookshelfDescription,
    BookshelfStatus,
    BookshelfType,
)
from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository
from api.app.modules.bookshelf.application.ports.input import (
    CreateBookshelfRequest,
    GetBookshelfRequest,
    DeleteBookshelfRequest,
    RenameBookshelfRequest,
)


# ============================================================================
# Domain Object Factories
# ============================================================================

@pytest.fixture
def library_id():
    """Generate a library UUID for testing"""
    return uuid4()


@pytest.fixture
def bookshelf_id():
    """Generate a bookshelf UUID for testing"""
    return uuid4()


@pytest.fixture
def bookshelf_name():
    """Create a valid BookshelfName ValueObject"""
    return BookshelfName("My Bookshelf")


@pytest.fixture
def bookshelf_description():
    """Create a valid BookshelfDescription ValueObject"""
    return BookshelfDescription("A collection of favorite books")


@pytest.fixture
def bookshelf_domain_object(library_id, bookshelf_name, bookshelf_description):
    """Create a complete Bookshelf domain object for testing"""
    bookshelf = Bookshelf.create(
        library_id=library_id,
        name=str(bookshelf_name),
        description=str(bookshelf_description) if bookshelf_description else None,
        type_=BookshelfType.NORMAL,
    )
    return bookshelf


@pytest.fixture
def basement_bookshelf_domain_object(library_id):
    """Create a Basement Bookshelf domain object (RULE-010)"""
    bookshelf = Bookshelf.create(
        library_id=library_id,
        name="Basement",
        description=None,
        type_=BookshelfType.BASEMENT,
    )
    return bookshelf


# ============================================================================
# Request DTO Factories
# ============================================================================

@pytest.fixture
def create_bookshelf_request(library_id):
    """Create a valid CreateBookshelfRequest DTO"""
    return CreateBookshelfRequest(
        library_id=library_id,
        name="Test Bookshelf",
        description="A test bookshelf for testing",
    )


@pytest.fixture
def get_bookshelf_request(bookshelf_id):
    """Create a GetBookshelfRequest DTO"""
    return GetBookshelfRequest(bookshelf_id=bookshelf_id)


@pytest.fixture
def delete_bookshelf_request(bookshelf_id):
    """Create a DeleteBookshelfRequest DTO"""
    return DeleteBookshelfRequest(bookshelf_id=bookshelf_id)


@pytest.fixture
def rename_bookshelf_request(bookshelf_id):
    """Create a RenameBookshelfRequest DTO"""
    return RenameBookshelfRequest(
        bookshelf_id=bookshelf_id,
        new_name="Renamed Bookshelf",
    )


# ============================================================================
# Mock Repository
# ============================================================================

class MockBookshelfRepository(IBookshelfRepository):
    """
    In-memory Mock Repository for testing UseCase layer without database.

    Simulates repository behavior:
    - Stores bookshelves in memory
    - Enforces unique names per library (RULE-006)
    - Enforces soft delete (RULE-005)
    - Validates Basement constraints (RULE-010)
    """

    def __init__(self):
        """Initialize with empty bookshelf storage"""
        self._bookshelves: dict = {}  # {bookshelf_id: Bookshelf}
        self._library_names: dict = {}  # {(library_id, name): bookshelf_id}

    async def save(self, bookshelf: Bookshelf) -> None:
        """Save (create or update) a bookshelf"""
        # Check for duplicate names in same library (RULE-006)
        key = (bookshelf.library_id, str(bookshelf.name))

        # Allow update of same bookshelf with same name
        existing_id = self._library_names.get(key)
        if existing_id and existing_id != bookshelf.id:
            raise ValueError(f"Bookshelf name '{bookshelf.name}' already exists in library")

        # Store bookshelf
        self._bookshelves[bookshelf.id] = bookshelf
        self._library_names[key] = bookshelf.id

    async def get_by_id(self, bookshelf_id) -> Optional[Bookshelf]:
        """Retrieve bookshelf by ID"""
        return self._bookshelves.get(bookshelf_id)

    async def get_by_library_id(self, library_id) -> List[Bookshelf]:
        """Get all active bookshelves in a library (RULE-005)"""
        return [
            bs for bs in self._bookshelves.values()
            if bs.library_id == library_id and bs.status == BookshelfStatus.ACTIVE
        ]

    async def get_basement_by_library_id(self, library_id) -> Optional[Bookshelf]:
        """Get basement bookshelf for a library (RULE-010)"""
        for bs in self._bookshelves.values():
            if bs.library_id == library_id and bs.type == BookshelfType.BASEMENT:
                return bs
        return None

    async def find_deleted_by_library(self, library_id, limit: int = 100, offset: int = 0) -> List[Bookshelf]:
        """Return deleted bookshelves for a library (used by some usecases/tests)."""
        deleted = [
            bs
            for bs in self._bookshelves.values()
            if bs.library_id == library_id and bs.status == BookshelfStatus.DELETED
        ]
        return deleted[offset : offset + limit]

    async def exists_by_name(self, library_id, name: str) -> bool:
        """Check name uniqueness per library (RULE-006)"""
        key = (library_id, name.strip())
        return key in self._library_names

    async def delete(self, bookshelf_id) -> None:
        """Soft delete a bookshelf (RULE-005)"""
        bs = self._bookshelves.get(bookshelf_id)
        if not bs:
            raise ValueError(f"Bookshelf {bookshelf_id} not found")

        # Prevent deletion of Basement (RULE-010)
        if bs.type == BookshelfType.BASEMENT:
            raise ValueError("Cannot delete Basement bookshelf")

        # Mark as deleted (soft delete)
        bs.mark_deleted()

    async def exists(self, bookshelf_id) -> bool:
        """Check if bookshelf exists"""
        return bookshelf_id in self._bookshelves


@pytest.fixture
def mock_repository():
    """Create a fresh MockBookshelfRepository for each test"""
    return MockBookshelfRepository()


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
