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

import os
import re
import pytest
import asyncio
from typing import AsyncGenerator

import pytest_asyncio

from alembic import command
from alembic.config import Config
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from unittest.mock import MagicMock, AsyncMock

from api.app.config.setting import get_settings

# Base import commented out - will be added when database layer is fully set up
# from infra.database import Base


# ============================================================================
# Test Database Setup
# ============================================================================

_DEVTEST_DB_5435_SAFE_RE = re.compile(
    r"^postgresql(\+psycopg)?://[^@]+@(?:localhost|127\.0\.0\.1):5435/wordloom_test$",
    re.IGNORECASE,
)


def _resolve_test_database_url() -> str:
    get_settings.cache_clear()
    settings = get_settings()
    url = settings.database_url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    return url


def _ensure_devtest_db_5435(url: str) -> None:
    if not _DEVTEST_DB_5435_SAFE_RE.match(url):
        raise RuntimeError(
            "[DEVTEST-DB-5435] Refusing to run DB tests for unsafe DATABASE_URL: "
            f"{url}. Expected localhost:5435/wordloom_test."
        )


@pytest.fixture(scope="session")
def _devtest_db_url() -> str:
    url = _resolve_test_database_url()

    # If user didn't opt-in to DB tests, skip any test that requires db_session.
    # This prevents accidental use of docker/sandbox or localhost:5432.
    if not _DEVTEST_DB_5435_SAFE_RE.match(url):
        pytest.skip(
            "DB tests require DATABASE_URL pointing to DEVTEST-DB-5435: "
            "postgresql+psycopg://...@localhost:5435/wordloom_test"
        )

    _ensure_devtest_db_5435(url)
    return url


@pytest.fixture(scope="session")
def _devtest_db_migrated(_devtest_db_url: str) -> None:
    """Run Alembic migrations once per pytest session.

    Safety: pinned to DEVTEST-DB-5435 only.
    """
    os.environ["DATABASE_URL"] = _devtest_db_url
    get_settings.cache_clear()

    # backend/api/app -> backend
    alembic_ini = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini")
    )
    if not os.path.exists(alembic_ini):
        raise RuntimeError(f"Alembic config not found: {alembic_ini}")
    cfg = Config(alembic_ini)
    # env.py also resolves from Settings; setting this is a helpful backstop.
    cfg.set_main_option("sqlalchemy.url", _devtest_db_url)
    command.upgrade(cfg, "head")


@pytest_asyncio.fixture(scope="session")
async def db_engine(
    _devtest_db_url: str, _devtest_db_migrated: None
) -> AsyncGenerator[AsyncEngine, None]:
    """AsyncEngine for DEVTEST-DB-5435 test database."""
    engine = create_async_engine(
        _devtest_db_url,
        echo=False,
        future=True,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Per-test transaction with rollback (screenshot1).

    Uses an outer transaction + SAVEPOINT (nested transaction) so code under test
    can call commit() without breaking test isolation.
    """

    async with db_engine.connect() as connection:
        outer_tx = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)

        await session.begin_nested()

        @event.listens_for(session.sync_session, "after_transaction_end")
        def _restart_savepoint(sess, trans):
            if trans.nested and not trans._parent.nested:
                sess.begin_nested()

        try:
            yield session
        finally:
            await session.close()
            await outer_tx.rollback()

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
