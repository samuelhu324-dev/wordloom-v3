"""Basement-specific exception types."""
from __future__ import annotations

from typing import Optional

from api.app.modules.book.exceptions import DomainException


class BasementError(DomainException):
    """Base error for Basement workflows."""


class BookAlreadyInBasementError(BasementError):
    code = "BOOK_ALREADY_IN_BASEMENT"
    http_status = 409

    def __init__(self, book_id: str):
        super().__init__(
            message=f"Book {book_id} is already stored in Basement",
            details={"book_id": book_id},
        )


class ForbiddenBasementOperationError(BasementError):
    code = "BASEMENT_OPERATION_FORBIDDEN"
    http_status = 403

    def __init__(self, *, book_id: str, reason: str, actor_id: Optional[str] = None):
        super().__init__(
            message=f"Operation rejected for Book {book_id}: {reason}",
            details={
                "book_id": book_id,
                "actor_id": actor_id,
                "reason": reason,
            },
        )
