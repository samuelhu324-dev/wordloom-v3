"""
Database Infrastructure - AsyncSession management

Provides database session and engine setup for SQLAlchemy async operations.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event
from typing import AsyncGenerator, Optional
import os

# Global engine and session factory (lazy initialized)
_engine: Optional[object] = None
_async_session_factory: Optional[object] = None

# Check if we're in a test environment
IS_TEST = os.getenv("TESTING", "false").lower() == "true"


def _get_database_url() -> str:
    """Get database URL based on environment"""
    if IS_TEST:
        return "sqlite+aiosqlite:///:memory:"

    from config import get_settings
    settings = get_settings()
    return settings.DATABASE_URL


def _initialize_engine():
    """Lazy initialize the database engine"""
    global _engine
    if _engine is not None:
        return _engine

    database_url = _get_database_url()

    if IS_TEST:
        _engine = create_async_engine(
            database_url,
            echo=False,
            future=True,
        )
    else:
        _engine = create_async_engine(
            database_url,
            echo=False,
            future=True,
            pool_size=20,
            max_overflow=0,
        )

    return _engine


def _initialize_session_factory():
    """Lazy initialize the async session factory"""
    global _async_session_factory
    if _async_session_factory is not None:
        return _async_session_factory

    engine = _initialize_engine()

    _async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    return _async_session_factory




def get_engine():
    """Get the database engine (lazy initialized)"""
    return _initialize_engine()


def get_async_session_factory():
    """Get the async session factory (lazy initialized)"""
    return _initialize_session_factory()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for AsyncSession.

    Usage (in FastAPI routes):
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_db_session)):
            # Query database
            result = await session.execute(select(Item))
            return result.scalars().all()
    """
    factory = _initialize_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()
