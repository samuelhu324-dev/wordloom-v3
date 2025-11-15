"""Media domain-specific exceptions - Business error hierarchy

POLICY-010: Media Management & Trash Lifecycle
POLICY-009: Media Storage & Quota Enforcement

All exceptions inherit from BusinessError base class.
Mapped to HTTP status codes in router layer.
"""

from typing import Optional
from uuid import UUID

from shared.errors import BusinessError


# ============================================================================
# Media-Specific Exceptions
# ============================================================================

class MediaNotFoundError(BusinessError):
    """Media with given ID does not exist."""
    status_code = 404
    error_code = "MEDIA_NOT_FOUND"
    message = "Media not found"

    def __init__(self, media_id: UUID, detail: Optional[str] = None):
        self.media_id = media_id
        self.detail = detail or f"Media {media_id} does not exist"
        super().__init__(self.message, self.detail)

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "media_id": str(self.media_id),
            "detail": self.detail
        }


class InvalidMimeTypeError(BusinessError):
    """POLICY-009: Unsupported or invalid MIME type for media."""
    status_code = 422
    error_code = "INVALID_MIME_TYPE"
    message = "Invalid MIME type"

    def __init__(self, mime_type: str, media_type: Optional[str] = None):
        self.mime_type = mime_type
        self.media_type = media_type
        detail = f"MIME type '{mime_type}' is not supported"
        if media_type:
            detail += f" for {media_type} media"
        super().__init__(self.message, detail)

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "mime_type": self.mime_type,
            "media_type": self.media_type,
            "detail": self.detail
        }


class FileSizeTooLargeError(BusinessError):
    """POLICY-009: File size exceeds type-specific limit."""
    status_code = 422
    error_code = "FILE_SIZE_TOO_LARGE"
    message = "File size exceeds limit"

    def __init__(self, media_type: str, file_size: int, max_size: int):
        self.media_type = media_type
        self.file_size = file_size
        self.max_size = max_size
        max_mb = max_size / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        detail = f"{media_type} file size ({actual_mb:.1f}MB) exceeds limit ({max_mb:.0f}MB)"
        super().__init__(self.message, detail)

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "media_type": self.media_type,
            "file_size": self.file_size,
            "max_size": self.max_size,
            "detail": self.detail
        }


class InvalidDimensionsError(BusinessError):
    """Image dimensions are invalid (too large, negative, etc.)."""
    status_code = 422
    error_code = "INVALID_DIMENSIONS"
    message = "Invalid image dimensions"

    def __init__(self, width: Optional[int], height: Optional[int], reason: str):
        self.width = width
        self.height = height
        detail = f"Image dimensions {width}x{height}: {reason}"
        super().__init__(self.message, detail)

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "width": self.width,
            "height": self.height,
            "detail": self.detail
        }


class InvalidDurationError(BusinessError):
    """Video duration is invalid (negative, zero, etc.)."""
    status_code = 422
    error_code = "INVALID_DURATION"
    message = "Invalid video duration"

    def __init__(self, duration_ms: Optional[int], reason: str):
        self.duration_ms = duration_ms
        detail = f"Video duration {duration_ms}ms: {reason}"
        super().__init__(self.message, detail)

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "duration_ms": self.duration_ms,
            "detail": self.detail
        }


class StorageQuotaExceededError(BusinessError):
    """POLICY-009: User/workspace storage quota exceeded."""
    status_code = 429
    error_code = "STORAGE_QUOTA_EXCEEDED"
    message = "Storage quota exceeded"

    def __init__(self, used: int, quota: int):
        self.used = used
        self.quota = quota
        used_gb = used / (1024 * 1024 * 1024)
        quota_gb = quota / (1024 * 1024 * 1024)
        detail = f"Used {used_gb:.2f}GB of {quota_gb:.2f}GB quota"
        super().__init__(self.message, detail)

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "used_bytes": self.used,
            "quota_bytes": self.quota,
            "detail": self.detail
        }


class MediaInTrashError(BusinessError):
    """POLICY-010: Cannot perform operation on media in trash."""
    status_code = 409
    error_code = "MEDIA_IN_TRASH"
    message = "Media is in trash"

    def __init__(self, media_id: UUID, operation: str = "access"):
        self.media_id = media_id
        self.operation = operation
        detail = f"Cannot {operation} media in trash (soft deleted)"
        super().__init__(self.message, detail)

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "media_id": str(self.media_id),
            "operation": self.operation,
            "detail": self.detail
        }


class CannotPurgeError(BusinessError):
    """POLICY-010: Cannot purge media (30-day trash retention not met)."""
    status_code = 409
    error_code = "CANNOT_PURGE"
    message = "Cannot purge media yet"

    def __init__(self, media_id: UUID, days_remaining: int):
        self.media_id = media_id
        self.days_remaining = days_remaining
        detail = f"Must wait {days_remaining} more days before purging (30-day retention)"
        super().__init__(self.message, detail)

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "media_id": str(self.media_id),
            "days_remaining": self.days_remaining,
            "detail": self.detail
        }


class CannotRestoreError(BusinessError):
    """Cannot restore media (not in trash or already purged)."""
    status_code = 409
    error_code = "CANNOT_RESTORE"
    message = "Cannot restore media"

    def __init__(self, media_id: UUID, reason: str):
        self.media_id = media_id
        detail = f"Cannot restore: {reason}"
        super().__init__(self.message, detail)

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "media_id": str(self.media_id),
            "detail": self.detail
        }


class AssociationError(BusinessError):
    """Cannot associate/disassociate media with entity."""
    status_code = 409
    error_code = "ASSOCIATION_ERROR"
    message = "Association operation failed"

    def __init__(self, media_id: UUID, entity_type: str, entity_id: UUID, reason: str):
        self.media_id = media_id
        self.entity_type = entity_type
        self.entity_id = entity_id
        detail = f"Cannot associate {entity_type}:{entity_id} with media: {reason}"
        super().__init__(self.message, detail)

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "media_id": str(self.media_id),
            "entity_type": self.entity_type,
            "entity_id": str(self.entity_id),
            "detail": self.detail
        }


class MediaOperationError(BusinessError):
    """Generic media operation error (internal error)."""
    status_code = 500
    error_code = "MEDIA_OPERATION_ERROR"
    message = "Media operation failed"

    def __init__(self, operation: str, reason: str):
        self.operation = operation
        detail = f"Operation '{operation}' failed: {reason}"
        super().__init__(self.message, detail)

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "operation": self.operation,
            "detail": self.detail
        }


# ============================================================================
# Repository-Level Exceptions
# ============================================================================

class MediaRepositoryException(BusinessError):
    """Base exception for repository layer errors."""
    status_code = 500
    error_code = "MEDIA_REPOSITORY_ERROR"
    message = "Media repository error"

    def __init__(self, detail: str):
        super().__init__(self.message, detail)


class MediaRepositoryQueryError(MediaRepositoryException):
    """Error querying media from database."""
    error_code = "MEDIA_QUERY_ERROR"
    message = "Query error"


class MediaRepositorySaveError(MediaRepositoryException):
    """Error saving media to database."""
    error_code = "MEDIA_SAVE_ERROR"
    message = "Save error"


class MediaRepositoryDeleteError(MediaRepositoryException):
    """Error deleting media from database."""
    error_code = "MEDIA_DELETE_ERROR"
    message = "Delete error"

