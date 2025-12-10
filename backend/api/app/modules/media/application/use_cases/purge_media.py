"""PurgeMedia UseCase - Hard delete media after 30-day retention

This use case handles:
- Validating media exists
- Checking media is eligible for purge (30+ days in trash)
- Hard deleting from database and storage
- Persisting via repository

POLICY-010: 30-day trash retention before purge (enforced)
"""

from uuid import UUID
from datetime import datetime, timezone, timedelta

from ...domain import Media
from ...application.ports.output import MediaRepository
from ...exceptions import (
    MediaNotFoundError,
    CannotPurgeError,
    MediaOperationError,
)


class PurgeMediaUseCase:
    """Hard delete media after 30-day retention"""

    RETENTION_DAYS = 30

    def __init__(self, repository: MediaRepository):
        self.repository = repository

    async def execute(self, media_id: UUID) -> None:
        """
        Execute purge media use case

        Args:
            media_id: Media ID to purge

        Raises:
            MediaNotFoundError: If media not found
            CannotPurgeError: If not eligible for purge
            MediaOperationError: On persistence error
        """
        media = await self.repository.get_by_id(media_id)
        if not media:
            raise MediaNotFoundError(media_id)

        if not media.is_eligible_for_purge():
            days_remaining = 0
            if media.trash_at:
                trash_duration = datetime.now(timezone.utc) - media.trash_at
                thirty_days = timedelta(days=self.RETENTION_DAYS)
                if trash_duration < thirty_days:
                    days_remaining = (thirty_days - trash_duration).days

            raise CannotPurgeError(
                media_id,
                "Media not eligible for purge",
                days_remaining
            )

        try:
            media.purge()
            await self.repository.purge(media_id)
        except Exception as e:
            raise MediaOperationError(f"Failed to purge media: {str(e)}")
