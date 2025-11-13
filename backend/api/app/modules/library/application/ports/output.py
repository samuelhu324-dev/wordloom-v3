"""
Library Repository Output Port

Abstract interface for Library persistence adapter.
Implementation: infra/storage/library_repository_impl.py
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from api.app.modules.library.domain import Library


class LibraryRepository(ABC):
    """Abstract repository for Library persistence"""

    @abstractmethod
    async def save(self, library: Library) -> Library:
        """Persist a library"""
        pass

    @abstractmethod
    async def get_by_id(self, library_id: UUID) -> Optional[Library]:
        """Fetch a library by ID"""
        pass

    @abstractmethod
    async def delete(self, library_id: UUID) -> None:
        """Delete a library"""
        pass

    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> List[Library]:
        """Get all libraries for a user"""
        pass
