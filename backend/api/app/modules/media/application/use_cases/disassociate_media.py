"""DisassociateMedia UseCase - Disassociate media from an entity

This use case handles:
- Validating media exists
- Deleting MediaAssociation record
- Updating domain state
- Persisting via repository
"""

from uuid import UUID

from ...domain import EntityTypeForMedia
from ...application.ports.output import MediaRepository
from ...exceptions import (
    MediaNotFoundError,
    MediaOperationError,
)


class DisassociateMediaUseCase:
    """Disassociate media from an entity"""

    def __init__(self, repository: MediaRepository):
        self.repository = repository

    async def execute(
        self,
        media_id: UUID,
        entity_type: EntityTypeForMedia,
        entity_id: UUID
    ) -> None:
        """
        Execute disassociate media use case

        Args:
            media_id: Media ID
            entity_type: Type of entity (Book, Bookshelf, Block)
            entity_id: Entity ID

        Raises:
            MediaNotFoundError: If media not found
            MediaOperationError: On persistence error
        """
        media = await self.repository.get_by_id(media_id)
        if not media:
            raise MediaNotFoundError(media_id)

        try:
            media.disassociate_from_entity(entity_type, entity_id)
            await self.repository.disassociate_media_from_entity(
                media_id,
                entity_type,
                entity_id
            )
        except Exception as e:
            raise MediaOperationError(f"Failed to disassociate media: {str(e)}")
