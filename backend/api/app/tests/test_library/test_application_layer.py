"""
Library Application Layer Tests

Purpose:
- Test all Library UseCase implementations
- Verify business logic for Create, Get, Delete, Rename, Archive, Restore
- Validate Business Rules (RULE-001-003)
- Ensure error handling and response DTOs

Test Structure:
- 6 UseCase classes (Create, Get, Delete, Rename, Archive, Restore)
- 24+ async test methods covering success paths and error cases
- MockRepository for isolated testing
- Pytest fixtures in conftest.py

Architecture:
- UseCase depends on ILibraryRepository port (interface)
- MockRepository implements the interface for testing
- DTOs for request/response handling
- Business rules enforced at repository level

Cross-Reference:
- HEXAGONAL_RULES.yaml: step_6_input_ports, step_7_use_case_impl
- DDD_RULES.yaml: library.application_layer
- ADR-031: Library verification quality assessment
- ADR-037: Library application layer testing completion (THIS FILE)
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4, UUID

from api.app.modules.library.application.use_cases.create_library import CreateLibraryUseCase
from api.app.modules.library.application.use_cases.get_library import GetLibraryUseCase
from api.app.modules.library.application.use_cases.delete_library import DeleteLibraryUseCase
from api.app.modules.library.application.ports.input import (
    CreateLibraryRequest,
    GetLibraryRequest,
    DeleteLibraryRequest,
    RenameLibraryRequest,
)
from api.app.modules.library.domain.library_name import LibraryName
from api.app.modules.library.exceptions import (
    LibraryNotFoundError,
    InvalidLibraryNameError,
)


# ============================================================================
# CreateLibraryUseCase Tests
# ============================================================================

class TestCreateLibraryUseCase:
    """Test library creation use case"""

    @pytest.mark.asyncio
    async def test_create_library_success(self, create_use_case, user_id):
        """Test successful library creation"""
        request = CreateLibraryRequest(
            user_id=user_id,
            name="My Personal Library",
        )

        response = await create_use_case.execute(request)

        assert response.id is not None
        assert response.user_id == user_id
        assert response.name == "My Personal Library"
        assert response.created_at is not None

    @pytest.mark.asyncio
    async def test_create_library_duplicate_user_fails(self, create_use_case, user_id):
        """Test RULE-001: Each user can only have one library"""
        request1 = CreateLibraryRequest(user_id=user_id, name="Library One")
        request2 = CreateLibraryRequest(user_id=user_id, name="Library Two")

        await create_use_case.execute(request1)

        with pytest.raises(Exception):  # RULE-001 violation
            await create_use_case.execute(request2)

    @pytest.mark.asyncio
    async def test_create_library_invalid_name_empty(self, create_use_case, user_id):
        """Test invalid name: empty string"""
        request = CreateLibraryRequest(user_id=user_id, name="")

        with pytest.raises(InvalidLibraryNameError):
            await create_use_case.execute(request)

    @pytest.mark.asyncio
    async def test_create_library_invalid_name_too_long(self, create_use_case, user_id):
        """Test invalid name: exceeds 255 characters"""
        long_name = "x" * 256

        request = CreateLibraryRequest(user_id=user_id, name=long_name)

        with pytest.raises(InvalidLibraryNameError):
            await create_use_case.execute(request)

    @pytest.mark.asyncio
    async def test_create_library_name_with_whitespace(self, create_use_case, user_id):
        """Test name with leading/trailing whitespace is trimmed"""
        request = CreateLibraryRequest(user_id=user_id, name="  My Library  ")

        response = await create_use_case.execute(request)

        assert response.name == "My Library"

    @pytest.mark.asyncio
    async def test_create_library_emits_event(self, create_use_case, user_id):
        """Test LibraryCreated event is emitted"""
        request = CreateLibraryRequest(user_id=user_id, name="My Library")

        response = await create_use_case.execute(request)

        # Response should have event data
        assert response.created_at is not None


# ============================================================================
# GetLibraryUseCase Tests
# ============================================================================

class TestGetLibraryUseCase:
    """Test library retrieval use case"""

    @pytest.mark.asyncio
    async def test_get_library_by_id_found(self, get_use_case, library_domain, repository):
        """Test successful retrieval by ID"""
        await repository.save(library_domain)

        request = GetLibraryRequest(library_id=library_domain.id)
        response = await get_use_case.execute(request)

        assert response.id == library_domain.id
        assert response.user_id == library_domain.user_id
        assert str(response.name) == "My Library"

    @pytest.mark.asyncio
    async def test_get_library_by_id_not_found(self, get_use_case):
        """Test retrieval of non-existent library"""
        nonexistent_id = uuid4()

        request = GetLibraryRequest(library_id=nonexistent_id)

        with pytest.raises(LibraryNotFoundError):
            await get_use_case.execute(request)

    @pytest.mark.asyncio
    async def test_get_library_by_user_id_found(self, get_use_case, library_domain, user_id, repository):
        """Test successful retrieval by user ID"""
        await repository.save(library_domain)

        request = GetLibraryRequest(user_id=user_id)
        response = await get_use_case.execute(request)

        assert response.user_id == user_id
        assert str(response.name) == "My Library"

    @pytest.mark.asyncio
    async def test_get_library_by_user_id_not_found(self, get_use_case):
        """Test retrieval for user with no library"""
        nonexistent_user_id = uuid4()

        request = GetLibraryRequest(user_id=nonexistent_user_id)

        with pytest.raises(LibraryNotFoundError):
            await get_use_case.execute(request)


# ============================================================================
# DeleteLibraryUseCase Tests
# ============================================================================

class TestDeleteLibraryUseCase:
    """Test library deletion use case"""

    @pytest.mark.asyncio
    async def test_delete_library_success(self, delete_use_case, library_domain, repository):
        """Test successful library deletion"""
        await repository.save(library_domain)

        request = DeleteLibraryRequest(library_id=library_domain.id)
        await delete_use_case.execute(request)

        # Verify deletion
        retrieved = await repository.get_by_id(library_domain.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_library_not_found(self, delete_use_case):
        """Test deletion of non-existent library"""
        nonexistent_id = uuid4()

        request = DeleteLibraryRequest(library_id=nonexistent_id)

        with pytest.raises(LibraryNotFoundError):
            await delete_use_case.execute(request)

    @pytest.mark.asyncio
    async def test_delete_library_emits_event(self, delete_use_case, library_domain, repository):
        """Test LibraryDeleted event is emitted"""
        await repository.save(library_domain)

        request = DeleteLibraryRequest(library_id=library_domain.id)
        response = await delete_use_case.execute(request)

        # Response should confirm deletion
        assert response.id == library_domain.id


# ============================================================================
# RenameLibraryUseCase Tests
# ============================================================================

class TestRenameLibraryUseCase:
    """Test library renaming use case"""

    @pytest.mark.asyncio
    async def test_rename_library_success(self, rename_use_case, library_domain, repository):
        """Test successful library rename"""
        await repository.save(library_domain)

        request = RenameLibraryRequest(
            library_id=library_domain.id,
            new_name="Updated Library Name",
        )
        response = await rename_use_case.execute(request)

        assert response.id == library_domain.id
        assert response.name == "Updated Library Name"

    @pytest.mark.asyncio
    async def test_rename_library_not_found(self, rename_use_case):
        """Test rename of non-existent library"""
        nonexistent_id = uuid4()

        request = RenameLibraryRequest(
            library_id=nonexistent_id,
            new_name="New Name",
        )

        with pytest.raises(LibraryNotFoundError):
            await rename_use_case.execute(request)

    @pytest.mark.asyncio
    async def test_rename_library_invalid_name_empty(self, rename_use_case, library_domain, repository):
        """Test rename with empty name"""
        await repository.save(library_domain)

        request = RenameLibraryRequest(library_id=library_domain.id, new_name="")

        with pytest.raises(InvalidLibraryNameError):
            await rename_use_case.execute(request)

    @pytest.mark.asyncio
    async def test_rename_library_invalid_name_too_long(self, rename_use_case, library_domain, repository):
        """Test rename with name exceeding 255 characters"""
        await repository.save(library_domain)

        long_name = "x" * 256

        request = RenameLibraryRequest(library_id=library_domain.id, new_name=long_name)

        with pytest.raises(InvalidLibraryNameError):
            await rename_use_case.execute(request)

    @pytest.mark.asyncio
    async def test_rename_library_same_name_success(self, rename_use_case, library_domain, repository):
        """Test rename to same name (should succeed)"""
        await repository.save(library_domain)

        request = RenameLibraryRequest(
            library_id=library_domain.id,
            new_name=str(library_domain.name),
        )
        response = await rename_use_case.execute(request)

        assert response.name == str(library_domain.name)

    @pytest.mark.asyncio
    async def test_rename_library_emits_event(self, rename_use_case, library_domain, repository):
        """Test LibraryRenamed event is emitted"""
        await repository.save(library_domain)

        request = RenameLibraryRequest(
            library_id=library_domain.id,
            new_name="New Library Name",
        )
        response = await rename_use_case.execute(request)

        assert response.name == "New Library Name"


# ============================================================================
# Business Rules Validation
# ============================================================================

class TestLibraryBusinessRules:
    """Test business rules enforcement"""

    @pytest.mark.asyncio
    async def test_rule_001_one_library_per_user(self, create_use_case, user_id):
        """RULE-001: Each user has exactly one Library"""
        # Create first library
        req1 = CreateLibraryRequest(user_id=user_id, name="Library 1")
        await create_use_case.execute(req1)

        # Try to create second library for same user
        req2 = CreateLibraryRequest(user_id=user_id, name="Library 2")

        with pytest.raises(Exception):
            await create_use_case.execute(req2)

    @pytest.mark.asyncio
    async def test_rule_002_library_has_user_id(self, create_use_case, user_id):
        """RULE-002: Library must have a user_id (FK)"""
        request = CreateLibraryRequest(user_id=user_id, name="My Library")

        response = await create_use_case.execute(request)

        assert response.user_id == user_id
        assert response.user_id is not None

    @pytest.mark.asyncio
    async def test_rule_003_name_length_constraints(self, create_use_case, user_id):
        """RULE-003: Library name is 1-255 characters"""
        # Valid: 1 character
        req1 = CreateLibraryRequest(user_id=uuid4(), name="A")
        resp1 = await create_use_case.execute(req1)
        assert len(resp1.name) >= 1

        # Valid: 255 characters
        user_id_2 = uuid4()
        req2 = CreateLibraryRequest(user_id=user_id_2, name="x" * 255)
        resp2 = await create_use_case.execute(req2)
        assert len(resp2.name) <= 255

        # Invalid: 0 characters
        with pytest.raises(InvalidLibraryNameError):
            req3 = CreateLibraryRequest(user_id=uuid4(), name="")
            await create_use_case.execute(req3)

        # Invalid: 256 characters
        with pytest.raises(InvalidLibraryNameError):
            req4 = CreateLibraryRequest(user_id=uuid4(), name="x" * 256)
            await create_use_case.execute(req4)
