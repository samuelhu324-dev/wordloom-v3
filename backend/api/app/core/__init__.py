"""
Core Module - System exceptions

Exports all system-level exceptions:
- SystemException: Base infrastructure exception
- DatabaseException: Database operation failed
- StorageException: File storage operation failed
- ConfigurationException: Configuration error
- ValidationException: Input validation failed
- AuthenticationException: Authentication failed
- AuthorizationException: Authorization failed (permission denied)

Note:
- Database and security config are in app.config module
- Domain-level business errors are in shared.errors module
"""

from .exceptions import (
    SystemException,
    DatabaseException,
    StorageException,
    ConfigurationException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
)

__all__ = [
    "SystemException",
    "DatabaseException",
    "StorageException",
    "ConfigurationException",
    "ValidationException",
    "AuthenticationException",
    "AuthorizationException",
]


