"""
Test Fixtures and Shared Utilities for Book Module Tests

This conftest.py provides:
- MockRepository implementations with business rule enforcement
- MockEventBus for event collection and verification
- Common fixtures for bookshelf_id, library_id, basement_shelf_id
- Async test setup and teardown
- Shared test data factories

Architecture:
- Fixtures are pytest scope='function' (isolated per test)
- MockRepository enforces RULE-009 through RULE-013
- MockEventBus tracks all published events
- No database access (pure in-memory)
- async/await with pytest-asyncio marker
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Direct imports from domain layer only (avoid application layer complexity)
from modules.book.domain import Book, BookTitle, BookSummary


# ============================================================================
# Local Test Exceptions
# ============================================================================

class BookNotFoundError(Exception):
    """Book not found"""
    pass


class BookOperationError(Exception):
    """Book operation error"""
    pass


# ============================================================================
# MOCK EVENT BUS
# ============================================================================

class MockEventBus:
    """
    In-memory event bus for testing

    Tracks all published events and allows inspection
    """

    def __init__(self):
        self.events: List = []

    async def publish(self, event) -> None:
        """Publish an event"""
        self.events.append(event)

    def get_events(self) -> List:
        """Get all events"""
        return self.events

    def get_events_of_type(self, event_type):
        """Get events of specific type"""
        return [e for e in self.events if isinstance(e, event_type)]

    def clear(self) -> None:
        """Clear all events"""
        self.events = []

    def __len__(self) -> int:
        return len(self.events)


# ============================================================================
# MOCK BOOK REPOSITORY
# ============================================================================

class MockBookRepository:
    """
    In-memory Book repository with business rule enforcement

    Implements all BookRepository interface methods:
    - save(book)
    - get_by_id(book_id)
    - list_by_bookshelf(bookshelf_id)
    - get_deleted_books(bookshelf_id)
    - list_paginated(bookshelf_id, offset, limit)
    - get_by_library_id(library_id)
    - exists_by_id(book_id)
    - delete(book_id)

    Business Rules Enforcement:
    - RULE-009: Unlimited books per bookshelf
    - RULE-010: Every book must have bookshelf_id
    - RULE-011: Books can transfer between shelves
    - RULE-012: Soft delete via is_deleted flag
    - RULE-013: Restoration from Basement
    """

    def __init__(self):
        self._books: Dict[str, Book] = {}  # book_id → Book
        self._bookshelf_books: Dict[str, List[str]] = {}  # bookshelf_id → [book_ids]
        self._library_books: Dict[str, List[str]] = {}  # library_id → [book_ids]

    async def save(self, book: Book) -> Book:
        """
        Save or update book

        Enforces RULE-010: Book must have bookshelf_id
        Enforces RULE-009: Unlimited books allowed
        """
        if not book.bookshelf_id:
            raise BookOperationError("Book must have bookshelf_id (RULE-010)")

        if not book.library_id:
            raise BookOperationError("Book must have library_id")

        # Store book
        self._books[book.id] = book

        # Track by bookshelf (RULE-009: Unlimited creation)
        if book.bookshelf_id not in self._bookshelf_books:
            self._bookshelf_books[book.bookshelf_id] = []
        if book.id not in self._bookshelf_books[book.bookshelf_id]:
            self._bookshelf_books[book.bookshelf_id].append(book.id)

        # Track by library
        if book.library_id not in self._library_books:
            self._library_books[book.library_id] = []
        if book.id not in self._library_books[book.library_id]:
            self._library_books[book.library_id].append(book.id)

        return book

    async def get_by_id(self, book_id) -> Book:
        """
        Get book by ID

        Returns both active and deleted books
        """
        book = self._books.get(book_id)
        if not book:
            raise BookNotFoundError(f"Book {book_id} not found")
        return book

    async def list_by_bookshelf(self, bookshelf_id) -> List[Book]:
        """
        List active books in bookshelf

        Enforces RULE-012: Excludes soft-deleted books (is_deleted=True)
        """
        book_ids = self._bookshelf_books.get(bookshelf_id, [])
        active_books = [
            self._books[bid] for bid in book_ids
            if bid in self._books and not self._books[bid].is_deleted
        ]
        return active_books

    async def get_deleted_books(self, bookshelf_id) -> List[Book]:
        """
        Get books in Basement for a bookshelf

        Enforces RULE-012: Returns only is_deleted=True books
        """
        book_ids = self._bookshelf_books.get(bookshelf_id, [])
        deleted_books = [
            self._books[bid] for bid in book_ids
            if bid in self._books and self._books[bid].is_deleted
        ]
        return deleted_books

    async def list_paginated(self, bookshelf_id, offset=0, limit=10) -> tuple[List[Book], int]:
        """
        List active books with pagination

        Returns (paginated_books, total_count)
        """
        books = await self.list_by_bookshelf(bookshelf_id)
        total = len(books)
        paginated = books[offset:offset + limit]
        return paginated, total

    async def get_by_library_id(self, library_id) -> List[Book]:
        """
        Get all books in library (cross-bookshelf query)

        Enforces RULE-011: Returns books from all shelves in library
        """
        book_ids = self._library_books.get(library_id, [])
        return [self._books[bid] for bid in book_ids if bid in self._books]

    async def exists_by_id(self, book_id) -> bool:
        """
        Check if book exists

        Optimization method: returns bool instead of raising exception
        """
        return book_id in self._books

    async def delete(self, book_id) -> None:
        """
        Hard delete book from repository

        Note: Used rarely. Soft delete uses is_deleted flag.
        """
        if book_id in self._books:
            del self._books[book_id]

    # Test utilities
    def get_all_books(self) -> List[Book]:
        """Get all books (for testing)"""
        return list(self._books.values())

    def clear(self) -> None:
        """Clear all books (for testing)"""
        self._books.clear()
        self._bookshelf_books.clear()
        self._library_books.clear()

    def get_book_count(self) -> int:
        """Get total book count (for testing)"""
        return len(self._books)


# ============================================================================
# MOCK BOOKSHELF REPOSITORY (For Cross-Module Testing)
# ============================================================================

class MockBookshelfRepository:
    """
    In-memory Bookshelf repository for cross-module integration testing

    Used to validate that books properly reference bookshelves
    """

    def __init__(self):
        self._bookshelves = {}

    async def get_by_id(self, bookshelf_id):
        """Get bookshelf by ID"""
        bookshelf = self._bookshelves.get(bookshelf_id)
        if not bookshelf:
            from modules.bookshelf.exceptions import BookshelfNotFoundError
            raise BookshelfNotFoundError(f"Bookshelf {bookshelf_id} not found")
        return bookshelf

    async def save(self, bookshelf) -> None:
        """Save bookshelf"""
        self._bookshelves[bookshelf.id] = bookshelf

    def add_bookshelf(self, bookshelf_id) -> None:
        """Add bookshelf for testing"""
        self._bookshelves[bookshelf_id] = {'id': bookshelf_id}


# ============================================================================
# MOCK LIBRARY REPOSITORY (For Cross-Module Testing)
# ============================================================================

class MockLibraryRepository:
    """
    In-memory Library repository for cross-module integration testing

    Used to validate that books properly reference libraries
    """

    def __init__(self):
        self._libraries = {}

    async def get_by_id(self, library_id):
        """Get library by ID"""
        library = self._libraries.get(library_id)
        if not library:
            from modules.library.exceptions import LibraryNotFoundError
            raise LibraryNotFoundError(f"Library {library_id} not found")
        return library

    async def save(self, library) -> None:
        """Save library"""
        self._libraries[library.id] = library

    def add_library(self, library_id) -> None:
        """Add library for testing"""
        self._libraries[library_id] = {'id': library_id}


# ============================================================================
# PYTEST FIXTURES - Repositories
# ============================================================================

@pytest.fixture
def book_repository():
    """Provide MockBookRepository fixture"""
    repo = MockBookRepository()
    yield repo
    repo.clear()  # Cleanup after each test


@pytest.fixture
def bookshelf_repository():
    """Provide MockBookshelfRepository fixture"""
    return MockBookshelfRepository()


@pytest.fixture
def library_repository():
    """Provide MockLibraryRepository fixture"""
    return MockLibraryRepository()


# ============================================================================
# PYTEST FIXTURES - Event Bus
# ============================================================================

@pytest.fixture
def event_bus():
    """Provide MockEventBus fixture"""
    bus = MockEventBus()
    yield bus
    bus.clear()  # Cleanup after each test


# ============================================================================
# PYTEST FIXTURES - IDs
# ============================================================================

@pytest.fixture
def bookshelf_id():
    """Generate bookshelf ID"""
    return uuid4()


@pytest.fixture
def library_id():
    """Generate library ID"""
    return uuid4()


@pytest.fixture
def basement_shelf_id():
    """Generate basement shelf ID (virtual container for deleted books)"""
    return uuid4()


@pytest.fixture
def user_id():
    """Generate user ID"""
    return uuid4()


# ============================================================================
# PYTEST FIXTURES - Test Data Factories
# ============================================================================

@pytest.fixture
def create_book_factory():
    """Factory for creating test books"""
    def _create_book(
        book_id=None,
        bookshelf_id=None,
        library_id=None,
        title="Test Book",
        summary=None,
        is_deleted=False,
    ):
        return Book(
            book_id=book_id or uuid4(),
            bookshelf_id=bookshelf_id or uuid4(),
            library_id=library_id or uuid4(),
            title=BookTitle(value=title),
            summary=BookSummary(value=summary) if summary else None,
            is_deleted=is_deleted,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    return _create_book


@pytest.fixture
def create_deleted_book_factory():
    """Factory for creating deleted test books"""
    def _create_deleted_book(
        book_id=None,
        basement_shelf_id=None,
        library_id=None,
        title="Deleted Book",
    ):
        return Book(
            book_id=book_id or uuid4(),
            bookshelf_id=basement_shelf_id or uuid4(),
            library_id=library_id or uuid4(),
            title=BookTitle(value=title),
            summary=None,
            is_deleted=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    return _create_deleted_book


# ============================================================================
# PYTEST FIXTURES - Async Setup/Teardown
# ============================================================================

@pytest.fixture
async def async_cleanup():
    """Provide async cleanup context"""
    resources = []
    yield resources
    # Cleanup
    for resource in resources:
        if hasattr(resource, 'close'):
            await resource.close()


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
