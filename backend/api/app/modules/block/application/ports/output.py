"""
Block Repository Output Port

Abstract interface for Block persistence adapter.
Implementation: infra/storage/block_repository_impl.py
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from api.app.modules.block.domain import Block


class BlockRepository(ABC):
    """Abstract repository for Block persistence"""

    @abstractmethod
    async def save(self, block: Block) -> Block:
        """Persist a block"""
        pass

    @abstractmethod
    async def get_by_id(self, block_id: UUID) -> Optional[Block]:
        """Fetch a block by ID"""
        pass

    @abstractmethod
    async def delete(self, block_id: UUID) -> None:
        """Delete a block"""
        pass

    @abstractmethod
    async def list_by_book(self, book_id: UUID) -> List[Block]:
        """Get all blocks in a book"""
        pass
