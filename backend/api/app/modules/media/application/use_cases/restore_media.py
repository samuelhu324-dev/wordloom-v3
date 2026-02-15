"""RestoreMedia UseCase - Restore media from trash

This use case handles:
- Validating media exists
- Checking media is in trash
- Clearing trash_at timestamp
- Persisting via repository
"""

from uuid import UUID

from ...domain import Media
from ...application.ports.input import RestoreMediaCommand
from ...application.ports.output import MediaRepository
from ...exceptions import (
    MediaNotFoundError,
    CannotRestoreError,
    MediaOperationError,
)


class RestoreMediaUseCase:
    """Restore media from trash"""

    def __init__(self, repository: MediaRepository):
        self.repository = repository

    async def execute_command(self, command: RestoreMediaCommand) -> Media:
        return await self.execute(command.media_id)

    async def execute(self, media_id: UUID) -> Media:
        """
        Execute restore media use case

        Args:
            media_id: Media ID to restore

        Returns:
            Restored Media domain object

        Raises:
            MediaNotFoundError: If media not found
            CannotRestoreError: If not in trash
            MediaOperationError: On persistence error
        """
        media = await self.repository.get_by_id(media_id)
        if not media:
            raise MediaNotFoundError(media_id)

        if not media.is_in_trash():
            raise CannotRestoreError(
                media_id,
                "Media is not in trash"
            )

        try:
            media.restore_from_trash()
            restored_media = await self.repository.save(media)
            return restored_media
        except Exception as e:
            raise MediaOperationError(f"Failed to restore media: {str(e)}")
