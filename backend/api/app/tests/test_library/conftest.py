"""
Library Module Test Configuration

Purpose:
- Provide fixtures for all Library module tests
- Implement MockRepository for isolated testing
- Create domain objects and test data factories

Fixtures:
- user_id: UUID for test user
- library_data: Dictionary with library test data
- library_factory: Factory function for ORM models
- library_domain: Library domain aggregate instance
- mock_repository: In-memory implementation of ILibraryRepository
- create_use_case, get_use_case, etc: UseCase instances with MockRepository

Architecture:
- MockRepository implements ILibraryRepository interface
- Enforces business rules (RULE-001: one library per user)
- In-memory storage for fast test execution
- Modeled after Bookshelf MockRepository pattern

Cross-Reference:
- backend/api/app/tests/test_bookshelf/conftest.py (reference implementation)
- modules.library.application.ports.output.ILibraryRepository
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4, UUID

from api.app.modules.library.domain.library import Library
from api.app.modules.library.domain.library_name import LibraryName
from api.app.modules.library.application.use_cases.create_library import CreateLibraryUseCase
from api.app.modules.library.application.use_cases.get_library import GetLibraryUseCase
from api.app.modules.library.application.use_cases.delete_library import DeleteLibraryUseCase
from api.app.modules.library.application.ports.output import ILibraryRepository


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def user_id() -> UUID:
    """Unique user ID for test isolation"""
    return uuid4()


@pytest.fixture
def library_data(user_id: UUID) -> dict:
    """Dictionary with library test data"""
    return {
        "id": uuid4(),
        "user_id": user_id,
        "name": "My Library",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def library_factory(library_data: dict):
    """Factory function for creating ORM models"""
    from infra.database.models.library_models import LibraryModel

    def _create(**kwargs):
        data = library_data.copy()
        data.update(kwargs)
        return LibraryModel.from_dict(data)

    return _create


@pytest.fixture
def library_domain(user_id: UUID) -> Library:
    """Library domain aggregate instance"""
    return Library.create(
        user_id=user_id,
        name=LibraryName("My Library"),
    )


# ============================================================================
# MockRepository Implementation
# ============================================================================

class MockEventBus:
    """Mock EventBus for testing - in-memory event storage"""

    def __init__(self):
        self.events = []

    async def publish(self, event):
        """Publish event (just store it for test inspection)"""
        self.events.append(event)

    def get_events(self):
        """Get all published events"""
        return self.events

    def clear(self):
        """Clear event history"""
        self.events = []


class MockLibraryRepository(ILibraryRepository):
    """
    In-memory implementation of ILibraryRepository for testing.

    Enforces Business Rules:
    - RULE-001: One library per user (user_id is unique key)
    - RULE-002: Library must have user_id
    - RULE-003: Name length constraints

    Storage:
    - _libraries: Dict[UUID, Library] - storage by library ID
    - _user_libraries: Dict[UUID, UUID] - index for RULE-001 (user_id → library_id)
    """

    def __init__(self):
        self._libraries: Dict[UUID, Library] = {}
        self._user_libraries: Dict[UUID, UUID] = {}  # user_id -> library_id (enforces RULE-001)

    async def save(self, library: Library) -> None:
        """
        Save library (insert or update).

        Enforces RULE-001: One library per user.
        """
        # Check RULE-001: Is this user already registered with a different library?
        if library.user_id in self._user_libraries:
            existing_lib_id = self._user_libraries[library.user_id]
            if existing_lib_id != library.id:
                # Different library for same user → RULE-001 violation
                raise ValueError(
                    f"User {library.user_id} already has a library. "
                    f"RULE-001: One library per user."
                )

        # Save to both storage locations
        self._libraries[library.id] = library
        self._user_libraries[library.user_id] = library.id

    async def get_by_id(self, library_id: UUID) -> Optional[Library]:
        """Retrieve library by ID"""
        return self._libraries.get(library_id)

    async def get_by_user_id(self, user_id: UUID) -> Optional[Library]:
        """Retrieve library by user ID (RULE-001: one per user)"""
        if user_id not in self._user_libraries:
            return None

        library_id = self._user_libraries[user_id]
        return self._libraries.get(library_id)

    async def delete(self, library_id: UUID) -> None:
        """Delete library"""
        library = self._libraries.pop(library_id, None)
        if library:
            self._user_libraries.pop(library.user_id, None)

    async def get_all(self) -> List[Library]:
        """Get all libraries (for testing)"""
        return list(self._libraries.values())

    async def exists(self, library_id: UUID) -> bool:
        """Check if library exists"""
        return library_id in self._libraries


class MockBookshelfRepository:
    """In-memory bookshelf repository used to satisfy CreateLibrary dependencies."""

    def __init__(self):
        self._bookshelves = {}

    async def save(self, bookshelf):
        self._bookshelves[bookshelf.id] = bookshelf

    async def exists(self, bookshelf_id):
        return bookshelf_id in self._bookshelves


# ============================================================================
# Repository Fixture
# ============================================================================

@pytest.fixture
def repository() -> MockLibraryRepository:
    """MockRepository instance for test isolation"""
    return MockLibraryRepository()


@pytest.fixture
def bookshelf_repository() -> MockBookshelfRepository:
    """Mock bookshelf repository for basement creation"""
    return MockBookshelfRepository()


@pytest.fixture
def event_bus() -> MockEventBus:
    """MockEventBus instance for test isolation"""
    return MockEventBus()


# ============================================================================
# UseCase Fixtures
# ============================================================================

@pytest.fixture
def create_use_case(
    repository: MockLibraryRepository,
    bookshelf_repository: MockBookshelfRepository,
    event_bus: MockEventBus,
) -> CreateLibraryUseCase:
    """CreateLibraryUseCase with MockRepository and MockEventBus"""
    return CreateLibraryUseCase(
        repository=repository,
        bookshelf_repository=bookshelf_repository,
        event_bus=event_bus,
    )


@pytest.fixture
def get_use_case(repository: MockLibraryRepository) -> GetLibraryUseCase:
    """GetLibraryUseCase with MockRepository"""
    return GetLibraryUseCase(repository=repository)


@pytest.fixture
def delete_use_case(repository: MockLibraryRepository, event_bus: MockEventBus) -> DeleteLibraryUseCase:
    """DeleteLibraryUseCase with MockRepository and MockEventBus"""
    return DeleteLibraryUseCase(repository=repository, event_bus=event_bus)
