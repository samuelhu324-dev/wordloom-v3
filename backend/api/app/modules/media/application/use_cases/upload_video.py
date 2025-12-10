"""UploadVideo UseCase - Upload and validate a video

This use case handles:
- Validating MIME type (MP4, WEBM, OGG)
- Validating file size (max 100MB)
- Validating storage quota
- Validating video dimensions (if provided)
- Validating video duration (if provided)
- Creating Media domain object
- Persisting via repository
"""

from typing import Optional
from uuid import UUID

from ...domain import Media, MediaMimeType
from ...application.ports.output import MediaRepository
from ...exceptions import (
    InvalidMimeTypeError,
    FileSizeTooLargeError,
    InvalidDimensionsError,
    InvalidDurationError,
    StorageQuotaExceededError,
    MediaOperationError,
)


class UploadVideoUseCase:
    """Upload and validate a video"""

    MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
    DEFAULT_STORAGE_QUOTA = 1024 * 1024 * 1024  # 1GB

    SUPPORTED_VIDEO_MIMES = {
        MediaMimeType.MP4,
        MediaMimeType.WEBM,
        MediaMimeType.OGG,
    }

    def __init__(self, repository: MediaRepository):
        self.repository = repository

    async def execute(
        self,
        filename: str,
        mime_type: MediaMimeType,
        file_size: int,
        storage_key: str,
        user_id: Optional[UUID] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        duration_ms: Optional[int] = None,
        storage_quota: int = DEFAULT_STORAGE_QUOTA,
        used_storage: int = 0
    ) -> Media:
        """
        Execute upload video use case

        Args:
            filename: Original filename with extension
            mime_type: Video MIME type
            file_size: File size in bytes
            storage_key: Unique identifier in storage backend
            user_id: Owner of the media (optional for anonymous uploads)
            width: Video width (optional)
            height: Video height (optional)
            duration_ms: Video duration in milliseconds (optional)
            storage_quota: User's storage quota in bytes
            used_storage: Currently used storage in bytes

        Returns:
            Uploaded Media domain object

        Raises:
            InvalidMimeTypeError: If MIME type not supported
            FileSizeTooLargeError: If file exceeds size limit
            InvalidDurationError: If duration invalid
            StorageQuotaExceededError: If quota exceeded
            MediaOperationError: On persistence error
        """
        # Validate MIME type
        if mime_type not in self.SUPPORTED_VIDEO_MIMES:
            raise InvalidMimeTypeError(mime_type.value, "video")

        # Validate file size
        if file_size > self.MAX_VIDEO_SIZE:
            raise FileSizeTooLargeError("video", file_size, self.MAX_VIDEO_SIZE)

        # Validate storage quota
        if used_storage + file_size > storage_quota:
            needed = used_storage + file_size - storage_quota
            raise StorageQuotaExceededError(used_storage, storage_quota, needed)

        # Validate duration if provided
        if duration_ms is not None:
            self._validate_video_duration(duration_ms)

        # Create media domain object
        try:
            media = Media.create_video(
                filename=filename,
                mime_type=mime_type,
                file_size=file_size,
                storage_key=storage_key,
                user_id=user_id,
                width=width,
                height=height,
                duration_ms=duration_ms
            )

            # Persist
            created_media = await self.repository.save(media)
            return created_media

        except Exception as e:
            if isinstance(e, (InvalidMimeTypeError, FileSizeTooLargeError, InvalidDurationError, StorageQuotaExceededError)):
                raise
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"[UploadVideoUseCase] Exception during save: {type(e).__name__}: {e}")
            raise MediaOperationError(f"Failed to upload video: {str(e)}")

    @staticmethod
    def _validate_video_duration(duration_ms: int) -> None:
        """Validate video duration"""
        if duration_ms <= 0 or duration_ms > 7200000:  # 2 hours
            raise InvalidDurationError(
                duration_ms,
                "Duration must be between 1-7200000 milliseconds (1ms-2 hours)"
            )
