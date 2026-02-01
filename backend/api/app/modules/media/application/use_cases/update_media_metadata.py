"""UpdateMediaMetadata UseCase - Update media dimensions or duration

This use case handles:
- Validating media exists
- Updating image dimensions (width/height)
- Updating video duration
- Validating new metadata
- Persisting via repository
"""

from typing import Optional
from uuid import UUID

from ...domain import Media
from ...application.ports.input import UpdateMediaMetadataCommand
from ...application.ports.output import MediaRepository
from ...exceptions import (
    MediaNotFoundError,
    InvalidDimensionsError,
    InvalidDurationError,
    MediaOperationError,
)


class UpdateMediaMetadataUseCase:
    """Update media dimensions or duration"""

    def __init__(self, repository: MediaRepository):
        self.repository = repository

    async def execute_command(self, command: UpdateMediaMetadataCommand) -> Media:
        if command.duration_ms is not None:
            return await self.execute_update_video_metadata(command.media_id, command.duration_ms)

        if command.width is not None or command.height is not None:
            if command.width is None or command.height is None:
                raise InvalidDimensionsError(
                    command.width or 0,
                    command.height or 0,
                    "Both width and height are required",
                )
            return await self.execute_update_image_metadata(command.media_id, command.width, command.height)

        raise InvalidDurationError(0, "Either duration_ms or (width,height) must be provided")

    async def execute_update_image_metadata(
        self,
        media_id: UUID,
        width: int,
        height: int
    ) -> Media:
        """
        Update image dimensions after extraction

        Args:
            media_id: Media ID
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            Updated Media domain object

        Raises:
            MediaNotFoundError: If media not found
            InvalidDimensionsError: If dimensions invalid
            MediaOperationError: On persistence error
        """
        media = await self.repository.get_by_id(media_id)
        if not media:
            raise MediaNotFoundError(media_id)

        try:
            self._validate_image_dimensions(width, height)
            media.update_dimensions(width, height)
            updated_media = await self.repository.save(media)
            return updated_media
        except Exception as e:
            if isinstance(e, (InvalidDimensionsError, MediaNotFoundError)):
                raise
            raise MediaOperationError(f"Failed to update image metadata: {str(e)}")

    async def execute_update_video_metadata(
        self,
        media_id: UUID,
        duration_ms: int
    ) -> Media:
        """
        Update video duration after extraction

        Args:
            media_id: Media ID
            duration_ms: Video duration in milliseconds

        Returns:
            Updated Media domain object

        Raises:
            MediaNotFoundError: If media not found
            InvalidDurationError: If duration invalid
            MediaOperationError: On persistence error
        """
        media = await self.repository.get_by_id(media_id)
        if not media:
            raise MediaNotFoundError(media_id)

        try:
            self._validate_video_duration(duration_ms)
            media.update_duration(duration_ms)
            updated_media = await self.repository.save(media)
            return updated_media
        except Exception as e:
            if isinstance(e, (InvalidDurationError, MediaNotFoundError)):
                raise
            raise MediaOperationError(f"Failed to update video metadata: {str(e)}")

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

    @staticmethod
    def _validate_video_duration(duration_ms: int) -> None:
        """Validate video duration"""
        if duration_ms <= 0 or duration_ms > 7200000:  # 2 hours
            raise InvalidDurationError(
                duration_ms,
                "Duration must be between 1-7200000 milliseconds (1ms-2 hours)"
            )
