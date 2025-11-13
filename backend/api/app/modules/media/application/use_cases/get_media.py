"""GetMedia UseCase - Get media by ID

This use case handles:
- Validating media exists
- Returning media domain object
"""

from uuid import UUID

from ...domain import Media
from ...application.ports.output import MediaRepository
from ...exceptions import (
    MediaNotFoundError,
    MediaOperationError,
)


class GetMediaUseCase:
    """Get media by ID"""

    def __init__(self, repository: MediaRepository):
        self.repository = repository

    async def execute(self, media_id: UUID) -> Media:
        """
        Execute get media use case

        Args:
            media_id: Media ID

        Returns:
            Media domain object

        Raises:
            MediaNotFoundError: If not found
            MediaOperationError: On query error
        """
        try:
            media = await self.repository.get_by_id(media_id)
            if not media:
                raise MediaNotFoundError(media_id)
            return media
        except Exception as e:
            if isinstance(e, MediaNotFoundError):
                raise
            raise MediaOperationError(f"Failed to get media: {str(e)}")
