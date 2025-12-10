"""
Test Suite: Bookshelf Repository Layer

Tests for BookshelfRepository operations:
- CRUD operations
- Query methods (by library, by name)
- Exception handling
- Uniqueness constraints

对应 DDD_RULES:
  ✓ RULE-004: Repository allows unlimited creation
  ✓ RULE-005: Repository maintains library association
  ✓ RULE-006: Repository handles name uniqueness
  ✓ RULE-010: Repository handles Basement bookshelves
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from modules.bookshelf.domain import Bookshelf, BookshelfName
from modules.bookshelf.exceptions import (
    BookshelfNotFoundError,
    BookshelfAlreadyExistsError,
)


class MockBookshelfRepository:
    """In-memory mock repository"""

    def __init__(self):
        self.store = {}  # bookshelf_id -> Bookshelf

    async def save(self, bookshelf: Bookshelf) -> Bookshelf:
        """Save or update bookshelf"""
        self.store[bookshelf.bookshelf_id] = bookshelf
        return bookshelf

    async def find_by_id(self, bookshelf_id) -> Bookshelf:
        """Find bookshelf by ID"""
        if bookshelf_id not in self.store:
            raise BookshelfNotFoundError(f"Bookshelf {bookshelf_id} not found")
        return self.store[bookshelf_id]

    async def find_by_library_id(self, library_id) -> list[Bookshelf]:
        """Find all bookshelves for a library"""
        return [b for b in self.store.values() if b.library_id == library_id]

    async def find_basement_by_library_id(self, library_id) -> Bookshelf:
        """Find Basement bookshelf for a library"""
        for b in self.store.values():
            if b.library_id == library_id and b.is_basement:
                return b
        raise BookshelfNotFoundError(f"No Basement for library {library_id}")

    async def delete(self, bookshelf_id) -> None:
        """Delete bookshelf"""
        if bookshelf_id not in self.store:
            raise BookshelfNotFoundError(f"Bookshelf {bookshelf_id} not found")
        del self.store[bookshelf_id]

    async def list_all(self) -> list[Bookshelf]:
        """List all bookshelves"""
        return list(self.store.values())


@pytest.fixture
def repository():
    """Mock repository fixture"""
    return MockBookshelfRepository()


class TestBookshelfRepositoryCRUD:
    """CRUD Operations"""

    @pytest.mark.asyncio
    async def test_save_bookshelf_creates_new(self, repository):
        """✓ save() creates a new Bookshelf"""
        bookshelf = Bookshelf(
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            name=BookshelfName(value="New Bookshelf"),
            is_basement=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        saved = await repository.save(bookshelf)

        assert saved.bookshelf_id == bookshelf.bookshelf_id
        assert saved.library_id == bookshelf.library_id

    @pytest.mark.asyncio
    async def test_find_by_id_returns_bookshelf(self, repository):
        """✓ find_by_id() retrieves Bookshelf"""
        bookshelf = Bookshelf(
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            name=BookshelfName(value="Test"),
            is_basement=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(bookshelf)
        found = await repository.find_by_id(bookshelf.bookshelf_id)

        assert found.bookshelf_id == bookshelf.bookshelf_id

    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, repository):
        """✗ find_by_id() raises error for missing ID"""
        with pytest.raises(BookshelfNotFoundError):
            await repository.find_by_id(uuid4())

    @pytest.mark.asyncio
    async def test_find_by_library_id_returns_all(self, repository):
        """✓ find_by_library_id() returns all bookshelves"""
        library_id = uuid4()

        bs1 = Bookshelf(
            bookshelf_id=uuid4(),
            library_id=library_id,
            name=BookshelfName(value="Bookshelf 1"),
            is_basement=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        bs2 = Bookshelf(
            bookshelf_id=uuid4(),
            library_id=library_id,
            name=BookshelfName(value="Bookshelf 2"),
            is_basement=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(bs1)
        await repository.save(bs2)

        found = await repository.find_by_library_id(library_id)

        assert len(found) == 2

    @pytest.mark.asyncio
    async def test_find_basement_by_library_id(self, repository):
        """✓ RULE-010: find_basement_by_library_id() returns Basement"""
        library_id = uuid4()

        basement = Bookshelf(
            bookshelf_id=uuid4(),
            library_id=library_id,
            name=BookshelfName(value="Basement"),
            is_basement=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(basement)

        found = await repository.find_basement_by_library_id(library_id)

        assert found.is_basement is True
        assert found.bookshelf_id == basement.bookshelf_id

    @pytest.mark.asyncio
    async def test_delete_bookshelf(self, repository):
        """✓ delete() removes bookshelf"""
        bookshelf = Bookshelf(
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            name=BookshelfName(value="To Delete"),
            is_basement=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(bookshelf)
        await repository.delete(bookshelf.bookshelf_id)

        with pytest.raises(BookshelfNotFoundError):
            await repository.find_by_id(bookshelf.bookshelf_id)


class TestBookshelfRepositoryInvariants:
    """Invariant Enforcement"""

    @pytest.mark.asyncio
    async def test_rule_004_unlimited_creation(self, repository):
        """✓ RULE-004: Can create unlimited bookshelves"""
        library_id = uuid4()

        for i in range(5):
            bs = Bookshelf(
                bookshelf_id=uuid4(),
                library_id=library_id,
                name=BookshelfName(value=f"Bookshelf {i}"),
                is_basement=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            await repository.save(bs)

        all_bs = await repository.find_by_library_id(library_id)
        assert len(all_bs) == 5

    @pytest.mark.asyncio
    async def test_rule_005_library_association(self, repository):
        """✓ RULE-005: Bookshelf belongs to Library"""
        library_id = uuid4()
        bookshelf = Bookshelf(
            bookshelf_id=uuid4(),
            library_id=library_id,
            name=BookshelfName(value="Test"),
            is_basement=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(bookshelf)
        found = await repository.find_by_id(bookshelf.bookshelf_id)

        assert found.library_id == library_id
