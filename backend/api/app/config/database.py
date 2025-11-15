"""
Database configuration and ORM setup

Provides:
- Base: SQLAlchemy ORM declarative base (all models inherit this)
- Session management utilities
"""

from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from .setting import get_settings

# ORM Base - All domain models inherit from this
Base = declarative_base()


def get_db_engine():
    """
    Create async SQLAlchemy engine

    Returns:
        AsyncEngine: Async database engine configured from settings
    """
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        future=True,
    )


async def get_db_session():
    """
    Dependency: Get async database session

    Yields:
        AsyncSession: Database session for operations
    """
    engine = get_db_engine()
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session_maker() as session:
        yield session
