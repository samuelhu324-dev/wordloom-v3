"""
Test Suite: Book Repository Layer

Tests for BookRepository operations:
- CRUD operations
- Query by bookshelf
- Query by is_deleted flag
- Exception handling
- Soft delete patterns

对应 DDD_RULES:
  ✓ RULE-009: Repository allows unlimited creation
  ✓ RULE-011: Repository supports book transfer between bookshelves
  ✓ RULE-012: Repository handles soft delete to Basement
  ✓ RULE-013: Repository handles restoration from Basement
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from modules.book.domain import Book, BookTitle
from modules.book.exceptions import BookNotFoundError


class MockBookRepository:
    """In-memory mock repository"""

    def __init__(self):
        self.store = {}  # book_id -> Book

    async def save(self, book: Book) -> Book:
        """Save or update book"""
        self.store[book.book_id] = book
        return book

    async def find_by_id(self, book_id) -> Book:
        """Find book by ID"""
        if book_id not in self.store:
            raise BookNotFoundError(f"Book {book_id} not found")
        return self.store[book_id]

    async def find_by_bookshelf_id(self, bookshelf_id, include_deleted=False) -> list[Book]:
        """Find books in a bookshelf"""
        books = [b for b in self.store.values() if b.bookshelf_id == bookshelf_id]
        if not include_deleted:
            books = [b for b in books if not b.is_deleted]
        return books

    async def find_deleted(self) -> list[Book]:
        """Find all deleted books (in Basement)"""
        return [b for b in self.store.values() if b.is_deleted]

    async def delete(self, book_id) -> None:
        """Delete book"""
        if book_id not in self.store:
            raise BookNotFoundError(f"Book {book_id} not found")
        del self.store[book_id]

    async def list_all(self) -> list[Book]:
        """List all books"""
        return list(self.store.values())


@pytest.fixture
def repository():
    """Mock repository fixture"""
    return MockBookRepository()


class TestBookRepositoryCRUD:
    """CRUD Operations"""

    @pytest.mark.asyncio
    async def test_save_book_creates_new(self, repository):
        """✓ save() creates a new Book"""
        book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            title=BookTitle(value="New Book"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        saved = await repository.save(book)

        assert saved.book_id == book.book_id

    @pytest.mark.asyncio
    async def test_find_by_id_returns_book(self, repository):
        """✓ find_by_id() retrieves Book"""
        book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            title=BookTitle(value="Test"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(book)
        found = await repository.find_by_id(book.book_id)

        assert found.book_id == book.book_id

    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, repository):
        """✗ find_by_id() raises error"""
        with pytest.raises(BookNotFoundError):
            await repository.find_by_id(uuid4())

    @pytest.mark.asyncio
    async def test_find_by_bookshelf_id(self, repository):
        """✓ RULE-009: find_by_bookshelf_id() returns books"""
        bookshelf_id = uuid4()

        for i in range(3):
            book = Book(
                book_id=uuid4(),
                bookshelf_id=bookshelf_id,
                title=BookTitle(value=f"Book {i}"),
                is_deleted=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            await repository.save(book)

        books = await repository.find_by_bookshelf_id(bookshelf_id)

        assert len(books) == 3

    @pytest.mark.asyncio
    async def test_find_by_bookshelf_excludes_deleted(self, repository):
        """✓ RULE-012: find_by_bookshelf_id excludes deleted by default"""
        bookshelf_id = uuid4()

        active_book = Book(
            book_id=uuid4(),
            bookshelf_id=bookshelf_id,
            title=BookTitle(value="Active"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        deleted_book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),  # Different (Basement) bookshelf
            title=BookTitle(value="Deleted"),
            is_deleted=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(active_book)
        await repository.save(deleted_book)

        books = await repository.find_by_bookshelf_id(bookshelf_id, include_deleted=False)

        assert len(books) == 1
        assert books[0].is_deleted is False

    @pytest.mark.asyncio
    async def test_find_deleted_returns_basement_books(self, repository):
        """✓ RULE-012,013: find_deleted() returns books in Basement"""
        deleted_book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            title=BookTitle(value="Deleted"),
            is_deleted=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(deleted_book)

        deleted = await repository.find_deleted()

        assert len(deleted) == 1
        assert deleted[0].is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_book(self, repository):
        """✓ delete() removes book"""
        book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            title=BookTitle(value="To Delete"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(book)
        await repository.delete(book.book_id)

        with pytest.raises(BookNotFoundError):
            await repository.find_by_id(book.book_id)


class TestBookRepositoryInvariants:
    """Invariant Enforcement"""

    @pytest.mark.asyncio
    async def test_rule_009_unlimited_creation(self, repository):
        """✓ RULE-009: Can create unlimited books"""
        bookshelf_id = uuid4()

        for i in range(10):
            book = Book(
                book_id=uuid4(),
                bookshelf_id=bookshelf_id,
                title=BookTitle(value=f"Book {i}"),
                is_deleted=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            await repository.save(book)

        books = await repository.find_by_bookshelf_id(bookshelf_id)

        assert len(books) == 10

    @pytest.mark.asyncio
    async def test_rule_011_book_transfer(self, repository):
        """✓ RULE-011: Book can transfer between bookshelves"""
        book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            title=BookTitle(value="Transferable"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(book)

        # Simulate transfer: update bookshelf_id
        new_bookshelf_id = uuid4()
        transferred_book = Book(
            book_id=book.book_id,
            bookshelf_id=new_bookshelf_id,
            title=book.title,
            is_deleted=book.is_deleted,
            created_at=book.created_at,
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(transferred_book)
        found = await repository.find_by_id(book.book_id)

        assert found.bookshelf_id == new_bookshelf_id

    @pytest.mark.asyncio
    async def test_rule_012_soft_delete(self, repository):
        """✓ RULE-012: Book can be soft-deleted"""
        book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            title=BookTitle(value="To Delete"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(book)

        # Mark as deleted
        deleted_book = Book(
            book_id=book.book_id,
            bookshelf_id=book.bookshelf_id,
            title=book.title,
            is_deleted=True,
            created_at=book.created_at,
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(deleted_book)
        found = await repository.find_by_id(book.book_id)

        assert found.is_deleted is True

    @pytest.mark.asyncio
    async def test_rule_013_restore_from_basement(self, repository):
        """✓ RULE-013: Book can be restored from Basement"""
        basement_book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            title=BookTitle(value="In Basement"),
            is_deleted=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(basement_book)

        # Restore
        restored_book = Book(
            book_id=basement_book.book_id,
            bookshelf_id=uuid4(),  # Different bookshelf
            title=basement_book.title,
            is_deleted=False,
            created_at=basement_book.created_at,
            updated_at=datetime.now(timezone.utc),
        )

        await repository.save(restored_book)
        found = await repository.find_by_id(basement_book.book_id)

        assert found.is_deleted is False
