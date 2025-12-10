"""
Shared domain/application exceptions.

These are lightweight HTTP-aware exceptions that application layer
use cases raise when domain invariants or resource lookups fail.
They complement the module-specific exception hierarchies but keep
common cases (404, 409) in one place for reuse.
"""

from typing import Any, Dict, Optional


class DomainException(Exception):
    """Base exception that carries an HTTP status and optional details."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "DOMAIN_ERROR",
        http_status: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status
        self.details = details or {}

    @property
    def http_status_code(self) -> int:
        """Expose http_status via a legacy-friendly name."""
        return self.http_status

    def to_dict(self) -> Dict[str, Any]:
        """Serialize exception to a common API-friendly shape."""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self) -> str:  # pragma: no cover - std repr
        return self.message


class ResourceNotFoundError(DomainException):
    """404 error when a referenced resource is missing."""

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        final_details = details or {}
        if resource_type:
            final_details.setdefault("resource_type", resource_type)
        if resource_id:
            final_details.setdefault("resource_id", resource_id)
        super().__init__(
            message or "Requested resource was not found",
            code="RESOURCE_NOT_FOUND",
            http_status=404,
            details=final_details,
        )


class IllegalStateError(DomainException):
    """409 error when an operation is attempted in an invalid state."""

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message or "Operation cannot be completed in the current state",
            code="ILLEGAL_STATE",
            http_status=409,
            details=details,
        )
