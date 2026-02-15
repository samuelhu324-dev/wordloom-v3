from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from .setting import get_settings

# ORM Base - All domain models inherit from this
Base = declarative_base()

# ============================================================================
# Global Engine Instance - Lazy loaded on first access
# ============================================================================

_engine = None
_session_factory = None


def _create_async_engine():
    """
    Create global async engine with proper configuration

    - Async driver: postgresql+psycopg (Windows-native, no compilation)
    - Connection pool: QueuePool with 10 pre-created connections
    - Echo: Controlled by settings.debug

    Returns:
        AsyncEngine: Singleton engine for entire application lifetime
    """
    settings = get_settings()

    # Ensure URL uses psycopg driver
    db_url = settings.database_url
    if db_url.startswith("postgresql://"):
        # Convert to psycopg driver
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif db_url.startswith("postgresql+asyncpg://"):
        # Convert from asyncpg to psycopg
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    elif not db_url.startswith("postgresql+psycopg://"):
        # If it's already specified with different driver, convert to psycopg
        if db_url.startswith("postgresql+"):
            db_url = db_url.split("://")[1]
            db_url = f"postgresql+psycopg://{db_url}"

    print(f"[OK] Database URL: {db_url}")

    # Create engine with connection pooling
    return create_async_engine(
        db_url,
        echo=settings.debug,
        future=True,
        pool_size=10,              # Number of connections to keep in pool
        max_overflow=20,           # Additional connections beyond pool_size
        pool_pre_ping=True,        # Verify connections before use
        pool_recycle=3600,         # Recycle connections after 1 hour
        connect_args={
            "timeout": 10,         # Connection timeout
            "command_timeout": 60, # Query timeout
        },
    )


async def get_db_engine():
    """
    Get or create global database engine instance (lazy loading)

    Returns:
        AsyncEngine: Shared global engine
    """
    global _engine
    if _engine is None:
        _engine = _create_async_engine()
    return _engine


# ============================================================================
# Global Session Factory
# ============================================================================

async def get_session_factory():
    """Get or create global session factory"""
    global _session_factory
    if _session_factory is None:
        engine = await get_db_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _session_factory


async def get_db_session():
    """
    Dependency: Get async database session from global engine

    Usage in FastAPI router:
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_db_session)):
            result = await session.execute(...)
            return result

    Yields:
        AsyncSession: Database session for operations
    """
    factory = await get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ============================================================================
# Shutdown Hook - Called on application shutdown
# ============================================================================

async def shutdown_db():
    """
    Cleanup database engine on application shutdown

    Called by FastAPI @app.on_event("shutdown")
    """
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        print("[OK] Database engine disposed")
