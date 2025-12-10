"""
Media Repository Output Port - Abstract Interface

This module defines the abstract repository interface (output port)
that application layer expects from infrastructure layer.

The actual SQLAlchemy implementation is in:
infra/storage/media_repository_impl.py

Responsibilities:
- Persist Media domain objects to database
- Fetch Media from database and convert to domain objects
- Enforce state machine: ACTIVE -> TRASH -> PURGED
- Enforce 30-day trash retention (POLICY-010)
- Manage Media-Entity associations
- Handle transaction rollback on errors
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from api.app.modules.media.domain import Media, MediaState, EntityTypeForMedia


class MediaRepository(ABC):
    """Abstract repository for Media persistence (Output Port)

    Defines contract that application layer (use cases) expects
    from infrastructure layer (storage adapters).
    
    This is an OUTPUT port because:
    - Use cases CALL these methods (output from use case)
    - Infrastructure IMPLEMENTS these methods (input to infrastructure)
    - Dependency: UseCase -> MediaRepository (abstract) -> Implementation (infra)
    """

    @abstractmethod
    async def save(self, media: Media) -> None:
        """Save new media or update existing media"""
        pass

    @abstractmethod
    async def get_by_id(self, media_id: UUID) -> Optional[Media]:
        """Get media by ID, or None if not found"""
        pass

    @abstractmethod
    async def list_active(self, skip: int = 0, limit: int = 100) -> List[Media]:
        """List all active media with pagination"""
        pass

    @abstractmethod
    async def list_in_trash(self, skip: int = 0, limit: int = 100) -> List[Media]:
        """List media in trash"""
        pass

    @abstractmethod
    async def delete(self, media_id: UUID) -> None:
        """Hard delete media (permanent)"""
        pass

    @abstractmethod
    async def move_to_trash(self, media_id: UUID) -> None:
        """Move media to trash (soft delete with expiration)"""
        pass

    @abstractmethod
    async def restore_from_trash(self, media_id: UUID) -> None:
        """Restore media from trash to active state"""
        pass

    @abstractmethod
    async def purge_expired(self, older_than_days: int = 30) -> int:
        """Hard delete media older than specified days, return count"""
        pass

    @abstractmethod
    async def count_by_state(self, state: MediaState) -> int:
        """Count media in given state"""
        pass
