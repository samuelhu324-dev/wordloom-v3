"""
Tag Repository Output Port

This file defines the abstract interface (output port) that the application layer
expects from the infrastructure layer for persistent storage of Tags.

The actual implementation (SQLAlchemyTagRepository) is in infra/storage/tag_repository_impl.py

Port Design:
  - Abstracts database technology (could be SQL, NoSQL, etc.)
  - Defines all data access methods needed by use cases
  - Uses domain types (Tag, TagAssociation) not ORM models
  - Enforces business logic (soft delete, uniqueness, hierarchies)

All methods are async to support both sync and async I/O patterns.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID

from api.app.modules.tag.domain import Tag, TagAssociation, EntityType


class TagRepository(ABC):
    """Abstract repository for Tag persistence (Output Port)

    Defines the contract that application layer (use cases) expects from
    infrastructure layer (storage adapters).

    This is an OUTPUT port because:
    - Use cases CALL these methods (output from use case)
    - Infrastructure IMPLEMENTS these methods (input to infrastructure)
    - Dependency flows: UseCase → TagRepository (abstract) → Implementation (infra)
    """

    # ========================================================================
    # Tag CRUD Operations
    # ========================================================================

    @abstractmethod
    async def save(self, tag: Tag) -> Tag:
        """
        Persist a tag (create or update)

        Args:
            tag: Tag domain object to persist

        Returns:
            Persisted tag with any updated metadata

        Raises:
            TagAlreadyExistsError: If name already exists (for active tags)
            TagRepositorySaveError: On persistence errors
        """
        pass

    @abstractmethod
    async def get_by_id(self, tag_id: UUID) -> Optional[Tag]:
        """
        Fetch a tag by ID

        Args:
            tag_id: UUID of the tag

        Returns:
            Tag domain object or None if not found

        Note:
            Returns tag regardless of deleted_at status
            Caller responsible for filtering if needed
        """
        pass

    @abstractmethod
    async def delete(self, tag_id: UUID) -> None:
        """
        Soft delete a tag (sets deleted_at timestamp)

        Args:
            tag_id: UUID of the tag to delete

        Raises:
            TagNotFoundError: If tag doesn't exist
            TagRepositoryException: On persistence errors
        """
        pass

    @abstractmethod
    async def restore(self, tag_id: UUID) -> None:
        """
        Restore a soft-deleted tag (clears deleted_at)

        Args:
            tag_id: UUID of the tag to restore

        Raises:
            TagNotFoundError: If tag doesn't exist
            TagRepositoryException: On persistence errors
        """
        pass

    # ========================================================================
    # Tag Query Operations
    # ========================================================================

    @abstractmethod
    async def get_all_toplevel(self, limit: int = 100) -> List[Tag]:
        """
        Get all top-level tags (parent_tag_id IS NULL, deleted_at IS NULL)

        Args:
            limit: Maximum number of tags to return

        Returns:
            List of top-level Tag domain objects

        Note:
            Only returns ACTIVE tags (deleted_at IS NULL)
        """
        pass

    @abstractmethod
    async def list_all(
        self,
        *,
        include_deleted: bool = False,
        only_top_level: bool = False,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "name_asc",
    ) -> Tuple[List[Tag], int]:
        """List tags with pagination and ordering.

        Args:
            include_deleted: Include soft-deleted tags when True.
            only_top_level: When True, only return tags with level==0 and no parent.
            limit: Maximum number of tags to return.
            offset: Number of tags to skip for pagination.
            order_by: Sort order identifier (name_asc, name_desc, usage_desc, created_desc).

        Returns:
            (tags, total_count) tuple.
        """
        pass

    @abstractmethod
    async def get_by_parent(self, parent_tag_id: UUID) -> List[Tag]:
        """
        Get all sub-tags of a parent tag

        Args:
            parent_tag_id: UUID of the parent tag

        Returns:
            List of child Tag domain objects

        Note:
            Only returns ACTIVE tags (deleted_at IS NULL)
        """
        pass

    @abstractmethod
    async def find_by_name(
        self,
        keyword: str,
        limit: int = 20,
        order_by: str = "name_asc",
    ) -> List[Tag]:
        """
        Search tags by partial name match (case-insensitive)

        Args:
            keyword: Search term
            limit: Maximum results
            order_by: Sort order identifier (name_asc, name_desc, usage_desc, created_desc)

        Returns:
            List of matching Tag domain objects

        Note:
            Only searches ACTIVE tags (deleted_at IS NULL)
        """
        pass

    @abstractmethod
    async def find_most_used(self, limit: int = 30) -> List[Tag]:
        """
        Get most frequently used tags (for UI menu bar)

        Args:
            limit: Maximum results

        Returns:
            List of Tag domain objects sorted by usage_count DESC

        Note:
            Only returns ACTIVE tags (deleted_at IS NULL)
        """
        pass

    @abstractmethod
    async def find_by_entity(
        self,
        entity_type: EntityType,
        entity_id: UUID
    ) -> List[Tag]:
        """
        Get all tags associated with a specific entity

        Args:
            entity_type: Type of entity (LIBRARY, BOOKSHELF, BOOK, BLOCK)
            entity_id: ID of the entity

        Returns:
            List of Tag domain objects tagged on this entity

        Note:
            Returns ACTIVE tags only
        """
        pass

    @abstractmethod
    async def find_entities_with_tag(
        self,
        tag_id: UUID,
        entity_type: EntityType
    ) -> List[UUID]:
        """
        Reverse lookup: get all entity IDs with a specific tag

        Args:
            tag_id: UUID of the tag
            entity_type: Type of entity to search (LIBRARY, BOOKSHELF, BOOK, BLOCK)

        Returns:
            List of entity UUIDs that have this tag

        Note:
            Includes entities where media is ACTIVE
        """
        pass

    # ========================================================================
    # Tag Association Operations
    # ========================================================================

    @abstractmethod
    async def associate_tag_with_entity(
        self,
        tag_id: UUID,
        entity_type: EntityType,
        entity_id: UUID
    ) -> TagAssociation:
        """
        Create a tag-entity association

        Args:
            tag_id: UUID of the tag
            entity_type: Type of entity (LIBRARY, BOOKSHELF, BOOK, BLOCK)
            entity_id: ID of the entity

        Returns:
            TagAssociation domain object

        Raises:
            TagNotFoundError: If tag doesn't exist
            TagAlreadyAssociatedError: If association already exists
            TagRepositoryException: On persistence errors

        Note:
            Increments tag.usage_count
        """
        pass

    @abstractmethod
    async def disassociate_tag_from_entity(
        self,
        tag_id: UUID,
        entity_type: EntityType,
        entity_id: UUID
    ) -> None:
        """
        Remove a tag-entity association

        Args:
            tag_id: UUID of the tag
            entity_type: Type of entity (LIBRARY, BOOKSHELF, BOOK, BLOCK)
            entity_id: ID of the entity

        Raises:
            TagAssociationNotFoundError: If association doesn't exist
            TagRepositoryException: On persistence errors

        Note:
            Decrements tag.usage_count
        """
        pass

    @abstractmethod
    async def count_associations(self, tag_id: UUID) -> int:
        """
        Count total associations for a tag

        Args:
            tag_id: UUID of the tag

        Returns:
            Number of active associations

        Note:
            Used to keep tag.usage_count in sync
        """
        pass

    # ========================================================================
    # Tag Validation Operations
    # ========================================================================

    @abstractmethod
    async def check_name_exists(
        self,
        name: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if a tag name already exists (active tags only)

        Args:
            name: Tag name to check
            exclude_id: Optional UUID to exclude from uniqueness check

        Returns:
            True if name exists (and not excluded), False otherwise

        Note:
            Only checks ACTIVE tags (deleted_at IS NULL)
            exclude_id allows update operations to compare with existing ID
        """
        pass
