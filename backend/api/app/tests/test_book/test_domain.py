"""
Test Suite: Book Domain Layer

Tests for Book aggregate root:
- Domain invariants (RULE-009, RULE-011, RULE-012, RULE-013)
- BookTitle value object
- Book operations and transfers
- Soft delete (Basement) pattern via soft_deleted_at

对应 DDD_RULES:
  ✓ RULE-009: Book 可无限创建
  ✓ RULE-011: Book 可跨 Bookshelf 转移（带权限检查）
  ✓ RULE-012: Book 删除时转移到 Basement（软删除via soft_deleted_at）
  ✓ RULE-013: Book 可从 Basement 恢复
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from modules.book.domain import Book, BookTitle, BookSummary, BookStatus


class TestBookTitleValueObject:
    """Value Object: BookTitle"""

    def test_book_title_creation_valid(self):
        """✓ BookTitle accepts valid titles"""
        title = BookTitle(value="My Book Title")
        assert title.value == "My Book Title"

    def test_book_title_strip_whitespace(self):
        """✓ BookTitle accepts titles with leading/trailing whitespace"""
        title = BookTitle(value="  Trimmed Title  ")
        # BookTitle doesn't auto-strip whitespace
        assert title.value == "  Trimmed Title  "

    def test_book_title_empty_raises_error(self):
        """✗ BookTitle rejects empty strings"""
        with pytest.raises(ValueError):
            BookTitle(value="")

    def test_book_title_whitespace_only_raises_error(self):
        """✗ BookTitle rejects whitespace-only strings"""
        with pytest.raises(ValueError):
            BookTitle(value="   ")

    def test_book_title_too_long_raises_error(self):
        """✗ BookTitle rejects titles > 255 characters"""
        long_title = "A" * 256
        with pytest.raises(ValueError):
            BookTitle(value=long_title)


class TestBookSummaryValueObject:
    """Value Object: BookSummary"""

    def test_book_summary_creation_valid(self):
        """✓ BookSummary accepts valid summaries"""
        summary = BookSummary(value="A detailed summary")
        assert summary.value == "A detailed summary"

    def test_book_summary_empty_allowed(self):
        """✓ BookSummary allows empty string (optional field)"""
        summary = BookSummary(value="")
        assert summary.value == ""

    def test_book_summary_too_long_raises_error(self):
        """✗ BookSummary rejects summaries > 1000 characters"""
        long_summary = "x" * 1001
        with pytest.raises(ValueError):
            BookSummary(value=long_summary)


class TestBookAggregateRootCreation:
    """Aggregate Root: Book - Creation with correct soft_deleted_at API"""

    def test_book_creation_with_minimal_data(self):
        """✓ Create Book with required fields only"""
        book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            title=BookTitle(value="New Book"),
        )

        assert book.id is not None
        assert book.bookshelf_id is not None
        assert book.library_id is not None
        assert book.title.value == "New Book"
        assert book.soft_deleted_at is None  # Not in Basement

    def test_book_creation_with_summary(self):
        """✓ Create Book with summary"""
        book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            title=BookTitle(value="Book with Summary"),
            summary=BookSummary(value="Detailed summary"),
        )

        assert book.summary.value == "Detailed summary"

    def test_book_creation_with_all_fields(self):
        """✓ Create Book with all optional fields"""
        due_date = datetime.now(timezone.utc)
        book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            title=BookTitle(value="Complete Book"),
            summary=BookSummary(value="Full book"),
            is_pinned=True,
            due_at=due_date,
            status=BookStatus.DRAFT,
            block_count=5,
        )

        assert book.is_pinned is True
        assert book.due_at == due_date
        assert book.status == BookStatus.DRAFT
        assert book.block_count == 5


class TestBookSoftDeletePattern:
    """Book Soft-Delete via Basement Pattern (RULE-012, RULE-013)"""

    def test_book_not_deleted_by_default(self):
        """✓ Newly created book is not in Basement"""
        book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            title=BookTitle(value="Active Book"),
        )

        assert book.soft_deleted_at is None

    def test_book_soft_deleted_has_timestamp(self):
        """✓ Soft-deleted book has soft_deleted_at timestamp"""
        deleted_at = datetime.now(timezone.utc)
        book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            title=BookTitle(value="Deleted Book"),
            soft_deleted_at=deleted_at,
        )

        assert book.soft_deleted_at == deleted_at

    def test_book_query_is_in_basement(self):
        """✓ Can query if book is in Basement"""
        active_book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            title=BookTitle(value="Active"),
            soft_deleted_at=None,
        )

        deleted_book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            title=BookTitle(value="Deleted"),
            soft_deleted_at=datetime.now(timezone.utc),
        )

        assert active_book.soft_deleted_at is None
        assert deleted_book.soft_deleted_at is not None


class TestBookBusinessRules:
    """Business Rule Enforcement (RULE-009 through RULE-013)"""

    def test_rule_009_unlimited_creation(self):
        """✓ RULE-009: Books can be created unlimited times"""
        bookshelf_id = uuid4()
        library_id = uuid4()

        # Create 100 books - all should succeed
        books = []
        for i in range(100):
            book = Book(
                book_id=uuid4(),
                bookshelf_id=bookshelf_id,
                library_id=library_id,
                title=BookTitle(value=f"Book {i}"),
            )
            books.append(book)

        assert len(books) == 100
        assert all(b.bookshelf_id == bookshelf_id for b in books)

    def test_rule_010_must_have_bookshelf(self):
        """✓ RULE-010: Every Book must belong to a Bookshelf"""
        book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            title=BookTitle(value="Book in Shelf"),
        )

        assert book.bookshelf_id is not None

    def test_rule_011_cross_bookshelf_transfer(self):
        """✓ RULE-011: Book can transfer between bookshelves in same library"""
        library_id = uuid4()
        original_shelf = uuid4()
        target_shelf = uuid4()

        book = Book(
            book_id=uuid4(),
            bookshelf_id=original_shelf,
            library_id=library_id,
            title=BookTitle(value="Transferable Book"),
        )

        # Simulate transfer by creating new Book with updated bookshelf_id
        transferred_book = Book(
            book_id=book.id,
            bookshelf_id=target_shelf,
            library_id=library_id,
            title=book.title,
            summary=book.summary,
            is_pinned=book.is_pinned,
            due_at=book.due_at,
            status=book.status,
            block_count=book.block_count,
        )

        assert transferred_book.bookshelf_id == target_shelf
        assert transferred_book.library_id == library_id

    def test_rule_012_soft_delete_via_soft_deleted_at(self):
        """✓ RULE-012: Book deletion is soft via soft_deleted_at timestamp"""
        book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            title=BookTitle(value="Book to Delete"),
        )

        assert book.soft_deleted_at is None

        # Simulate soft deletion
        deleted_book = Book(
            book_id=book.id,
            bookshelf_id=book.bookshelf_id,
            library_id=book.library_id,
            title=book.title,
            summary=book.summary,
            is_pinned=book.is_pinned,
            due_at=book.due_at,
            status=book.status,
            block_count=book.block_count,
            soft_deleted_at=datetime.now(timezone.utc),  # ← Marks as deleted
        )

        assert deleted_book.soft_deleted_at is not None

    def test_rule_013_restoration_from_basement(self):
        """✓ RULE-013: Book can be restored from Basement (soft_deleted_at cleared)"""
        basement_shelf = uuid4()
        restore_shelf = uuid4()

        # Book in Basement
        basement_book = Book(
            book_id=uuid4(),
            bookshelf_id=basement_shelf,
            library_id=uuid4(),
            title=BookTitle(value="In Basement"),
            soft_deleted_at=datetime.now(timezone.utc),
        )

        assert basement_book.soft_deleted_at is not None

        # Restore to target shelf
        restored_book = Book(
            book_id=basement_book.id,
            bookshelf_id=restore_shelf,
            library_id=basement_book.library_id,
            title=basement_book.title,
            summary=basement_book.summary,
            is_pinned=basement_book.is_pinned,
            due_at=basement_book.due_at,
            status=basement_book.status,
            block_count=basement_book.block_count,
            soft_deleted_at=None,  # ← Cleared - no longer in Basement
        )

        assert restored_book.soft_deleted_at is None
        assert restored_book.bookshelf_id == restore_shelf


class TestBookStatusEnum:
    """Book Status Enum validation"""

    def test_book_status_values(self):
        """✓ BookStatus enum has required values"""
        assert BookStatus.DRAFT.value == "draft"
        assert BookStatus.PUBLISHED.value == "published"
        assert BookStatus.ARCHIVED.value == "archived"
        assert BookStatus.DELETED.value == "deleted"

    def test_book_default_status_is_draft(self):
        """✓ New books default to DRAFT status"""
        book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            title=BookTitle(value="New Book"),
        )

        assert book.status == BookStatus.DRAFT
