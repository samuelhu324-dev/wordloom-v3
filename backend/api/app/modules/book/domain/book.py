"""
Book Aggregate Root

Core business logic for content containers with Blocks.

Purpose:
- Represents content container under a Bookshelf
- Manages Block references (ordered list via block_count)
- Manages state: status, is_pinned, due_at, etc.
- Does NOT manage: preview_image (→ Media), usage_count (→ Chronicle)

Architecture:
- Pure domain layer with zero infrastructure dependencies
- Emits DomainEvents on state changes
- Uses Repository pattern for persistence abstraction

Invariants:
- Book associated to Bookshelf through bookshelf_id FK (not embedded object)
- Book associated to Library through library_id FK (for permission checks)
- Title must exist and be ≤ 255 characters
- Summary optional, ≤ 1000 characters
- Status must be DRAFT | PUBLISHED | ARCHIVED | DELETED
- soft_deleted_at marks Books in Basement view
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from shared.base import AggregateRoot, DomainEvent
from .book_title import BookTitle
from .book_summary import BookSummary
from .events import (
    BookStatus,
    BookCreated,
    BookRenamed,
    BookStatusChanged,
    BookDeleted,
    BlocksUpdated,
    BookMovedToBookshelf,
    BookMovedToBasement,
    BookRestoredFromBasement,
)


class Book(AggregateRoot):
    """
    Book Aggregate Root (独立聚合根)

    Design Decision: Independent aggregate
    - Does NOT directly contain Block objects (Blocks associated via book_id FK)
    - Uses block_count field for counting, not collection holding
    - Service layer responsible for Book transfers and deletions

    Business Rules:
    - Created with title and bookshelf_id
    - Can transfer to other Bookshelf (BookMovedToBookshelf event, RULE-011)
    - Deletion = transfer to Basement (BookMovedToBasement event, RULE-012)
    - Can restore from Basement (BookRestoredFromBasement event, RULE-013)
    """

    def __init__(
        self,
        book_id: UUID,
        bookshelf_id: UUID,
        library_id: UUID,
        title: BookTitle,
        summary: BookSummary = None,
        is_pinned: bool = False,
        due_at: Optional[datetime] = None,
        status: BookStatus = BookStatus.DRAFT,
        block_count: int = 0,
        soft_deleted_at: Optional[datetime] = None,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self.id = book_id
        self.bookshelf_id = bookshelf_id
        self.library_id = library_id  # ← Redundant FK (for permission checks)
        self.title = title
        self.summary = summary or BookSummary()
        self.is_pinned = is_pinned
        self.due_at = due_at
        self.status = status
        self.block_count = block_count
        self.soft_deleted_at = soft_deleted_at  # ← Marks if in Basement
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.events: List[DomainEvent] = []

    # ========================================================================
    # Factory Methods
    # ========================================================================

    @classmethod
    def create(
        cls,
        bookshelf_id: UUID,
        library_id: UUID,
        title: str,
        summary: Optional[str] = None,
    ) -> Book:
        """
        Factory method to create a new Book

        Args:
            bookshelf_id: ID of the parent Bookshelf
            library_id: ID of the parent Library (redundant FK for permission checks)
            title: Title of the Book
            summary: Optional summary

        Returns:
            New Book instance with BookCreated event

        Raises:
            ValueError: If title or summary invalid
        """
        book_id = uuid4()
        book_title = BookTitle(value=title)
        book_summary = BookSummary(value=summary)
        now = datetime.now(timezone.utc)

        book = cls(
            book_id=book_id,
            bookshelf_id=bookshelf_id,
            library_id=library_id,
            title=book_title,
            summary=book_summary,
            status=BookStatus.DRAFT,
            created_at=now,
            updated_at=now,
        )

        book.emit(
            BookCreated(
                book_id=book_id,
                bookshelf_id=bookshelf_id,
                title=title,
                occurred_at=now,
            )
        )

        return book

    # ========================================================================
    # Business Methods
    # ========================================================================

    def rename(self, new_title: str) -> None:
        """Rename the Book"""
        new_book_title = BookTitle(value=new_title)

        if self.title.value == new_book_title.value:
            return

        old_title = self.title.value
        self.title = new_book_title
        self.updated_at = datetime.now(timezone.utc)

        self.emit(
            BookRenamed(
                book_id=self.id,
                old_title=old_title,
                new_title=new_title,
                occurred_at=self.updated_at,
            )
        )

    def change_status(self, new_status: BookStatus) -> None:
        """Change Book status"""
        if self.status == new_status:
            return

        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

        self.emit(
            BookStatusChanged(
                book_id=self.id,
                old_status=old_status,
                new_status=new_status,
                occurred_at=self.updated_at,
            )
        )

    def mark_deleted(self) -> None:
        """Mark Book as deleted (soft delete)"""
        self.change_status(BookStatus.DELETED)
        now = datetime.now(timezone.utc)

        self.emit(
            BookDeleted(
                book_id=self.id,
                bookshelf_id=self.bookshelf_id,
                occurred_at=now,
            )
        )

    def move_to_bookshelf(self, new_bookshelf_id: UUID) -> None:
        """
        Transfer Book to new Bookshelf (真实转移，不是复制)

        Business Rules:
        1. Book must exist
        2. New Bookshelf must exist and be accessible
        3. Cannot transfer to current bookshelf
        4. Emits BookMovedToBookshelf event (RULE-011)

        Args:
            new_bookshelf_id: Target Bookshelf ID

        Raises:
            ValueError: If transfer is illegal
        """
        if self.bookshelf_id == new_bookshelf_id:
            raise ValueError("Book is already in the target bookshelf")

        # Actual transfer
        old_bookshelf_id = self.bookshelf_id
        self.bookshelf_id = new_bookshelf_id
        self.updated_at = datetime.now(timezone.utc)

        # Emit event
        self.emit(BookMovedToBookshelf(
            book_id=self.id,
            old_bookshelf_id=old_bookshelf_id,
            new_bookshelf_id=new_bookshelf_id,
            moved_at=self.updated_at,
        ))

    def move_to_basement(self, basement_bookshelf_id: UUID) -> None:
        """
        Transfer Book to Basement (deletion via soft delete, RULE-012)

        This is actually a move to Basement bookshelf with soft_deleted_at marked.

        Args:
            basement_bookshelf_id: Basement Bookshelf ID
        """
        old_bookshelf_id = self.bookshelf_id
        now = datetime.now(timezone.utc)

        # Actual transfer
        self.bookshelf_id = basement_bookshelf_id
        self.soft_deleted_at = now  # ← Mark as in Basement
        self.updated_at = now

        self.emit(BookMovedToBasement(
            book_id=self.id,
            old_bookshelf_id=old_bookshelf_id,
            basement_bookshelf_id=basement_bookshelf_id,
            deleted_at=now,
        ))

    def restore_from_basement(self, restore_to_bookshelf_id: UUID) -> None:
        """
        Restore Book from Basement (RULE-013)

        Args:
            restore_to_bookshelf_id: Target Bookshelf ID for restoration
        """
        if self.soft_deleted_at is None:
            raise ValueError("Book is not in Basement")

        basement_id = self.bookshelf_id
        now = datetime.now(timezone.utc)

        # Transfer back
        self.bookshelf_id = restore_to_bookshelf_id
        self.soft_deleted_at = None  # ← Clear Basement marker
        self.updated_at = now

        self.emit(BookRestoredFromBasement(
            book_id=self.id,
            basement_bookshelf_id=basement_id,
            restored_to_bookshelf_id=restore_to_bookshelf_id,
            restored_at=now,
        ))

    def update_block_count(self, count: int) -> None:
        """Update block count (called when Blocks are modified)"""
        self.block_count = count
        self.updated_at = datetime.now(timezone.utc)

        self.emit(
            BlocksUpdated(
                book_id=self.id,
                block_count=count,
                occurred_at=self.updated_at,
            )
        )

    # ========================================================================
    # Query Methods (Simplified as Properties)
    # ========================================================================

    @property
    def is_draft(self) -> bool:
        """Check if Book is in draft status"""
        return self.status == BookStatus.DRAFT

    @property
    def is_published(self) -> bool:
        """Check if Book is published"""
        return self.status == BookStatus.PUBLISHED

    @property
    def is_archived(self) -> bool:
        """Check if Book is archived"""
        return self.status == BookStatus.ARCHIVED

    @property
    def is_deleted(self) -> bool:
        """Check if Book is deleted"""
        return self.status == BookStatus.DELETED

    @property
    def can_edit(self) -> bool:
        """Check if Book can be edited"""
        return self.status != BookStatus.DELETED

    @property
    def is_in_basement(self) -> bool:
        """检查是否在 Basement"""
        return self.soft_deleted_at is not None

    def __repr__(self) -> str:
        return f"<Book(id={self.id}, bookshelf_id={self.bookshelf_id}, title={self.title.value})>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Book):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
