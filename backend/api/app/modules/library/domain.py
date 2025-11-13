"""
Library Domain - Core business logic for user's top-level container

Purpose:
- Represents a single Library per user (top-level aggregate)
- Manages minimal metadata (name, created_at)
- Does NOT manage: cover_url (→ Media), icon (→ Media), usage_count (→ Chronicle)

Architecture:
- Pure domain layer with zero infrastructure dependencies
- Emits DomainEvents on state changes (LibraryCreated, LibraryRenamed, LibraryDeleted)
- Uses Repository pattern for persistence abstraction
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from shared.base import AggregateRoot, DomainEvent, ValueObject


# ============================================================================
# Domain Events
# ============================================================================

@dataclass
class LibraryCreated(DomainEvent):
    """Domain event emitted when a new Library is created"""
    library_id: UUID
    user_id: UUID
    name: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.library_id


@dataclass
class LibraryRenamed(DomainEvent):
    """Domain event emitted when Library name is changed"""
    library_id: UUID
    old_name: str
    new_name: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.library_id


@dataclass
class LibraryDeleted(DomainEvent):
    """Domain event emitted when Library is deleted"""
    library_id: UUID
    user_id: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.library_id


@dataclass
class BasementCreated(DomainEvent):
    """Domain event emitted when Basement (recycle bin) is automatically created with Library"""
    basement_bookshelf_id: UUID
    library_id: UUID
    user_id: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.library_id


# ============================================================================
# Value Objects
# ============================================================================

@dataclass(frozen=True)
class LibraryName(ValueObject):
    """Value object for Library name"""
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Library name cannot be empty")
        if len(self.value) > 255:
            raise ValueError("Library name cannot exceed 255 characters")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class LibraryMetadata(ValueObject):
    """Value object for Library metadata"""
    name: LibraryName
    user_id: UUID

    def __post_init__(self):
        if not self.user_id:
            raise ValueError("User ID cannot be empty")


# ============================================================================
# Aggregate Root
# ============================================================================

class Library(AggregateRoot):
    """
    Library Aggregate Root

    Invariants:
    - Each user can only have one Library
    - Library name must be non-empty and ≤ 255 characters
    - Library must have a user_id
    - Library contains zero or more Bookshelves (managed by Bookshelf Domain)
    - Cover, icon, and usage metadata are managed by Media/Chronicle Domains

    Business Rules:
    - Created with initial name (LibraryCreated event)
    - Name can be updated (LibraryRenamed event)
    - Can be marked as deleted (LibraryDeleted event, soft delete)
    """

    def __init__(
        self,
        library_id: UUID,
        user_id: UUID,
        name: LibraryName,
        basement_bookshelf_id: UUID = None,
        created_at: datetime = None,
        updated_at: datetime = None,
        soft_deleted_at: Optional[datetime] = None,
    ):
        super().__init__()
        self.id = library_id
        self.user_id = user_id
        self.name = name
        self.basement_bookshelf_id = basement_bookshelf_id  # ← 特殊的 Basement 书架
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.soft_deleted_at = soft_deleted_at
        self.events = []

    # ========================================================================
    # Factory Methods
    # ========================================================================

    @classmethod
    def create(cls, user_id: UUID, name: str) -> Library:
        """
        Factory method to create a new Library

        Args:
            user_id: The ID of the user who owns this Library
            name: The name of the Library

        Returns:
            New Library instance with LibraryCreated and BasementCreated events

        Raises:
            ValueError: If name is invalid
        """
        library_id = uuid4()
        basement_id = uuid4()  # ← 自动为每个 Library 创建 Basement
        library_name = LibraryName(value=name)
        now = datetime.now(timezone.utc)

        library = cls(
            library_id=library_id,
            user_id=user_id,
            name=library_name,
            basement_bookshelf_id=basement_id,
            created_at=now,
            updated_at=now,
        )

        # 发出两个事件：Library 创建 + Basement 创建
        library.emit(
            LibraryCreated(
                library_id=library_id,
                user_id=user_id,
                name=name,
                occurred_at=now,
            )
        )

        library.emit(
            BasementCreated(
                basement_bookshelf_id=basement_id,
                library_id=library_id,
                user_id=user_id,
                occurred_at=now,
            )
        )

        return library

    # ========================================================================
    # Business Methods
    # ========================================================================

    def rename(self, new_name: str) -> None:
        """
        Rename the Library

        Args:
            new_name: The new name for the Library

        Raises:
            ValueError: If new_name is invalid

        Side Effects:
            - Updates Library.name
            - Updates Library.updated_at
            - Emits LibraryRenamed event
        """
        new_library_name = LibraryName(value=new_name)

        if self.name.value == new_library_name.value:
            return  # No change needed

        old_name = self.name.value
        self.name = new_library_name
        self.updated_at = datetime.now(timezone.utc)

        self.emit(
            LibraryRenamed(
                library_id=self.id,
                old_name=old_name,
                new_name=new_name,
                occurred_at=self.updated_at,
            )
        )

    def mark_deleted(self) -> None:
        """
        Mark the Library as deleted (soft delete)

        This emits a LibraryDeleted event. The actual deletion cascade
        (deleting Bookshelves, Books, Blocks) is handled by Domain Services
        and Infrastructure layer (database cascade rules).

        Side Effects:
            - Emits LibraryDeleted event
        """
        now = datetime.now(timezone.utc)
        self.updated_at = now

        self.emit(
            LibraryDeleted(
                library_id=self.id,
                user_id=self.user_id,
                occurred_at=now,
            )
        )

    # ========================================================================
    # Query Methods
    # ========================================================================

    def get_metadata(self) -> LibraryMetadata:
        """
        Get Library metadata as a Value Object

        Returns:
            LibraryMetadata containing name and user_id
        """
        return LibraryMetadata(name=self.name, user_id=self.user_id)

    def __repr__(self) -> str:
        return f"<Library(id={self.id}, user_id={self.user_id}, name={self.name.value})>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Library):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
