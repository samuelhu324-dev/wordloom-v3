"""
Database Session Management

Provides async database session factory and dependency injection.
Uses psycopg3 async driver (Windows-native, no compilation).

NOTE: Engine is lazy-loaded on first use to ensure event loop policy is set first!
"""

import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


def _convert_to_psycopg(url: str) -> str:
    """
    Convert database URL to use psycopg async driver

    - If postgresql://, convert to postgresql+psycopg://
    - If already has driver, replace with psycopg
    - Returns as-is if already postgresql+psycopg://
    """
    if url.startswith("postgresql+psycopg://"):
        return url
    elif url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql+"):
        parts = url.split("://", 1)
        if len(parts) == 2:
            return f"postgresql+psycopg://{parts[1]}"

    return url


# Get raw database URL
# Use resolved DATABASE_URL (main.py guarantees env set). Provide resilient fallback.
_raw_url = os.getenv("DATABASE_URL") or "postgresql://postgres:pgpass@localhost:5432/wordloom"

# Convert to psycopg for async driver
DATABASE_URL = _convert_to_psycopg(_raw_url)

print(f"[OK] Database: {DATABASE_URL}")

# ============================================================================
# Global Engine Instance - Lazy loaded
# ============================================================================

_engine = None
_session_factory = None


async def get_engine():
    """Get or create global engine"""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            DATABASE_URL,
            echo=False,
            future=True,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
            # psycopg不支持timeout connect_arg，使用command_timeout代替
            # 移除timeout配置避免psycopg错误
        )
    return _engine


async def get_session_factory():
    """Get or create global session factory"""
    global _session_factory
    if _session_factory is None:
        engine = await get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _session_factory


# Compatibility: expose as module-level for backward compatibility
AsyncSessionLocal = None


async def _init_async_session_local():
    """Initialize AsyncSessionLocal on first use"""
    global AsyncSessionLocal
    if AsyncSessionLocal is None:
        AsyncSessionLocal = await get_session_factory()
    return AsyncSessionLocal


async def get_db_session():
    """
    Dependency: Get async database session

    Usage in router:
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_db_session)):
            ...
    """
    factory = await get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def shutdown_engine():
    """
    Cleanup: Dispose engine resources

    Call this on application shutdown
    """
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        print("[OK] Database engine disposed")