"""AssociateTag UseCase - Associate a tag with an entity

This use case handles:
- Validating tag exists and not deleted
- Creating TagAssociation record
- Incrementing tag.usage_count
- Idempotent: associating twice returns success
- Persisting via repository

Supported entity types: Book, Bookshelf, Block
"""

from uuid import UUID

from ...domain import EntityType
from ...application.ports.output import TagRepository
from ...exceptions import (
    TagNotFoundError,
    TagOperationError,
)


class AssociateTagUseCase:
    """Associate a tag with an entity"""

    def __init__(self, repository: TagRepository):
        self.repository = repository

    async def execute(
        self,
        tag_id: UUID,
        entity_type: EntityType,
        entity_id: UUID
    ) -> None:
        """
        Execute associate tag use case

        Args:
            tag_id: ID of tag to associate
            entity_type: Type of entity (Book, Bookshelf, Block)
            entity_id: ID of entity

        Raises:
            TagNotFoundError: If tag not found
            TagOperationError: If tag is deleted or on persistence error
        """
        tag = await self.repository.get_by_id(tag_id)
        if not tag:
            raise TagNotFoundError(tag_id)

        if tag.is_deleted():
            raise TagOperationError(f"Cannot associate deleted tag {tag_id}")

        try:
            await self.repository.associate_tag_with_entity(
                tag_id,
                entity_type,
                entity_id
            )
        except Exception as e:
            raise TagOperationError(f"Failed to associate tag: {str(e)}")
