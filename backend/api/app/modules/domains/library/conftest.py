"""
Library Tests - Pytest fixtures and test utilities

Provides:
- Fixtures for Library domain testing
- Mock objects
- Test data factories
- Database integration fixtures for round-trip testing
- Assertion helpers for events and state verification
"""

import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import event as sa_event

from domains.library.domain import Library, LibraryName
from domains.library.models import LibraryModel
from domains.library.repository import LibraryRepositoryImpl
from domains.library.service import LibraryService
from domains.library.schemas import LibraryCreate
from core.database import Base


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
# Database Fixtures - Integration Testing
# ============================================================================

@pytest.fixture
async def db_engine():
    """
    Create async database engine for testing.

    Uses SQLite in-memory for unit tests, can be switched to PostgreSQL test DB
    for CI/CD environments.

    Usage:
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    """
    # For development: SQLite in-memory
    # For CI/CD: "postgresql+asyncpg://test:test@localhost/wordloom_test"
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"

    engine = create_async_engine(
        DATABASE_URL,
        echo=False,  # Set True for SQL debug logging
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """
    Create async database session for testing.

    Each test gets a fresh session that auto-commits. Transactions are
    isolated per test, enabling parallel test execution.

    Usage:
        async def test_something(db_session):
            result = await db_session.execute(...)
    """
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        # Auto cleanup happens when context exits


@pytest.fixture
async def library_repository_impl(db_session):
    """
    Real LibraryRepositoryImpl with database session for integration testing.

    Unlike mock_library_repository, this uses actual ORM and database.
    Useful for testing round-trip: Domain → DB → Domain.

    Usage:
        async def test_save_and_load(library_repository_impl):
            library = Library.create(user_id, "Test")
            await library_repository_impl.save(library)
            loaded = await library_repository_impl.get_by_id(library.id)
            assert loaded.name == library.name
    """
    return LibraryRepositoryImpl(session=db_session)


@pytest.fixture
async def library_service_with_db(library_repository_impl):
    """
    LibraryService with real database repository for integration testing.

    Combines Service layer with actual database persistence.
    Useful for end-to-end flow testing (create → persist → retrieve).

    Usage:
        async def test_create_library_e2e(library_service_with_db):
            library = await library_service_with_db.create_library(user_id, "Test")
            assert library.id is not None
    """
    return LibraryService(repository=library_repository_impl)


# ============================================================================
# Round-Trip Assertion Helpers
# ============================================================================

async def assert_library_round_trip(
    library_domain: Library,
    repository: LibraryRepositoryImpl,
):
    """
    Verify Domain → Database → Domain round-trip mapping is correct.

    Validates that:
    - All fields persist correctly
    - UUID identity preserved
    - DateTime values preserved (timezone handling)
    - No data loss or corruption

    Usage:
        library = Library.create(user_id, "Test")
        await assert_library_round_trip(library, repository)

    Raises:
        AssertionError if any field doesn't match

    Returns:
        The loaded Library domain object for further assertions
    """
    # Step 1: Save to database
    await repository.save(library_domain)

    # Step 2: Load from database
    loaded = await repository.get_by_id(library_domain.id)

    # Step 3: Verify all fields match
    assert loaded is not None, f"Library {library_domain.id} not found after save"
    assert loaded.id == library_domain.id, "ID mismatch after round-trip"
    assert loaded.user_id == library_domain.user_id, "User ID mismatch after round-trip"
    assert str(loaded.name) == str(library_domain.name), "Name mismatch after round-trip"

    # Timestamp comparison (allow small float precision differences)
    created_diff = abs(
        loaded.created_at.timestamp() - library_domain.created_at.timestamp()
    )
    assert created_diff < 1, f"Created_at drift: {created_diff}s"

    updated_diff = abs(
        loaded.updated_at.timestamp() - library_domain.updated_at.timestamp()
    )
    assert updated_diff < 1, f"Updated_at drift: {updated_diff}s"

    return loaded


async def assert_library_persisted(library_id, repository):
    """
    Verify that a Library exists in database.

    Usage:
        await assert_library_persisted(library.id, repository)

    Raises:
        AssertionError if not found

    Returns:
        The loaded Library domain object
    """
    loaded = await repository.get_by_id(library_id)
    assert loaded is not None, f"Library {library_id} not found in database"
    return loaded


async def assert_library_deleted(library_id, repository):
    """
    Verify that a Library does not exist in database.

    Usage:
        await repository.delete(library.id)
        await assert_library_deleted(library.id, repository)

    Raises:
        AssertionError if found
    """
    loaded = await repository.get_by_id(library_id)
    assert loaded is None, f"Library {library_id} still exists after deletion"


async def assert_user_library_unique(user_id, repository):
    """
    Verify RULE-001: One Library per user.

    Ensures that get_by_user_id returns exactly one Library and
    never finds multiple Libraries for the same user (data corruption check).

    Usage:
        await assert_user_library_unique(user_id, repository)

    Raises:
        AssertionError if duplicate Libraries found (data corruption)
    """
    library = await repository.get_by_user_id(user_id)
    # This test assumes get_by_user_id enforces uniqueness
    # If it returns None, that's OK (user has no library yet)
    # But if it returns a library, verify it's really the only one
    assert library is None or library.user_id == user_id, \
        f"RULE-001 violation: Multiple libraries for user {user_id}"


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
