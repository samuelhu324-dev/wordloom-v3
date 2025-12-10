"""
Book Domain Events

Events emitted by the Book aggregate root to communicate state changes
to other bounded contexts and infrastructure layers.

Events follow DDD patterns:
- Immutable domain objects
- Include all relevant context (aggregate_id, entity IDs, state changes)
- Published through event bus to Infrastructure layer
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID
from enum import Enum

from api.app.shared.base import DomainEvent


# ============================================================================
# Enums (needed by events)
# ============================================================================

class BookStatus(str, Enum):
    """Status of a Book"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class BookMaturity(str, Enum):
    """Maturity lifecycle for a Book aggregate"""
    SEED = "seed"
    GROWING = "growing"
    STABLE = "stable"
    LEGACY = "legacy"


# ============================================================================
# Domain Events
# ============================================================================

@dataclass
class BookCreated(DomainEvent):
    """Emitted when a new Book is created"""
    book_id: UUID
    bookshelf_id: UUID
    title: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BookRenamed(DomainEvent):
    """Emitted when Book title is changed"""
    book_id: UUID
    old_title: str
    new_title: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BookStatusChanged(DomainEvent):
    """Emitted when Book status changes"""
    book_id: UUID
    old_status: BookStatus
    new_status: BookStatus
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BookMaturityChanged(DomainEvent):
    """Emitted when Book maturity lifecycle changes"""
    book_id: UUID
    old_maturity: BookMaturity
    new_maturity: BookMaturity
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BookDeleted(DomainEvent):
    """Emitted when Book is deleted"""
    book_id: UUID
    bookshelf_id: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BlocksUpdated(DomainEvent):
    """Emitted when Book's Blocks are updated"""
    book_id: UUID
    block_count: int
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BookMovedToBookshelf(DomainEvent):
    """Emitted when Book is moved to a different Bookshelf (RULE-011)"""
    book_id: UUID
    old_bookshelf_id: UUID
    new_bookshelf_id: UUID
    moved_at: datetime
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BookMovedToBasement(DomainEvent):
    """Emitted when Book is moved to Basement (soft delete, RULE-012)"""
    book_id: UUID
    old_bookshelf_id: UUID
    basement_bookshelf_id: UUID
    deleted_at: datetime
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BookRestoredFromBasement(DomainEvent):
    """Emitted when Book is restored from Basement (RULE-013)"""
    book_id: UUID
    basement_bookshelf_id: UUID
    restored_to_bookshelf_id: UUID
    restored_at: datetime
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id
