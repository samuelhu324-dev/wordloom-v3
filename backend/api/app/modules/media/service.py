"""Media Service - Business logic layer

Service layer for Media domain, handling:
- File upload with validation (MIME type, size, metadata extraction)
- Soft delete to trash with 30-day retention (POLICY-010)
- Hard purge after retention period
- Media-entity association management
- Storage quota enforcement (POLICY-009)
- Trash lifecycle management

Key Responsibilities:
1. Validate upload MIME types and file sizes
2. Extract metadata (dimensions for images, duration for videos)
3. Enforce storage quotas
4. Manage trash retention (30 days)
5. Handle purge operations
6. Update domain state via repository
"""

from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timezone

from domain import (
    Media,
    MediaType,
    MediaMimeType,
    MediaState,
    EntityTypeForMedia
)
from repository import MediaRepository
from exceptions import (
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
)


# ============================================================================
# Constants
# ============================================================================

# File size limits (bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
DEFAULT_STORAGE_QUOTA = 1024 * 1024 * 1024  # 1GB

# Supported MIME types
SUPPORTED_IMAGE_MIMES = {
    MediaMimeType.JPEG,
    MediaMimeType.PNG,
    MediaMimeType.WEBP,
    MediaMimeType.GIF,
}

SUPPORTED_VIDEO_MIMES = {
    MediaMimeType.MP4,
    MediaMimeType.WEBM,
    MediaMimeType.OGG,
}


# ============================================================================
# Media Service
# ============================================================================

class MediaService:
    """Service for Media operations"""

    def __init__(self, repository: MediaRepository):
        """Initialize service with repository"""
        self.repository = repository

    # ========================================================================
    # Upload Operations
    # ========================================================================

    async def upload_image(
        self,
        filename: str,
        mime_type: MediaMimeType,
        file_size: int,
        storage_key: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        storage_quota: int = DEFAULT_STORAGE_QUOTA,
        used_storage: int = 0
    ) -> Media:
        """Upload and validate an image

        Args:
            filename: Original filename with extension
            mime_type: Image MIME type
            file_size: File size in bytes
            storage_key: Unique identifier in storage backend
            width: Image width (optional, extracted after upload)
            height: Image height (optional, extracted after upload)
            storage_quota: User's storage quota in bytes
            used_storage: Currently used storage in bytes

        Returns:
            Media: Uploaded media object

        Raises:
            InvalidMimeTypeError: If MIME type not supported
            FileSizeTooLargeError: If file exceeds size limit
            InvalidDimensionsError: If dimensions invalid
            StorageQuotaExceededError: If quota exceeded
        """
        # Validate MIME type
        if mime_type not in SUPPORTED_IMAGE_MIMES:
            raise InvalidMimeTypeError(
                mime_type.value,
                "image"
            )

        # Validate file size
        if file_size > MAX_IMAGE_SIZE:
            raise FileSizeTooLargeError(
                "image",
                file_size,
                MAX_IMAGE_SIZE
            )

        # Validate storage quota
        if used_storage + file_size > storage_quota:
            needed = used_storage + file_size - storage_quota
            raise StorageQuotaExceededError(
                used_storage,
                storage_quota,
                needed
            )

        # Validate dimensions if provided
        if width is not None and height is not None:
            self._validate_image_dimensions(width, height)

        # Create media domain object
        media = Media.create_image(
            filename=filename,
            mime_type=mime_type,
            file_size=file_size,
            storage_key=storage_key,
            width=width,
            height=height
        )

        # Persist
        return await self.repository.save(media)

    async def upload_video(
        self,
        filename: str,
        mime_type: MediaMimeType,
        file_size: int,
        storage_key: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        duration_ms: Optional[int] = None,
        storage_quota: int = DEFAULT_STORAGE_QUOTA,
        used_storage: int = 0
    ) -> Media:
        """Upload and validate a video

        Args:
            filename: Original filename with extension
            mime_type: Video MIME type
            file_size: File size in bytes
            storage_key: Unique identifier in storage backend
            width: Video width (optional)
            height: Video height (optional)
            duration_ms: Video duration in milliseconds (optional)
            storage_quota: User's storage quota in bytes
            used_storage: Currently used storage in bytes

        Returns:
            Media: Uploaded media object

        Raises:
            InvalidMimeTypeError: If MIME type not supported
            FileSizeTooLargeError: If file exceeds size limit
            InvalidDurationError: If duration invalid
            StorageQuotaExceededError: If quota exceeded
        """
        # Validate MIME type
        if mime_type not in SUPPORTED_VIDEO_MIMES:
            raise InvalidMimeTypeError(
                mime_type.value,
                "video"
            )

        # Validate file size
        if file_size > MAX_VIDEO_SIZE:
            raise FileSizeTooLargeError(
                "video",
                file_size,
                MAX_VIDEO_SIZE
            )

        # Validate storage quota
        if used_storage + file_size > storage_quota:
            needed = used_storage + file_size - storage_quota
            raise StorageQuotaExceededError(
                used_storage,
                storage_quota,
                needed
            )

        # Validate duration if provided
        if duration_ms is not None:
            self._validate_video_duration(duration_ms)

        # Create media domain object
        media = Media.create_video(
            filename=filename,
            mime_type=mime_type,
            file_size=file_size,
            storage_key=storage_key,
            width=width,
            height=height,
            duration_ms=duration_ms
        )

        # Persist
        return await self.repository.save(media)

    # ========================================================================
    # Metadata Operations
    # ========================================================================

    async def update_image_metadata(
        self,
        media_id: UUID,
        width: int,
        height: int
    ) -> Media:
        """Update image dimensions after extraction

        Args:
            media_id: Media ID
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            Media: Updated media object

        Raises:
            MediaNotFoundError: If media not found
            InvalidDimensionsError: If dimensions invalid
        """
        media = await self.repository.get_by_id(media_id)
        if not media:
            raise MediaNotFoundError(media_id)

        self._validate_image_dimensions(width, height)

        media.update_dimensions(width, height)
        return await self.repository.save(media)

    async def update_video_metadata(
        self,
        media_id: UUID,
        duration_ms: int
    ) -> Media:
        """Update video duration after extraction

        Args:
            media_id: Media ID
            duration_ms: Video duration in milliseconds

        Returns:
            Media: Updated media object

        Raises:
            MediaNotFoundError: If media not found
            InvalidDurationError: If duration invalid
        """
        media = await self.repository.get_by_id(media_id)
        if not media:
            raise MediaNotFoundError(media_id)

        self._validate_video_duration(duration_ms)

        media.update_duration(duration_ms)
        return await self.repository.save(media)

    # ========================================================================
    # Trash & Lifecycle Operations
    # ========================================================================

    async def delete_media(self, media_id: UUID) -> Media:
        """Soft delete media to trash

        Args:
            media_id: Media ID to delete

        Returns:
            Media: Updated media object in trash

        Raises:
            MediaNotFoundError: If media not found
            MediaInTrashError: If already in trash
        """
        media = await self.repository.get_by_id(media_id)
        if not media:
            raise MediaNotFoundError(media_id)

        if media.is_in_trash():
            raise MediaInTrashError(media_id, "delete")

        media.move_to_trash()
        return await self.repository.save(media)

    async def restore_media(self, media_id: UUID) -> Media:
        """Restore media from trash

        Args:
            media_id: Media ID to restore

        Returns:
            Media: Restored media object

        Raises:
            MediaNotFoundError: If media not found
            CannotRestoreError: If not in trash
        """
        media = await self.repository.get_by_id(media_id)
        if not media:
            raise MediaNotFoundError(media_id)

        if not media.is_in_trash():
            raise CannotRestoreError(
                media_id,
                "Media is not in trash"
            )

        media.restore_from_trash()
        return await self.repository.save(media)

    async def restore_batch(self, media_ids: List[UUID]) -> Tuple[int, List[UUID]]:
        """Restore multiple media from trash

        Args:
            media_ids: List of media IDs to restore

        Returns:
            Tuple of (restored_count, failed_ids)
        """
        restored_count = 0
        failed_ids = []

        for media_id in media_ids:
            try:
                await self.restore_media(media_id)
                restored_count += 1
            except Exception:
                failed_ids.append(media_id)

        return restored_count, failed_ids

    async def purge_media(self, media_id: UUID) -> None:
        """Hard delete media after 30-day retention

        Args:
            media_id: Media ID to purge

        Raises:
            MediaNotFoundError: If media not found
            CannotPurgeError: If not eligible for purge
        """
        media = await self.repository.get_by_id(media_id)
        if not media:
            raise MediaNotFoundError(media_id)

        if not media.is_eligible_for_purge():
            days_remaining = 0
            if media.trash_at:
                from datetime import timedelta
                trash_duration = datetime.now(timezone.utc) - media.trash_at
                thirty_days = timedelta(days=30)
                if trash_duration < thirty_days:
                    days_remaining = (thirty_days - trash_duration).days

            raise CannotPurgeError(
                media_id,
                "Media not eligible for purge",
                days_remaining
            )

        media.purge()
        await self.repository.purge(media_id)

    async def purge_expired(self) -> Tuple[int, int]:
        """Auto-purge all media eligible for purge (30+ days in trash)

        Returns:
            Tuple of (purged_count, total_freed_bytes)
        """
        eligible = await self.repository.find_eligible_for_purge()

        purged_count = 0
        total_freed = 0

        for media in eligible:
            try:
                media.purge()
                await self.repository.purge(media.id)
                purged_count += 1
                total_freed += media.file_size
            except Exception:
                # Log but continue purging others
                continue

        return purged_count, total_freed

    # ========================================================================
    # Association Operations
    # ========================================================================

    async def associate_with_entity(
        self,
        media_id: UUID,
        entity_type: EntityTypeForMedia,
        entity_id: UUID
    ) -> None:
        """Associate media with an entity

        Args:
            media_id: Media ID
            entity_type: Type of entity
            entity_id: Entity ID

        Raises:
            MediaNotFoundError: If media not found
            MediaInTrashError: If media is in trash
        """
        media = await self.repository.get_by_id(media_id)
        if not media:
            raise MediaNotFoundError(media_id)

        if media.is_in_trash():
            raise MediaInTrashError(media_id, "associate")

        media.associate_with_entity(entity_type, entity_id)
        await self.repository.associate_media_with_entity(
            media_id,
            entity_type,
            entity_id
        )

    async def disassociate_from_entity(
        self,
        media_id: UUID,
        entity_type: EntityTypeForMedia,
        entity_id: UUID
    ) -> None:
        """Disassociate media from an entity

        Args:
            media_id: Media ID
            entity_type: Type of entity
            entity_id: Entity ID
        """
        media = await self.repository.get_by_id(media_id)
        if not media:
            raise MediaNotFoundError(media_id)

        media.disassociate_from_entity(entity_type, entity_id)
        await self.repository.disassociate_media_from_entity(
            media_id,
            entity_type,
            entity_id
        )

    # ========================================================================
    # Query Operations
    # ========================================================================

    async def get_media(self, media_id: UUID) -> Media:
        """Get media by ID

        Raises:
            MediaNotFoundError: If not found
        """
        media = await self.repository.get_by_id(media_id)
        if not media:
            raise MediaNotFoundError(media_id)
        return media

    async def get_entity_media(
        self,
        entity_type: EntityTypeForMedia,
        entity_id: UUID
    ) -> List[Media]:
        """Get all media for an entity"""
        return await self.repository.find_by_entity(entity_type, entity_id)

    async def get_trash(self, skip: int = 0, limit: int = 20) -> Tuple[List[Media], int]:
        """Get paginated trash media"""
        return await self.repository.find_in_trash(skip, limit)

    async def get_active(self, skip: int = 0, limit: int = 20) -> Tuple[List[Media], int]:
        """Get paginated active media"""
        return await self.repository.find_active(skip, limit)

    async def get_trash_count(self) -> int:
        """Get total count of media in trash"""
        return await self.repository.count_in_trash()

    # ========================================================================
    # Validation Helpers
    # ========================================================================

    @staticmethod
    def _validate_image_dimensions(width: int, height: int) -> None:
        """Validate image dimensions

        Raises:
            InvalidDimensionsError: If dimensions invalid
        """
        if not width or width <= 0 or width > 8000:
            raise InvalidDimensionsError(
                width,
                height,
                "Width must be between 1-8000 pixels"
            )

        if not height or height <= 0 or height > 8000:
            raise InvalidDimensionsError(
                width,
                height,
                "Height must be between 1-8000 pixels"
            )

    @staticmethod
    def _validate_video_duration(duration_ms: int) -> None:
        """Validate video duration

        Raises:
            InvalidDurationError: If duration invalid
        """
        if duration_ms <= 0 or duration_ms > 7200000:  # 2 hours
            raise InvalidDurationError(
                duration_ms,
                "Duration must be between 1-7200000 milliseconds (1ms-2 hours)"
            )
