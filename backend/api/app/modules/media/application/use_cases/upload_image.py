"""UploadImage UseCase - Upload and validate an image

This use case handles:
- Validating MIME type (JPEG, PNG, WEBP, GIF)
- Validating file size (max 10MB)
- Validating storage quota
- Validating image dimensions (if provided)
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
    StorageQuotaExceededError,
    MediaOperationError,
)


class UploadImageUseCase:
    """Upload and validate an image"""

    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    DEFAULT_STORAGE_QUOTA = 1024 * 1024 * 1024  # 1GB

    SUPPORTED_IMAGE_MIMES = {
        MediaMimeType.JPEG,
        MediaMimeType.PNG,
        MediaMimeType.WEBP,
        MediaMimeType.GIF,
    }

    def __init__(self, repository: MediaRepository):
        self.repository = repository

    async def execute(
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
        """
        Execute upload image use case

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
            Uploaded Media domain object

        Raises:
            InvalidMimeTypeError: If MIME type not supported
            FileSizeTooLargeError: If file exceeds size limit
            InvalidDimensionsError: If dimensions invalid
            StorageQuotaExceededError: If quota exceeded
            MediaOperationError: On persistence error
        """
        # Validate MIME type
        if mime_type not in self.SUPPORTED_IMAGE_MIMES:
            raise InvalidMimeTypeError(mime_type.value, "image")

        # Validate file size
        if file_size > self.MAX_IMAGE_SIZE:
            raise FileSizeTooLargeError("image", file_size, self.MAX_IMAGE_SIZE)

        # Validate storage quota
        if used_storage + file_size > storage_quota:
            needed = used_storage + file_size - storage_quota
            raise StorageQuotaExceededError(used_storage, storage_quota, needed)

        # Validate dimensions if provided
        if width is not None and height is not None:
            self._validate_image_dimensions(width, height)

        # Create media domain object
        try:
            media = Media.create_image(
                filename=filename,
                mime_type=mime_type,
                file_size=file_size,
                storage_key=storage_key,
                width=width,
                height=height
            )

            # Persist
            created_media = await self.repository.save(media)
            return created_media

        except Exception as e:
            if isinstance(e, (InvalidMimeTypeError, FileSizeTooLargeError, InvalidDimensionsError, StorageQuotaExceededError)):
                raise
            raise MediaOperationError(f"Failed to upload image: {str(e)}")

    @staticmethod
    def _validate_image_dimensions(width: int, height: int) -> None:
        """Validate image dimensions"""
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
