"""Basement domain entities used by the Application layer."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from api.app.modules.book.domain import Book


@dataclass(frozen=True)
class BasementBookSnapshot:
    """Immutable projection of a book currently residing in Basement."""

    id: UUID
    library_id: UUID
    bookshelf_id: UUID
    previous_bookshelf_id: Optional[UUID]
    title: str
    summary: Optional[str]
    status: str
    block_count: int
    moved_to_basement_at: Optional[datetime]
    soft_deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, book: Book) -> "BasementBookSnapshot":
        return cls(
            id=book.id,
            library_id=book.library_id,
            bookshelf_id=book.bookshelf_id,
            previous_bookshelf_id=getattr(book, "previous_bookshelf_id", None),
            title=book.title.value if hasattr(book.title, "value") else str(book.title),
            summary=book.summary.value if getattr(book, "summary", None) else None,
            status=book.status.value if hasattr(book.status, "value") else str(book.status),
            block_count=getattr(book, "block_count", 0) or 0,
            moved_to_basement_at=getattr(book, "moved_to_basement_at", None),
            soft_deleted_at=getattr(book, "soft_deleted_at", None),
            created_at=book.created_at,
            updated_at=book.updated_at,
        )

    @property
    def is_in_basement(self) -> bool:
        return self.soft_deleted_at is not None
