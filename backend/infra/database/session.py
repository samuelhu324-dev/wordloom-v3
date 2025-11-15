"""
Database Session Management

Provides async database session factory and dependency injection.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
import os

# Database connection string
# Convert regular postgresql:// to postgresql+psycopg:// for async driver
_raw_url = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:pgpass@127.0.0.1:5433/wordloom"
)

# Ensure async driver is used (psycopg supports async natively)
if _raw_url.startswith("postgresql://"):
    DATABASE_URL = _raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    DATABASE_URL = _raw_url

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db_session():
    """
    Dependency: Get async database session

    Usage in router:
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_db_session)):
            ...
    """
    async with AsyncSessionLocal() as session:
        yield session
