"""
App-Level Pytest Configuration
===============================

Purpose:
- Setup test database engine (SQLite in-memory)
- Create async session factory
- Provide authentication and dependency mocks
- Session and dependency fixtures for all app tests

Scope: Module level (app-wide fixtures)

Hierarchy:
- Global (backend/conftest.py): Event loop, pytest config
- App (this file): Database engine, sessions, auth mocks
- Tests (backend/api/app/tests/conftest.py): Integration test fixtures
- Modules (backend/api/app/modules/*/conftest.py): Domain-specific factories
"""

import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

# Base import commented out - will be added when database layer is fully set up
# from infra.database import Base


# ============================================================================
# Test Database Setup
# ============================================================================

# @pytest.fixture(scope="session")
# async def test_db_engine(event_loop):
#     """
#     Create SQLite async engine for all tests
#
#     Features:
#     - In-memory SQLite database (fast, isolated per session)
#     - Async support via aiosqlite
#     - Foreign key constraints enabled
#     - Schema created automatically
#
#     Scope: session (one engine for all tests)
#     Returns: AsyncEngine
#     """
#     engine = create_async_engine(
#         "sqlite+aiosqlite:///:memory:",
#         echo=False,
#         connect_args={"timeout": 30},
#     )
#
#     # Create all tables from ORM models
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#
#     yield engine
#
#     # Cleanup
#     await engine.dispose()
#
#
# @pytest.fixture(scope="function")
# async def db_session(test_db_engine, event_loop) -> AsyncGenerator[AsyncSession, None]:
#     """
#     Create isolated async database session for each test
#
#     Features:
#     - Fresh transaction for each test
#     - Automatic rollback after test (no side effects)
#     - Dependency injection ready
#
#     Scope: function (new session per test)
#     Returns: AsyncSession (sqlalchemy async session)
#
#     Usage:
#         async def test_something(db_session):
#             repo = LibraryRepository(db_session)
#             # ... test code ...
#     """
#     async_session = async_sessionmaker(
#         test_db_engine,
#         class_=AsyncSession,
#         expire_on_commit=False,
#         join_transaction_mode="create"
#     )
#
#     async with async_session() as session:
#         # Start transaction
#         await session.begin()
#
#         yield session
#
#         # Rollback after test (no side effects)
#         await session.rollback()


# ============================================================================
# Authentication Mocks
# ============================================================================

@pytest.fixture
def mock_current_user():
    """
    Mock authenticated user for testing

    Returns: MagicMock with typical user properties
    """
    user = MagicMock()
    user.id = "test-user-123"
    user.email = "test@example.com"
    user.is_active = True
    user.role = "user"
    return user


@pytest.fixture
def mock_admin_user():
    """
    Mock admin user for testing administrative operations

    Returns: MagicMock with admin properties
    """
    user = MagicMock()
    user.id = "admin-user-123"
    user.email = "admin@example.com"
    user.is_active = True
    user.role = "admin"
    return user


# ============================================================================
# Dependency Overrides
# ============================================================================

@pytest.fixture
def mock_get_db():
    """
    Mock database dependency for FastAPI tests

    Returns: AsyncMock that returns db_session
    """
    return AsyncMock()


@pytest.fixture
def mock_get_current_user():
    """
    Mock current user dependency for FastAPI tests

    Returns: Function that returns mock user
    """
    async def _get_current_user():
        user = MagicMock()
        user.id = "test-user-123"
        user.email = "test@example.com"
        return user

    return _get_current_user


# ============================================================================
# Test Data Builders
# ============================================================================

class TestDataFactory:
    """
    Factory for creating test data objects

    Provides: Builders for domain models with sensible defaults
    """

    @staticmethod
    def make_user_id(suffix: str = "123") -> str:
        """Create test user ID"""
        return f"user-{suffix}"

    @staticmethod
    def make_library_id(suffix: str = "lib-001") -> str:
        """Create test library ID"""
        return f"lib-{suffix}"

    @staticmethod
    def make_bookshelf_id(suffix: str = "bs-001") -> str:
        """Create test bookshelf ID"""
        return f"bs-{suffix}"

    @staticmethod
    def make_book_id(suffix: str = "book-001") -> str:
        """Create test book ID"""
        return f"book-{suffix}"

    @staticmethod
    def make_block_id(suffix: str = "block-001") -> str:
        """Create test block ID"""
        return f"block-{suffix}"


@pytest.fixture
def test_data():
    """
    Provide test data factory

    Returns: TestDataFactory instance
    """
    return TestDataFactory()


# ============================================================================
# Pytest Markers & Configuration
# ============================================================================

def pytest_configure(config):
    """Add app-specific markers"""
    config.addinivalue_line(
        "markers",
        "db: mark test as requiring database access"
    )
    config.addinivalue_line(
        "markers",
        "repo: mark test as testing repository layer"
    )
    config.addinivalue_line(
        "markers",
        "service: mark test as testing service layer"
    )
    config.addinivalue_line(
        "markers",
        "schema: mark test as testing schema validation"
    )
    config.addinivalue_line(
        "markers",
        "router: mark test as testing HTTP router"
    )
