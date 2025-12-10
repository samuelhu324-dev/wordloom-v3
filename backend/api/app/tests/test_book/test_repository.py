"""
Test Suite: Book Repository Layer

Tests for BookRepository operations:
- CRUD operations
- Query by bookshelf
- Query by soft_deleted_at field
- Exception handling
- Soft delete patterns via soft_deleted_at

对应 DDD_RULES:
  ✓ RULE-009: Repository allows unlimited creation
  ✓ RULE-010: Repository enforces book-belongs-to-bookshelf
  ✓ RULE-011: Repository supports book transfer between bookshelves
  ✓ RULE-012: Repository handles soft delete via soft_deleted_at
  ✓ RULE-013: Repository handles restoration (soft_deleted_at cleared)
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from modules.book import (
    Book,
    BookTitle,
    BookSummary,
    BookNotFoundError,
)


class MockBookRepository:
    """In-memory mock repository for testing (synchronous)"""

    def __init__(self):
        self.store = {}  # book_id -> Book

    def save(self, book: Book) -> Book:
        """Save or update book"""
        self.store[book.id] = book
        return book

    def find_by_id(self, book_id) -> Book:
        """Find book by ID (ignores soft delete)"""
        if book_id not in self.store:
            raise BookNotFoundError(f"Book {book_id} not found")
        return self.store[book_id]

    def find_by_bookshelf_id(self, bookshelf_id, include_deleted=False) -> list[Book]:
        """Find books in a bookshelf by bookshelf_id"""
        books = [b for b in self.store.values() if b.bookshelf_id == bookshelf_id]
        if not include_deleted:
            # Exclude soft-deleted books (soft_deleted_at IS NOT NULL)
            books = [b for b in books if b.soft_deleted_at is None]
        return books

    def find_deleted(self) -> list[Book]:
        """Find all soft-deleted books (soft_deleted_at IS NOT NULL)"""
        return [b for b in self.store.values() if b.soft_deleted_at is not None]

    def delete(self, book_id) -> None:
        """Delete book from store"""
        if book_id not in self.store:
            raise BookNotFoundError(f"Book {book_id} not found")
        del self.store[book_id]

    def list_all(self) -> list[Book]:
        """List all books (active only)"""
        return [b for b in self.store.values() if b.soft_deleted_at is None]


@pytest.fixture
def repository():
    """Mock repository fixture"""
    return MockBookRepository()


class TestBookRepositoryCRUD:
    """CRUD Operations"""

    def test_save_book_creates_new(self, repository):
        """✓ save() creates a new Book"""
        book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            title=BookTitle(value="New Book"),
        )

        saved = repository.save(book)

        assert saved.id == book.id

    def test_find_by_id_returns_book(self, repository):
        """✓ find_by_id() retrieves Book"""
        book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            title=BookTitle(value="Test"),
        )

        repository.save(book)
        found = repository.find_by_id(book.id)

        assert found.id == book.id

    def test_find_by_id_not_found(self, repository):
        """✗ find_by_id() raises error when not found"""
        with pytest.raises(BookNotFoundError):
            repository.find_by_id(uuid4())

    def test_find_by_bookshelf_id(self, repository):
        """✓ RULE-009: find_by_bookshelf_id() returns active books"""
        bookshelf_id = uuid4()
        library_id = uuid4()

        for i in range(3):
            book = Book(
                book_id=uuid4(),
                bookshelf_id=bookshelf_id,
                library_id=library_id,
                title=BookTitle(value=f"Book {i}"),
            )
            repository.save(book)

        books = repository.find_by_bookshelf_id(bookshelf_id)

        assert len(books) == 3

    def test_find_by_bookshelf_excludes_deleted(self, repository):
        """✓ RULE-012: find_by_bookshelf_id excludes soft-deleted by default"""
        bookshelf_id = uuid4()
        library_id = uuid4()

        active_book = Book(
            book_id=uuid4(),
            bookshelf_id=bookshelf_id,
            library_id=library_id,
            title=BookTitle(value="Active"),
            soft_deleted_at=None,  # Active
        )

        deleted_book = Book(
            book_id=uuid4(),
            bookshelf_id=bookshelf_id,
            library_id=library_id,
            title=BookTitle(value="Deleted"),
            soft_deleted_at=datetime.now(timezone.utc),  # In Basement
        )

        repository.save(active_book)
        repository.save(deleted_book)

        books = repository.find_by_bookshelf_id(bookshelf_id, include_deleted=False)

        assert len(books) == 1
        assert books[0].soft_deleted_at is None

    def test_find_deleted_returns_basement_books(self, repository):
        """✓ RULE-012,013: find_deleted() returns books with soft_deleted_at"""
        deleted_book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            title=BookTitle(value="Deleted"),
            soft_deleted_at=datetime.now(timezone.utc),
        )

        repository.save(deleted_book)

        deleted = repository.find_deleted()

        assert len(deleted) == 1
        assert deleted[0].soft_deleted_at is not None

    def test_delete_book(self, repository):
        """✓ delete() removes book from store"""
        book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            title=BookTitle(value="To Delete"),
        )

        repository.save(book)
        repository.delete(book.id)

        with pytest.raises(BookNotFoundError):
            repository.find_by_id(book.id)


class TestBookRepositoryInvariants:
    """Invariant Enforcement via Repository"""

    def test_rule_009_unlimited_creation(self, repository):
        """✓ RULE-009: Can create unlimited books in repository"""
        bookshelf_id = uuid4()
        library_id = uuid4()

        for i in range(10):
            book = Book(
                book_id=uuid4(),
                bookshelf_id=bookshelf_id,
                library_id=library_id,
                title=BookTitle(value=f"Book {i}"),
            )
            repository.save(book)

        books = repository.find_by_bookshelf_id(bookshelf_id)

        assert len(books) == 10

    def test_rule_010_book_must_have_bookshelf(self, repository):
        """✓ RULE-010: Every book in repository has bookshelf_id"""
        book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            title=BookTitle(value="Has Bookshelf"),
        )

        saved = repository.save(book)

        assert saved.bookshelf_id is not None

    def test_rule_011_book_transfer_between_bookshelves(self, repository):
        """✓ RULE-011: Book can transfer between bookshelves via repository"""
        library_id = uuid4()
        original_shelf = uuid4()
        target_shelf = uuid4()

        original_book = Book(
            book_id=uuid4(),
            bookshelf_id=original_shelf,
            library_id=library_id,
            title=BookTitle(value="Transferable"),
        )

        repository.save(original_book)

        # Simulate transfer: update bookshelf_id
        transferred_book = Book(
            book_id=original_book.id,
            bookshelf_id=target_shelf,  # Changed
            library_id=library_id,
            title=original_book.title,
            summary=original_book.summary,
            is_pinned=original_book.is_pinned,
            due_at=original_book.due_at,
            status=original_book.status,
            block_count=original_book.block_count,
        )

        repository.save(transferred_book)
        found = repository.find_by_id(original_book.id)

        assert found.bookshelf_id == target_shelf

    def test_rule_012_soft_delete_via_soft_deleted_at(self, repository):
        """✓ RULE-012: Book soft-deletion sets soft_deleted_at timestamp"""
        library_id = uuid4()
        bookshelf_id = uuid4()

        original_book = Book(
            book_id=uuid4(),
            bookshelf_id=bookshelf_id,
            library_id=library_id,
            title=BookTitle(value="To Delete"),
            soft_deleted_at=None,  # Not deleted
        )

        repository.save(original_book)

        # Soft delete: set soft_deleted_at
        deletion_time = datetime.now(timezone.utc)
        deleted_book = Book(
            book_id=original_book.id,
            bookshelf_id=bookshelf_id,
            library_id=library_id,
            title=original_book.title,
            summary=original_book.summary,
            is_pinned=original_book.is_pinned,
            due_at=original_book.due_at,
            status=original_book.status,
            block_count=original_book.block_count,
            soft_deleted_at=deletion_time,  # ← Marks as deleted
        )

        repository.save(deleted_book)
        found = repository.find_by_id(original_book.id)

        assert found.soft_deleted_at is not None
        assert found.soft_deleted_at == deletion_time

    def test_rule_013_restore_from_basement(self, repository):
        """✓ RULE-013: Book can be restored from Basement (soft_deleted_at cleared)"""
        library_id = uuid4()
        basement_shelf = uuid4()
        restore_shelf = uuid4()

        basement_book = Book(
            book_id=uuid4(),
            bookshelf_id=basement_shelf,
            library_id=library_id,
            title=BookTitle(value="In Basement"),
            soft_deleted_at=datetime.now(timezone.utc),  # In Basement
        )

        repository.save(basement_book)

        # Restore: clear soft_deleted_at and move to target shelf
        restored_book = Book(
            book_id=basement_book.id,
            bookshelf_id=restore_shelf,  # Moved
            library_id=library_id,
            title=basement_book.title,
            summary=basement_book.summary,
            is_pinned=basement_book.is_pinned,
            due_at=basement_book.due_at,
            status=basement_book.status,
            block_count=basement_book.block_count,
            soft_deleted_at=None,  # ← Cleared - no longer in Basement
        )

        repository.save(restored_book)
        found = repository.find_by_id(basement_book.id)

        assert found.soft_deleted_at is None
        assert found.bookshelf_id == restore_shelf
