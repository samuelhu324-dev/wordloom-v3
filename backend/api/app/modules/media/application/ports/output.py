"""
Media Repository Output Port

This file defines the abstract interface (output port) that the application layer
expects from the infrastructure layer for persistent storage of Media.

The actual implementation (SQLAlchemyMediaRepository) is in infra/storage/media_repository_impl.py

Port Design:
  - Abstracts database technology and file storage backend
  - Defines all data access methods needed by use cases
  - Uses domain types (Media, MediaState) not ORM models
  - Enforces business logic (trash lifecycle, 30-day retention)
  - Manages both metadata (database) and file storage

All methods are async to support both sync and async I/O patterns.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime

from app.modules.media.domain import Media, MediaState, EntityTypeForMedia


class MediaRepository(ABC):
    """Abstract repository for Media persistence (Output Port)

    Defines the contract that application layer (use cases) expects from
    infrastructure layer (storage adapters).

    This is an OUTPUT port because:
    - Use cases CALL these methods (output from use case)
    - Infrastructure IMPLEMENTS these methods (input to infrastructure)
    - Dependency flows: UseCase â†?MediaRepository (abstract) â†?Implementation (infra)

    Responsibilities:
    - Persist media metadata to database
    - Manage media state transitions (ACTIVE â†?TRASH â†?HARD_DELETE)
    - Enforce 30-day trash retention (POLICY-010)
    - Coordinate with file storage for physical file I/O
    """

    # ========================================================================
    # Media CRUD Operations
    # ========================================================================

    @abstractmethod
    async def save(self, media: Media) -> Media:
        """
        Persist media metadata (create or update)

        Args:
            media: Media domain object to persist

        Returns:
            Persisted media with any updated metadata

        Raises:
            MediaRepositorySaveError: On persistence errors
        """
        pass

    @abstractmethod
    async def get_by_id(self, media_id: UUID) -> Optional[Media]:
        """
        Fetch media by ID (including soft-deleted and purged)

        Args:
            media_id: UUID of the media

        Returns:
            Media domain object or None if not found

        Note:
            Returns media regardless of state (ACTIVE|TRASH|PURGED)
            Caller responsible for filtering if needed
        """
        pass

    @abstractmethod
    async def delete(self, media_id: UUID) -> None:
        """
        Soft delete media (move to trash, set trash_at timestamp)

        POLICY-010: Media moved to trash awaits 30-day retention before purge

        Args:
            media_id: UUID of the media to delete

        Raises:
            MediaNotFoundError: If media doesn't exist
            MediaInTrashError: If already in trash
            MediaRepositoryException: On persistence errors
        """
        pass

    @abstractmethod
    async def restore(self, media_id: UUID) -> None:
        """
        Restore media from trash (clear trash_at timestamp)

        POLICY-010: Can only restore if still within 30-day window

        Args:
            media_id: UUID of the media to restore

        Raises:
            MediaNotFoundError: If media doesn't exist
            CannotRestoreError: If already active or purge grace period expired
            MediaRepositoryException: On persistence errors
        """
        pass

    @abstractmethod
    async def purge(self, media_id: UUID) -> None:
        """
        Hard delete media (after 30-day retention period expired)

        POLICY-010: Only callable on trash items past retention window

        Args:
            media_id: UUID of the media to purge

        Raises:
            MediaNotFoundError: If media doesn't exist
            CannotPurgeError: If not in trash or too soon to purge
            MediaRepositoryException: On persistence errors

        Side Effects:
            - Sets deleted_at timestamp (for audit trail)
            - MediaFileStorage adapter responsible for actual file deletion
        """
        pass

    # ========================================================================
    # Media Query Operations
    # ========================================================================

    @abstractmethod
    async def find_by_entity(
        self,
        entity_type: EntityTypeForMedia,
        entity_id: UUID
    ) -> List[Media]:
        """
        Get all active media associated with an entity

        Args:
            entity_type: Type of entity (BOOK, BOOKSHELF, BLOCK)
            entity_id: UUID of the entity

        Returns:
            List of ACTIVE Media domain objects

        Note:
            Only returns ACTIVE media (state='active')
        """
        pass

    @abstractmethod
    async def find_in_trash(
        self,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Media], int]:
        """
        Get paginated trash media with total count

        Args:
            skip: Offset for pagination
            limit: Number of items per page

        Returns:
            Tuple of (media_list, total_count)

        Note:
            Only returns TRASH media (state='trash' AND deleted_at IS NULL)
            Sorted by trash_at DESC (most recent first)
        """
        pass

    @abstractmethod
    async def find_active(
        self,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Media], int]:
        """
        Get paginated active media with total count

        Args:
            skip: Offset for pagination
            limit: Number of items per page

        Returns:
            Tuple of (media_list, total_count)

        Note:
            Only returns ACTIVE media (state='active' AND deleted_at IS NULL)
            Sorted by created_at DESC (most recent first)
        """
        pass

    @abstractmethod
    async def count_in_trash(self) -> int:
        """
        Count total media items in trash

        Returns:
            Number of items in trash (state='trash' AND deleted_at IS NULL)

        Note:
            Used for trash UI badge/counter
        """
        pass

    @abstractmethod
    async def find_eligible_for_purge(self) -> List[Media]:
        """
        Find media that has been in trash for 30+ days

        Returns:
            List of Media items eligible for hard delete

        Note:
            Items must satisfy: state='trash' AND trash_at <= (NOW - 30 days)
            Used by purge_expired_media use case for batch cleanup
        """
        pass

    @abstractmethod
    async def find_by_storage_key(self, storage_key: str) -> Optional[Media]:
        """
        Find media by storage key (for deduplication)

        Args:
            storage_key: Unique identifier in storage backend (S3 key or local path)

        Returns:
            Media object or None if not found

        Note:
            Used during upload to prevent duplicate storage of same file
        """
        pass

    # ========================================================================
    # Media Association Operations
    # ========================================================================

    @abstractmethod
    async def associate_media_with_entity(
        self,
        media_id: UUID,
        entity_type: EntityTypeForMedia,
        entity_id: UUID
    ) -> None:
        """
        Create a media-entity association

        Args:
            media_id: UUID of the media
            entity_type: Type of entity (BOOK, BOOKSHELF, BLOCK)
            entity_id: UUID of the entity

        Raises:
            MediaNotFoundError: If media doesn't exist
            MediaAlreadyAssociatedError: If association already exists
            MediaRepositoryException: On persistence errors
        """
        pass

    @abstractmethod
    async def disassociate_media_from_entity(
        self,
        media_id: UUID,
        entity_type: EntityTypeForMedia,
        entity_id: UUID
    ) -> None:
        """
        Remove a media-entity association

        Args:
            media_id: UUID of the media
            entity_type: Type of entity (BOOK, BOOKSHELF, BLOCK)
            entity_id: UUID of the entity

        Raises:
            MediaAssociationNotFoundError: If association doesn't exist
            MediaRepositoryException: On persistence errors
        """
        pass

    # ========================================================================
    # Media Validation Operations
    # ========================================================================

    @abstractmethod
    async def check_key_exists(self, storage_key: str) -> bool:
        """
        Check if a storage key already exists

        Args:
            storage_key: Unique key in storage backend

        Returns:
            True if exists, False otherwise

        Note:
            Used to prevent duplicate file uploads
        """
        pass

