"""AssociateMedia UseCase - Associate media with an entity

This use case handles:
- Validating media exists
- Checking media is not in trash
- Creating MediaAssociation record
- Updating domain state
- Persisting via repository

Supported entity types: Book, Bookshelf, Block
"""

from uuid import UUID

from ...domain import EntityTypeForMedia
from ...application.ports.input import AssociateMediaCommand
from ...application.ports.output import MediaRepository
from ...exceptions import (
    MediaNotFoundError,
    MediaInTrashError,
    MediaOperationError,
)


class AssociateMediaUseCase:
    """Associate media with an entity"""

    def __init__(self, repository: MediaRepository):
        self.repository = repository

    async def execute_command(self, command: AssociateMediaCommand) -> None:
        await self.execute(command.media_id, command.entity_type, command.entity_id)

    async def execute(
        self,
        media_id: UUID,
        entity_type: EntityTypeForMedia,
        entity_id: UUID
    ) -> None:
        """
        Execute associate media use case

        Args:
            media_id: Media ID
            entity_type: Type of entity (Book, Bookshelf, Block)
            entity_id: Entity ID

        Raises:
            MediaNotFoundError: If media not found
            MediaInTrashError: If media is in trash
            MediaOperationError: On persistence error
        """
        media = await self.repository.get_by_id(media_id)
        if not media:
            raise MediaNotFoundError(media_id)

        if media.is_in_trash():
            raise MediaInTrashError(media_id, "associate")

        try:
            media.associate_with_entity(entity_type, entity_id)
            await self.repository.associate_media_with_entity(
                media_id,
                entity_type,
                entity_id
            )
        except Exception as e:
            raise MediaOperationError(f"Failed to associate media: {str(e)}")
