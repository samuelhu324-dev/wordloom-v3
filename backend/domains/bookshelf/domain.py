"""
Bookshelf Domain - Business logic for organizing Books

Purpose:
- Represents unlimited classification containers under a Library
- Manages state: is_pinned, is_favorite, status
- Does NOT manage: cover_url (→ Media), icon (→ Media), usage_count (→ Chronicle)

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

class BookshelfStatus(str, Enum):
    """Status of a Bookshelf"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


# ============================================================================
# Domain Events
# ============================================================================

@dataclass
class BookshelfCreated(DomainEvent):
    """Emitted when a new Bookshelf is created"""
    bookshelf_id: UUID
    library_id: UUID
    name: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.bookshelf_id


@dataclass
class BookshelfRenamed(DomainEvent):
    """Emitted when Bookshelf is renamed"""
    bookshelf_id: UUID
    old_name: str
    new_name: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.bookshelf_id


@dataclass
class BookshelfPinned(DomainEvent):
    """Emitted when Bookshelf is pinned"""
    bookshelf_id: UUID
    pinned_at: datetime
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.bookshelf_id


@dataclass
class BookshelfUnpinned(DomainEvent):
    """Emitted when Bookshelf is unpinned"""
    bookshelf_id: UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.bookshelf_id


@dataclass
class BookshelfFavorited(DomainEvent):
    """Emitted when Bookshelf is marked as favorite"""
    bookshelf_id: UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.bookshelf_id


@dataclass
class BookshelfUnfavorited(DomainEvent):
    """Emitted when Bookshelf is unfavorited"""
    bookshelf_id: UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.bookshelf_id


@dataclass
class BookshelfStatusChanged(DomainEvent):
    """Emitted when Bookshelf status changes"""
    bookshelf_id: UUID
    old_status: BookshelfStatus
    new_status: BookshelfStatus
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.bookshelf_id


@dataclass
class BookshelfDeleted(DomainEvent):
    """Emitted when Bookshelf is deleted"""
    bookshelf_id: UUID
    library_id: UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.bookshelf_id


# ============================================================================
# Value Objects
# ============================================================================

@dataclass(frozen=True)
class BookshelfName(ValueObject):
    """Value object for Bookshelf name"""
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Bookshelf name cannot be empty")
        if len(self.value) > 255:
            raise ValueError("Bookshelf name cannot exceed 255 characters")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class BookshelfDescription(ValueObject):
    """Value object for Bookshelf description"""
    value: Optional[str] = None

    def __post_init__(self):
        if self.value is not None and len(self.value) > 1000:
            raise ValueError("Bookshelf description cannot exceed 1000 characters")

    def __str__(self) -> str:
        return self.value or ""


# ============================================================================
# Aggregate Root
# ============================================================================

class Bookshelf(AggregateRoot):
    """
    Bookshelf Aggregate Root

    Invariants:
    - Bookshelf must have a Library (parent aggregate)
    - Name is required, ≤ 255 characters
    - Can only have one status at a time
    - A Bookshelf cannot be both pinned and unpinned
    - Bookshelf contains zero or more Books (managed by Book Domain)
    - Media (cover, icon) managed by Media Domain
    - Usage statistics managed by Chronicle Domain

    Business Rules:
    - Created with initial name and Library reference
    - Name can be updated (BookshelfRenamed event)
    - Can be pinned/unpinned (BookshelfPinned/BookshelfUnpinned events)
    - Can be favorited/unfavorited (BookshelfFavorited/BookshelfUnfavorited events)
    - Status can change: active → archived → deleted (BookshelfStatusChanged event)
    """

    def __init__(
        self,
        bookshelf_id: UUID,
        library_id: UUID,
        name: BookshelfName,
        description: BookshelfDescription = None,
        is_pinned: bool = False,
        pinned_at: Optional[datetime] = None,
        is_favorite: bool = False,
        status: BookshelfStatus = BookshelfStatus.ACTIVE,
        book_count: int = 0,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self.id = bookshelf_id
        self.library_id = library_id
        self.name = name
        self.description = description or BookshelfDescription()
        self.is_pinned = is_pinned
        self.pinned_at = pinned_at
        self.is_favorite = is_favorite
        self.status = status
        self.book_count = book_count
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.events: List[DomainEvent] = []

    # ========================================================================
    # Factory Methods
    # ========================================================================

    @classmethod
    def create(
        cls,
        library_id: UUID,
        name: str,
        description: Optional[str] = None,
    ) -> Bookshelf:
        """
        Factory method to create a new Bookshelf

        Args:
            library_id: ID of the parent Library
            name: Name of the Bookshelf
            description: Optional description

        Returns:
            New Bookshelf instance with BookshelfCreated event

        Raises:
            ValueError: If name or description invalid
        """
        bookshelf_id = uuid4()
        bookshelf_name = BookshelfName(value=name)
        bookshelf_desc = BookshelfDescription(value=description)
        now = datetime.utcnow()

        bookshelf = cls(
            bookshelf_id=bookshelf_id,
            library_id=library_id,
            name=bookshelf_name,
            description=bookshelf_desc,
            status=BookshelfStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        bookshelf.emit(
            BookshelfCreated(
                bookshelf_id=bookshelf_id,
                library_id=library_id,
                name=name,
                occurred_at=now,
            )
        )

        return bookshelf

    # ========================================================================
    # Business Methods - Name Management
    # ========================================================================

    def rename(self, new_name: str) -> None:
        """Rename the Bookshelf"""
        new_bookshelf_name = BookshelfName(value=new_name)

        if self.name.value == new_bookshelf_name.value:
            return

        old_name = self.name.value
        self.name = new_bookshelf_name
        self.updated_at = datetime.utcnow()

        self.emit(
            BookshelfRenamed(
                bookshelf_id=self.id,
                old_name=old_name,
                new_name=new_name,
                occurred_at=self.updated_at,
            )
        )

    def set_description(self, description: Optional[str]) -> None:
        """Update the Bookshelf description"""
        self.description = BookshelfDescription(value=description)
        self.updated_at = datetime.utcnow()

    # ========================================================================
    # Business Methods - State Management
    # ========================================================================

    def pin(self) -> None:
        """Pin this Bookshelf to top"""
        if self.is_pinned:
            return

        self.is_pinned = True
        self.pinned_at = datetime.utcnow()
        self.updated_at = self.pinned_at

        self.emit(
            BookshelfPinned(
                bookshelf_id=self.id,
                pinned_at=self.pinned_at,
                occurred_at=self.pinned_at,
            )
        )

    def unpin(self) -> None:
        """Unpin this Bookshelf"""
        if not self.is_pinned:
            return

        self.is_pinned = False
        self.pinned_at = None
        self.updated_at = datetime.utcnow()

        self.emit(
            BookshelfUnpinned(
                bookshelf_id=self.id,
                occurred_at=self.updated_at,
            )
        )

    def mark_favorite(self) -> None:
        """Mark this Bookshelf as favorite"""
        if self.is_favorite:
            return

        self.is_favorite = True
        self.updated_at = datetime.utcnow()

        self.emit(
            BookshelfFavorited(
                bookshelf_id=self.id,
                occurred_at=self.updated_at,
            )
        )

    def unmark_favorite(self) -> None:
        """Unmark this Bookshelf as favorite"""
        if not self.is_favorite:
            return

        self.is_favorite = False
        self.updated_at = datetime.utcnow()

        self.emit(
            BookshelfUnfavorited(
                bookshelf_id=self.id,
                occurred_at=self.updated_at,
            )
        )

    def change_status(self, new_status: BookshelfStatus) -> None:
        """Change Bookshelf status"""
        if self.status == new_status:
            return

        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()

        self.emit(
            BookshelfStatusChanged(
                bookshelf_id=self.id,
                old_status=old_status,
                new_status=new_status,
                occurred_at=self.updated_at,
            )
        )

    def archive(self) -> None:
        """Archive this Bookshelf"""
        self.change_status(BookshelfStatus.ARCHIVED)

    def unarchive(self) -> None:
        """Unarchive this Bookshelf"""
        self.change_status(BookshelfStatus.ACTIVE)

    def mark_deleted(self) -> None:
        """Mark Bookshelf as deleted (soft delete)"""
        self.change_status(BookshelfStatus.DELETED)
        now = datetime.utcnow()

        self.emit(
            BookshelfDeleted(
                bookshelf_id=self.id,
                library_id=self.library_id,
                occurred_at=now,
            )
        )

    # ========================================================================
    # Query Methods
    # ========================================================================

    def can_accept_books(self) -> bool:
        """Check if Bookshelf can accept new Books"""
        return self.status != BookshelfStatus.DELETED

    def is_active(self) -> bool:
        """Check if Bookshelf is active"""
        return self.status == BookshelfStatus.ACTIVE

    def is_archived(self) -> bool:
        """Check if Bookshelf is archived"""
        return self.status == BookshelfStatus.ARCHIVED

    def is_deleted(self) -> bool:
        """Check if Bookshelf is deleted"""
        return self.status == BookshelfStatus.DELETED

    def __repr__(self) -> str:
        return f"<Bookshelf(id={self.id}, library_id={self.library_id}, name={self.name.value}, status={self.status})>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Bookshelf):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
