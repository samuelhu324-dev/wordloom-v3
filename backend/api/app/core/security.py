"""
Security Module - Authentication and authorization utilities

Provides security dependencies for FastAPI routes.
"""

from uuid import UUID, uuid4

async def get_current_user_id() -> UUID:
    """
    Dependency injection for current user ID.

    In production, this would decode JWT tokens.
    For testing, returns a fixed UUID.

    Usage in FastAPI route:
        async def get_libraries(user_id: UUID = Depends(get_current_user_id)):
            ...
    """
    # TODO: In production, extract from JWT token or session
    # For now, return a test user ID
    return uuid4()
