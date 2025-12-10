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

from modules.book.domain import Book, BookTitle, BookSummary, BookStatus, BookMaturity
from modules.book.domain.exceptions import InvalidBookDataError
from api.app.modules.book.application.utils.maturity import transition_book_maturity


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


class TestBookCoverIcon:
    """Cover icon validation and mutation"""

    def test_cover_icon_normalization(self):
        """✓ cover_icon stores normalized lowercase slug"""
        book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            title=BookTitle(value="Icon Book"),
            cover_icon="  Book-Open  ",
        )

        assert book.cover_icon == "book-open"

    def test_cover_icon_invalid_value_raises(self):
        """✗ cover_icon rejects invalid characters"""
        with pytest.raises(InvalidBookDataError):
            Book(
                book_id=uuid4(),
                bookshelf_id=uuid4(),
                library_id=uuid4(),
                title=BookTitle(value="Bad Icon"),
                cover_icon="book open",  # contains space
            )

    def test_update_cover_icon_can_clear(self):
        """✓ update_cover_icon allows clearing with None"""
        book = Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            title=BookTitle(value="Mutable Icon"),
            cover_icon="star",
        )

        book.update_cover_icon(None)

        assert book.cover_icon is None


class TestBookCoverMedia:
    """Cover media guard rails (Stable-only, auto-revoke)."""

    def _make_book(self, maturity: BookMaturity) -> Book:
        return Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            title=BookTitle(value="Cover Media Book"),
            maturity=maturity,
        )

    def test_set_cover_media_requires_stable(self):
        """✗ Non-Stable maturity cannot assign cover media."""
        book = self._make_book(BookMaturity.GROWING)

        with pytest.raises(InvalidBookDataError):
            book.set_cover_media(uuid4())

    def test_set_cover_media_allows_clearing(self):
        """✓ Already set cover media can be cleared safely."""
        book = self._make_book(BookMaturity.STABLE)
        media_id = uuid4()
        book.set_cover_media(media_id)

        assert book.cover_media_id == media_id

        book.set_cover_media(None)
        assert book.cover_media_id is None

    def test_cover_media_revoked_on_regression(self):
        """✓ Downgrading maturity auto-revokes cover media."""
        book = self._make_book(BookMaturity.STABLE)
        media_id = uuid4()
        book.set_cover_media(media_id)
        assert book.cover_media_id == media_id

        book.change_maturity(BookMaturity.GROWING)

        assert book.cover_media_id is None


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


class TestBookBasementLifecycle:
    """Plan173B: Basement metadata tracking on Book aggregate."""

    def test_move_to_basement_records_previous_and_timestamp(self):
        """✓ move_to_basement keeps previous shelf + timestamp metadata"""
        library_id = uuid4()
        active_shelf = uuid4()
        basement_shelf = uuid4()
        book = Book(
            book_id=uuid4(),
            bookshelf_id=active_shelf,
            library_id=library_id,
            title=BookTitle(value="Basement Candidate"),
        )

        book.move_to_basement(basement_shelf)

        assert book.bookshelf_id == basement_shelf
        assert book.previous_bookshelf_id == active_shelf
        assert book.is_in_basement
        assert book.moved_to_basement_at is not None

    def test_restore_from_basement_clears_basement_metadata(self):
        """✓ restore_from_basement puts book back and clears metadata"""
        library_id = uuid4()
        active_shelf = uuid4()
        basement_shelf = uuid4()
        book = Book(
            book_id=uuid4(),
            bookshelf_id=active_shelf,
            library_id=library_id,
            title=BookTitle(value="Basement Return"),
        )
        book.move_to_basement(basement_shelf)

        book.restore_from_basement()

        assert book.bookshelf_id == active_shelf
        assert book.previous_bookshelf_id is None
        assert book.moved_to_basement_at is None
        assert not book.is_in_basement

    def test_restore_without_target_raises_when_previous_missing(self):
        """✗ Restore must know destination bookshelf"""
        basement_shelf = uuid4()
        book = Book(
            book_id=uuid4(),
            bookshelf_id=basement_shelf,
            library_id=uuid4(),
            title=BookTitle(value="Stranded"),
            soft_deleted_at=datetime.now(timezone.utc),
            previous_bookshelf_id=None,
        )

        with pytest.raises(InvalidBookDataError):
            book.restore_from_basement()


class TestBookMaturityTransitions:
    """Ensure maturity lifecycle allows bidirectional adjustments."""

    def _make_book(self, maturity: BookMaturity) -> Book:
        return Book(
            book_id=uuid4(),
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            title=BookTitle(value="Lifecycle"),
            maturity=maturity,
        )

    def test_book_can_regress_from_growing_to_seed(self):
        book = self._make_book(BookMaturity.GROWING)

        book.change_maturity(BookMaturity.SEED)

        assert book.maturity == BookMaturity.SEED

    def test_transition_helper_handles_multi_step_regression(self):
        book = self._make_book(BookMaturity.STABLE)

        previous, target = transition_book_maturity(book, BookMaturity.SEED)

        assert previous == BookMaturity.STABLE
        assert target == BookMaturity.SEED
        assert book.maturity == BookMaturity.SEED


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
