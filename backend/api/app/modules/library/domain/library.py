"""
Library Domain - Core business logic for user's top-level container

Purpose:
- Represents a single Library per user (top-level aggregate root)
- Manages core state: name, user_id, timestamps
- Emits DomainEvents on state changes
- Does NOT manage: cover_url (→ Media), icon (→ Media), usage_count (→ Chronicle)

Architecture:
- Pure domain layer with zero infrastructure dependencies
- Uses only shared.base and local value objects
- Factory pattern for creation (Library.create)
- Immutable value objects (LibraryName)

Invariants (from DDD_RULES.yaml):
- RULE-001: Each user has exactly one Library
- RULE-002: Library must have a user_id (FK)
- RULE-003: Library name is non-empty and ≤ 255 characters

Cross-Reference:
- DDD_RULES.yaml: library domain definition
- HEXAGONAL_RULES.yaml: Domain layer constraints (Part 1)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from shared.base import AggregateRoot

# 本地导入（Domain 层内部）
from .library_name import LibraryName
from .events import (
    LibraryCreated,
    LibraryRenamed,
    LibraryDeleted,
    BasementCreated,
    LibraryRestored,
)


# ============================================================================
# Aggregate Root: Library
# ============================================================================

class Library(AggregateRoot):
    """
    Library Aggregate Root

    Top-level container for a user's knowledge base. Represents RULE-001:
    each user has exactly one Library.

    State:
    - id (UUID): Immutable unique identifier
    - user_id (UUID): Immutable reference to User
    - name (LibraryName): Mutable, validated by ValueObject
    - basement_bookshelf_id (UUID): Auto-created recycle bin (RULE-010)
    - timestamps: created_at, updated_at, soft_deleted_at
    - events: List of emitted DomainEvents

    Invariants:
    - user_id must be non-null (RULE-002)
    - name must be non-empty and ≤ 255 characters (RULE-003)
    - Cannot have duplicate user_id (RULE-001) - enforced by Repository

    Business Rules:
    - Created via Library.create() factory (emits LibraryCreated + BasementCreated)
    - Name can be updated via rename() (emits LibraryRenamed)
    - Can be marked deleted via mark_deleted() (emits LibraryDeleted)

    Non-Responsibility:
    - Media management (Media domain)
    - Bookshelf/Book/Block management (their respective domains)
    - Usage statistics (Chronicle domain)
    - UI styling (Media/Theme domains)
    """

    def __init__(
        self,
        library_id: UUID,
        user_id: UUID,
        name: LibraryName,
        basement_bookshelf_id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        soft_deleted_at: Optional[datetime] = None,
    ):
        """
        Internal constructor - use Library.create() instead

        Args:
            library_id: Immutable unique identifier
            user_id: Immutable user reference (RULE-001, RULE-002)
            name: LibraryName value object (RULE-003 validated)
            basement_bookshelf_id: Auto-created recycle bin UUID (RULE-010)
            created_at: Creation timestamp
            updated_at: Last update timestamp
            soft_deleted_at: Soft delete timestamp (if deleted)

        Raises:
            ValueError: If name is invalid (ValueObject validation)
        """
        super().__init__()
        self.id = library_id
        self.user_id = user_id
        self.name = name  # LibraryName handles RULE-003 validation
        self.basement_bookshelf_id = basement_bookshelf_id
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.soft_deleted_at = soft_deleted_at
        self.events: List = []  # Collected events (sent to EventBus by Service)

    # ========================================================================
    # Factory Methods (Creation)
    # ========================================================================

    @classmethod
    def create(cls, user_id: UUID, name: str) -> Library:
        """
        Factory method to create a new Library

        Implements RULE-001 creation workflow:
        1. Generate unique IDs (library_id, basement_id)
        2. Validate name via LibraryName ValueObject (RULE-003)
        3. Create Library instance
        4. Emit LibraryCreated event
        5. Emit BasementCreated event (RULE-010)

        Args:
            user_id: The ID of the user who owns this Library (RULE-002)
            name: The name of the Library (must be 1-255 chars, RULE-003)

        Returns:
            New Library instance with events pending emission

        Raises:
            ValueError: If name is invalid

            Example:
            >>> library = Library.create(
            ...     user_id=UUID("user-123"),
            ...     name="My Knowledge Base"
            ... )
            >>> len(library.events)  # 2 events emitted
            2

        Cross-Reference:
            - DDD_RULES.yaml: RULE-001 implementation
            - HEXAGONAL_RULES.yaml: EventBus adapter
        """
        library_id = uuid4()
        basement_id = uuid4()  # 自动为每个 Library 创建 Basement（RULE-010）
        library_name = LibraryName(value=name)  # Validates RULE-003
        now = datetime.now(timezone.utc)

        # 创建 Library 实例
        library = cls(
            library_id=library_id,
            user_id=user_id,
            name=library_name,
            basement_bookshelf_id=basement_id,
            created_at=now,
            updated_at=now,
        )

        # 发出 LibraryCreated 事件（RULE-001）
        library.emit(
            LibraryCreated(
                library_id=library_id,
                user_id=user_id,
                name=name,
                occurred_at=now,
            )
        )

        # 发出 BasementCreated 事件（RULE-010）
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
    # Business Methods (State Changes)
    # ========================================================================

    def rename(self, new_name: str) -> None:
        """
        Rename the Library

        Validates new name via LibraryName ValueObject (RULE-003).
        If name is unchanged, no-op.

        Args:
            new_name: The new name for the Library (must be 1-255 chars)

        Returns:
            None (modifies state in-place)

        Raises:
            ValueError: If new_name is invalid

        Side Effects:
            - Updates Library.name
            - Updates Library.updated_at
            - Emits LibraryRenamed event

            Example:
            >>> library.rename("Updated Knowledge Base")
            >>> library.name.value
            'Updated Knowledge Base'
            >>> len(library.events)
            1  # LibraryRenamed event

        Cross-Reference:
            - DDD_RULES.yaml: RULE-003 validation
        """
        # Validate new name (RULE-003)
        new_library_name = LibraryName(value=new_name)

        # No-op if name unchanged
        if self.name.value == new_library_name.value:
            return

        old_name = self.name.value
        self.name = new_library_name
        self.updated_at = datetime.now(timezone.utc)

        # Emit event for listeners (Audit, UI update, etc.)
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

        Emits LibraryDeleted event. The actual cascade deletion
        (Bookshelves, Books, Blocks, Media) is handled by:
        1. Event listeners in backend/infra/event_bus/handlers/
        2. Database cascade rules (on_delete=CASCADE)
        3. Service layer orchestration

        Returns:
            None (modifies state in-place)

        Side Effects:
            - Emits LibraryDeleted event (triggering cascade)
            - Does NOT call repository.delete() here
            - Repository.save() will persist soft_deleted_at

            Example:
            >>> library.mark_deleted()
            >>> len(library.events)
            1  # LibraryDeleted event

        Cross-Reference:
            - DDD_RULES.yaml: Soft delete strategy
            - HEXAGONAL_RULES.yaml: EventBus adapter (cascade triggers)
        """
        now = datetime.now(timezone.utc)
        self.updated_at = now
        self.soft_deleted_at = now  # Mark as deleted

        self.emit(
            LibraryDeleted(
                library_id=self.id,
                user_id=self.user_id,
                occurred_at=now,
            )
        )

    def restore(self) -> None:
        """
        Restore the Library from Basement (soft delete reversal)

        Implements BASEMENT-001 recovery workflow for Library (root aggregate).
        As the root entity, there is no parent dependency check needed.

        Returns:
            None (modifies state in-place)

        Raises:
            ValueError: If Library is not deleted

        Side Effects:
            - Sets soft_deleted_at to None (mark as active)
            - Updates updated_at timestamp
            - Emits LibraryRestored event
            - Does NOT restore child entities (Bookshelves) - optional via cascade

        Example:
            >>> library.mark_deleted()
            >>> library.restore()
            >>> library.is_deleted()
            False

        Cross-Reference:
            - DDD_RULES.yaml: BASEMENT-001 recovery rules
            - ADR-038: Deletion & Recovery Unified Framework
        """
        if not self.is_deleted():
            raise ValueError(
                f"Cannot restore Library {self.id}: not deleted (soft_deleted_at is None)"
            )

        now = datetime.now(timezone.utc)
        self.soft_deleted_at = None  # Revert soft delete
        self.updated_at = now

        self.emit(
            LibraryRestored(
                library_id=self.id,
                user_id=self.user_id,
                restored_at=now,
                occurred_at=now,
            )
        )

    # ========================================================================
    # Query Methods (Immutable)
    # ========================================================================

    def get_name_value(self) -> str:
        """Get name as string (convenience method)"""
        return self.name.value

    def is_deleted(self) -> bool:
        """Check if Library is soft-deleted"""
        return self.soft_deleted_at is not None

    # ========================================================================
    # Equality & Hashing
    # ========================================================================

    def __repr__(self) -> str:
        return (
            f"<Library("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"name='{self.name.value}', "
            f"deleted={self.is_deleted()}"
            f")>"
        )

    def __eq__(self, other: object) -> bool:
        """Equality by ID (Aggregate Root pattern)"""
        if not isinstance(other, Library):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hashable by ID"""
        return hash(self.id)