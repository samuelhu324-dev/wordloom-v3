"""Tag Service - Business logic for tag management

Architecture (ADR-025: Tag Service Design):
==========================================
- Orchestrates domain objects and persistence
- Implements business rules (RULE-018/019/020)
- Handles cross-entity operations (associate/disassociate)
- Manages tag hierarchies and usage statistics
- Does NOT handle HTTP-level concerns (routing, response formatting)

Methods:
- create_tag() - create new top-level tag with validation
- create_subtag() - create hierarchical sub-tag with cycle detection
- update_tag() - modify tag properties
- delete_tag() / restore_tag() - soft delete operations
- associate_tag() - link tag to entity
- disassociate_tag() - remove tag from entity
- get_tags_for_entity() - query all tags on an entity
- search_tags() - search by name or hierarchy
- get_most_used_tags() - for menu/dashboard display
"""

from typing import List, Optional, Set
from uuid import UUID
from datetime import datetime, timezone

from domain import Tag, EntityType, TagCreated
from models import TagModel
from repository import TagRepository
from exceptions import (
    TagNotFoundError,
    TagAlreadyExistsError,
    TagInvalidNameError,
    TagInvalidColorError,
    TagInvalidHierarchyError,
    TagAlreadyAssociatedError,
    TagAssociationNotFoundError,
    TagAlreadyDeletedError,
    TagOperationError,
)


class TagService:
    """Tag business logic service"""

    def __init__(self, repository: TagRepository):
        self.repository = repository

    # ========================================================================
    # Tag Creation
    # ========================================================================

    async def create_tag(
        self,
        name: str,
        color: str,
        icon: Optional[str] = None,
        description: Optional[str] = None
    ) -> Tag:
        """
        Create a new top-level tag

        Validations:
        - name: non-empty, 1-50 chars, unique (case-insensitive)
        - color: valid hex format (#RRGGBB or #RRGGBBAA)
        - icon: optional lucide icon name
        - No duplicate active tags with same name

        Returns: Created Tag domain object
        Raises: TagInvalidNameError, TagInvalidColorError, TagAlreadyExistsError
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
            return await self.repository.save(tag)

        except Exception as e:
            if isinstance(e, (TagInvalidNameError, TagInvalidColorError, TagAlreadyExistsError)):
                raise
            raise TagOperationError(f"Failed to create tag: {str(e)}")

    async def create_subtag(
        self,
        parent_tag_id: UUID,
        name: str,
        color: str,
        icon: Optional[str] = None
    ) -> Tag:
        """
        Create a hierarchical sub-tag

        Validations:
        - parent_tag_id must reference an existing, non-deleted tag
        - Cannot create cycles (parent cannot be a descendant of child)
        - Maximum hierarchy depth: 3 levels (0=top, 1=sub, 2=sub-sub)
        - name: unique within context (TBD)
        - color and icon follow same rules as create_tag()

        Returns: Created Tag domain object
        Raises: TagNotFoundError, TagInvalidHierarchyError, etc.
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

        # Check hierarchy depth
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
        if not color.startswith("#"):
            raise TagInvalidColorError(color, "Color must start with #")
        if len(color) not in [7, 9]:
            raise TagInvalidColorError(color, "Color must be 6 or 8 digit hex")

        # Create domain object
        try:
            tag = Tag.create_subtag(
                parent_tag_id=parent_tag_id,
                name=name,
                color=color,
                icon=icon,
                parent_level=parent.level
            )

            # Persist
            return await self.repository.save(tag)

        except Exception as e:
            if isinstance(e, (TagNotFoundError, TagInvalidHierarchyError, TagInvalidNameError, TagInvalidColorError)):
                raise
            raise TagOperationError(f"Failed to create subtag: {str(e)}")

    # ========================================================================
    # Tag Updates
    # ========================================================================

    async def update_tag(
        self,
        tag_id: UUID,
        name: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
        description: Optional[str] = None
    ) -> Tag:
        """
        Update tag properties

        Validations:
        - tag must exist and not be soft-deleted
        - if name changed: must remain unique
        - if color changed: must remain valid hex format

        Returns: Updated Tag domain object
        Raises: TagNotFoundError, TagAlreadyDeletedError, TagAlreadyExistsError, etc.
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
            return await self.repository.save(tag)

        except Exception as e:
            if isinstance(e, (TagNotFoundError, TagAlreadyDeletedError, TagAlreadyExistsError, TagInvalidNameError, TagInvalidColorError)):
                raise
            raise TagOperationError(f"Failed to update tag: {str(e)}")

    # ========================================================================
    # Tag Lifecycle
    # ========================================================================

    async def delete_tag(self, tag_id: UUID) -> None:
        """
        Soft delete a tag

        Effect:
        - Marks tag as deleted (sets deleted_at)
        - Tag no longer appears in queries (except explicit deleted queries)
        - Associations are preserved (for audit trail)
        - Can be restored later

        Raises: TagNotFoundError, TagAlreadyDeletedError
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

    async def restore_tag(self, tag_id: UUID) -> Tag:
        """
        Restore a soft-deleted tag

        Effect:
        - Clears deleted_at timestamp
        - Tag becomes queryable again
        - Associations are restored

        Raises: TagNotFoundError
        """
        tag = await self.repository.get_by_id(tag_id)
        if not tag:
            raise TagNotFoundError(tag_id)

        if not tag.is_deleted():
            return tag  # Already active

        try:
            await self.repository.restore(tag_id)
            return await self.repository.get_by_id(tag_id)
        except Exception as e:
            raise TagOperationError(f"Failed to restore tag: {str(e)}")

    # ========================================================================
    # Tag-Entity Associations
    # ========================================================================

    async def associate_tag_with_entity(
        self,
        tag_id: UUID,
        entity_type: EntityType,
        entity_id: UUID
    ) -> None:
        """
        Associate a tag with an entity (Book/Bookshelf/Block)

        Effect:
        - Creates TagAssociation record
        - Increments tag.usage_count
        - Idempotent: associating twice returns success

        Raises: TagNotFoundError, TagAlreadyDeletedError
        """
        tag = await self.repository.get_by_id(tag_id)
        if not tag:
            raise TagNotFoundError(tag_id)

        if tag.is_deleted():
            raise TagOperationError(f"Cannot associate deleted tag {tag_id}")

        try:
            await self.repository.associate_tag_with_entity(tag_id, entity_type, entity_id)
        except Exception as e:
            raise TagOperationError(f"Failed to associate tag: {str(e)}")

    async def disassociate_tag_from_entity(
        self,
        tag_id: UUID,
        entity_type: EntityType,
        entity_id: UUID
    ) -> None:
        """
        Remove association between a tag and an entity

        Effect:
        - Deletes TagAssociation record
        - Decrements tag.usage_count
        - Idempotent: disassociating non-existent association is no-op

        Raises: TagNotFoundError
        """
        tag = await self.repository.get_by_id(tag_id)
        if not tag:
            raise TagNotFoundError(tag_id)

        try:
            await self.repository.disassociate_tag_from_entity(tag_id, entity_type, entity_id)
        except Exception as e:
            raise TagOperationError(f"Failed to disassociate tag: {str(e)}")

    # ========================================================================
    # Tag Queries
    # ========================================================================

    async def get_tags_for_entity(
        self,
        entity_type: EntityType,
        entity_id: UUID
    ) -> List[Tag]:
        """Get all tags associated with a specific entity"""
        try:
            return await self.repository.find_by_entity(entity_type, entity_id)
        except Exception as e:
            raise TagOperationError(f"Failed to get entity tags: {str(e)}")

    async def search_tags(
        self,
        keyword: str,
        limit: int = 20
    ) -> List[Tag]:
        """Search tags by partial name match"""
        if not keyword or len(keyword) > 100:
            return []

        try:
            return await self.repository.find_by_name(keyword, limit=limit)
        except Exception as e:
            raise TagOperationError(f"Failed to search tags: {str(e)}")

    async def get_most_used_tags(self, limit: int = 30) -> List[Tag]:
        """Get most frequently used tags (for menu bar display)"""
        try:
            return await self.repository.find_most_used(limit=limit)
        except Exception as e:
            raise TagOperationError(f"Failed to get popular tags: {str(e)}")

    async def get_tag_hierarchy(self, parent_tag_id: Optional[UUID] = None) -> List[Tag]:
        """Get hierarchical tags (only top-level if parent_tag_id is None)"""
        try:
            if parent_tag_id is None:
                return await self.repository.get_all_toplevel()
            else:
                return await self.repository.get_by_parent(parent_tag_id)
        except Exception as e:
            raise TagOperationError(f"Failed to get tag hierarchy: {str(e)}")

    async def get_tag_by_id(self, tag_id: UUID) -> Optional[Tag]:
        """Get a tag by ID (including soft-deleted)"""
        try:
            return await self.repository.get_by_id(tag_id)
        except Exception as e:
            raise TagOperationError(f"Failed to get tag: {str(e)}")

    async def get_entities_with_tag(
        self,
        tag_id: UUID,
        entity_type: EntityType
    ) -> List[UUID]:
        """Reverse lookup: get all entities with a specific tag"""
        try:
            return await self.repository.find_entities_with_tag(tag_id, entity_type)
        except Exception as e:
            raise TagOperationError(f"Failed to reverse lookup tag: {str(e)}")
