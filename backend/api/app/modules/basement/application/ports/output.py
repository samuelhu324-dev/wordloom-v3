"""Output ports for Basement application layer."""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID

from ...domain.basement_entry import BasementEntry


class BasementRepository(ABC):
    """Repository interface for BasementEntry persistence."""

    @abstractmethod
    async def save(self, entry: BasementEntry) -> BasementEntry:
        """Persist a BasementEntry."""
        pass

    @abstractmethod
    async def get_by_id(self, entry_id: UUID) -> Optional[BasementEntry]:
        """Retrieve a single entry by ID."""
        pass

    @abstractmethod
    async def get_by_book_id(self, book_id: UUID) -> Optional[BasementEntry]:
        """Find the entry associated with a specific book."""
        pass

    @abstractmethod
    async def list_by_library(
        self, library_id: UUID, skip: int = 0, limit: int = 20
    ) -> Tuple[List[BasementEntry], int]:
        """List all entries for a library with pagination. Returns (entries, total_count)."""
        pass

    @abstractmethod
    async def delete(self, entry_id: UUID) -> None:
        """Remove an entry from the Basement (used during restore or hard delete)."""
        pass

    @abstractmethod
    async def delete_by_book_id(self, book_id: UUID) -> None:
        """Remove the entry linked to a book_id."""
        pass
