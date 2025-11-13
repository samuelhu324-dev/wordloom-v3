"""DeleteTag UseCase - Soft delete a tag

This use case handles:
- Validating tag exists and not already deleted
- Setting deleted_at timestamp
- Preserving associations (for audit trail)
- Persisting via repository
"""

from uuid import UUID

from ...application.ports.output import TagRepository
from ...exceptions import (
    TagNotFoundError,
    TagAlreadyDeletedError,
    TagOperationError,
)


class DeleteTagUseCase:
    """Soft delete a tag"""

    def __init__(self, repository: TagRepository):
        self.repository = repository

    async def execute(self, tag_id: UUID) -> None:
        """
        Execute delete tag use case

        Args:
            tag_id: ID of tag to delete

        Raises:
            TagNotFoundError: If tag not found
            TagAlreadyDeletedError: If tag already deleted
            TagOperationError: On persistence error
        """
        tag = await self.repository.get_by_id(tag_id)
        if not tag:
            raise TagNotFoundError(tag_id)

        if tag.is_deleted():
            raise TagAlreadyDeletedError(tag_id)

        try:
            await self.repository.delete(tag_id)
        except Exception as e:
            raise TagOperationError(f"Failed to delete tag: {str(e)}")
