"""Tag AggregateRoot and ValueObjects - Core domain logic

RULE-018: Tag Creation & Management
RULE-019: Tag-Entity Association
RULE-020: Tag Hierarchy

Pure domain layer with zero infrastructure dependencies.
All domain logic and invariants implemented here.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from api.app.shared.base import AggregateRoot, ValueObject, DomainEvent
from .enums import EntityType
from .events import (
    TagCreated, TagRenamed, TagColorChanged, TagDeleted,
    TagAssociatedWithEntity, TagDisassociatedFromEntity
)


# ============================================================================
# Value Objects
# ============================================================================

@dataclass(frozen=True)
class TagAssociation(ValueObject):
    """
    Immutable link between a Tag and an entity (Book/Bookshelf/Block).

    Invariants:
    - tag_id and entity_id must be valid UUIDs
    - entity_type must be one of: BOOKSHELF, BOOK, BLOCK
    - (tag_id, entity_type, entity_id) is a unique composite key
    """
    tag_id: UUID
    entity_type: EntityType
    entity_id: UUID
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not self.tag_id:
            raise ValueError("tag_id cannot be empty")
        if not self.entity_id:
            raise ValueError("entity_id cannot be empty")
        if self.entity_type not in EntityType:
            raise ValueError(f"Invalid entity_type: {self.entity_type}")

    def __eq__(self, other: object) -> bool:
        """Two associations are equal if they link the same tag to the same entity"""
        if not isinstance(other, TagAssociation):
            return NotImplemented
        return (
            self.tag_id == other.tag_id
            and self.entity_type == other.entity_type
            and self.entity_id == other.entity_id
        )

    def __hash__(self) -> int:
        return hash((self.tag_id, self.entity_type.value, self.entity_id))


# ============================================================================
# Aggregate Root
# ============================================================================

@dataclass
class Tag(AggregateRoot):
    """
    Tag Aggregate Root - Global tag definition.

    Invariants (RULE-018: Tag Creation & Management):
    - name: non-empty string, max 50 characters, unique
    - color: valid hex color code (e.g., #FF5733)
    - icon: optional lucide icon name (e.g., bookmark, star)
    - description: optional text
    - parent_tag_id: optional UUID (for hierarchical tags, RULE-020)
    - level: 0 for top-level, 1+ for subtags (automatically calculated)
    - usage_count: cached count of associations (updated by Service layer)
    - deleted_at: soft delete marker (RULE-018)
    - created_at: immutable timestamp
    - updated_at: updated on any change

    Rules (per DDD_RULES.yaml):
    - NO automatic sync between tag levels (independent associations)
    - Tags can be searched by keyword (case-insensitive partial match)
    - Usage count is cached and updated asynchronously (for performance)
    - Soft delete preserves associations (for audit trail)
    """

    id: UUID
    name: str
    color: str
    icon: Optional[str] = None
    description: Optional[str] = None

    # Hierarchical structure (RULE-020)
    parent_tag_id: Optional[UUID] = None
    level: int = 0  # 0=toplevel, 1=subtag, 2=sub-subtag, etc.

    # Statistics
    usage_count: int = 0  # Cached: number of TagAssociation records

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

    # Event tracking
    _events: List[DomainEvent] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """Validate invariants on creation"""
        self._validate_name()
        self._validate_color()

    def _validate_name(self) -> None:
        """Name must be non-empty and <= 50 characters"""
        if not self.name or not self.name.strip():
            raise ValueError("Tag name cannot be empty")
        if len(self.name) > 50:
            raise ValueError("Tag name must be <= 50 characters")

    def _validate_color(self) -> None:
        """Color must be valid hex code"""
        if not self.color or not self.color.startswith("#"):
            raise ValueError("Color must be hex code (e.g., #FF5733)")
        if len(self.color) not in [7, 9]:  # #RRGGBB or #RRGGBBAA
            raise ValueError("Color must be 6 or 8 digit hex code")

    # ========================================================================
    # Factory Methods
    # ========================================================================

    @staticmethod
    def create_toplevel(
        name: str,
        color: str,
        icon: Optional[str] = None,
        description: Optional[str] = None
    ) -> Tag:
        """Factory: Create a top-level Tag"""
        tag = Tag(
            id=uuid4(),
            name=name,
            color=color,
            icon=icon,
            description=description,
            level=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        tag._events.append(TagCreated(
            tag_id=tag.id,
            name=name,
            color=color,
            is_toplevel=True
        ))
        return tag

    @staticmethod
    def create_subtag(
        parent_tag_id: UUID,
        name: str,
        color: str,
        icon: Optional[str] = None,
        parent_level: int = 0
    ) -> Tag:
        """Factory: Create a hierarchical sub-Tag"""
        tag = Tag(
            id=uuid4(),
            name=name,
            color=color,
            icon=icon,
            parent_tag_id=parent_tag_id,
            level=parent_level + 1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        tag._events.append(TagCreated(
            tag_id=tag.id,
            name=name,
            color=color,
            is_toplevel=False
        ))
        return tag

    # ========================================================================
    # Commands (State Modification)
    # ========================================================================

    def rename(self, new_name: str) -> None:
        """Change tag name"""
        if new_name == self.name:
            return  # No change

        self._validate_name_value(new_name)
        old_name = self.name
        object.__setattr__(self, "name", new_name)
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

        self._events.append(TagRenamed(
            tag_id=self.id,
            old_name=old_name,
            new_name=new_name
        ))

    def update_color(self, new_color: str) -> None:
        """Change tag color"""
        if new_color == self.color:
            return  # No change

        self._validate_color_value(new_color)
        old_color = self.color
        object.__setattr__(self, "color", new_color)
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

        self._events.append(TagColorChanged(
            tag_id=self.id,
            old_color=old_color,
            new_color=new_color
        ))

    def update_icon(self, new_icon: Optional[str]) -> None:
        """Update icon"""
        if new_icon == self.icon:
            return
        object.__setattr__(self, "icon", new_icon)
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

    def update_description(self, new_description: Optional[str]) -> None:
        """Update description"""
        if new_description == self.description:
            return
        object.__setattr__(self, "description", new_description)
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

    def soft_delete(self) -> None:
        """Soft delete: mark as deleted but preserve associations"""
        if self.deleted_at:
            raise ValueError(f"Tag {self.id} already deleted at {self.deleted_at}")

        object.__setattr__(self, "deleted_at", datetime.now(timezone.utc))
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

        self._events.append(TagDeleted(tag_id=self.id))

    def restore(self) -> None:
        """Restore from soft delete"""
        if not self.deleted_at:
            raise ValueError(f"Tag {self.id} is not deleted")

        object.__setattr__(self, "deleted_at", None)
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

    def increment_usage(self, by: int = 1) -> None:
        """Increment usage count (called when a new association is created)"""
        object.__setattr__(self, "usage_count", max(0, self.usage_count + by))
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

    def decrement_usage(self, by: int = 1) -> None:
        """Decrement usage count (called when an association is removed)"""
        object.__setattr__(self, "usage_count", max(0, self.usage_count - by))
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

    def associate_with_entity(
        self,
        entity_type: EntityType,
        entity_id: UUID
    ) -> TagAssociation:
        """Create an association between this tag and an entity"""
        association = TagAssociation(
            tag_id=self.id,
            entity_type=entity_type,
            entity_id=entity_id
        )

        self._events.append(TagAssociatedWithEntity(
            tag_id=self.id,
            entity_type=entity_type,
            entity_id=entity_id
        ))

        return association

    def disassociate_from_entity(
        self,
        entity_type: EntityType,
        entity_id: UUID
    ) -> None:
        """Remove association between this tag and an entity"""
        self._events.append(TagDisassociatedFromEntity(
            tag_id=self.id,
            entity_type=entity_type,
            entity_id=entity_id
        ))

    # ========================================================================
    # Queries (Read-only State Inspection)
    # ========================================================================

    def is_deleted(self) -> bool:
        """Check if tag is soft-deleted"""
        return self.deleted_at is not None

    def is_toplevel(self) -> bool:
        """Check if this is a top-level tag"""
        return self.parent_tag_id is None and self.level == 0

    # ========================================================================
    # Private Validators
    # ========================================================================

    def _validate_name_value(self, name: str) -> None:
        """Helper to validate name value"""
        if not name or not name.strip():
            raise ValueError("Tag name cannot be empty")
        if len(name) > 50:
            raise ValueError("Tag name must be <= 50 characters")

    def _validate_color_value(self, color: str) -> None:
        """Helper to validate color value"""
        if not color or not color.startswith("#"):
            raise ValueError("Color must be hex code (e.g., #FF5733)")
        if len(color) not in [7, 9]:
            raise ValueError("Color must be 6 or 8 digit hex code")

    # ========================================================================
    # Event Tracking (inherited from AggregateRoot)
    # ========================================================================

    @property
    def events(self) -> List[DomainEvent]:
        """Get all uncommitted domain events"""
        return self._events.copy()

    def clear_events(self) -> None:
        """Clear all uncommitted events (called after persistence)"""
        self._events.clear()
