"""DTOs used by Basement use cases."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class MoveBookToBasementCommand:
    book_id: UUID
    basement_bookshelf_id: UUID
    actor_id: Optional[UUID] = None
    reason: Optional[str] = None


@dataclass
class RestoreBookFromBasementCommand:
    book_id: UUID
    target_bookshelf_id: Optional[UUID] = None
    actor_id: Optional[UUID] = None


@dataclass
class HardDeleteBookCommand:
    book_id: UUID
    deleted_at: Optional[datetime] = None
    actor_id: Optional[UUID] = None


@dataclass
class ListBasementBooksQuery:
    library_id: UUID
    skip: int = 0
    limit: int = 20


@dataclass
class SoftDeleteBlockCommand:
    block_id: UUID
    book_id: UUID
