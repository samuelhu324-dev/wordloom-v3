"""
System-level exceptions - Infrastructure and core errors

These are different from Domain/Business errors.
- SystemException: Infrastructure/system level (database, config, file storage)
- BusinessError: Domain logic level (in shared/errors.py)

Pattern:
- SystemException: Used by config, database, storage layers
- Should be caught and mapped to HTTP errors in main.py exception handlers
"""

from typing import Optional, Dict, Any


class SystemException(Exception):
    """
    Base system exception for infrastructure-level errors

    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code (e.g., "DB_CONNECTION_ERROR")
        http_status_code: Corresponding HTTP status code
        details: Additional error context (dict)
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.http_status_code = http_status_code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(SystemException):
    """Database operation failed"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            http_status_code=500,
            details=details,
        )


class StorageException(SystemException):
    """File storage operation failed"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="STORAGE_ERROR",
            http_status_code=500,
            details=details,
        )


class ConfigurationException(SystemException):
    """Configuration error at startup"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            http_status_code=500,
            details=details,
        )


class ValidationException(SystemException):
    """Input validation failed (infrastructure level)"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            http_status_code=422,
            details=details,
        )


class AuthenticationException(SystemException):
    """Authentication failed (invalid credentials, missing token)"""

    def __init__(self, message: str = "Unauthorized", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            http_status_code=401,
            details=details,
        )


class AuthorizationException(SystemException):
    """Authorization failed (insufficient permissions)"""

    def __init__(self, message: str = "Forbidden", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="FORBIDDEN",
            http_status_code=403,
            details=details,
        )
