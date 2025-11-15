"""Tag domain events - Pure event definitions

RULE-018: Tag Creation & Management
RULE-019: Tag-Entity Association

Emitted by Tag AggregateRoot on state changes.
Consumed by event handlers for side effects (usage count tracking, etc.)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import UUID

from shared.base import DomainEvent
from .enums import EntityType


@dataclass
class TagCreated(DomainEvent):
    """Emitted when a new Tag is created (top-level or subtag)."""
    tag_id: UUID
    name: str
    color: str
    is_toplevel: bool
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.tag_id


@dataclass
class TagRenamed(DomainEvent):
    """Emitted when Tag name is changed."""
    tag_id: UUID
    old_name: str
    new_name: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.tag_id


@dataclass
class TagColorChanged(DomainEvent):
    """Emitted when Tag color is changed."""
    tag_id: UUID
    old_color: str
    new_color: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.tag_id


@dataclass
class TagDeleted(DomainEvent):
    """Emitted when Tag is soft-deleted (associations preserved)."""
    tag_id: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.tag_id


@dataclass
class TagAssociatedWithEntity(DomainEvent):
    """Emitted when a Tag is associated with an entity (Book/Bookshelf/Block)."""
    tag_id: UUID
    entity_type: EntityType
    entity_id: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.tag_id


@dataclass
class TagDisassociatedFromEntity(DomainEvent):
    """Emitted when a Tag is removed from an entity."""
    tag_id: UUID
    entity_type: EntityType
    entity_id: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.tag_id
