"""
Bookshelf Domain Events

Purpose:
- Defines all domain events emitted by Bookshelf aggregate
- Events represent state changes that occurred and are immutable records
- Used for event sourcing and side effects

Events:
1. BookshelfCreated - 创建新书架
2. BookshelfRenamed - 重命名书架
3. BookshelfStatusChanged - 状态变更
4. BookshelfDeleted - 删除书架
"""

from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime, timezone
from api.app.shared.base import DomainEvent


# ============================================================================
# Domain Events
# ============================================================================

@dataclass
class BookshelfCreated(DomainEvent):
    """
    Event: Bookshelf Created

    Emitted when: New bookshelf created via Bookshelf.create()
    Aggregrate ID: bookshelf.id
    """

    aggregate_id: UUID = None  # bookshelf_id
    library_id: UUID = None
    name: str = None
    type: str = None  # "normal" or "basement"
    occurred_at: datetime = None

    def __post_init__(self) -> None:
        """Set occurred_at if not provided"""
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))


@dataclass
class BookshelfRenamed(DomainEvent):
    """
    Event: Bookshelf Renamed

    Emitted when: Bookshelf.rename(new_name) called
    Aggregrate ID: bookshelf.id
    """

    aggregate_id: UUID = None  # bookshelf_id
    library_id: UUID = None
    old_name: str = None
    new_name: str = None
    occurred_at: datetime = None

    def __post_init__(self) -> None:
        """Set occurred_at if not provided"""
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))


@dataclass
class BookshelfStatusChanged(DomainEvent):
    """
    Event: Bookshelf Status Changed

    Emitted when: Bookshelf.change_status(new_status) called
    Aggregrate ID: bookshelf.id
    Status transitions: ACTIVE → ARCHIVED → DELETED
    """

    aggregate_id: UUID = None  # bookshelf_id
    library_id: UUID = None
    old_status: str = None  # "active", "archived", or "deleted"
    new_status: str = None  # "active", "archived", or "deleted"
    occurred_at: datetime = None

    def __post_init__(self) -> None:
        """Set occurred_at if not provided"""
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))


@dataclass
class BookshelfDeleted(DomainEvent):
    """
    Event: Bookshelf Deleted

    Emitted when: Bookshelf.mark_deleted() called
    Aggregrate ID: bookshelf.id

    Note: Basement bookshelf cannot be deleted
    """

    aggregate_id: UUID = None  # bookshelf_id
    library_id: UUID = None
    name: str = None
    occurred_at: datetime = None

    def __post_init__(self) -> None:
        """Set occurred_at if not provided"""
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))


# ============================================================================
# Event Registry
# ============================================================================

BOOKSHELF_EVENTS = [
    BookshelfCreated,
    BookshelfRenamed,
    BookshelfStatusChanged,
    BookshelfDeleted,
]
