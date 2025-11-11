"""
Book Domain - Business logic for content containers with Blocks

Purpose:
- Represents content container under a Bookshelf
- Manages Block references (ordered list)
- Manages state: status, is_pinned, due_at, etc.
- Does NOT manage: preview_image (→ Media), usage_count (→ Chronicle)

Architecture:
- Pure domain layer with zero infrastructure dependencies
- Emits DomainEvents on state changes
- Uses Repository pattern for persistence abstraction
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from enum import Enum

from shared.base import AggregateRoot, DomainEvent, ValueObject


# ============================================================================
# Enums
# ============================================================================

class BookStatus(str, Enum):
    """Status of a Book"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


# ============================================================================
# Domain Events
# ============================================================================

@dataclass
class BookCreated(DomainEvent):
    """Emitted when a new Book is created"""
    book_id: UUID
    bookshelf_id: UUID
    title: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BookRenamed(DomainEvent):
    """Emitted when Book title is changed"""
    book_id: UUID
    old_title: str
    new_title: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BookPinned(DomainEvent):
    """Emitted when Book is pinned"""
    book_id: UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BookUnpinned(DomainEvent):
    """Emitted when Book is unpinned"""
    book_id: UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BookStatusChanged(DomainEvent):
    """Emitted when Book status changes"""
    book_id: UUID
    old_status: BookStatus
    new_status: BookStatus
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BookDeleted(DomainEvent):
    """Emitted when Book is deleted"""
    book_id: UUID
    bookshelf_id: UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BlocksUpdated(DomainEvent):
    """Emitted when Book's Blocks are updated"""
    book_id: UUID
    block_count: int
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


# ============================================================================
# Value Objects
# ============================================================================

@dataclass(frozen=True)
class BookTitle(ValueObject):
    """Value object for Book title"""
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Book title cannot be empty")
        if len(self.value) > 255:
            raise ValueError("Book title cannot exceed 255 characters")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class BookSummary(ValueObject):
    """Value object for Book summary"""
    value: Optional[str] = None

    def __post_init__(self):
        if self.value is not None and len(self.value) > 1000:
            raise ValueError("Book summary cannot exceed 1000 characters")

    def __str__(self) -> str:
        return self.value or ""


# ============================================================================
# Aggregate Root
# ============================================================================

class Book(AggregateRoot):
    """
    Book Aggregate Root

    Invariants:
    - Book must have a Bookshelf (parent aggregate)
    - Title is required, ≤ 255 characters
    - Summary is optional, ≤ 1000 characters
    - Block references are managed independently by Block Domain
    - Book tracks: is_pinned, due_at, status
    - Media (preview_image) managed by Media Domain
    - Usage statistics managed by Chronicle Domain

    Business Rules:
    - Created with initial title and Bookshelf reference
    - Title can be updated (BookRenamed event)
    - Can be pinned/unpinned (BookPinned/BookUnpinned events)
    - Status can change: draft → published → archived → deleted (BookStatusChanged event)
    - Contains ordered Blocks (managed by Block Domain)
    """

    def __init__(
        self,
        book_id: UUID,
        bookshelf_id: UUID,
        title: BookTitle,
        summary: BookSummary = None,
        is_pinned: bool = False,
        due_at: Optional[datetime] = None,
        status: BookStatus = BookStatus.DRAFT,
        block_count: int = 0,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self.id = book_id
        self.bookshelf_id = bookshelf_id
        self.title = title
        self.summary = summary or BookSummary()
        self.is_pinned = is_pinned
        self.due_at = due_at
        self.status = status
        self.block_count = block_count
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.events: List[DomainEvent] = []

    # ========================================================================
    # Factory Methods
    # ========================================================================

    @classmethod
    def create(
        cls,
        bookshelf_id: UUID,
        title: str,
        summary: Optional[str] = None,
    ) -> Book:
        """
        Factory method to create a new Book

        Args:
            bookshelf_id: ID of the parent Bookshelf
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
        now = datetime.utcnow()

        book = cls(
            book_id=book_id,
            bookshelf_id=bookshelf_id,
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
        self.updated_at = datetime.utcnow()

        self.emit(
            BookRenamed(
                book_id=self.id,
                old_title=old_title,
                new_title=new_title,
                occurred_at=self.updated_at,
            )
        )

    def set_summary(self, summary: Optional[str]) -> None:
        """Update the Book summary"""
        self.summary = BookSummary(value=summary)
        self.updated_at = datetime.utcnow()

    def set_due_date(self, due_at: Optional[datetime]) -> None:
        """Set or clear the due date"""
        self.due_at = due_at
        self.updated_at = datetime.utcnow()

    def pin(self) -> None:
        """Pin this Book"""
        if self.is_pinned:
            return

        self.is_pinned = True
        self.updated_at = datetime.utcnow()

        self.emit(
            BookPinned(
                book_id=self.id,
                occurred_at=self.updated_at,
            )
        )

    def unpin(self) -> None:
        """Unpin this Book"""
        if not self.is_pinned:
            return

        self.is_pinned = False
        self.updated_at = datetime.utcnow()

        self.emit(
            BookUnpinned(
                book_id=self.id,
                occurred_at=self.updated_at,
            )
        )

    def change_status(self, new_status: BookStatus) -> None:
        """Change Book status"""
        if self.status == new_status:
            return

        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()

        self.emit(
            BookStatusChanged(
                book_id=self.id,
                old_status=old_status,
                new_status=new_status,
                occurred_at=self.updated_at,
            )
        )

    def publish(self) -> None:
        """Publish this Book"""
        self.change_status(BookStatus.PUBLISHED)

    def archive(self) -> None:
        """Archive this Book"""
        self.change_status(BookStatus.ARCHIVED)

    def mark_deleted(self) -> None:
        """Mark Book as deleted (soft delete)"""
        self.change_status(BookStatus.DELETED)
        now = datetime.utcnow()

        self.emit(
            BookDeleted(
                book_id=self.id,
                bookshelf_id=self.bookshelf_id,
                occurred_at=now,
            )
        )

    def update_block_count(self, count: int) -> None:
        """Update block count (called when Blocks are modified)"""
        self.block_count = count
        self.updated_at = datetime.utcnow()

        self.emit(
            BlocksUpdated(
                book_id=self.id,
                block_count=count,
                occurred_at=self.updated_at,
            )
        )

    # ========================================================================
    # Query Methods
    # ========================================================================

    def is_draft(self) -> bool:
        """Check if Book is in draft status"""
        return self.status == BookStatus.DRAFT

    def is_published(self) -> bool:
        """Check if Book is published"""
        return self.status == BookStatus.PUBLISHED

    def is_archived(self) -> bool:
        """Check if Book is archived"""
        return self.status == BookStatus.ARCHIVED

    def is_deleted(self) -> bool:
        """Check if Book is deleted"""
        return self.status == BookStatus.DELETED

    def can_edit(self) -> bool:
        """Check if Book can be edited"""
        return self.status != BookStatus.DELETED

    def __repr__(self) -> str:
        return f"<Book(id={self.id}, bookshelf_id={self.bookshelf_id}, title={self.title.value})>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Book):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
