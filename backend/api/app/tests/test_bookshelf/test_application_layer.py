"""
Test Suite: Bookshelf Application Layer - UseCase Tests

Tests for all 4 core UseCases:
- CreateBookshelfUseCase
- GetBookshelfUseCase
- DeleteBookshelfUseCase
- RenameBookshelfUseCase

Coverage: 16 test cases
- CreateBookshelf: 4 tests (normal + duplicate + validation + optional)
- GetBookshelf: 2 tests (found + not found)
- DeleteBookshelf: 3 tests (normal + basement + not found)
- RenameBookshelf: 4 tests (normal + duplicate + validation + not found)
- Repository Layer: 3 tests (CRUD operations)
"""

import pytest
from uuid import uuid4

from api.app.modules.bookshelf.application.use_cases.create_bookshelf import CreateBookshelfUseCase
from api.app.modules.bookshelf.application.use_cases.get_bookshelf import GetBookshelfUseCase
from api.app.modules.bookshelf.application.use_cases.delete_bookshelf import DeleteBookshelfUseCase
from api.app.modules.bookshelf.application.use_cases.rename_bookshelf import RenameBookshelfUseCase
from api.app.modules.bookshelf.application.ports.input import (
    CreateBookshelfRequest,
    GetBookshelfRequest,
    DeleteBookshelfRequest,
    RenameBookshelfRequest,
)
from api.app.modules.bookshelf.domain import BookshelfType, BookshelfStatus


# ============================================================================
# CreateBookshelfUseCase Tests (4 tests)
# ============================================================================

class TestCreateBookshelfUseCase:
    """Test CreateBookshelfUseCase - Create new bookshelf"""

    @pytest.mark.asyncio
    async def test_create_bookshelf_success(self, mock_repository, library_id):
        """✓ CreateBookshelfUseCase: Normal creation succeeds"""
        use_case = CreateBookshelfUseCase(mock_repository)
        request = CreateBookshelfRequest(
            library_id=library_id,
            name="My Bookshelf",
            description="A personal collection",
        )

        response = await use_case.execute(request)

        assert response.id is not None
        assert response.library_id == library_id
        assert response.name == "My Bookshelf"
        assert response.description == "A personal collection"
        assert response.bookshelf_type == "normal"
        assert response.status == "active"

    @pytest.mark.asyncio
    async def test_create_bookshelf_duplicate_name_fails(self, mock_repository, library_id):
        """✗ CreateBookshelfUseCase: Duplicate name per library fails (RULE-006)"""
        use_case = CreateBookshelfUseCase(mock_repository)
        request1 = CreateBookshelfRequest(
            library_id=library_id,
            name="Duplicate Name",
            description="First",
        )
        request2 = CreateBookshelfRequest(
            library_id=library_id,
            name="Duplicate Name",  # Same name
            description="Second",
        )

        # First creation succeeds
        await use_case.execute(request1)

        # Second creation fails
        with pytest.raises(ValueError, match="already exists"):
            await use_case.execute(request2)

    @pytest.mark.asyncio
    async def test_create_bookshelf_invalid_name_length_fails(self, mock_repository, library_id):
        """✗ CreateBookshelfUseCase: Invalid name length fails"""
        use_case = CreateBookshelfUseCase(mock_repository)

        # Too long (> 255 chars)
        request_too_long = CreateBookshelfRequest(
            library_id=library_id,
            name="A" * 256,
            description="Too long name",
        )

        with pytest.raises(ValueError):
            await use_case.execute(request_too_long)

    @pytest.mark.asyncio
    async def test_create_bookshelf_with_optional_description(self, mock_repository, library_id):
        """✓ CreateBookshelfUseCase: Optional description works"""
        use_case = CreateBookshelfUseCase(mock_repository)
        request = CreateBookshelfRequest(
            library_id=library_id,
            name="Bookshelf Without Description",
            description=None,  # Optional
        )

        response = await use_case.execute(request)

        assert response.name == "Bookshelf Without Description"
        assert response.description is None


# ============================================================================
# GetBookshelfUseCase Tests (2 tests)
# ============================================================================

class TestGetBookshelfUseCase:
    """Test GetBookshelfUseCase - Retrieve bookshelf by ID"""

    @pytest.mark.asyncio
    async def test_get_bookshelf_found(self, mock_repository, bookshelf_domain_object):
        """✓ GetBookshelfUseCase: Retrieve existing bookshelf"""
        # Setup: Save bookshelf first
        await mock_repository.save(bookshelf_domain_object)

        use_case = GetBookshelfUseCase(mock_repository)
        request = GetBookshelfRequest(bookshelf_id=bookshelf_domain_object.id)

        response = await use_case.execute(request)

        assert response.id == bookshelf_domain_object.id
        assert response.library_id == bookshelf_domain_object.library_id
        assert response.name == str(bookshelf_domain_object.name)
        assert response.status == "active"

    @pytest.mark.asyncio
    async def test_get_bookshelf_not_found(self, mock_repository):
        """✗ GetBookshelfUseCase: Non-existent bookshelf raises error"""
        use_case = GetBookshelfUseCase(mock_repository)
        request = GetBookshelfRequest(bookshelf_id=uuid4())

        with pytest.raises(ValueError, match="not found"):
            await use_case.execute(request)


# ============================================================================
# DeleteBookshelfUseCase Tests (3 tests)
# ============================================================================

class TestDeleteBookshelfUseCase:
    """Test DeleteBookshelfUseCase - Soft delete bookshelf"""

    @pytest.mark.asyncio
    async def test_delete_bookshelf_success(self, mock_repository, bookshelf_domain_object):
        """✓ DeleteBookshelfUseCase: Normal soft delete succeeds"""
        # Setup: Save bookshelf first
        await mock_repository.save(bookshelf_domain_object)

        use_case = DeleteBookshelfUseCase(mock_repository)
        request = DeleteBookshelfRequest(bookshelf_id=bookshelf_domain_object.id)

        response = await use_case.execute(request)

        assert response.id == bookshelf_domain_object.id
        assert response.status == "deleted"

    @pytest.mark.asyncio
    async def test_delete_bookshelf_basement_fails(self, mock_repository, basement_bookshelf_domain_object):
        """✗ DeleteBookshelfUseCase: Cannot delete Basement (RULE-010)"""
        # Setup: Save basement bookshelf
        await mock_repository.save(basement_bookshelf_domain_object)

        use_case = DeleteBookshelfUseCase(mock_repository)
        request = DeleteBookshelfRequest(bookshelf_id=basement_bookshelf_domain_object.id)

        with pytest.raises(ValueError, match="Cannot delete Basement"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_delete_bookshelf_not_found(self, mock_repository):
        """✗ DeleteBookshelfUseCase: Non-existent bookshelf raises error"""
        use_case = DeleteBookshelfUseCase(mock_repository)
        request = DeleteBookshelfRequest(bookshelf_id=uuid4())

        with pytest.raises(ValueError, match="not found"):
            await use_case.execute(request)


# ============================================================================
# RenameBookshelfUseCase Tests (4 tests)
# ============================================================================

class TestRenameBookshelfUseCase:
    """Test RenameBookshelfUseCase - Rename bookshelf"""

    @pytest.mark.asyncio
    async def test_rename_bookshelf_success(self, mock_repository, bookshelf_domain_object):
        """✓ RenameBookshelfUseCase: Normal rename succeeds"""
        # Setup: Save bookshelf first
        await mock_repository.save(bookshelf_domain_object)

        use_case = RenameBookshelfUseCase(mock_repository)
        request = RenameBookshelfRequest(
            bookshelf_id=bookshelf_domain_object.id,
            new_name="Renamed Bookshelf",
        )

        response = await use_case.execute(request)

        assert response.id == bookshelf_domain_object.id
        assert response.name == "Renamed Bookshelf"

    @pytest.mark.asyncio
    async def test_rename_bookshelf_duplicate_name_fails(self, mock_repository, library_id):
        """✗ RenameBookshelfUseCase: Duplicate name fails (RULE-006)"""
        # Setup: Create two bookshelves
        bs1 = bookshelf_domain_object = None
        # Using CreateBookshelfUseCase to create first bookshelf
        from api.app.modules.bookshelf.application.use_cases.create_bookshelf import CreateBookshelfUseCase

        create_use_case = CreateBookshelfUseCase(mock_repository)
        req1 = CreateBookshelfRequest(library_id=library_id, name="Bookshelf 1")
        resp1 = await create_use_case.execute(req1)
        bs1_id = resp1.id

        req2 = CreateBookshelfRequest(library_id=library_id, name="Bookshelf 2")
        resp2 = await create_use_case.execute(req2)
        bs2_id = resp2.id

        # Try to rename Bookshelf 2 to Bookshelf 1's name
        use_case = RenameBookshelfUseCase(mock_repository)
        request = RenameBookshelfRequest(
            bookshelf_id=bs2_id,
            new_name="Bookshelf 1",  # Already exists
        )

        with pytest.raises(ValueError, match="already exists"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_rename_bookshelf_invalid_length_fails(self, mock_repository, bookshelf_domain_object):
        """✗ RenameBookshelfUseCase: Invalid name length fails"""
        # Setup: Save bookshelf first
        await mock_repository.save(bookshelf_domain_object)

        use_case = RenameBookshelfUseCase(mock_repository)
        request = RenameBookshelfRequest(
            bookshelf_id=bookshelf_domain_object.id,
            new_name="A" * 256,  # Too long
        )

        with pytest.raises(ValueError):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_rename_bookshelf_not_found(self, mock_repository):
        """✗ RenameBookshelfUseCase: Non-existent bookshelf raises error"""
        use_case = RenameBookshelfUseCase(mock_repository)
        request = RenameBookshelfRequest(
            bookshelf_id=uuid4(),
            new_name="New Name",
        )

        with pytest.raises(ValueError, match="not found"):
            await use_case.execute(request)


# ============================================================================
# Repository Layer Tests (3 tests)
# ============================================================================

class TestBookshelfRepository:
    """Test MockBookshelfRepository - All 7 methods"""

    @pytest.mark.asyncio
    async def test_repository_save_and_get(self, mock_repository, bookshelf_domain_object):
        """✓ Repository: Save and retrieve bookshelf"""
        await mock_repository.save(bookshelf_domain_object)
        retrieved = await mock_repository.get_by_id(bookshelf_domain_object.id)

        assert retrieved is not None
        assert retrieved.id == bookshelf_domain_object.id
        assert str(retrieved.name) == str(bookshelf_domain_object.name)

    @pytest.mark.asyncio
    async def test_repository_get_by_library_id(self, mock_repository, bookshelf_domain_object, library_id):
        """✓ Repository: Get all active bookshelves by library"""
        await mock_repository.save(bookshelf_domain_object)

        bookshelves = await mock_repository.get_by_library_id(library_id)

        assert len(bookshelves) == 1
        assert bookshelves[0].id == bookshelf_domain_object.id

    @pytest.mark.asyncio
    async def test_repository_unique_name_enforcement(self, mock_repository, library_id, bookshelf_name):
        """✓ Repository: Enforces name uniqueness (RULE-006)"""
        # Create first bookshelf
        bs1 = bookshelf_domain_object = None
        from api.app.modules.bookshelf.domain import Bookshelf
        bs1 = Bookshelf.create(library_id=library_id, name=str(bookshelf_name))
        await mock_repository.save(bs1)

        # Try to create second with same name
        bs2 = Bookshelf.create(library_id=library_id, name=str(bookshelf_name))

        with pytest.raises(ValueError, match="already exists"):
            await mock_repository.save(bs2)
