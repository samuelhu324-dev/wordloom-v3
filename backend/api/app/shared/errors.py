"""
Domain-level business errors

These represent violations of domain invariants and business rules.
Different from SystemException (infrastructure level in core.exceptions).

Pattern:
- Raised when domain rules are violated
- Caught and mapped to HTTP 422 Unprocessable Entity by default
- Can be caught specifically in application layer for recovery

Modules should extend BusinessError for their domain-specific errors.
"""

from typing import Optional, Dict, Any


class BusinessError(Exception):
    """
    Base business error - represents violation of domain invariants

    Characteristics:
    - Raised when domain rules/business logic is violated
    - HTTP 422 by default (vs 500 for SystemException)
    - Contains error_code for API clients

    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code (e.g., "LIBRARY_ALREADY_EXISTS")
        http_status_code: Corresponding HTTP status code (default 422)
        details: Additional context (dict)
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 422,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.http_status_code = http_status_code
        self.details = details or {}
        super().__init__(self.message)


# ============================================================================
# Library Domain Errors
# ============================================================================

class LibraryError(BusinessError):
    """Base Library domain error"""

    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 422,
        details: Optional[Dict] = None,
    ):
        super().__init__(message, error_code, http_status_code, details)


class LibraryNotFoundError(LibraryError):
    """Library does not exist"""

    def __init__(self, library_id: str):
        super().__init__(
            message=f"Library '{library_id}' not found",
            error_code="LIBRARY_NOT_FOUND",
            http_status_code=404,
        )


class LibraryAlreadyExistsError(LibraryError):
    """User already has a library (violates RULE-001)"""

    def __init__(self):
        super().__init__(
            message="User can only have one library (RULE-001 violation)",
            error_code="LIBRARY_ALREADY_EXISTS",
            http_status_code=409,
        )


# ============================================================================
# Bookshelf Domain Errors
# ============================================================================

class BookshelfError(BusinessError):
    """Base Bookshelf domain error"""

    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 422,
        details: Optional[Dict] = None,
    ):
        super().__init__(message, error_code, http_status_code, details)


class BookshelfNotFoundError(BookshelfError):
    """Bookshelf does not exist"""

    def __init__(self, bookshelf_id: str):
        super().__init__(
            message=f"Bookshelf '{bookshelf_id}' not found",
            error_code="BOOKSHELF_NOT_FOUND",
            http_status_code=404,
        )


class BookshelfCannotDeleteBasementError(BookshelfError):
    """Cannot delete Basement bookshelf (RULE-010)"""

    def __init__(self):
        super().__init__(
            message="Cannot delete Basement bookshelf (RULE-010 violation)",
            error_code="BASEMENT_DELETE_FORBIDDEN",
            http_status_code=422,
        )


class BookshelfNameDuplicateError(BookshelfError):
    """Bookshelf name already exists in library (RULE-006)"""

    def __init__(self, name: str, library_id: str):
        super().__init__(
            message=f"Bookshelf name '{name}' already exists in library (RULE-006 violation)",
            error_code="BOOKSHELF_DUPLICATE_NAME",
            http_status_code=409,
            details={"name": name, "library_id": library_id},
        )


# ============================================================================
# Book Domain Errors
# ============================================================================

class BookError(BusinessError):
    """Base Book domain error"""

    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 422,
        details: Optional[Dict] = None,
    ):
        super().__init__(message, error_code, http_status_code, details)


class BookNotFoundError(BookError):
    """Book does not exist"""

    def __init__(self, book_id: str):
        super().__init__(
            message=f"Book '{book_id}' not found",
            error_code="BOOK_NOT_FOUND",
            http_status_code=404,
        )


class BookPermissionError(BookError):
    """User does not have permission (cross-library access - RULE-011)"""

    def __init__(self, book_id: str):
        super().__init__(
            message=f"Permission denied for Book '{book_id}' (RULE-011 violation)",
            error_code="BOOK_PERMISSION_DENIED",
            http_status_code=403,
        )


class BookInvalidBasementError(BookError):
    """Target is not a valid Basement (RULE-013)"""

    def __init__(self):
        super().__init__(
            message="Target bookshelf is not a Basement (RULE-013 violation)",
            error_code="BOOK_INVALID_BASEMENT",
            http_status_code=422,
        )


# ============================================================================
# Block Domain Errors
# ============================================================================

class BlockError(BusinessError):
    """Base Block domain error"""

    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 422,
        details: Optional[Dict] = None,
    ):
        super().__init__(message, error_code, http_status_code, details)


class BlockNotFoundError(BlockError):
    """Block does not exist"""

    def __init__(self, block_id: str):
        super().__init__(
            message=f"Block '{block_id}' not found",
            error_code="BLOCK_NOT_FOUND",
            http_status_code=404,
        )


class BlockInvalidTypeError(BlockError):
    """Block type is invalid"""

    def __init__(self, block_type: str):
        super().__init__(
            message=f"Block type '{block_type}' is invalid",
            error_code="BLOCK_INVALID_TYPE",
            http_status_code=422,
        )


# ============================================================================
# Tag Domain Errors
# ============================================================================

class TagError(BusinessError):
    """Base Tag domain error"""

    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 422,
        details: Optional[Dict] = None,
    ):
        super().__init__(message, error_code, http_status_code, details)


class TagNotFoundError(TagError):
    """Tag does not exist"""

    def __init__(self, tag_id: str):
        super().__init__(
            message=f"Tag '{tag_id}' not found",
            error_code="TAG_NOT_FOUND",
            http_status_code=404,
        )


class TagNameDuplicateError(TagError):
    """Tag name already exists (RULE-018)"""

    def __init__(self, name: str):
        super().__init__(
            message=f"Tag name '{name}' already exists (RULE-018 violation)",
            error_code="TAG_DUPLICATE_NAME",
            http_status_code=409,
        )


# ============================================================================
# Media Domain Errors
# ============================================================================

class MediaError(BusinessError):
    """Base Media domain error"""

    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 422,
        details: Optional[Dict] = None,
    ):
        super().__init__(message, error_code, http_status_code, details)


class MediaNotFoundError(MediaError):
    """Media file does not exist"""

    def __init__(self, media_id: str):
        super().__init__(
            message=f"Media '{media_id}' not found",
            error_code="MEDIA_NOT_FOUND",
            http_status_code=404,
        )


class MediaStorageQuotaExceededError(MediaError):
    """Storage quota exceeded (POLICY-009)"""

    def __init__(self, user_id: str):
        super().__init__(
            message=f"Storage quota exceeded for user '{user_id}' (POLICY-009 violation)",
            error_code="MEDIA_QUOTA_EXCEEDED",
            http_status_code=422,
        )
