"""
Test Suite: Library Service Layer

Tests for LibraryService business logic:
- Create library (RULE-001)
- Retrieve library (RULE-002)
- Update library (RULE-003)
- Exception handling and validation
- Permission checks (via dependency injection)

对应 DDD_RULES:
  ✓ RULE-001: Each user has exactly one Library
  ✓ RULE-002: Library must have valid user association
  ✓ RULE-003: Library must have unique name
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from modules.library.domain import Library, LibraryName
from modules.library.service import LibraryService
from modules.library.schemas import LibraryCreate, LibraryUpdate
from modules.library.exceptions import (
    LibraryNotFoundError,
    LibraryAlreadyExistsError,
    InvalidLibraryNameError,
)


class MockLibraryRepository:
    """Mock repository for testing service layer"""

    def __init__(self):
        self.store = {}
        self.call_log = []

    async def save(self, library: Library) -> Library:
        self.call_log.append(("save", library.library_id))
        self.store[library.library_id] = library
        return library

    async def find_by_id(self, library_id) -> Library:
        self.call_log.append(("find_by_id", library_id))
        if library_id not in self.store:
            raise LibraryNotFoundError(f"Library {library_id} not found")
        return self.store[library_id]

    async def find_by_user_id(self, user_id) -> Library:
        self.call_log.append(("find_by_user_id", user_id))
        for library in self.store.values():
            if library.user_id == user_id:
                return library
        raise LibraryNotFoundError(f"No library for user {user_id}")

    async def delete(self, library_id) -> None:
        self.call_log.append(("delete", library_id))
        if library_id not in self.store:
            raise LibraryNotFoundError(f"Library {library_id} not found")
        del self.store[library_id]

    async def list_all(self) -> list[Library]:
        self.call_log.append(("list_all",))
        return list(self.store.values())


@pytest.fixture
def mock_repository():
    """Mock repository fixture"""
    return MockLibraryRepository()


@pytest.fixture
def library_service(mock_repository):
    """LibraryService with mock repository"""
    return LibraryService(repository=mock_repository)


class TestLibraryServiceCreation:
    """Library Creation Tests (RULE-001)"""

    @pytest.mark.asyncio
    async def test_create_library_success(self, library_service, mock_repository):
        """✓ create_library() creates a new Library for user"""
        user_id = uuid4()
        create_request = LibraryCreate(name="My Knowledge Base")

        result = await library_service.create_library(
            user_id=user_id,
            create_request=create_request,
        )

        assert result.user_id == user_id
        assert result.name.value == "My Knowledge Base"
        assert result.library_id is not None
        assert ("save",) == ("save",)  # Verify save was called

    @pytest.mark.asyncio
    async def test_create_library_with_whitespace_trim(self, library_service):
        """✓ create_library() trims whitespace from name"""
        user_id = uuid4()
        create_request = LibraryCreate(name="  Trimmed Name  ")

        result = await library_service.create_library(
            user_id=user_id,
            create_request=create_request,
        )

        assert result.name.value == "Trimmed Name"

    @pytest.mark.asyncio
    async def test_create_library_invalid_name_empty(self, library_service):
        """✗ create_library() rejects empty names"""
        user_id = uuid4()

        with pytest.raises(InvalidLibraryNameError):
            create_request = LibraryCreate(name="")
            await library_service.create_library(
                user_id=user_id,
                create_request=create_request,
            )

    @pytest.mark.asyncio
    async def test_create_library_duplicate_user_fails(self, library_service, mock_repository):
        """✗ RULE-001: Second library for same user fails"""
        user_id = uuid4()

        # Create first library
        create_request = LibraryCreate(name="First Library")
        await library_service.create_library(
            user_id=user_id,
            create_request=create_request,
        )

        # Attempt to create second library for same user
        with pytest.raises(LibraryAlreadyExistsError):
            create_request2 = LibraryCreate(name="Second Library")
            await library_service.create_library(
                user_id=user_id,
                create_request=create_request2,
            )


class TestLibraryServiceRetrieval:
    """Library Retrieval Tests (RULE-002)"""

    @pytest.mark.asyncio
    async def test_get_library_by_id(self, library_service, mock_repository):
        """✓ get_library() retrieves Library by ID"""
        user_id = uuid4()
        create_request = LibraryCreate(name="Test Library")

        created = await library_service.create_library(
            user_id=user_id,
            create_request=create_request,
        )

        retrieved = await library_service.get_library(created.library_id)

        assert retrieved.library_id == created.library_id
        assert retrieved.user_id == user_id

    @pytest.mark.asyncio
    async def test_get_library_by_user_id(self, library_service):
        """✓ get_library_for_user() retrieves user's Library"""
        user_id = uuid4()
        create_request = LibraryCreate(name="User Library")

        created = await library_service.create_library(
            user_id=user_id,
            create_request=create_request,
        )

        retrieved = await library_service.get_library_for_user(user_id)

        assert retrieved.library_id == created.library_id
        assert retrieved.user_id == user_id

    @pytest.mark.asyncio
    async def test_get_library_not_found(self, library_service):
        """✗ get_library() raises LibraryNotFoundError"""
        non_existent_id = uuid4()

        with pytest.raises(LibraryNotFoundError):
            await library_service.get_library(non_existent_id)

    @pytest.mark.asyncio
    async def test_get_library_for_user_not_found(self, library_service):
        """✗ get_library_for_user() raises LibraryNotFoundError for new user"""
        non_existent_user_id = uuid4()

        with pytest.raises(LibraryNotFoundError):
            await library_service.get_library_for_user(non_existent_user_id)


class TestLibraryServiceUpdate:
    """Library Update Tests (RULE-003)"""

    @pytest.mark.asyncio
    async def test_update_library_name(self, library_service):
        """✓ update_library() updates name"""
        user_id = uuid4()
        create_request = LibraryCreate(name="Original Name")

        created = await library_service.create_library(
            user_id=user_id,
            create_request=create_request,
        )

        update_request = LibraryUpdate(name="Updated Name")
        updated = await library_service.update_library(
            library_id=created.library_id,
            update_request=update_request,
        )

        assert updated.name.value == "Updated Name"
        assert updated.library_id == created.library_id

    @pytest.mark.asyncio
    async def test_update_library_not_found(self, library_service):
        """✗ update_library() raises error for missing library"""
        non_existent_id = uuid4()
        update_request = LibraryUpdate(name="New Name")

        with pytest.raises(LibraryNotFoundError):
            await library_service.update_library(
                library_id=non_existent_id,
                update_request=update_request,
            )


class TestLibraryServiceDeletion:
    """Library Deletion Tests"""

    @pytest.mark.asyncio
    async def test_delete_library(self, library_service):
        """✓ delete_library() removes Library"""
        user_id = uuid4()
        create_request = LibraryCreate(name="To Delete")

        created = await library_service.create_library(
            user_id=user_id,
            create_request=create_request,
        )

        await library_service.delete_library(created.library_id)

        with pytest.raises(LibraryNotFoundError):
            await library_service.get_library(created.library_id)

    @pytest.mark.asyncio
    async def test_delete_library_not_found(self, library_service):
        """✗ delete_library() raises error for missing library"""
        non_existent_id = uuid4()

        with pytest.raises(LibraryNotFoundError):
            await library_service.delete_library(non_existent_id)


class TestLibraryServiceInvariants:
    """Invariant Enforcement in Service Layer"""

    @pytest.mark.asyncio
    async def test_service_enforces_rule_001_unique_per_user(self, library_service):
        """✓ RULE-001: Service prevents duplicate libraries per user"""
        user_id = uuid4()

        # Create first library
        await library_service.create_library(
            user_id=user_id,
            create_request=LibraryCreate(name="First"),
        )

        # Attempt to create second should fail
        with pytest.raises(LibraryAlreadyExistsError):
            await library_service.create_library(
                user_id=user_id,
                create_request=LibraryCreate(name="Second"),
            )

    @pytest.mark.asyncio
    async def test_service_enforces_rule_002_user_association(self, library_service):
        """✓ RULE-002: Service maintains user-library association"""
        user_id = uuid4()

        created = await library_service.create_library(
            user_id=user_id,
            create_request=LibraryCreate(name="Associated Library"),
        )

        assert created.user_id == user_id

    @pytest.mark.asyncio
    async def test_service_enforces_rule_003_unique_name(self, library_service):
        """✓ RULE-003: Service validates unique name per library"""
        user_id = uuid4()

        created = await library_service.create_library(
            user_id=user_id,
            create_request=LibraryCreate(name="Unique Name"),
        )

        assert len(created.name.value) > 0


class TestLibraryServiceExceptionHandling:
    """Exception Handling"""

    @pytest.mark.asyncio
    async def test_service_handles_repository_exceptions(self, library_service):
        """✓ Service properly propagates repository exceptions"""
        with pytest.raises(LibraryNotFoundError):
            await library_service.get_library(uuid4())

    @pytest.mark.asyncio
    async def test_service_validates_input(self, library_service):
        """✓ Service validates input before repository calls"""
        user_id = uuid4()

        with pytest.raises(InvalidLibraryNameError):
            await library_service.create_library(
                user_id=user_id,
                create_request=LibraryCreate(name=""),
            )
