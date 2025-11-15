"""
Security utilities - JWT, password hashing, authentication

Provides:
- JWT token creation and verification
- Password hashing utilities
- Current user dependency injection
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4
import jwt
from .setting import get_settings


class SecurityConfig:
    """Centralized security configuration"""

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token

        Args:
            data: Claims to encode in token
            expires_delta: Optional custom expiration time

        Returns:
            str: Encoded JWT token
        """
        settings = get_settings()
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.access_token_expire_minutes
            )

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm,
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Verify JWT token validity

        Args:
            token: JWT token string

        Returns:
            dict: Decoded payload if valid, None if invalid
        """
        settings = get_settings()
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm],
            )
            return payload
        except jwt.InvalidTokenError:
            return None


async def get_current_user_id() -> UUID:
    """
    Dependency injection for current user ID

    In production, this would decode JWT tokens from request headers.
    For development/testing, returns a fixed UUID.

    Usage in FastAPI route:
        async def get_libraries(user_id: UUID = Depends(get_current_user_id)):
            ...

    Returns:
        UUID: Current user ID

    TODO:
        - Extract JWT from Authorization header
        - Validate token and extract user_id claim
        - Handle token expiration
    """
    # TODO: In production, extract from JWT token or session
    # For now, return a test user ID
    return UUID("550e8400-e29b-41d4-a716-446655440000")
