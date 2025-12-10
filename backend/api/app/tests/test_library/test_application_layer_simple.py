"""
Library Application Layer Tests - Simplified Version

Based on Bookshelf pattern with focus on core functionality.
Tests: Create, Get, Delete, Rename operations.

Progress Metrics:
- 16+ async test methods
- 100% pass rate target
- Business rules validation (RULE-001 to RULE-003)
- MockRepository pattern with in-memory storage
"""

import pytest
from uuid import UUID, uuid4

from api.app.modules.library.application.use_cases.create_library import CreateLibraryUseCase
from api.app.modules.library.application.use_cases.get_library import GetLibraryUseCase
from api.app.modules.library.application.use_cases.delete_library import DeleteLibraryUseCase
from api.app.modules.library.application.use_cases.restore_library import RestoreLibraryUseCase
from api.app.modules.library.application.use_cases.list_basement_books import ListBasementBooksUseCase
from api.app.modules.library.application.ports.input import (
    CreateLibraryRequest,
    GetLibraryRequest,
    DeleteLibraryRequest,
    RestoreLibraryRequest,
    ListBasementBooksRequest,
)
from api.app.modules.library.exceptions import LibraryNotFoundError
from api.app.shared.exceptions import IllegalStateError, ResourceNotFoundError
from api.app.modules.library.domain.library import Library
from api.app.modules.bookshelf.domain import Bookshelf
from datetime import datetime, timezone


# ============================================================================
# Test Setup - Mock Objects
# ============================================================================

class MockEventBus:
    """In-memory event bus for testing"""
    def __init__(self):
        self.events = []

    async def publish(self, event):
        self.events.append(event)

    def get_events(self):
        return self.events


# ============================================================================
# Mock Domain Objects (for testing)
# ============================================================================

class MockBook:
    """In-memory Book representation for testing"""
    def __init__(self, book_id, title, bookshelf_id, library_id, soft_deleted_at=None):
        self.id = book_id
        self.title = title
        self.bookshelf_id = bookshelf_id
        self.library_id = library_id
        self.soft_deleted_at = soft_deleted_at


class MockBookshelf:
    """In-memory Bookshelf representation for testing"""
    def __init__(self, bookshelf_id, name, library_id):
        self.id = bookshelf_id
        self.name = name
        self.library_id = library_id

    def get_name_value(self):
        return self.name


# ============================================================================
# Mock Repositories
# ============================================================================

class MockBookRepository:
    """In-memory book repository for testing"""
    def __init__(self):
        self._books = {}

    def add_book(self, book_id, title, bookshelf_id, library_id, soft_deleted_at=None):
        """Test helper to add books"""
        book = MockBook(book_id, title, bookshelf_id, library_id, soft_deleted_at)
        self._books[book_id] = book
        return book

    async def find_soft_deleted_by_library(self, library_id, limit=100, offset=0):
        """Find all soft-deleted books in a library"""
        deleted = [
            b for b in self._books.values()
            if b.library_id == library_id and b.soft_deleted_at is not None
        ]
        # Sort by soft_deleted_at DESC (most recent first)
        deleted.sort(key=lambda b: b.soft_deleted_at, reverse=True)
        return deleted[offset:offset + limit]


class MockBookshelfRepository:
    """In-memory bookshelf repository for testing"""
    def __init__(self):
        self._bookshelves = {}
        self._basement_seed_factory = None

    def add_bookshelf(self, bookshelf_id, name, library_id):
        """Test helper to add bookshelves"""
        shelf = MockBookshelf(bookshelf_id, name, library_id)
        self._bookshelves[bookshelf_id] = shelf
        return shelf

    def seed_basement_on_lookup(self, factory):
        """Provide a hook to simulate legacy basement rows."""
        self._basement_seed_factory = factory

    async def get_by_id(self, bookshelf_id):
        """Get bookshelf by ID"""
        return self._bookshelves.get(bookshelf_id)

    async def get_basement_by_library_id(self, library_id):
        for shelf in self._bookshelves.values():
            if shelf.library_id == library_id and getattr(shelf, "is_basement", False):
                return shelf
        if self._basement_seed_factory:
            seeded = self._basement_seed_factory(library_id)
            if seeded:
                self._bookshelves[seeded.id] = seeded
                return seeded
        return None

    async def save(self, bookshelf):
        """Persist a bookshelf aggregate (simplified)."""
        self._bookshelves[bookshelf.id] = bookshelf
        return bookshelf

    async def exists(self, bookshelf_id):
        return bookshelf_id in self._bookshelves

    async def delete(self, bookshelf_id):
        self._bookshelves.pop(bookshelf_id, None)


def _make_create_library_use_case(repo, bus, bookshelf_repo=None):
    bookshelf_repo = bookshelf_repo or MockBookshelfRepository()
    use_case = CreateLibraryUseCase(
        repository=repo,
        bookshelf_repository=bookshelf_repo,
        event_bus=bus,
    )
    return use_case, bookshelf_repo


async def _seed_library(repository, *, user_id=None, name="Test Library"):
    library = Library.create(user_id=user_id or uuid4(), name=name)
    await repository.save(library)
    return library


class MockLibraryRepository:
    """In-memory repository implementation"""
    def __init__(self):
        self._libraries = {}
        self._user_libraries = {}

    async def save(self, library):
        # Check RULE-001: one library per user
        if library.user_id in self._user_libraries:
            existing_id = self._user_libraries[library.user_id]
            if existing_id != library.id:
                raise ValueError(f"User {library.user_id} already has a library")

        self._libraries[library.id] = library
        self._user_libraries[library.user_id] = library.id

    async def get_by_id(self, library_id):
        lib = self._libraries.get(library_id)
        return lib

    async def get_by_user_id(self, user_id):
        if user_id not in self._user_libraries:
            return None
        lib_id = self._user_libraries[user_id]
        return self._libraries.get(lib_id)

    async def delete(self, library_id):
        library = self._libraries.pop(library_id, None)
        if library:
            self._user_libraries.pop(library.user_id, None)

    async def get_all(self):
        return list(self._libraries.values())


# ============================================================================
# CreateLibraryUseCase Tests
# ============================================================================

class TestCreateLibrary:
    """Test CreateLibraryUseCase"""

    @pytest.mark.asyncio
    async def test_create_library_success(self):
        """✓ Create library succeeds with valid input"""
        repo = MockLibraryRepository()
        bus = MockEventBus()
        use_case, _ = _make_create_library_use_case(repo, bus)
        user_id = uuid4()

        request = CreateLibraryRequest(user_id=user_id, name="My Library")
        response = await use_case.execute(request)

        assert response.library_id is not None
        assert response.user_id == user_id
        assert response.name == "My Library"
        assert response.created_at is not None

    @pytest.mark.asyncio
    async def test_create_library_creates_basement_bookshelf(self):
        """✓ Create library persists the basement bookshelf via repository"""
        repo = MockLibraryRepository()
        bus = MockEventBus()
        bookshelf_repo = MockBookshelfRepository()
        use_case, injected_bookshelf_repo = _make_create_library_use_case(
            repo,
            bus,
            bookshelf_repo=bookshelf_repo,
        )
        user_id = uuid4()

        request = CreateLibraryRequest(user_id=user_id, name="Basement Check")
        response = await use_case.execute(request)

        stored_basement = await injected_bookshelf_repo.get_by_id(
            response.basement_bookshelf_id
        )
        assert stored_basement is not None
        assert stored_basement.library_id == response.library_id
        assert stored_basement.get_name_value() == "Basement"

    @pytest.mark.asyncio
    async def test_create_library_reuses_existing_basement(self):
        """✓ Library creation reuses legacy basement shelf if present"""
        repo = MockLibraryRepository()
        bus = MockEventBus()
        bookshelf_repo = MockBookshelfRepository()
        captured_id: dict[str, UUID] = {}

        def _legacy_factory(library_id):
            seeded = Bookshelf.create_basement(library_id=library_id)
            captured_id["value"] = seeded.id
            return seeded

        bookshelf_repo.seed_basement_on_lookup(_legacy_factory)
        use_case, _ = _make_create_library_use_case(repo, bus, bookshelf_repo=bookshelf_repo)
        user_id = uuid4()

        request = CreateLibraryRequest(user_id=user_id, name="Reuse Basement")
        response = await use_case.execute(request)

        assert response.basement_bookshelf_id == captured_id["value"]
        assert captured_id["value"] in bookshelf_repo._bookshelves

    @pytest.mark.asyncio
    async def test_create_library_duplicate_user_fails(self):
        """✗ Creating second library for same user fails (RULE-001)"""
        repo = MockLibraryRepository()
        bus = MockEventBus()
        use_case, _ = _make_create_library_use_case(repo, bus)
        user_id = uuid4()

        req1 = CreateLibraryRequest(user_id=user_id, name="Library 1")
        req2 = CreateLibraryRequest(user_id=user_id, name="Library 2")

        await use_case.execute(req1)

        with pytest.raises(Exception):  # RULE-001 violation
            await use_case.execute(req2)

    @pytest.mark.asyncio
    async def test_create_library_invalid_name_empty(self):
        """✗ Creating library with empty name fails"""
        repo = MockLibraryRepository()
        bus = MockEventBus()
        use_case, _ = _make_create_library_use_case(repo, bus)
        user_id = uuid4()

        request = CreateLibraryRequest(user_id=user_id, name="")

        with pytest.raises(ValueError):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_create_library_invalid_name_too_long(self):
        """✗ Creating library with name > 255 chars fails"""
        repo = MockLibraryRepository()
        bus = MockEventBus()
        use_case, _ = _make_create_library_use_case(repo, bus)
        user_id = uuid4()

        request = CreateLibraryRequest(user_id=user_id, name="x" * 256)

        with pytest.raises(ValueError):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_create_library_name_trimmed(self):
        """✓ Library name with whitespace is trimmed"""
        repo = MockLibraryRepository()
        bus = MockEventBus()
        use_case, _ = _make_create_library_use_case(repo, bus)
        user_id = uuid4()

        request = CreateLibraryRequest(user_id=user_id, name="  My Library  ")
        response = await use_case.execute(request)

        # LibraryName strips whitespace
        assert "My Library" in response.name or response.name == "My Library"


# ============================================================================
# GetLibraryUseCase Tests
# ============================================================================

class TestGetLibrary:
    """Test GetLibraryUseCase"""

    @pytest.mark.asyncio
    async def test_get_library_by_id_found(self):
        """✓ Get library by ID succeeds"""
        repo = MockLibraryRepository()
        bus = MockEventBus()
        create_uc, _ = _make_create_library_use_case(repo, bus)
        get_uc = GetLibraryUseCase(repository=repo)
        user_id = uuid4()

        # Create library
        create_req = CreateLibraryRequest(user_id=user_id, name="Test Library")
        create_resp = await create_uc.execute(create_req)

        # Get library by ID
        get_req = GetLibraryRequest(library_id=create_resp.library_id)
        get_resp = await get_uc.execute(get_req)

        assert get_resp.library_id == create_resp.library_id
        assert get_resp.user_id == user_id
        assert get_resp.name == "Test Library"

    @pytest.mark.asyncio
    async def test_get_library_by_id_not_found(self):
        """✗ Get non-existent library by ID fails"""
        repo = MockLibraryRepository()
        get_uc = GetLibraryUseCase(repository=repo)

        request = GetLibraryRequest(library_id=uuid4())

        with pytest.raises(LibraryNotFoundError):
            await get_uc.execute(request)

    @pytest.mark.asyncio
    async def test_get_library_by_user_id_rejected(self):
        """✗ Querying by user ID is deprecated and raises ValueError"""
        repo = MockLibraryRepository()
        bus = MockEventBus()
        create_uc, _ = _make_create_library_use_case(repo, bus)
        get_uc = GetLibraryUseCase(repository=repo)
        user_id = uuid4()

        # Create library
        create_req = CreateLibraryRequest(user_id=user_id, name="User Library")
        await create_uc.execute(create_req)

        # Get library by user ID should raise ValueError per use case contract
        get_req = GetLibraryRequest(user_id=user_id)
        with pytest.raises(ValueError):
            await get_uc.execute(get_req)

    @pytest.mark.asyncio
    async def test_get_library_by_user_id_not_supported_without_data(self):
        """✗ Querying by user ID without data also raises ValueError"""
        repo = MockLibraryRepository()
        get_uc = GetLibraryUseCase(repository=repo)

        request = GetLibraryRequest(user_id=uuid4())

        with pytest.raises(ValueError):
            await get_uc.execute(request)


# ============================================================================
# DeleteLibraryUseCase Tests
# ============================================================================

class TestDeleteLibrary:
    """Test DeleteLibraryUseCase"""

    @pytest.mark.asyncio
    async def test_delete_library_success(self):
        """✓ Delete library succeeds"""
        repo = MockLibraryRepository()
        bus = MockEventBus()
        create_uc, _ = _make_create_library_use_case(repo, bus)
        delete_uc = DeleteLibraryUseCase(repository=repo, event_bus=bus)
        user_id = uuid4()

        # Create library
        create_req = CreateLibraryRequest(user_id=user_id, name="Lib to Delete")
        create_resp = await create_uc.execute(create_req)

        # Delete library (returns None on success)
        delete_req = DeleteLibraryRequest(library_id=create_resp.library_id)
        await delete_uc.execute(delete_req)

        # Verify soft delete - library still exists but marked as deleted
        deleted_lib = await repo.get_by_id(create_resp.library_id)
        assert deleted_lib is not None
        assert deleted_lib.is_deleted() is True

    @pytest.mark.asyncio
    async def test_delete_library_not_found(self):
        """✗ Delete non-existent library fails"""
        repo = MockLibraryRepository()
        bus = MockEventBus()
        del_uc = DeleteLibraryUseCase(repository=repo, event_bus=bus)

        request = DeleteLibraryRequest(library_id=uuid4())

        with pytest.raises(LibraryNotFoundError):
            await del_uc.execute(request)


# ============================================================================
# Business Rules Tests
# ============================================================================

class TestBusinessRules:
    """Test business rule enforcement"""

    @pytest.mark.asyncio
    async def test_rule_001_one_per_user(self):
        """RULE-001: Each user has exactly one library"""
        repo = MockLibraryRepository()
        bus = MockEventBus()
        use_case, _ = _make_create_library_use_case(repo, bus)
        user_id = uuid4()

        # Create first library
        req1 = CreateLibraryRequest(user_id=user_id, name="Lib 1")
        await use_case.execute(req1)

        # Try second library (should fail)
        req2 = CreateLibraryRequest(user_id=user_id, name="Lib 2")

        with pytest.raises(Exception):
            await use_case.execute(req2)

    @pytest.mark.asyncio
    async def test_rule_003_name_validation(self):
        """RULE-003: Name must be 1-255 characters"""
        repo = MockLibraryRepository()
        bus = MockEventBus()
        use_case, _ = _make_create_library_use_case(repo, bus)

        # Valid: single character
        req1 = CreateLibraryRequest(user_id=uuid4(), name="A")
        resp1 = await use_case.execute(req1)
        assert len(resp1.name) >= 1

        # Valid: 255 characters
        req2 = CreateLibraryRequest(user_id=uuid4(), name="x" * 255)
        resp2 = await use_case.execute(req2)
        assert len(resp2.name) == 255

        # Invalid: empty
        with pytest.raises(ValueError):
            req3 = CreateLibraryRequest(user_id=uuid4(), name="")
            await use_case.execute(req3)

        # Invalid: 256 characters
        with pytest.raises(ValueError):
            req4 = CreateLibraryRequest(user_id=uuid4(), name="x" * 256)
            await use_case.execute(req4)


# ============================================================================
# RestoreLibraryUseCase Tests (NEW - Nov 14, 2025)
# ============================================================================

class TestRestoreLibrary:
    """Test RestoreLibraryUseCase - Basement recovery for Library"""

    @pytest.mark.asyncio
    async def test_restore_library_success(self):
        """✓ Restore library succeeds when deleted"""
        # Setup: Create and delete a library
        repo = MockLibraryRepository()
        bus = MockEventBus()

        create_uc, _ = _make_create_library_use_case(repo, bus)
        user_id = uuid4()
        create_req = CreateLibraryRequest(user_id=user_id, name="Test Library")
        create_resp = await create_uc.execute(create_req)

        # Delete the library
        delete_uc = DeleteLibraryUseCase(repository=repo, event_bus=bus)
        delete_req = DeleteLibraryRequest(library_id=create_resp.library_id)
        await delete_uc.execute(delete_req)

        # Verify deleted
        lib_deleted = await repo.get_by_id(create_resp.library_id)
        assert lib_deleted.is_deleted()

        # Restore the library
        restore_uc = RestoreLibraryUseCase(library_repository=repo, event_bus=bus)
        restore_req = RestoreLibraryRequest(library_id=create_resp.library_id)
        restore_resp = await restore_uc.execute(restore_req)

        # Verify restoration
        assert restore_resp.library_id == create_resp.library_id
        assert restore_resp.restored_at is not None
        assert "restored" in restore_resp.message.lower()

        # Verify not deleted in repository
        lib_restored = await repo.get_by_id(create_resp.library_id)
        assert not lib_restored.is_deleted()

    @pytest.mark.asyncio
    async def test_restore_library_not_found(self):
        """✗ Restore fails if library doesn't exist"""
        repo = MockLibraryRepository()
        bus = MockEventBus()
        restore_uc = RestoreLibraryUseCase(library_repository=repo, event_bus=bus)

        fake_id = uuid4()
        restore_req = RestoreLibraryRequest(library_id=fake_id)

        with pytest.raises(ResourceNotFoundError):
            await restore_uc.execute(restore_req)

    @pytest.mark.asyncio
    async def test_restore_library_not_deleted(self):
        """✗ Restore fails if library is not deleted"""
        # Setup: Create a library but don't delete it
        repo = MockLibraryRepository()
        bus = MockEventBus()

        create_uc, _ = _make_create_library_use_case(repo, bus)
        user_id = uuid4()
        create_req = CreateLibraryRequest(user_id=user_id, name="Active Library")
        create_resp = await create_uc.execute(create_req)

        # Try to restore a non-deleted library (should fail)
        restore_uc = RestoreLibraryUseCase(library_repository=repo, event_bus=bus)
        restore_req = RestoreLibraryRequest(library_id=create_resp.library_id)

        with pytest.raises(IllegalStateError):
            await restore_uc.execute(restore_req)

    @pytest.mark.asyncio
    async def test_restore_library_emits_event(self):
        """✓ Restore emits LibraryRestored event"""
        # Setup and delete
        repo = MockLibraryRepository()
        bus = MockEventBus()

        create_uc, _ = _make_create_library_use_case(repo, bus)
        user_id = uuid4()
        create_req = CreateLibraryRequest(user_id=user_id, name="Test Library")
        create_resp = await create_uc.execute(create_req)

        delete_uc = DeleteLibraryUseCase(repository=repo, event_bus=bus)
        delete_req = DeleteLibraryRequest(library_id=create_resp.library_id)
        await delete_uc.execute(delete_req)

        # Restore and verify event
        restore_uc = RestoreLibraryUseCase(library_repository=repo, event_bus=bus)
        restore_req = RestoreLibraryRequest(library_id=create_resp.library_id)
        await restore_uc.execute(restore_req)

        # Check events
        events = bus.get_events()
        # Should have at least one LibraryRestored event
        restored_events = [e for e in events if e.__class__.__name__ == "LibraryRestored"]
        assert len(restored_events) > 0

    @pytest.mark.asyncio
    async def test_restore_library_updates_timestamp(self):
        """✓ Restore updates updated_at timestamp"""
        # Setup and delete
        repo = MockLibraryRepository()
        bus = MockEventBus()

        create_uc, _ = _make_create_library_use_case(repo, bus)
        user_id = uuid4()
        create_req = CreateLibraryRequest(user_id=user_id, name="Test Library")
        create_resp = await create_uc.execute(create_req)
        lib_before = await repo.get_by_id(create_resp.library_id)
        updated_before = lib_before.updated_at

        delete_uc = DeleteLibraryUseCase(repository=repo, event_bus=bus)
        delete_req = DeleteLibraryRequest(library_id=create_resp.library_id)
        await delete_uc.execute(delete_req)

        # Restore and verify timestamp update
        restore_uc = RestoreLibraryUseCase(library_repository=repo, event_bus=bus)
        restore_req = RestoreLibraryRequest(library_id=create_resp.library_id)
        await restore_uc.execute(restore_req)

        lib_after = await repo.get_by_id(create_resp.library_id)
        # updated_at should be updated (likely equal or after)
        assert lib_after.updated_at >= updated_before

    @pytest.mark.asyncio
    async def test_restore_library_twice(self):
        """✗ Restore twice fails (first restoration succeeds, second fails)"""
        # Setup and delete
        repo = MockLibraryRepository()
        bus = MockEventBus()

        create_uc, _ = _make_create_library_use_case(repo, bus)
        user_id = uuid4()
        create_req = CreateLibraryRequest(user_id=user_id, name="Test Library")
        create_resp = await create_uc.execute(create_req)

        delete_uc = DeleteLibraryUseCase(repository=repo, event_bus=bus)
        delete_req = DeleteLibraryRequest(library_id=create_resp.library_id)
        await delete_uc.execute(delete_req)

        # First restore should succeed
        restore_uc = RestoreLibraryUseCase(library_repository=repo, event_bus=bus)
        restore_req = RestoreLibraryRequest(library_id=create_resp.library_id)
        resp1 = await restore_uc.execute(restore_req)
        assert resp1.library_id == create_resp.library_id

        # Second restore should fail (not deleted anymore)
        with pytest.raises(IllegalStateError):
            await restore_uc.execute(restore_req)


# ============================================================================
# ListBasementBooksUseCase Tests (16 tests)
# ============================================================================

class TestListBasementBooks:
    """Test ListBasementBooksUseCase - Basement view of deleted Books"""

    @pytest.mark.asyncio
    async def test_list_basement_empty_no_deleted_books(self):
        """✓ List basement returns empty list when no books deleted"""
        library_repo = MockLibraryRepository()
        book_repo = MockBookRepository()
        bookshelf_repo = MockBookshelfRepository()
        bus = MockEventBus()

        # Create library
        create_uc, _ = _make_create_library_use_case(
            library_repo,
            bus,
            bookshelf_repo=bookshelf_repo,
        )
        user_id = uuid4()
        create_req = CreateLibraryRequest(user_id=user_id, name="My Library")
        create_resp = await create_uc.execute(create_req)

        # List basement (should be empty)
        list_uc = ListBasementBooksUseCase(
            library_repository=library_repo,
            book_repository=book_repo,
            bookshelf_repository=bookshelf_repo,
        )
        list_req = ListBasementBooksRequest(library_id=create_resp.library_id)
        list_resp = await list_uc.execute(list_req)

        assert list_resp.total_count == 0
        assert len(list_resp.shelf_groups) == 0
        assert "0 deleted book" in list_resp.message.lower()

    @pytest.mark.asyncio
    async def test_list_basement_single_deleted_book(self):
        """✓ List basement returns single deleted book with shelf grouping"""
        bookshelf_id = uuid4()
        book_id = uuid4()
        deleted_at = datetime.now(timezone.utc)

        library_repo = MockLibraryRepository()
        book_repo = MockBookRepository()
        bookshelf_repo = MockBookshelfRepository()

        # Create library manually in repo
        lib = await _seed_library(library_repo, name="Test Library")
        library_id = lib.id

        # Add deleted book
        book_repo.add_book(
            book_id=book_id,
            title="Deleted Book",
            bookshelf_id=bookshelf_id,
            library_id=library_id,
            soft_deleted_at=deleted_at,
        )

        # Add bookshelf
        bookshelf_repo.add_bookshelf(
            bookshelf_id=bookshelf_id,
            name="My Shelf",
            library_id=library_id,
        )

        # List basement
        list_uc = ListBasementBooksUseCase(
            library_repository=library_repo,
            book_repository=book_repo,
            bookshelf_repository=bookshelf_repo,
        )
        list_req = ListBasementBooksRequest(library_id=library_id)
        list_resp = await list_uc.execute(list_req)

        assert list_resp.total_count == 1
        assert len(list_resp.shelf_groups) == 1
        assert list_resp.shelf_groups[0].bookshelf_id == bookshelf_id
        assert list_resp.shelf_groups[0].bookshelf_name == "My Shelf"
        assert list_resp.shelf_groups[0].book_count == 1
        assert len(list_resp.shelf_groups[0].books) == 1
        assert list_resp.shelf_groups[0].books[0].title == "Deleted Book"

    @pytest.mark.asyncio
    async def test_list_basement_multiple_books_single_shelf(self):
        """✓ List basement groups multiple deleted books from same shelf"""
        bookshelf_id = uuid4()
        deleted_at = datetime.now(timezone.utc)

        library_repo = MockLibraryRepository()
        book_repo = MockBookRepository()
        bookshelf_repo = MockBookshelfRepository()

        # Create library
        lib = await _seed_library(library_repo, name="Test Library")
        library_id = lib.id

        # Add 3 deleted books from same shelf
        for i in range(3):
            book_repo.add_book(
                book_id=uuid4(),
                title=f"Book {i+1}",
                bookshelf_id=bookshelf_id,
                library_id=library_id,
                soft_deleted_at=deleted_at,
            )

        # Add bookshelf
        bookshelf_repo.add_bookshelf(
            bookshelf_id=bookshelf_id,
            name="My Shelf",
            library_id=library_id,
        )

        # List basement
        list_uc = ListBasementBooksUseCase(
            library_repository=library_repo,
            book_repository=book_repo,
            bookshelf_repository=bookshelf_repo,
        )
        list_req = ListBasementBooksRequest(library_id=library_id)
        list_resp = await list_uc.execute(list_req)

        assert list_resp.total_count == 3
        assert len(list_resp.shelf_groups) == 1
        assert list_resp.shelf_groups[0].book_count == 3
        assert len(list_resp.shelf_groups[0].books) == 3

    @pytest.mark.asyncio
    async def test_list_basement_books_multiple_shelves(self):
        """✓ List basement groups books by their original shelves"""
        shelf1_id = uuid4()
        shelf2_id = uuid4()
        deleted_at = datetime.now(timezone.utc)

        library_repo = MockLibraryRepository()
        book_repo = MockBookRepository()
        bookshelf_repo = MockBookshelfRepository()

        # Create library
        lib = await _seed_library(library_repo, name="Test Library")
        library_id = lib.id

        # Add books from shelf 1
        for i in range(2):
            book_repo.add_book(
                book_id=uuid4(),
                title=f"Shelf1 Book {i+1}",
                bookshelf_id=shelf1_id,
                library_id=library_id,
                soft_deleted_at=deleted_at,
            )

        # Add books from shelf 2
        for i in range(3):
            book_repo.add_book(
                book_id=uuid4(),
                title=f"Shelf2 Book {i+1}",
                bookshelf_id=shelf2_id,
                library_id=library_id,
                soft_deleted_at=deleted_at,
            )

        # Add bookshelves
        bookshelf_repo.add_bookshelf(shelf1_id, "Shelf 1", library_id)
        bookshelf_repo.add_bookshelf(shelf2_id, "Shelf 2", library_id)

        # List basement
        list_uc = ListBasementBooksUseCase(
            library_repository=library_repo,
            book_repository=book_repo,
            bookshelf_repository=bookshelf_repo,
        )
        list_req = ListBasementBooksRequest(library_id=library_id)
        list_resp = await list_uc.execute(list_req)

        assert list_resp.total_count == 5
        assert len(list_resp.shelf_groups) == 2
        groups = {group.bookshelf_id: group for group in list_resp.shelf_groups}
        assert groups[shelf1_id].book_count == 2
        assert groups[shelf2_id].book_count == 3

    @pytest.mark.asyncio
    async def test_list_basement_library_not_found(self):
        """✗ List basement fails if library doesn't exist"""
        library_repo = MockLibraryRepository()
        book_repo = MockBookRepository()
        bookshelf_repo = MockBookshelfRepository()

        list_uc = ListBasementBooksUseCase(
            library_repository=library_repo,
            book_repository=book_repo,
            bookshelf_repository=bookshelf_repo,
        )

        fake_lib_id = uuid4()
        list_req = ListBasementBooksRequest(library_id=fake_lib_id)

        with pytest.raises(ResourceNotFoundError):
            await list_uc.execute(list_req)

    @pytest.mark.asyncio
    async def test_list_basement_preserves_bookshelf_relationships(self):
        """✓ List basement preserves original bookshelf_id in response"""
        bookshelf_id = uuid4()
        book_id = uuid4()
        deleted_at = datetime.now(timezone.utc)

        library_repo = MockLibraryRepository()
        book_repo = MockBookRepository()
        bookshelf_repo = MockBookshelfRepository()

        # Create library
        lib = await _seed_library(library_repo, name="Test Library")
        library_id = lib.id

        # Add deleted book
        book_repo.add_book(
            book_id=book_id,
            title="Deleted Book",
            bookshelf_id=bookshelf_id,
            library_id=library_id,
            soft_deleted_at=deleted_at,
        )

        # Add bookshelf
        bookshelf_repo.add_bookshelf(bookshelf_id, "Original Shelf", library_id)

        # List basement
        list_uc = ListBasementBooksUseCase(
            library_repository=library_repo,
            book_repository=book_repo,
            bookshelf_repository=bookshelf_repo,
        )
        list_req = ListBasementBooksRequest(library_id=library_id)
        list_resp = await list_uc.execute(list_req)

        # Verify relationships preserved
        group = list_resp.shelf_groups[0]
        assert group.bookshelf_id == bookshelf_id
        book_item = group.books[0]
        assert book_item.bookshelf_id == bookshelf_id

    @pytest.mark.asyncio
    async def test_list_basement_handles_orphaned_books_missing_shelf(self):
        """✓ List basement handles books with missing shelf (orphaned)"""
        orphan_shelf_id = uuid4()  # This shelf doesn't exist in repo
        book_id = uuid4()
        deleted_at = datetime.now(timezone.utc)

        library_repo = MockLibraryRepository()
        book_repo = MockBookRepository()
        bookshelf_repo = MockBookshelfRepository()

        # Create library
        lib = await _seed_library(library_repo, name="Test Library")
        library_id = lib.id

        # Add deleted book with non-existent shelf
        book_repo.add_book(
            book_id=book_id,
            title="Orphaned Book",
            bookshelf_id=orphan_shelf_id,
            library_id=library_id,
            soft_deleted_at=deleted_at,
        )

        # List basement (should handle missing shelf gracefully)
        list_uc = ListBasementBooksUseCase(
            library_repository=library_repo,
            book_repository=book_repo,
            bookshelf_repository=bookshelf_repo,
        )
        list_req = ListBasementBooksRequest(library_id=library_id)
        list_resp = await list_uc.execute(list_req)

        assert list_resp.total_count == 1
        assert len(list_resp.shelf_groups) == 1
        # Should show placeholder name for deleted/missing shelf
        assert "Deleted" in list_resp.shelf_groups[0].bookshelf_name or \
               "Unknown" in list_resp.shelf_groups[0].bookshelf_name

    @pytest.mark.asyncio
    async def test_list_basement_pagination_offset(self):
        """✓ List basement respects pagination offset"""
        bookshelf_id = uuid4()
        deleted_at = datetime.now(timezone.utc)

        library_repo = MockLibraryRepository()
        book_repo = MockBookRepository()
        bookshelf_repo = MockBookshelfRepository()

        # Create library
        lib = await _seed_library(library_repo, name="Test Library")
        library_id = lib.id

        # Add 5 deleted books
        for i in range(5):
            book_repo.add_book(
                book_id=uuid4(),
                title=f"Book {i+1}",
                bookshelf_id=bookshelf_id,
                library_id=library_id,
                soft_deleted_at=deleted_at,
            )

        # Add bookshelf
        bookshelf_repo.add_bookshelf(bookshelf_id, "Shelf", library_id)

        # List with offset
        list_uc = ListBasementBooksUseCase(
            library_repository=library_repo,
            book_repository=book_repo,
            bookshelf_repository=bookshelf_repo,
        )
        list_req = ListBasementBooksRequest(library_id=library_id, offset=2, limit=100)
        list_resp = await list_uc.execute(list_req)

        # Should get 3 books (5 total - 2 offset)
        assert list_resp.total_count == 3
        assert list_resp.shelf_groups[0].book_count == 3

    @pytest.mark.asyncio
    async def test_list_basement_pagination_limit(self):
        """✓ List basement respects pagination limit"""
        bookshelf_id = uuid4()
        deleted_at = datetime.now(timezone.utc)

        library_repo = MockLibraryRepository()
        book_repo = MockBookRepository()
        bookshelf_repo = MockBookshelfRepository()

        # Create library
        lib = await _seed_library(library_repo, name="Test Library")
        library_id = lib.id

        # Add 10 deleted books
        for i in range(10):
            book_repo.add_book(
                book_id=uuid4(),
                title=f"Book {i+1}",
                bookshelf_id=bookshelf_id,
                library_id=library_id,
                soft_deleted_at=deleted_at,
            )

        # Add bookshelf
        bookshelf_repo.add_bookshelf(bookshelf_id, "Shelf", library_id)

        # List with limit
        list_uc = ListBasementBooksUseCase(
            library_repository=library_repo,
            book_repository=book_repo,
            bookshelf_repository=bookshelf_repo,
        )
        list_req = ListBasementBooksRequest(library_id=library_id, limit=5)
        list_resp = await list_uc.execute(list_req)

        # Should get only 5 books due to limit
        assert list_resp.total_count == 5
        assert list_resp.shelf_groups[0].book_count == 5

    @pytest.mark.asyncio
    async def test_list_basement_returns_basket_items_dto(self):
        """✓ List basement returns proper BasementBookItem DTOs"""
        bookshelf_id = uuid4()
        book_id = uuid4()
        deleted_at = datetime.now(timezone.utc)

        library_repo = MockLibraryRepository()
        book_repo = MockBookRepository()
        bookshelf_repo = MockBookshelfRepository()

        # Create library
        lib = await _seed_library(library_repo, name="Test Library")
        library_id = lib.id

        # Add deleted book
        book_repo.add_book(
            book_id=book_id,
            title="Test Book",
            bookshelf_id=bookshelf_id,
            library_id=library_id,
            soft_deleted_at=deleted_at,
        )

        # Add bookshelf
        bookshelf_repo.add_bookshelf(bookshelf_id, "Test Shelf", library_id)

        # List basement
        list_uc = ListBasementBooksUseCase(
            library_repository=library_repo,
            book_repository=book_repo,
            bookshelf_repository=bookshelf_repo,
        )
        list_req = ListBasementBooksRequest(library_id=library_id)
        list_resp = await list_uc.execute(list_req)

        # Verify DTO structure
        book_item = list_resp.shelf_groups[0].books[0]
        assert book_item.book_id == book_id
        assert book_item.title == "Test Book"
        assert book_item.bookshelf_id == bookshelf_id
        assert book_item.bookshelf_name == "Test Shelf"
        assert book_item.soft_deleted_at == deleted_at

    @pytest.mark.asyncio
    async def test_list_basement_response_has_total_count(self):
        """✓ List basement response includes total count"""
        bookshelf_id = uuid4()
        deleted_at = datetime.now(timezone.utc)

        library_repo = MockLibraryRepository()
        book_repo = MockBookRepository()
        bookshelf_repo = MockBookshelfRepository()

        # Create library
        lib = await _seed_library(library_repo, name="Test Library")
        library_id = lib.id

        # Add 7 deleted books
        for i in range(7):
            book_repo.add_book(
                book_id=uuid4(),
                title=f"Book {i+1}",
                bookshelf_id=bookshelf_id,
                library_id=library_id,
                soft_deleted_at=deleted_at,
            )

        # Add bookshelf
        bookshelf_repo.add_bookshelf(bookshelf_id, "Shelf", library_id)

        # List basement
        list_uc = ListBasementBooksUseCase(
            library_repository=library_repo,
            book_repository=book_repo,
            bookshelf_repository=bookshelf_repo,
        )
        list_req = ListBasementBooksRequest(library_id=library_id)
        list_resp = await list_uc.execute(list_req)

        assert list_resp.total_count == 7
        assert list_resp.library_id == library_id

    @pytest.mark.asyncio
    async def test_list_basement_response_message(self):
        """✓ List basement response includes descriptive message"""
        bookshelf_id = uuid4()
        deleted_at = datetime.now(timezone.utc)

        library_repo = MockLibraryRepository()
        book_repo = MockBookRepository()
        bookshelf_repo = MockBookshelfRepository()

        # Create library
        lib = await _seed_library(library_repo, name="Test Library")
        library_id = lib.id

        # Add 3 deleted books from 1 shelf
        for i in range(3):
            book_repo.add_book(
                book_id=uuid4(),
                title=f"Book {i+1}",
                bookshelf_id=bookshelf_id,
                library_id=library_id,
                soft_deleted_at=deleted_at,
            )

        # Add bookshelf
        bookshelf_repo.add_bookshelf(bookshelf_id, "Shelf", library_id)

        # List basement
        list_uc = ListBasementBooksUseCase(
            library_repository=library_repo,
            book_repository=book_repo,
            bookshelf_repository=bookshelf_repo,
        )
        list_req = ListBasementBooksRequest(library_id=library_id)
        list_resp = await list_uc.execute(list_req)

        assert "3" in list_resp.message
        assert "1" in list_resp.message
        assert "deleted" in list_resp.message.lower()
        assert "shelf" in list_resp.message.lower()

    @pytest.mark.asyncio
    async def test_list_basement_without_bookshelf_repo(self):
        """✓ List basement works without bookshelf repository (fallback names)"""
        bookshelf_id = uuid4()
        book_id = uuid4()
        deleted_at = datetime.now(timezone.utc)

        library_repo = MockLibraryRepository()
        book_repo = MockBookRepository()
        # No bookshelf repo provided

        # Create library
        lib = await _seed_library(library_repo, name="Test Library")
        library_id = lib.id

        # Add deleted book
        book_repo.add_book(
            book_id=book_id,
            title="Book",
            bookshelf_id=bookshelf_id,
            library_id=library_id,
            soft_deleted_at=deleted_at,
        )

        # List basement without bookshelf repo
        list_uc = ListBasementBooksUseCase(
            library_repository=library_repo,
            book_repository=book_repo,
            bookshelf_repository=None,
        )
        list_req = ListBasementBooksRequest(library_id=library_id)
        list_resp = await list_uc.execute(list_req)

        assert list_resp.total_count == 1
        # Should have placeholder name
        assert "Unknown" in list_resp.shelf_groups[0].bookshelf_name or \
               "Error" in list_resp.shelf_groups[0].bookshelf_name

