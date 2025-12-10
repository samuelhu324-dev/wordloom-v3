"""BasementEntry aggregate root - tracks books currently in the recycle area."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from api.app.modules.book.domain import Book


@dataclass
class BasementEntry:
    """Immutable record capturing when a book entered the Basement.

    This serves as a dedicated projection for listing/audit without
    repeatedly querying the Books table with soft_deleted_at filters.
    """

    id: UUID
    book_id: UUID
    library_id: UUID
    bookshelf_id: UUID
    previous_bookshelf_id: Optional[UUID]
    title_snapshot: str
    summary_snapshot: Optional[str]
    status_snapshot: str
    block_count_snapshot: int
    moved_at: datetime
    created_at: datetime

    @classmethod
    def from_book(cls, book: Book, moved_at: Optional[datetime] = None) -> "BasementEntry":
        """Create a new BasementEntry from a Book aggregate at deletion time."""
        now = moved_at or datetime.utcnow()
        return cls(
            id=uuid4(),
            book_id=book.id,
            library_id=book.library_id,
            bookshelf_id=book.bookshelf_id,
            previous_bookshelf_id=getattr(book, "previous_bookshelf_id", None),
            title_snapshot=book.title.value if hasattr(book.title, "value") else str(book.title),
            summary_snapshot=book.summary.value if getattr(book, "summary", None) else None,
            status_snapshot=book.status.value if hasattr(book.status, "value") else str(book.status),
            block_count_snapshot=getattr(book, "block_count", 0) or 0,
            moved_at=now,
            created_at=now,
        )
