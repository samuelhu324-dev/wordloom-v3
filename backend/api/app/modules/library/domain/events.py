"""
Library Domain Events

Purpose:
- Define all events that can be emitted by the Library Aggregate Root
- Used for event sourcing and cross-domain communication
- Events are immutable data structures (frozen dataclasses)

Events Defined:
1. LibraryCreated - Emitted when a new Library is created
2. LibraryRenamed - Emitted when Library name is changed
3. LibraryDeleted - Emitted when Library is deleted (soft delete)
4. BasementCreated - Emitted when Basement is auto-created with Library

Cross-Reference:
- DDD_RULES.yaml: library.events section
- HEXAGONAL_RULES.yaml: EventBus adapter section
- Related: backend/infra/event_bus.py (EventBus implementation)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from shared.base import DomainEvent


# ============================================================================
# Domain Events
# ============================================================================

@dataclass
class LibraryCreated(DomainEvent):
    """
    Event: Library was created

    Emitted by: Library.create() factory method
    Listeners:
      - Bookshelf domain (creates automatic Basement)
      - Chronicle domain (initializes session)

    Invariant: RULE-001 (每用户一库)
    """

    library_id: UUID = None
    user_id: UUID = None
    name: str = None
    occurred_at: datetime = None

    def __post_init__(self) -> None:
        """Set occurred_at if not provided"""
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        """Event sourcing: which aggregate does this event belong to?"""
        return self.library_id

    def __repr__(self) -> str:
        return (
            f"LibraryCreated("
            f"library_id={self.library_id}, "
            f"user_id={self.user_id}, "
            f"name='{self.name}', "
            f"occurred_at={self.occurred_at.isoformat()}"
            f")"
        )


@dataclass
class LibraryRenamed(DomainEvent):
    """
    Event: Library name was changed

    Emitted by: Library.rename() method
    Listeners:
      - UI update (show renamed library)
      - Audit log

    Invariant: RULE-003 (名称非空且 ≤255 字符)
    """

    library_id: UUID = None
    old_name: str = None
    new_name: str = None
    occurred_at: datetime = None

    def __post_init__(self) -> None:
        """Set occurred_at if not provided"""
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.library_id

    def __repr__(self) -> str:
        return (
            f"LibraryRenamed("
            f"library_id={self.library_id}, "
            f"old_name='{self.old_name}', "
            f"new_name='{self.new_name}', "
            f"occurred_at={self.occurred_at.isoformat()}"
            f")"
        )


@dataclass
class LibraryDeleted(DomainEvent):
    """
    Event: Library was deleted (soft delete)

    Emitted by: Library.mark_deleted() method
    Listeners:
      - Bookshelf domain (cascade delete to Basement)
      - Media domain (mark associated media as deleted)
      - Chronicle domain (cleanup sessions)
      - UI update (remove from list)

    Note: This is a soft delete event. Hard deletion happens later by a purge job.
    """

    library_id: UUID = None
    user_id: UUID = None
    occurred_at: datetime = None

    def __post_init__(self) -> None:
        """Set occurred_at if not provided"""
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.library_id

    def __repr__(self) -> str:
        return (
            f"LibraryDeleted("
            f"library_id={self.library_id}, "
            f"user_id={self.user_id}, "
            f"occurred_at={self.occurred_at.isoformat()}"
            f")"
        )


@dataclass
class BasementCreated(DomainEvent):
    """
    Event: Basement (recycle bin) bookshelf was auto-created with Library

    Emitted by: Library.create() factory method
    Listeners:
      - Bookshelf domain (creates the Basement entity)

    Invariant: RULE-010 (每个 Library 自动创建 Basement)

    Note: This event is special - it's emitted by Library but triggers Bookshelf creation.
          The actual Basement creation is done by listening to this event.
    """

    basement_bookshelf_id: UUID = None
    library_id: UUID = None
    user_id: UUID = None
    occurred_at: datetime = None

    def __post_init__(self) -> None:
        """Set occurred_at if not provided"""
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        """This event belongs to Library aggregate"""
        return self.library_id

    def __repr__(self) -> str:
        return (
            f"BasementCreated("
            f"basement_bookshelf_id={self.basement_bookshelf_id}, "
            f"library_id={self.library_id}, "
            f"user_id={self.user_id}, "
            f"occurred_at={self.occurred_at.isoformat()}"
            f")"
        )


@dataclass
class LibraryRestored(DomainEvent):
    """
    Event: Library was restored from Basement (soft delete reversed)

    Emitted by: Library.restore() method
    Listeners:
      - UI update (show restored library)
      - Audit log
      - Bookshelf domain (optionally restore child bookshelves)

    Invariant: BASEMENT-001 (恢复时父级必须存在 - Library 是根，无此限制)

    Note: Restoration marks soft_deleted_at as None, reverting the soft delete.
    """

    library_id: UUID = None
    user_id: UUID = None
    restored_at: datetime = None
    occurred_at: datetime = None

    def __post_init__(self) -> None:
        """Set occurred_at if not provided"""
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.library_id

    def __repr__(self) -> str:
        return (
            f"LibraryRestored("
            f"library_id={self.library_id}, "
            f"user_id={self.user_id}, "
            f"restored_at={self.restored_at.isoformat()}, "
            f"occurred_at={self.occurred_at.isoformat()}"
            f")"
        )


# ============================================================================
# Event Registry (for documentation)
# ============================================================================

LIBRARY_EVENTS = [
    LibraryCreated,
    LibraryRenamed,
    LibraryDeleted,
    BasementCreated,
    LibraryRestored,
]

"""
Event Flow Diagram:

User Action          Domain Method           Events Emitted
─────────────────────────────────────────────────────────────
Create Library   →   Library.create()    →   LibraryCreated
                                         →   BasementCreated

Rename Library   →   Library.rename()    →   LibraryRenamed

Delete Library   →   Library.mark_deleted()  →   LibraryDeleted

All events eventually reach:
  - EventBus (backend/infra/event_bus.py)
  - Event Handlers (backend/infra/event_bus/handlers/)
  - Audit Log
  - External Services
"""