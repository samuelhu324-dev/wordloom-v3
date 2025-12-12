"""CreateSubtag UseCase - Create a hierarchical sub-tag

This use case handles:
- Validating parent tag exists and not deleted
- Checking hierarchy depth (max 3 levels)
- Cycle detection (parent cannot be descendant of child)
- Creating Tag domain object with parent reference
- Persisting via repository

RULE-020: Maximum hierarchy depth is 3 levels (top, sub, sub-sub)
"""

from typing import Optional
from uuid import UUID

from ...domain import Tag, DEFAULT_COLOR
from ...application.ports.output import TagRepository
from ...exceptions import (
    TagNotFoundError,
    TagInvalidNameError,
    TagInvalidColorError,
    TagInvalidHierarchyError,
    TagOperationError,
)


class CreateSubtagUseCase:
    """Create a hierarchical sub-tag under a parent tag"""

    def __init__(self, repository: TagRepository):
        self.repository = repository

    async def execute(
        self,
        parent_tag_id: UUID,
        name: str,
        color: Optional[str],
        icon: Optional[str] = None,
        description: Optional[str] = None
    ) -> Tag:
        """
        Execute create subtag use case

        Args:
            parent_tag_id: ID of parent tag
            name: Subtag name (1-50 chars)
            color: Color in hex format
            icon: Optional lucide icon name

        Returns:
            Created Tag domain object with parent reference

        Raises:
            TagNotFoundError: If parent not found
            TagInvalidHierarchyError: If hierarchy rules violated
            TagInvalidNameError: If name is invalid
            TagInvalidColorError: If color is invalid
            TagOperationError: On persistence error
        """
        # Validate parent exists
        parent = await self.repository.get_by_id(parent_tag_id)
        if not parent:
            raise TagNotFoundError(parent_tag_id)

        if parent.is_deleted():
            raise TagInvalidHierarchyError(
                "Cannot create subtag under a deleted tag",
                parent_tag_id
            )

        # Check hierarchy depth (RULE-020: max 3 levels)
        if parent.level >= 2:
            raise TagInvalidHierarchyError(
                f"Maximum hierarchy depth is 3 levels (current parent level: {parent.level})",
                parent_tag_id
            )

        # Validate name
        if not name or not name.strip():
            raise TagInvalidNameError("Tag name cannot be empty", name)
        if len(name) > 50:
            raise TagInvalidNameError("Tag name must be <= 50 characters", name)

        # Validate color
        normalized_color = color or DEFAULT_COLOR
        if not normalized_color.startswith("#"):
            raise TagInvalidColorError(normalized_color, "Color must start with #")
        if len(normalized_color) not in [7, 9]:
            raise TagInvalidColorError(normalized_color, "Color must be 6 or 8 digit hex")

        # Create domain object
        try:
            tag = Tag.create_subtag(
                parent_tag_id=parent_tag_id,
                name=name,
                color=normalized_color,
                icon=icon,
                description=description,
                parent_level=parent.level
            )

            # Persist
            created_tag = await self.repository.save(tag)
            return created_tag

        except Exception as e:
            if isinstance(e, (TagNotFoundError, TagInvalidHierarchyError, TagInvalidNameError, TagInvalidColorError)):
                raise
            raise TagOperationError(f"Failed to create subtag: {str(e)}")
