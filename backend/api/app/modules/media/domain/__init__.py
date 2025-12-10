"""Media domain layer - Pure business logic, zero infrastructure dependencies

POLICY-010: Media Management & Trash Lifecycle
POLICY-009: Media Storage & Quota Enforcement

Public API:
- Media: AggregateRoot
- MediaPath: ValueObject
- MediaType, MediaMimeType, MediaState, EntityTypeForMedia: Enums
- DomainEvents: MediaUploaded, MediaAssociatedWithEntity, etc.
- Exceptions: MediaNotFoundError, MediaInTrashError, etc.
"""

# Enums
from .enums import MediaType, MediaMimeType, MediaState, EntityTypeForMedia

# Domain Model
from .media import Media, MediaPath

# Domain Events
from .events import (
    MediaUploaded,
    MediaAssociatedWithEntity,
    MediaDisassociatedFromEntity,
    MediaMovedToTrash,
    MediaRestored,
    MediaPurged,
)

# Exceptions
from .exceptions import (
    MediaNotFoundError,
    InvalidMimeTypeError,
    FileSizeTooLargeError,
    InvalidDimensionsError,
    InvalidDurationError,
    StorageQuotaExceededError,
    MediaInTrashError,
    CannotPurgeError,
    CannotRestoreError,
    AssociationError,
    MediaOperationError,
    MediaRepositoryException,
    MediaRepositoryQueryError,
    MediaRepositorySaveError,
    MediaRepositoryDeleteError,
)

__all__ = [
    # Enums
    "MediaType",
    "MediaMimeType",
    "MediaState",
    "EntityTypeForMedia",
    # Domain Model
    "Media",
    "MediaPath",
    # Events
    "MediaUploaded",
    "MediaAssociatedWithEntity",
    "MediaDisassociatedFromEntity",
    "MediaMovedToTrash",
    "MediaRestored",
    "MediaPurged",
    # Exceptions
    "MediaNotFoundError",
    "InvalidMimeTypeError",
    "FileSizeTooLargeError",
    "InvalidDimensionsError",
    "InvalidDurationError",
    "StorageQuotaExceededError",
    "MediaInTrashError",
    "CannotPurgeError",
    "CannotRestoreError",
    "AssociationError",
    "MediaOperationError",
    "MediaRepositoryException",
    "MediaRepositoryQueryError",
    "MediaRepositorySaveError",
    "MediaRepositoryDeleteError",
]
