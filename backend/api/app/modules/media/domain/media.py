"""Media AggregateRoot and ValueObjects - Core domain logic

POLICY-010: Media Management & Trash Lifecycle
POLICY-009: Media Storage & Quota Enforcement

Pure domain layer with zero infrastructure dependencies.
All domain logic and invariants implemented here.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

from shared.base import AggregateRoot, ValueObject, DomainEvent
from .enums import MediaType, MediaMimeType, MediaState, EntityTypeForMedia
from .events import (
    MediaUploaded, MediaAssociatedWithEntity, MediaDisassociatedFromEntity,
    MediaMovedToTrash, MediaRestored, MediaPurged
)


# ============================================================================
# Value Objects
# ============================================================================

@dataclass(frozen=True)
class MediaPath(ValueObject):
    """
    Immutable file path and location metadata

    Invariants:
    - storage_key: unique identifier in storage backend (e.g., S3 key, local path)
    - filename: original filename with extension
    - mime_type: must be from MediaMimeType enum
    - file_size: must be > 0 and within limits (10MB for image, 100MB for video)
    """
    storage_key: str
    filename: str
    mime_type: MediaMimeType
    file_size: int

    def __post_init__(self):
        if not self.storage_key or not self.storage_key.strip():
            raise ValueError("storage_key cannot be empty")
        if not self.filename or not self.filename.strip():
            raise ValueError("filename cannot be empty")
        if self.file_size <= 0:
            raise ValueError("file_size must be positive")

    def __eq__(self, other: object) -> bool:
        """Two paths are equal if they point to same storage location"""
        if not isinstance(other, MediaPath):
            return NotImplemented
        return self.storage_key == other.storage_key

    def __hash__(self) -> int:
        return hash(self.storage_key)


# ============================================================================
# Aggregate Root
# ============================================================================

@dataclass
class Media(AggregateRoot):
    """
    Media Aggregate Root - File with metadata and lifecycle management

    Invariants (POLICY-010: Media Management & Trash):
    - id: unique UUID
    - filename: non-empty string with extension
    - media_type: IMAGE or VIDEO
    - mime_type: from MediaMimeType enum (validated on creation)
    - file_size: positive integer within type limits
    - state: ACTIVE or TRASH (soft delete)
    - storage_key: unique identifier in storage backend
    - width/height: dimensions for images (optional for videos)
    - duration_ms: length for videos (optional for images)
    - trash_at: timestamp when moved to trash (for 30-day retention)
    - created_at: immutable upload timestamp
    - updated_at: updated on state changes
    - deleted_at: hard delete marker (only after 30-day retention)

    Rules:
    - POLICY-010: Files in trash auto-purge after 30 days
    - POLICY-009: Storage quota enforced per user/workspace
    - NO automatic cleanup of associations (orphaned references allowed)
    - Soft delete preserves associations for audit trail
    """

    id: UUID
    filename: str
    media_type: MediaType
    mime_type: MediaMimeType
    file_size: int
    storage_key: str

    # Image/Video metadata
    width: Optional[int] = None
    height: Optional[int] = None
    duration_ms: Optional[int] = None

    # State management
    state: MediaState = MediaState.ACTIVE
    trash_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Event tracking
    _events: List[DomainEvent] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """Validate invariants on creation"""
        self._validate_filename()
        self._validate_file_size()
        self._validate_mime_type()

    def _validate_filename(self) -> None:
        """Filename must be non-empty and have extension"""
        if not self.filename or not self.filename.strip():
            raise ValueError("Filename cannot be empty")
        if "." not in self.filename:
            raise ValueError("Filename must have extension")
        if len(self.filename) > 255:
            raise ValueError("Filename must be <= 255 characters")

    def _validate_file_size(self) -> None:
        """Validate file size limits based on media type"""
        if self.file_size <= 0:
            raise ValueError("File size must be positive")

        # Type-specific limits
        if self.media_type == MediaType.IMAGE:
            max_size = 10 * 1024 * 1024  # 10MB for images
            if self.file_size > max_size:
                raise ValueError(f"Image file size must be <= 10MB, got {self.file_size} bytes")
        elif self.media_type == MediaType.VIDEO:
            max_size = 100 * 1024 * 1024  # 100MB for videos
            if self.file_size > max_size:
                raise ValueError(f"Video file size must be <= 100MB, got {self.file_size} bytes")

    def _validate_mime_type(self) -> None:
        """Validate MIME type matches media type"""
        if self.media_type == MediaType.IMAGE:
            image_types = {
                MediaMimeType.JPEG, MediaMimeType.PNG,
                MediaMimeType.WEBP, MediaMimeType.GIF
            }
            if self.mime_type not in image_types:
                raise ValueError(
                    f"Invalid image MIME type: {self.mime_type}. "
                    f"Allowed: {', '.join(t.value for t in image_types)}"
                )
        elif self.media_type == MediaType.VIDEO:
            video_types = {
                MediaMimeType.MP4, MediaMimeType.WEBM, MediaMimeType.OGG
            }
            if self.mime_type not in video_types:
                raise ValueError(
                    f"Invalid video MIME type: {self.mime_type}. "
                    f"Allowed: {', '.join(t.value for t in video_types)}"
                )

    @staticmethod
    def create_image(
        filename: str,
        mime_type: MediaMimeType,
        file_size: int,
        storage_key: str,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Media:
        """Factory: Create a new Image media"""
        media = Media(
            id=uuid4(),
            filename=filename,
            media_type=MediaType.IMAGE,
            mime_type=mime_type,
            file_size=file_size,
            storage_key=storage_key,
            width=width,
            height=height,
            state=MediaState.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        media._events.append(MediaUploaded(
            media_id=media.id,
            filename=filename,
            media_type=MediaType.IMAGE,
            mime_type=mime_type,
            file_size=file_size
        ))
        return media

    @staticmethod
    def create_video(
        filename: str,
        mime_type: MediaMimeType,
        file_size: int,
        storage_key: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        duration_ms: Optional[int] = None
    ) -> Media:
        """Factory: Create a new Video media"""
        media = Media(
            id=uuid4(),
            filename=filename,
            media_type=MediaType.VIDEO,
            mime_type=mime_type,
            file_size=file_size,
            storage_key=storage_key,
            width=width,
            height=height,
            duration_ms=duration_ms,
            state=MediaState.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        media._events.append(MediaUploaded(
            media_id=media.id,
            filename=filename,
            media_type=MediaType.VIDEO,
            mime_type=mime_type,
            file_size=file_size
        ))
        return media

    def associate_with_entity(
        self,
        entity_type: EntityTypeForMedia,
        entity_id: UUID
    ) -> None:
        """Link this media to an entity (Bookshelf/Book/Block)"""
        if self.is_in_trash():
            raise ValueError(f"Cannot associate trash media {self.id} with entity")

        self._events.append(MediaAssociatedWithEntity(
            media_id=self.id,
            entity_type=entity_type,
            entity_id=entity_id
        ))
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

    def disassociate_from_entity(
        self,
        entity_type: EntityTypeForMedia,
        entity_id: UUID
    ) -> None:
        """Remove link between this media and an entity"""
        self._events.append(MediaDisassociatedFromEntity(
            media_id=self.id,
            entity_type=entity_type,
            entity_id=entity_id
        ))
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

    def move_to_trash(self) -> None:
        """Soft delete: move to trash with 30-day retention (POLICY-010)"""
        if self.is_in_trash():
            raise ValueError(f"Media {self.id} is already in trash")

        object.__setattr__(self, "state", MediaState.TRASH)
        object.__setattr__(self, "trash_at", datetime.now(timezone.utc))
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

        self._events.append(MediaMovedToTrash(media_id=self.id))

    def restore_from_trash(self) -> None:
        """Restore from trash to active state"""
        if not self.is_in_trash():
            raise ValueError(f"Media {self.id} is not in trash")

        object.__setattr__(self, "state", MediaState.ACTIVE)
        object.__setattr__(self, "trash_at", None)
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

        self._events.append(MediaRestored(media_id=self.id))

    def purge(self) -> None:
        """Hard delete: permanently remove (after 30-day trash retention)"""
        if not self.is_in_trash():
            raise ValueError(f"Media {self.id} is not in trash")

        # Check if 30 days have passed
        if self.trash_at:
            trash_duration = datetime.now(timezone.utc) - self.trash_at
            thirty_days = timedelta(days=30)
            if trash_duration < thirty_days:
                days_remaining = (thirty_days - trash_duration).days
                raise ValueError(
                    f"Cannot purge: media must stay in trash for 30 days. "
                    f"{days_remaining} days remaining."
                )

        object.__setattr__(self, "deleted_at", datetime.now(timezone.utc))
        self._events.append(MediaPurged(media_id=self.id))

    def is_in_trash(self) -> bool:
        """Check if media is in trash state"""
        return self.state == MediaState.TRASH

    def is_purged(self) -> bool:
        """Check if media is permanently deleted"""
        return self.deleted_at is not None

    def is_eligible_for_purge(self) -> bool:
        """Check if media can be purged (30 days in trash)"""
        if not self.is_in_trash() or not self.trash_at:
            return False

        trash_duration = datetime.now(timezone.utc) - self.trash_at
        thirty_days = timedelta(days=30)
        return trash_duration >= thirty_days

    def update_dimensions(self, width: int, height: int) -> None:
        """Update image dimensions (extracted after upload)"""
        if self.media_type != MediaType.IMAGE:
            raise ValueError("Cannot update dimensions for non-image media")

        object.__setattr__(self, "width", width)
        object.__setattr__(self, "height", height)
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

    def update_duration(self, duration_ms: int) -> None:
        """Update video duration (extracted after upload)"""
        if self.media_type != MediaType.VIDEO:
            raise ValueError("Cannot update duration for non-video media")
        if duration_ms <= 0:
            raise ValueError("Duration must be positive")

        object.__setattr__(self, "duration_ms", duration_ms)
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

    def get_storage_path(self) -> str:
        """Get the storage key for this media"""
        return self.storage_key

    def get_file_extension(self) -> str:
        """Get file extension from filename"""
        if "." not in self.filename:
            return ""
        return self.filename.split(".")[-1].lower()

    # DomainEvent tracking (inherited from AggregateRoot)
    @property
    def events(self) -> List[DomainEvent]:
        """Get all uncommitted domain events"""
        return self._events.copy()

    def clear_events(self) -> None:
        """Clear all uncommitted events (called after persistence)"""
        self._events.clear()

