"""DeleteMedia UseCase - Soft delete media to trash

This use case handles:
- Validating media exists
- Checking media is not already in trash
- Setting trash_at timestamp
- Persisting via repository

POLICY-010: 30-day retention before purge
"""

from uuid import UUID

from ...domain import Media
from ...application.ports.output import MediaRepository
from ...exceptions import (
    MediaNotFoundError,
    MediaInTrashError,
    MediaOperationError,
)


class DeleteMediaUseCase:
    """Soft delete media to trash"""

    def __init__(self, repository: MediaRepository):
        self.repository = repository

    async def execute(self, media_id: UUID) -> Media:
        """
        Execute delete media use case

        Args:
            media_id: Media ID to delete

        Returns:
            Updated Media domain object in trash

        Raises:
            MediaNotFoundError: If media not found
            MediaInTrashError: If already in trash
            MediaOperationError: On persistence error
        """
        media = await self.repository.get_by_id(media_id)
        if not media:
            raise MediaNotFoundError(media_id)

        if media.is_in_trash():
            raise MediaInTrashError(media_id, "delete")

        try:
            media.move_to_trash()
            deleted_media = await self.repository.save(media)
            return deleted_media
        except Exception as e:
            raise MediaOperationError(f"Failed to delete media: {str(e)}")
