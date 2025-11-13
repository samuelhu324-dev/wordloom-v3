"""Media Module - File storage with trash lifecycle management

High-level exports for Media module components.

Domain Layer:
- Media: AggregateRoot for file representation
- MediaPath: ValueObject for file location/metadata
- MediaType: Enum (IMAGE, VIDEO)
- MediaMimeType: Enum for supported MIME types
- MediaState: Enum (ACTIVE, TRASH)
- EntityTypeForMedia: Enum (BOOKSHELF, BOOK, BLOCK)
- 6 DomainEvents: MediaUploaded, MediaAssociatedWithEntity, etc.

Exception Layer:
- MediaException: Base exception
- 11+ specific exceptions with HTTP status mapping
- RepositoryException: Persistence layer errors

Persistence Layer:
- MediaRepository: Abstract interface
- SQLAlchemyMediaRepository: ORM implementation
- MediaModel: SQLAlchemy ORM model
- MediaAssociationModel: Association ORM model

Service Layer:
- MediaService: Business logic (upload, delete, purge, restore)

API Layer:
- router: FastAPI endpoints
- Schemas: Pydantic request/response models
"""

# ============================================================================
# Domain Exports
# ============================================================================

from domain import (
    # Main aggregates
    Media,
    MediaPath,

    # Enums
    MediaType,
    MediaMimeType,
    MediaState,
    EntityTypeForMedia,

    # Domain events
    MediaUploaded,
    MediaAssociatedWithEntity,
    MediaDisassociatedFromEntity,
    MediaMovedToTrash,
    MediaRestored,
    MediaPurged,
)


# ============================================================================
# Exception Exports
# ============================================================================

from exceptions import (
    # Base exceptions
    DomainException,
    MediaException,

    # Domain exceptions
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

    # Repository exceptions
    MediaRepositoryException,
    MediaRepositoryQueryError,
    MediaRepositorySaveError,
    MediaRepositoryDeleteError,
)


# ============================================================================
# Repository Exports
# ============================================================================

from repository import (
    MediaRepository,
    SQLAlchemyMediaRepository,
)


# ============================================================================
# Models Exports
# ============================================================================

from models import (
    MediaModel,
    MediaAssociationModel,
)


# ============================================================================
# Service Exports
# ============================================================================

from service import (
    MediaService,
)


# ============================================================================
# Schema Exports
# ============================================================================

from schemas import (
    # Request schemas
    UploadMediaRequest,
    UpdateMediaMetadataRequest,
    AssociateMediaRequest,
    DisassociateMediaRequest,
    RestoreMediaRequest,
    BatchRestoreRequest,
    PurgeExpiredMediaRequest,

    # Response schemas
    MediaResponse,
    MediaListResponse,
    MediaTrashResponse,
    MediaTrashListResponse,
    MediaAssociationResponse,
    EntityMediaListResponse,
    BatchRestoreResponse,
    PurgeExpiredResponse,
    UploadMediaResponse,
    ErrorResponse,

    # Enums
    MediaTypeSchema,
    MediaMimeTypeSchema,
    MediaStateSchema,
    EntityTypeSchema,
)


# ============================================================================
# Router Exports
# ============================================================================

from router import (
    router,
    get_media_service,
)


# ============================================================================
# Public API
# ============================================================================

__all__ = [
    # Domain
    "Media",
    "MediaPath",
    "MediaType",
    "MediaMimeType",
    "MediaState",
    "EntityTypeForMedia",
    "MediaUploaded",
    "MediaAssociatedWithEntity",
    "MediaDisassociatedFromEntity",
    "MediaMovedToTrash",
    "MediaRestored",
    "MediaPurged",

    # Exceptions
    "DomainException",
    "MediaException",
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

    # Repository
    "MediaRepository",
    "SQLAlchemyMediaRepository",

    # Models
    "MediaModel",
    "MediaAssociationModel",

    # Service
    "MediaService",

    # Schemas
    "UploadMediaRequest",
    "UpdateMediaMetadataRequest",
    "AssociateMediaRequest",
    "DisassociateMediaRequest",
    "RestoreMediaRequest",
    "BatchRestoreRequest",
    "PurgeExpiredMediaRequest",
    "MediaResponse",
    "MediaListResponse",
    "MediaTrashResponse",
    "MediaTrashListResponse",
    "MediaAssociationResponse",
    "EntityMediaListResponse",
    "BatchRestoreResponse",
    "PurgeExpiredResponse",
    "UploadMediaResponse",
    "ErrorResponse",
    "MediaTypeSchema",
    "MediaMimeTypeSchema",
    "MediaStateSchema",
    "EntityTypeSchema",

    # Router
    "router",
    "get_media_service",
]
