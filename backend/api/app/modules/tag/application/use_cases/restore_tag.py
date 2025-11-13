"""RestoreTag UseCase - Restore a soft-deleted tag

This use case handles:
- Validating tag exists
- Clearing deleted_at timestamp
- Making tag queryable again
- Restoring associations
- Persisting via repository
"""

from uuid import UUID

from ...domain import Tag
from ...application.ports.output import TagRepository
from ...exceptions import (
    TagNotFoundError,
    TagOperationError,
)


class RestoreTagUseCase:
    """Restore a soft-deleted tag"""

    def __init__(self, repository: TagRepository):
        self.repository = repository

    async def execute(self, tag_id: UUID) -> Tag:
        """
        Execute restore tag use case

        Args:
            tag_id: ID of tag to restore

        Returns:
            Restored Tag domain object (or same if not deleted)

        Raises:
            TagNotFoundError: If tag not found
            TagOperationError: On persistence error
        """
        tag = await self.repository.get_by_id(tag_id)
        if not tag:
            raise TagNotFoundError(tag_id)

        if not tag.is_deleted():
            return tag  # Already active

        try:
            await self.repository.restore(tag_id)
            restored_tag = await self.repository.get_by_id(tag_id)
            return restored_tag
        except Exception as e:
            raise TagOperationError(f"Failed to restore tag: {str(e)}")
