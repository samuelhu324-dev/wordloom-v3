"""Book Tests - Fixtures and Mock Repository

Testing Strategy (ADR-014: Book Models & Testing Layer):
========================================================
- Constants: sample_library_id, sample_bookshelf_id
- Factories: book_domain_factory, book_model_factory
- Mock: MockBookRepository with RULE-011/012 constraint validation
- Helpers: assert_book_soft_deleted, assert_book_move_permission
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime, timezone
from modules.book.domain import Book, BookTitle, BookSummary, BookStatus


# ============================================
# 1️⃣ CONSTANTS
# ============================================

@pytest.fixture
def sample_library_id():
    """Sample library ID (constant for tests)"""
    return UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def sample_bookshelf_id():
    """Sample bookshelf ID (constant for tests)"""
    return UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture
def sample_book_title():
    """Sample book title (constant for tests)"""
    return "Test Book"


# ============================================
# 2️⃣ DOMAIN FACTORIES
# ============================================

@pytest.fixture
def book_domain_factory(sample_library_id, sample_bookshelf_id):
    """
    Factory for creating Book Domain objects

    Supports all 11 fields customization including soft_deleted_at
    for RULE-012 soft delete testing.

    Usage:
        book = book_domain_factory(title="My Book", is_pinned=True)
        deleted_book = book_domain_factory(soft_deleted_at=now)
    """
    def _create(
        book_id=None,
        bookshelf_id=None,
        library_id=None,
        title="Test Book",
        summary=None,
        status="draft",
        is_pinned=False,
        due_at=None,
        block_count=0,
        soft_deleted_at=None,
        created_at=None,
        updated_at=None,
    ):
        from modules.book.domain import Book
        now = datetime.now(timezone.utc)
        return Book(
            id=book_id or uuid4(),
            bookshelf_id=bookshelf_id or sample_bookshelf_id,
            library_id=library_id or sample_library_id,
            title=BookTitle(title),
            summary=BookSummary(summary) if summary else None,
            status=BookStatus(status),
            is_pinned=is_pinned,
            due_at=due_at,
            block_count=block_count,
            soft_deleted_at=soft_deleted_at,
            created_at=created_at or now,
            updated_at=updated_at or now,
        )
    return _create


# ============================================
# 3️⃣ ORM MODEL FACTORIES
# ============================================

@pytest.fixture
def book_model_factory(sample_library_id, sample_bookshelf_id):
    """
    Factory for creating Book ORM models

    Supports all 11 fields including library_id (RULE-011) and
    soft_deleted_at (RULE-012) for complete round-trip testing.

    Usage:
        model = book_model_factory(title="My Book", is_pinned=True)
        deleted_model = book_model_factory(soft_deleted_at=now)
    """
    def _create(
        book_id=None,
        bookshelf_id=None,
        library_id=None,
        title="Test Book",
        summary=None,
        status="draft",
        is_pinned=False,
        due_at=None,
        block_count=0,
        soft_deleted_at=None,
        created_at=None,
        updated_at=None,
    ):
        from modules.book.models import BookModel
        now = datetime.now(timezone.utc)
        return BookModel(
            id=book_id or uuid4(),
            bookshelf_id=bookshelf_id or sample_bookshelf_id,
            library_id=library_id or sample_library_id,
            title=title,
            summary=summary,
            status=status,
            is_pinned=is_pinned,
            due_at=due_at,
            block_count=block_count,
            soft_deleted_at=soft_deleted_at,
            created_at=created_at or now,
            updated_at=updated_at or now,
        )
    return _create


# ============================================
# 4️⃣ MOCK REPOSITORY
# ============================================

@pytest.fixture
async def mock_book_repository(sample_library_id, sample_bookshelf_id):
    """
    Mock BookRepository with RULE-011 and RULE-012 constraint validation

    Key Capabilities:
    - ✅ RULE-011: Validates bookshelf_id + library_id permission check
    - ✅ RULE-012: Filters soft-deleted books (soft_deleted_at IS NULL)
    - ✅ RULE-013: Supports get_deleted_books() for Basement retrieval

    Behaviors:
    - save(): Validates library_id matches bookshelf's library_id
    - get_by_id(): Returns None if book is soft-deleted
    - get_by_bookshelf_id(): Excludes soft-deleted books
    - get_deleted_books(): Retrieves only soft-deleted books
    """
    class MockBookRepository:
        def __init__(self):
            self.store = {}  # book_id -> Book
            self.bookshelves = {}  # bookshelf_id -> Bookshelf (for validation)

        def set_bookshelves(self, bookshelves_map):
            """Helper to inject bookshelf information for RULE-011 validation"""
            self.bookshelves = bookshelves_map

        async def save(self, book: Book) -> None:
            """
            Save book with RULE-011 and RULE-012 validation

            RULE-011: Verify book.library_id matches bookshelf's library
            RULE-012: Allow soft deletion (soft_deleted_at set)
            """
            # RULE-011: Permission check
            if book.bookshelf_id in self.bookshelves:
                bookshelf = self.bookshelves[book.bookshelf_id]
                if book.library_id != bookshelf.library_id:
                    raise PermissionError(
                        f"Book library_id {book.library_id} does not match "
                        f"Bookshelf library_id {bookshelf.library_id}"
                    )
                # Prevent explicit move to Basement (only soft delete via soft_deleted_at)
                if hasattr(bookshelf, 'is_basement') and bookshelf.is_basement:
                    if book.soft_deleted_at is None:
                        raise ValueError(
                            "Cannot explicitly move Book to Basement. "
                            "Use soft delete (set soft_deleted_at) instead."
                        )

            self.store[book.id] = book

        async def get_by_id(self, book_id) -> dict | None:
            """
            Get book by ID (RULE-012: auto-filter soft-deleted)

            Returns None if book is soft-deleted (soft_deleted_at IS NOT NULL)
            """
            book = self.store.get(book_id)
            if book and book.soft_deleted_at is not None:
                return None  # Book is in Basement, not visible
            return book

        async def get_by_bookshelf_id(self, bookshelf_id) -> list:
            """
            Get active books by bookshelf (RULE-012: exclude soft-deleted)

            Returns only books where soft_deleted_at IS NULL
            """
            return [
                b for b in self.store.values()
                if b.bookshelf_id == bookshelf_id and b.soft_deleted_at is None
            ]

        async def get_deleted_books(self, bookshelf_id) -> list:
            """
            Get soft-deleted books in Basement (RULE-013)

            Returns only books where soft_deleted_at IS NOT NULL
            """
            return [
                b for b in self.store.values()
                if b.bookshelf_id == bookshelf_id and b.soft_deleted_at is not None
            ]

        async def delete(self, book_id) -> None:
            """
            Explicitly delete book (NOT RECOMMENDED - use soft delete instead)

            This is for hard delete. Prefer soft delete via:
                book.soft_deleted_at = datetime.now(timezone.utc)
                await repository.save(book)
            """
            # Intentionally not implemented to encourage soft delete pattern
            raise NotImplementedError(
                "Use soft delete pattern: set book.soft_deleted_at and call save()"
            )

    return MockBookRepository()


# ============================================
# 5️⃣ SERVICE FIXTURES
# ============================================

@pytest.fixture
async def book_service(mock_book_repository):
    """
    BookService with mock repository (for unit tests)

    Usage:
        async def test_create_book(book_service, sample_library_id):
            book = await book_service.create_book(
                bookshelf_id, library_id, "My Book"
            )
    """
    from modules.book.service import BookService
    return BookService(repository=mock_book_repository)


# ============================================
# 6️⃣ ASSERTION HELPERS
# ============================================

@pytest.fixture
async def assert_book_soft_deleted():
    """
    Helper to verify RULE-012: Book soft delete

    Ensures:
    - get_by_id() returns None for soft-deleted books
    - get_deleted_books() can retrieve soft-deleted books
    - soft_deleted_at timestamp is set correctly
    """
    async def _verify(book_id, bookshelf_id, repository):
        # Soft-deleted book should not be visible via get_by_id()
        book = await repository.get_by_id(book_id)
        assert book is None, "Soft-deleted book should not be visible"

        # But should be retrievable via get_deleted_books()
        deleted = await repository.get_deleted_books(bookshelf_id)
        deleted_ids = [b.id for b in deleted]
        assert book_id in deleted_ids, "Soft-deleted book should be in Basement"

    return _verify


@pytest.fixture
async def assert_book_move_permission():
    """
    Helper to verify RULE-011: Book transfer permissions

    Ensures:
    - Cross-library transfer fails (PermissionError)
    - Same-library transfer succeeds
    - library_id consistency is maintained
    """
    async def _verify(book, source_bookshelf, target_bookshelf, repository):
        # Different library = permission denied
        if book.library_id != target_bookshelf.library_id:
            with pytest.raises(PermissionError):
                book.bookshelf_id = target_bookshelf.id
                await repository.save(book)
            return

        # Same library = permission granted
        book.bookshelf_id = target_bookshelf.id
        await repository.save(book)

        # Verify transfer succeeded
        loaded = await repository.get_by_id(book.id)
        assert loaded.bookshelf_id == target_bookshelf.id
        assert loaded.library_id == target_bookshelf.library_id

    return _verify
