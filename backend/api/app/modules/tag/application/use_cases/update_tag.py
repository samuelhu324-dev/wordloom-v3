"""UpdateTag UseCase - Update tag properties

This use case handles:
- Validating tag exists and not deleted
- Updating name (with uniqueness check)
- Updating color (with format validation)
- Updating icon and description
- Persisting changes via repository
"""

from typing import Optional
from uuid import UUID

from ...domain import Tag
from ...application.ports.output import TagRepository
from ...exceptions import (
    TagNotFoundError,
    TagAlreadyDeletedError,
    TagInvalidNameError,
    TagInvalidColorError,
    TagAlreadyExistsError,
    TagOperationError,
)


class UpdateTagUseCase:
    """Update tag properties"""

    def __init__(self, repository: TagRepository):
        self.repository = repository

    async def execute(
        self,
        tag_id: UUID,
        name: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
        description: Optional[str] = None
    ) -> Tag:
        """
        Execute update tag use case

        Args:
            tag_id: ID of tag to update
            name: New name (optional)
            color: New color (optional)
            icon: New icon (optional)
            description: New description (optional)

        Returns:
            Updated Tag domain object

        Raises:
            TagNotFoundError: If tag not found
            TagAlreadyDeletedError: If tag is deleted
            TagInvalidNameError: If name is invalid
            TagInvalidColorError: If color is invalid
            TagAlreadyExistsError: If new name already exists
            TagOperationError: On persistence error
        """
        tag = await self.repository.get_by_id(tag_id)
        if not tag:
            raise TagNotFoundError(tag_id)

        if tag.is_deleted():
            raise TagAlreadyDeletedError(tag_id)

        # Apply updates
        try:
            if name is not None and name != tag.name:
                if not name.strip():
                    raise TagInvalidNameError("Tag name cannot be empty", name)
                if len(name) > 50:
                    raise TagInvalidNameError("Tag name must be <= 50 characters", name)
                if await self.repository.check_name_exists(name, exclude_id=tag_id):
                    raise TagAlreadyExistsError(name)
                tag.rename(name)

            if color is not None and color != tag.color:
                if not color.startswith("#"):
                    raise TagInvalidColorError(color, "Color must start with #")
                if len(color) not in [7, 9]:
                    raise TagInvalidColorError(color, "Color must be 6 or 8 digit hex")
                tag.update_color(color)

            if icon is not None:
                tag.update_icon(icon)

            if description is not None:
                tag.update_description(description)

            # Persist
            updated_tag = await self.repository.save(tag)
            return updated_tag

        except Exception as e:
            if isinstance(e, (TagNotFoundError, TagAlreadyDeletedError, TagAlreadyExistsError, TagInvalidNameError, TagInvalidColorError)):
                raise
            raise TagOperationError(f"Failed to update tag: {str(e)}")
