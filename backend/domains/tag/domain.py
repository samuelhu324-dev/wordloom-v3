"""
Tag Domain - Global tagging system

Purpose:
- Global Tag system (not tied to specific entities)
- Manages N:M relationship to Books via BookTag junction table
- Tracks tag metadata: name, color, icon, description, usage count

Architecture:
- Pure domain layer with zero infrastructure dependencies
- Tags are global resources (shared across all Books)
- Emits DomainEvents on state changes
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from shared.base import AggregateRoot, DomainEvent, ValueObject


# ============================================================================
# Domain Events
# ============================================================================

@dataclass
class TagCreated(DomainEvent):
    """Emitted when a new Tag is created"""
    tag_id: UUID
    name: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.tag_id


@dataclass
class TagRenamed(DomainEvent):
    """Emitted when Tag name is changed"""
    tag_id: UUID
    old_name: str
    new_name: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.tag_id


@dataclass
class TagUpdated(DomainEvent):
    """Emitted when Tag metadata is updated"""
    tag_id: UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.tag_id


@dataclass
class TagDeleted(DomainEvent):
    """Emitted when Tag is deleted"""
    tag_id: UUID
    name: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.tag_id


# ============================================================================
# Value Objects
# ============================================================================

@dataclass(frozen=True)
class TagName(ValueObject):
    """Value object for unique tag name"""
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Tag name cannot be empty")
        if len(self.value) > 100:
            raise ValueError("Tag name cannot exceed 100 characters")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TagColor(ValueObject):
    """Value object for tag color (hex)"""
    value: str = "#808080"  # Default gray

    def __post_init__(self):
        if not self.value.startswith("#") or len(self.value) != 7:
            raise ValueError("Color must be hex format (#RRGGBB)")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TagIcon(ValueObject):
    """Value object for tag icon (Lucide icon name)"""
    value: Optional[str] = None

    def __str__(self) -> str:
        return self.value or ""


# ============================================================================
# Aggregate Root
# ============================================================================

class Tag(AggregateRoot):
    """
    Tag Aggregate Root

    Invariants:
    - Tag name must be unique across all tags
    - Tag name is required, ≤ 100 characters
    - Color must be hex format (#RRGGBB)
    - Icon is optional (Lucide icon name)
    - Count tracks usage but is not part of business logic
    - Tag relationships (N:M to Books) managed via BookTag junction table

    Business Rules:
    - Created with unique name
    - Name can be updated (renamed)
    - Metadata (color, icon, description) can be updated
    - Usage count is tracked but managed by infrastructure
    """

    def __init__(
        self,
        tag_id: UUID,
        name: TagName,
        color: TagColor = None,
        icon: Optional[TagIcon] = None,
        description: Optional[str] = None,
        count: int = 0,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self.id = tag_id
        self.name = name
        self.color = color or TagColor()
        self.icon = icon or TagIcon()
        self.description = description or ""
        self.count = count  # Cache of usage count
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.events: List[DomainEvent] = []

    # ========================================================================
    # Factory Methods
    # ========================================================================

    @classmethod
    def create(
        cls,
        name: str,
        color: Optional[str] = None,
        icon: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Tag:
        """
        Factory method to create a new Tag

        Args:
            name: Unique tag name
            color: Hex color (#RRGGBB), defaults to #808080
            icon: Lucide icon name
            description: Optional description

        Returns:
            New Tag instance with TagCreated event

        Raises:
            ValueError: If name, color, or icon invalid
        """
        tag_id = uuid4()
        tag_name = TagName(value=name)
        tag_color = TagColor(value=color) if color else TagColor()
        tag_icon = TagIcon(value=icon) if icon else TagIcon()
        now = datetime.utcnow()

        tag = cls(
            tag_id=tag_id,
            name=tag_name,
            color=tag_color,
            icon=tag_icon,
            description=description,
            created_at=now,
            updated_at=now,
        )

        tag.emit(
            TagCreated(
                tag_id=tag_id,
                name=name,
                occurred_at=now,
            )
        )

        return tag

    # ========================================================================
    # Business Methods
    # ========================================================================

    def rename(self, new_name: str) -> None:
        """Rename the Tag (must remain unique)"""
        new_tag_name = TagName(value=new_name)

        if self.name.value == new_tag_name.value:
            return

        old_name = self.name.value
        self.name = new_tag_name
        self.updated_at = datetime.utcnow()

        self.emit(
            TagRenamed(
                tag_id=self.id,
                old_name=old_name,
                new_name=new_name,
                occurred_at=self.updated_at,
            )
        )

    def set_color(self, color: str) -> None:
        """Update tag color"""
        new_color = TagColor(value=color)
        self.color = new_color
        self.updated_at = datetime.utcnow()

        self.emit(
            TagUpdated(
                tag_id=self.id,
                occurred_at=self.updated_at,
            )
        )

    def set_icon(self, icon: Optional[str]) -> None:
        """Update tag icon"""
        new_icon = TagIcon(value=icon)
        self.icon = new_icon
        self.updated_at = datetime.utcnow()

        self.emit(
            TagUpdated(
                tag_id=self.id,
                occurred_at=self.updated_at,
            )
        )

    def set_description(self, description: Optional[str]) -> None:
        """Update tag description"""
        self.description = description or ""
        self.updated_at = datetime.utcnow()

        self.emit(
            TagUpdated(
                tag_id=self.id,
                occurred_at=self.updated_at,
            )
        )

    def increment_usage(self) -> None:
        """Increment usage count (called when tag is added to Book)"""
        self.count += 1

    def decrement_usage(self) -> None:
        """Decrement usage count (called when tag is removed from Book)"""
        if self.count > 0:
            self.count -= 1

    def mark_deleted(self) -> None:
        """Mark Tag as deleted"""
        now = datetime.utcnow()
        self.updated_at = now

        self.emit(
            TagDeleted(
                tag_id=self.id,
                name=self.name.value,
                occurred_at=now,
            )
        )

    # ========================================================================
    # Query Methods
    # ========================================================================

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name={self.name.value}, count={self.count})>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Tag):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
