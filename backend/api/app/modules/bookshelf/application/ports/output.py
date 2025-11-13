"""
Bookshelf Repository Output Port

Abstract interface for Bookshelf persistence adapter.
Implementation: infra/storage/bookshelf_repository_impl.py
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from api.app.modules.bookshelf.domain import Bookshelf


class BookshelfRepository(ABC):
    """Abstract repository for Bookshelf persistence"""

    @abstractmethod
    async def save(self, bookshelf: Bookshelf) -> Bookshelf:
        """Persist a bookshelf"""
        pass

    @abstractmethod
    async def get_by_id(self, bookshelf_id: UUID) -> Optional[Bookshelf]:
        """Fetch a bookshelf by ID"""
        pass

    @abstractmethod
    async def delete(self, bookshelf_id: UUID) -> None:
        """Delete a bookshelf"""
        pass

    @abstractmethod
    async def list_by_library(self, library_id: UUID) -> List[Bookshelf]:
        """Get all bookshelves in a library"""
        pass
