"""DisassociateTag UseCase - Remove tag association from an entity

This use case handles:
- Validating tag exists
- Deleting TagAssociation record
- Decrementing tag.usage_count
- Idempotent: disassociating non-existent association is no-op
- Persisting via repository
"""

from uuid import UUID

from ...domain import EntityType
from ...application.ports.output import TagRepository
from ...exceptions import (
    TagNotFoundError,
    TagOperationError,
)


class DisassociateTagUseCase:
    """Remove association between a tag and an entity"""

    def __init__(self, repository: TagRepository):
        self.repository = repository

    async def execute(
        self,
        tag_id: UUID,
        entity_type: EntityType,
        entity_id: UUID
    ) -> None:
        """
        Execute disassociate tag use case

        Args:
            tag_id: ID of tag to disassociate
            entity_type: Type of entity (Book, Bookshelf, Block)
            entity_id: ID of entity

        Raises:
            TagNotFoundError: If tag not found
            TagOperationError: On persistence error
        """
        tag = await self.repository.get_by_id(tag_id)
        if not tag:
            raise TagNotFoundError(tag_id)

        try:
            await self.repository.disassociate_tag_from_entity(
                tag_id,
                entity_type,
                entity_id
            )
        except Exception as e:
            raise TagOperationError(f"Failed to disassociate tag: {str(e)}")
