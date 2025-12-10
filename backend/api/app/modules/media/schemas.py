"""Media Schemas - Pydantic v2 validation models

Request/Response models for Media API endpoints with field validation.

Follows Pydantic v2 patterns:
- BaseModel for all schemas
- Field() for constraints (min_length, max_length, regex, etc.)
- Validators for custom logic
- Config(from_attributes=True) for ORM conversion
- Optional fields with default=None for nullable columns
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class MediaTypeSchema(str, Enum):
    """Media type enum for API"""
    IMAGE = "image"
    VIDEO = "video"


class MediaMimeTypeSchema(str, Enum):
    """Supported MIME types"""
    # Images
    JPEG = "image/jpeg"
    PNG = "image/png"
    WEBP = "image/webp"
    GIF = "image/gif"

    # Videos
    MP4 = "video/mp4"
    WEBM = "video/webm"
    OGG = "video/ogg"


class MediaStateSchema(str, Enum):
    """Media state enum"""
    ACTIVE = "ACTIVE"
    TRASH = "TRASH"


class EntityTypeSchema(str, Enum):
    """Entity types that can reference media"""
    BOOKSHELF = "bookshelf"
    BOOK = "book"
    BLOCK = "block"


# ============================================================================
# Request Models
# ============================================================================

class UploadMediaRequest(BaseModel):
    """Request model for uploading media (multipart form data)

    Note: Actual file is handled by FastAPI UploadFile, not this schema.
    This schema is for metadata that accompanies the file upload.
    """
    # Media type will be inferred from MIME type in most cases
    # This allows explicit override if needed
    force_media_type: Optional[MediaTypeSchema] = Field(
        None,
        description="Force media type (optional, usually auto-detected from MIME type)"
    )

    # Optional metadata extraction
    extract_metadata: bool = Field(
        True,
        description="Whether to extract metadata (dimensions for images, duration for videos)"
    )


class UpdateMediaMetadataRequest(BaseModel):
    """Request model for updating media metadata (after extraction)"""
    width: Optional[int] = Field(
        None,
        ge=1,
        le=8000,
        description="Image width in pixels (1-8000)"
    )

    height: Optional[int] = Field(
        None,
        ge=1,
        le=8000,
        description="Image height in pixels (1-8000)"
    )

    duration_ms: Optional[int] = Field(
        None,
        ge=1,
        le=7200000,  # 2 hours
        description="Video duration in milliseconds (1-7200000)"
    )


class AssociateMediaRequest(BaseModel):
    """Request model for associating media with an entity"""
    entity_type: EntityTypeSchema = Field(
        ...,
        description="Type of entity (BOOKSHELF, BOOK, or BLOCK)"
    )

    entity_id: UUID = Field(
        ...,
        description="ID of the entity"
    )


class DisassociateMediaRequest(BaseModel):
    """Request model for removing media association"""
    entity_type: EntityTypeSchema = Field(
        ...,
        description="Type of entity"
    )

    entity_id: UUID = Field(
        ...,
        description="ID of the entity"
    )


class RestoreMediaRequest(BaseModel):
    """Request model for restoring media from trash"""
    # No additional fields needed - just the media_id from path


class BatchRestoreRequest(BaseModel):
    """Request model for batch restoring multiple media from trash"""
    media_ids: List[UUID] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of media IDs to restore (1-100)"
    )


class PurgeExpiredMediaRequest(BaseModel):
    """Request model for purging expired media"""
    dry_run: bool = Field(
        False,
        description="If True, returns what would be purged without actually deleting"
    )


# ============================================================================
# Response Models
# ============================================================================

class MediaResponse(BaseModel):
    """Response model for a single media file

    Contains full media information and metadata.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(
        ...,
        description="Media ID"
    )

    filename: str = Field(
        ...,
        description="Original filename with extension"
    )

    storage_key: str = Field(
        ...,
        description="Unique identifier in storage backend"
    )

    media_type: MediaTypeSchema = Field(
        ...,
        description="Type of media (IMAGE or VIDEO)"
    )

    mime_type: MediaMimeTypeSchema = Field(
        ...,
        description="MIME type of the file"
    )

    file_size: int = Field(
        ...,
        description="File size in bytes"
    )

    width: Optional[int] = Field(
        None,
        description="Image width in pixels (for images only)"
    )

    height: Optional[int] = Field(
        None,
        description="Image height in pixels (for images only)"
    )

    duration_ms: Optional[int] = Field(
        None,
        description="Video duration in milliseconds (for videos only)"
    )

    state: MediaStateSchema = Field(
        ...,
        description="Current state (ACTIVE or TRASH)"
    )

    trash_at: Optional[datetime] = Field(
        None,
        description="Timestamp when moved to trash (NULL if not in trash)"
    )

    created_at: datetime = Field(
        ...,
        description="Upload timestamp"
    )

    updated_at: datetime = Field(
        ...,
        description="Last update timestamp"
    )

    @field_validator("file_size")
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        """Ensure file size is positive"""
        if v <= 0:
            raise ValueError("file_size must be positive")
        return v


class MediaListResponse(BaseModel):
    """Response model for paginated media list"""
    items: List[MediaResponse] = Field(
        ...,
        description="List of media items"
    )

    total: int = Field(
        ...,
        ge=0,
        description="Total number of media items"
    )

    skip: int = Field(
        ...,
        ge=0,
        description="Number of items skipped"
    )

    limit: int = Field(
        ...,
        gt=0,
        description="Maximum items per page"
    )


class MediaTrashResponse(BaseModel):
    """Response model for media in trash with retention info"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(
        ...,
        description="Media ID"
    )

    filename: str = Field(
        ...,
        description="Original filename"
    )

    file_size: int = Field(
        ...,
        description="File size in bytes"
    )

    media_type: MediaTypeSchema = Field(
        ...,
        description="Type of media"
    )

    trash_at: datetime = Field(
        ...,
        description="When moved to trash"
    )

    days_until_purge: int = Field(
        ...,
        ge=0,
        description="Days remaining until auto-purge (0 = eligible for purge)"
    )

    eligible_for_purge: bool = Field(
        ...,
        description="Whether this item can be purged now"
    )


class MediaTrashListResponse(BaseModel):
    """Response model for paginated trash list"""
    items: List[MediaTrashResponse] = Field(
        ...,
        description="List of trash media items"
    )

    total: int = Field(
        ...,
        ge=0,
        description="Total items in trash"
    )

    skip: int = Field(
        ...,
        ge=0,
        description="Number of items skipped"
    )

    limit: int = Field(
        ...,
        gt=0,
        description="Maximum items per page"
    )


class MediaAssociationResponse(BaseModel):
    """Response model for media association"""
    model_config = ConfigDict(from_attributes=True)

    media_id: UUID = Field(
        ...,
        description="Media ID"
    )

    entity_type: EntityTypeSchema = Field(
        ...,
        description="Type of entity"
    )

    entity_id: UUID = Field(
        ...,
        description="ID of entity"
    )

    created_at: datetime = Field(
        ...,
        description="Association creation timestamp"
    )


class EntityMediaListResponse(BaseModel):
    """Response model for all media associated with an entity"""
    entity_type: EntityTypeSchema = Field(
        ...,
        description="Type of entity"
    )

    entity_id: UUID = Field(
        ...,
        description="ID of entity"
    )

    media_items: List[MediaResponse] = Field(
        ...,
        description="List of media associated with entity"
    )

    count: int = Field(
        ...,
        ge=0,
        description="Total count of media items"
    )


class BatchRestoreResponse(BaseModel):
    """Response model for batch restore operation"""
    total_requested: int = Field(
        ...,
        description="Total media IDs requested to restore"
    )

    restored_count: int = Field(
        ...,
        description="Number successfully restored"
    )

    failed_count: int = Field(
        ...,
        description="Number that failed to restore"
    )

    failed_media_ids: List[UUID] = Field(
        default_factory=list,
        description="IDs that failed to restore"
    )


class PurgeExpiredResponse(BaseModel):
    """Response model for purge operation"""
    purged_count: int = Field(
        ...,
        description="Number of media items purged"
    )

    purged_size_bytes: int = Field(
        ...,
        ge=0,
        description="Total size of purged media in bytes"
    )

    remaining_trash_count: int = Field(
        ...,
        ge=0,
        description="Number of items still in trash"
    )


class UploadMediaResponse(BaseModel):
    """Response model for successful media upload"""
    media: MediaResponse = Field(
        ...,
        description="Uploaded media details"
    )

    upload_url: Optional[str] = Field(
        None,
        description="Presigned URL for direct upload (if applicable)"
    )

    message: str = Field(
        ...,
        description="Status message"
    )


class ErrorResponse(BaseModel):
    """Response model for error responses"""
    code: str = Field(
        ...,
        description="Error code (e.g., MEDIA_NOT_FOUND)"
    )

    message: str = Field(
        ...,
        description="Human-readable error message"
    )

    details: Optional[dict] = Field(
        None,
        description="Additional error details"
    )

    http_status: int = Field(
        ...,
        description="HTTP status code"
    )
