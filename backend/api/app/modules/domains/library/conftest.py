"""
Library Tests - Pytest fixtures and test utilities

Provides:
- Fixtures for Library domain testing
- Mock objects
- Test data factories
"""

import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from domains.library.domain import Library, LibraryName
from domains.library.models import LibraryModel
from domains.library.repository import LibraryRepositoryImpl
from domains.library.service import LibraryService
from domains.library.schemas import LibraryCreate


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_user_id():
    """Sample user ID for testing"""
    return uuid4()


@pytest.fixture
def sample_library_id():
    """Sample library ID for testing"""
    return uuid4()


@pytest.fixture
def sample_library_name():
    """Sample library name"""
    return "My Test Library"


@pytest.fixture
def library_domain_factory(sample_user_id):
    """
    Factory fixture for creating Library domain objects

    Usage:
        library = library_domain_factory(name="Custom Name")
    """
    def _create(
        library_id=None,
        user_id=None,
        name="Test Library",
        created_at=None,
        updated_at=None,
    ):
        return Library(
            library_id=library_id or uuid4(),
            user_id=user_id or sample_user_id,
            name=LibraryName(value=name),
            created_at=created_at or datetime.utcnow(),
            updated_at=updated_at or datetime.utcnow(),
        )

    return _create


@pytest.fixture
def library_model_factory(sample_user_id):
    """
    Factory fixture for creating Library ORM models

    Usage:
        model = library_model_factory(name="Custom Name")
    """
    def _create(
        id=None,
        user_id=None,
        name="Test Library",
        created_at=None,
        updated_at=None,
    ):
        return LibraryModel(
            id=id or uuid4(),
            user_id=user_id or sample_user_id,
            name=name,
            created_at=created_at or datetime.utcnow(),
            updated_at=updated_at or datetime.utcnow(),
        )

    return _create


@pytest.fixture
async def mock_library_repository(library_domain_factory):
    """
    Mock LibraryRepository for testing Service layer

    Implements in-memory storage for testing
    """
    class MockLibraryRepository:
        def __init__(self):
            self.store = {}  # library_id -> Library

        async def save(self, library: Library) -> None:
            self.store[library.id] = library

        async def get_by_id(self, library_id) -> Library | None:
            return self.store.get(library_id)

        async def get_by_user_id(self, user_id) -> Library | None:
            for library in self.store.values():
                if library.user_id == user_id:
                    return library
            return None

        async def delete(self, library_id) -> None:
            self.store.pop(library_id, None)

        async def exists(self, library_id) -> bool:
            return library_id in self.store

    return MockLibraryRepository()


@pytest.fixture
async def library_service(mock_library_repository):
    """
    LibraryService instance with mock repository
    """
    return LibraryService(repository=mock_library_repository)


@pytest.fixture
def library_create_schema():
    """
    LibraryCreate schema factory
    """
    def _create(name="Test Library"):
        return LibraryCreate(name=name)

    return _create


# ============================================================================
# Utility Functions
# ============================================================================

def assert_library_created_event(library: Library):
    """
    Assert that LibraryCreated event was emitted

    Usage:
        library = Library.create(...)
        assert_library_created_event(library)
    """
    from domains.library.domain import LibraryCreated

    assert len(library.events) > 0, "No events emitted"
    event = library.events[0]
    assert isinstance(event, LibraryCreated), f"Expected LibraryCreated, got {type(event)}"


def assert_library_renamed_event(library: Library):
    """
    Assert that LibraryRenamed event was emitted

    Usage:
        library.rename("New Name")
        assert_library_renamed_event(library)
    """
    from domains.library.domain import LibraryRenamed

    assert len(library.events) > 0, "No events emitted"
    event = library.events[-1]
    assert isinstance(event, LibraryRenamed), f"Expected LibraryRenamed, got {type(event)}"
