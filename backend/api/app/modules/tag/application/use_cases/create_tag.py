"""CreateTag UseCase - Create a new top-level tag

This use case handles:
- Validating tag name (1-50 chars, unique, case-insensitive)
- Validating color (valid hex format)
- Creating Tag domain object
- Persisting via repository

RULE-018: Tag name must be unique (case-insensitive)
RULE-019: Color must be valid hex (#RRGGBB or #RRGGBBAA)
"""

from typing import Optional
from uuid import UUID

from ...domain import Tag, TagCreated
from ...application.ports.output import TagRepository
from ...exceptions import (
    TagInvalidNameError,
    TagInvalidColorError,
    TagAlreadyExistsError,
    TagOperationError,
)


class CreateTagUseCase:
    """Create a new top-level tag"""

    def __init__(self, repository: TagRepository):
        self.repository = repository

    async def execute(
        self,
        name: str,
        color: str,
        icon: Optional[str] = None,
        description: Optional[str] = None
    ) -> Tag:
        """
        Execute create tag use case

        Args:
            name: Tag name (1-50 chars)
            color: Color in hex format (#RRGGBB or #RRGGBBAA)
            icon: Optional lucide icon name
            description: Optional description

        Returns:
            Created Tag domain object

        Raises:
            TagInvalidNameError: If name is invalid
            TagInvalidColorError: If color is invalid
            TagAlreadyExistsError: If name already exists
            TagOperationError: On persistence error
        """
        # Validate name
        if not name or not name.strip():
            raise TagInvalidNameError("Tag name cannot be empty", name)
        if len(name) > 50:
            raise TagInvalidNameError("Tag name must be <= 50 characters", name)

        # Validate color
        if not color.startswith("#"):
            raise TagInvalidColorError(color, "Color must start with #")
        if len(color) not in [7, 9]:
            raise TagInvalidColorError(color, "Color must be 6 or 8 digit hex")

        # Check uniqueness
        if await self.repository.check_name_exists(name):
            raise TagAlreadyExistsError(name)

        # Create domain object
        try:
            tag = Tag.create_toplevel(
                name=name,
                color=color,
                icon=icon,
                description=description
            )

            # Persist
            created_tag = await self.repository.save(tag)

            # Domain event will be published by domain object
            return created_tag

        except Exception as e:
            if isinstance(e, (TagInvalidNameError, TagInvalidColorError, TagAlreadyExistsError)):
                raise
            raise TagOperationError(f"Failed to create tag: {str(e)}")
