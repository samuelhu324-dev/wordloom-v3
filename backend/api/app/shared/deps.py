"""
Dependency injection utilities for FastAPI routes

Provides:
- get_db: Database session dependency
- get_event_bus: Event bus dependency
- Other reusable dependencies
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import get_db_session as _get_db_session
from shared.events import get_event_bus as _get_event_bus


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency: Get database session for route

    Usage in routes:
        @router.get("/libraries")
        async def get_libraries(db: AsyncSession = Depends(get_db)):
            ...

    Yields:
        AsyncSession: Database session
    """
    async for session in _get_db_session():
        yield session


async def get_event_bus():
    """
    Dependency: Get event bus for route

    Usage in routes:
        from shared.events import EventBus

        @router.post("/books")
        async def create_book(
            book_dto: BookCreateDTO,
            event_bus: EventBus = Depends(get_event_bus),
        ):
            ...

    Returns:
        EventBus: Global event bus instance
    """
    return _get_event_bus()

