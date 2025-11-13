"""
Library Exceptions - Domain-specific exceptions

Implements comprehensive exception hierarchy with HTTP status code mapping.
Corresponds to DDD_RULES RULE-001, RULE-002, RULE-003.

Exception Hierarchy:
  DomainException (base)
    ├─ LibraryException
    │   ├─ NotFoundError (404)
    │   ├─ AlreadyExistsError (409)
    │   ├─ InvalidNameError (422)
    │   └─ UserAssociationError (422)
    └─ RepositoryException
        └─ PersistenceError (500)
"""

from typing import Optional, Dict, Any


# ============================================
# Base Exceptions
# ============================================

class DomainException(Exception):
    """
    Base exception for all Domain exceptions.
    Provides structured error serialization for API responses.
    """
    code: str = "DOMAIN_ERROR"
    http_status: int = 500
    details: Dict[str, Any] = {}

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        http_status: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if http_status:
            self.http_status = http_status
        if details:
            self.details = details
        else:
            self.details = {}

    @property
    def http_status_code(self) -> int:
        """Alias for http_status (backward compatibility)"""
        return self.http_status

    def to_dict(self) -> Dict[str, Any]:
        """Serialize exception to API response format"""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self) -> str:
        return self.message


# ============================================
# Library Domain Exceptions
# ============================================

class LibraryException(DomainException):
    """Base for all Library Domain exceptions"""
    pass


class LibraryNotFoundError(LibraryException):
    """
    Raised when a Library is not found.

    RULE-001: Every user must have exactly one Library.
    This exception indicates that the requested Library ID does not exist.

    HTTP Status: 404 Not Found
    """
    code = "LIBRARY_NOT_FOUND"
    http_status = 404

    def __init__(
        self,
        library_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        message = "Library not found"
        if library_id:
            message += f": {library_id}"
        if user_id:
            message += f" for user {user_id}"

        super().__init__(
            message=message,
            code=self.code,
            http_status=self.http_status,
            details={
                "library_id": str(library_id) if library_id else None,
                "user_id": str(user_id) if user_id else None,
            }
        )


class LibraryAlreadyExistsError(LibraryException):
    """
    Raised when attempting to create a second Library for a user.

    RULE-001: Each user can own exactly one Library (1:1 relationship).
    Attempting to create a second Library violates this invariant.

    HTTP Status: 409 Conflict
    """
    code = "LIBRARY_ALREADY_EXISTS"
    http_status = 409

    def __init__(
        self,
        user_id: str,
        existing_library_id: Optional[str] = None,
    ):
        message = f"User {user_id} already has a Library"
        if existing_library_id:
            message += f" ({existing_library_id})"

        super().__init__(
            message=message,
            code=self.code,
            http_status=self.http_status,
            details={
                "user_id": str(user_id),
                "existing_library_id": str(existing_library_id) if existing_library_id else None,
            }
        )


class InvalidLibraryNameError(LibraryException):
    """
    Raised when Library name validation fails.

    RULE-003: Library name must satisfy: 1 <= len(name) <= 255
    Name cannot be empty or contain only whitespace.

    HTTP Status: 422 Unprocessable Entity
    """
    code = "INVALID_LIBRARY_NAME"
    http_status = 422

    def __init__(
        self,
        name: Optional[str] = None,
        reason: str = "Invalid name provided",
    ):
        message = f"Invalid Library name: {reason}"
        if name is not None:
            message += f" (got: '{name}')"

        super().__init__(
            message=message,
            code=self.code,
            http_status=self.http_status,
            details={
                "provided_name": name,
                "reason": reason,
                "constraints": {
                    "min_length": 1,
                    "max_length": 255,
                    "cannot_be_empty": True,
                    "cannot_be_whitespace_only": True,
                }
            }
        )


class LibraryUserAssociationError(LibraryException):
    """
    Raised when Library's user_id is invalid or missing.

    RULE-002: Library.user_id must reference a valid User.
    Every Library must have a valid user_id association.

    HTTP Status: 422 Unprocessable Entity
    """
    code = "LIBRARY_USER_ASSOCIATION_ERROR"
    http_status = 422

    def __init__(
        self,
        library_id: str,
        reason: str,
        user_id: Optional[str] = None,
    ):
        message = f"Library user association error: {reason}"

        super().__init__(
            message=message,
            code=self.code,
            http_status=self.http_status,
            details={
                "library_id": str(library_id),
                "user_id": str(user_id) if user_id else None,
                "reason": reason,
            }
        )


class LibraryOperationError(LibraryException):
    """
    Raised when a generic Library operation fails.

    Used for unexpected operation failures that don't fit other specific exception types.

    HTTP Status: 500 Internal Server Error
    """
    code = "LIBRARY_OPERATION_ERROR"
    http_status = 500

    def __init__(
        self,
        operation: str,
        reason: str,
        library_id: Optional[str] = None,
    ):
        message = f"Failed to {operation} Library"
        if library_id:
            message += f" {library_id}"
        message += f": {reason}"

        super().__init__(
            message=message,
            code=self.code,
            http_status=self.http_status,
            details={
                "operation": operation,
                "library_id": str(library_id) if library_id else None,
                "reason": reason,
            }
        )


# ============================================
# Infrastructure/Repository Exceptions
# ============================================

class RepositoryException(DomainException):
    """Base for Repository/Infrastructure layer exceptions"""
    code = "REPOSITORY_ERROR"
    http_status = 500


class LibraryPersistenceError(RepositoryException):
    """
    Raised when database persistence operation fails.

    Occurs when:
    - Database constraint violations
    - Integrity check failures
    - Transaction rollback
    - Database connection issues

    HTTP Status: 500 Internal Server Error
    """
    code = "LIBRARY_PERSISTENCE_ERROR"
    http_status = 500

    def __init__(
        self,
        operation: str,
        reason: str,
        original_error: Optional[Exception] = None,
    ):
        message = f"Failed to persist Library during {operation}: {reason}"

        super().__init__(
            message=message,
            code=self.code,
            http_status=self.http_status,
            details={
                "operation": operation,
                "reason": reason,
                "original_error": str(original_error) if original_error else None,
            }
        )


# ============================================
# Exception Helper Mapping
# ============================================

EXCEPTION_HTTP_STATUS_MAP = {
    LibraryNotFoundError: 404,
    LibraryAlreadyExistsError: 409,
    InvalidLibraryNameError: 422,
    LibraryUserAssociationError: 422,
    LibraryOperationError: 500,
    LibraryPersistenceError: 500,
}
