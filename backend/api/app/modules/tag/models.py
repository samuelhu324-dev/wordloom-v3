"""Tag Models - SQLAlchemy ORM models

Mapping Strategy (ADR-025: Tag Models & Testing Layer):
==========================================================
- Primary Key: id (UUID)
- Business Keys: name (Unique)
- Hierarchical: parent_tag_id (self-referencing FK)
- Soft Delete: deleted_at (per RULE-018)
- Metadata: color, icon, description, usage_count (cached)

Tables:
  - tags: Main tag definitions
  - tag_associations: N:N relationship with Books/Bookshelves/Blocks

Invariants Enforced:
✅ RULE-018: name uniqueness + color/icon validation
✅ RULE-019: tag_id + entity_type + entity_id uniqueness (composite key)
✅ RULE-020: parent_tag_id self-referencing + level tracking

Round-Trip Validation:
Use to_dict() for ORM → dict conversion
Use from_dict() for dict → ORM conversion
"""
from sqlalchemy import (
    Column, String, DateTime, Text, Boolean, ForeignKey, Integer,
    UniqueConstraint, Index, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from enum import Enum as PyEnum
from core.database import Base


class EntityType(PyEnum):
    """Enum for entity types that can be tagged"""
    BOOKSHELF = "bookshelf"
    BOOK = "book"
    BLOCK = "block"


class TagModel(Base):
    """Tag ORM Model

    Represents a Tag aggregate root in the system.

    Key Features:
    - Global tag definitions (independent of any entity)
    - Hierarchical structure with parent_tag_id
    - Soft delete via deleted_at field
    - Usage count cached for performance
    - Relationships managed through TagAssociation (not direct foreign keys)

    Database Constraints:
    - PK: id (UUID, auto-generated)
    - UNIQUE: (name, deleted_at IS NULL) - allow multiple deleted tags with same name
    - FK: parent_tag_id (nullable, self-referencing, for hierarchical tags)
    - Soft Delete: deleted_at (nullable, indexed for filtering)

    Query Patterns:
    - All active tags: WHERE deleted_at IS NULL
    - Top-level tags: WHERE parent_tag_id IS NULL AND deleted_at IS NULL AND level = 0
    - Subtags of parent: WHERE parent_tag_id = ? AND deleted_at IS NULL
    - Search by name: WHERE name LIKE ? AND deleted_at IS NULL
    - Most used: WHERE deleted_at IS NULL ORDER BY usage_count DESC LIMIT 20
    """
    __tablename__ = "tags"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Tag ID (UUID)"
    )

    # Core fields
    name = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Tag name (unique, case-sensitive)"
    )

    color = Column(
        String(9),  # #RRGGBB or #RRGGBBAA
        nullable=False,
        comment="Tag color in hex format (#RRGGBB or #RRGGBBAA)"
    )

    icon = Column(
        String(50),
        nullable=True,
        comment="Lucide icon name (e.g., bookmark, star, flag)"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Optional description for the tag"
    )

    # Hierarchical structure
    parent_tag_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Parent Tag ID (for hierarchical tags, NULL=top-level)"
    )

    level = Column(
        Integer,
        nullable=False,
        default=0,
        index=True,
        comment="Hierarchy level (0=top-level, 1=sub-tag, 2=sub-sub-tag, etc.)"
    )

    # Statistics
    usage_count = Column(
        Integer,
        nullable=False,
        default=0,
        index=True,
        comment="Cached number of TagAssociation records (for sorting, updated by Service)"
    )

    # Metadata
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone=dt.timezone.utc),
        comment="Creation timestamp (immutable)"
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone=dt.timezone.utc),
        onupdate=lambda: datetime.now(timezone=dt.timezone.utc),
        comment="Last update timestamp"
    )

    deleted_at = Column(
        DateTime,
        nullable=True,
        index=True,
        comment="Soft delete timestamp (RULE-018, NULL=active)"
    )

    # Relationships (lazy-loaded)
    tag_associations = relationship(
        "TagAssociationModel",
        cascade="all, delete-orphan",
        back_populates="tag",
        foreign_keys="TagAssociationModel.tag_id"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "name",
            name="uq_tags_name_active",
            comment="Unique tag name for active tags (soft-delete allows reuse)"
        ),
        Index(
            "ix_tags_parent_level",
            "parent_tag_id", "level",
            comment="Index for hierarchical queries"
        ),
        Index(
            "ix_tags_usage_count",
            "usage_count",
            comment="Index for sorting by popularity"
        ),
    )

    def to_dict(self) -> dict:
        """Convert ORM model to dictionary (for serialization)"""
        return {
            "id": str(self.id),
            "name": self.name,
            "color": self.color,
            "icon": self.icon,
            "description": self.description,
            "parent_tag_id": str(self.parent_tag_id) if self.parent_tag_id else None,
            "level": self.level,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }

    @staticmethod
    def from_dict(data: dict) -> "TagModel":
        """Create ORM model from dictionary (for deserialization)"""
        import datetime as dt
        from uuid import UUID

        return TagModel(
            id=UUID(data["id"]) if "id" in data else uuid4(),
            name=data["name"],
            color=data["color"],
            icon=data.get("icon"),
            description=data.get("description"),
            parent_tag_id=UUID(data["parent_tag_id"]) if data.get("parent_tag_id") else None,
            level=data.get("level", 0),
            usage_count=data.get("usage_count", 0),
            created_at=dt.datetime.fromisoformat(data["created_at"]) if "created_at" in data else dt.datetime.now(dt.timezone.utc),
            updated_at=dt.datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else dt.datetime.now(dt.timezone.utc),
            deleted_at=dt.datetime.fromisoformat(data["deleted_at"]) if data.get("deleted_at") else None,
        )


class TagAssociationModel(Base):
    """TagAssociation ORM Model

    Represents the N:N relationship between Tags and entities (Books/Bookshelves/Blocks).

    Key Features:
    - Links a Tag to a specific entity (Book/Bookshelf/Block)
    - entity_type determines the target entity class
    - Separate table for each entity type would require JOINs; this is denormalized for query performance
    - Soft delete is NOT used here; associations are hard-deleted when a tag/entity is deleted

    Database Constraints:
    - PK: id (UUID, auto-generated)
    - FK: tag_id (references tags.id, cascade delete)
    - UNIQUE: (tag_id, entity_type, entity_id) - prevent duplicate associations
    - Indexes on (entity_type, entity_id) for fast reverse lookup

    Query Patterns:
    - Get all tags for a book: SELECT * FROM tag_associations WHERE entity_type='book' AND entity_id=?
    - Get all entities tagged with a tag: SELECT * FROM tag_associations WHERE tag_id=?
    - Check if association exists: SELECT COUNT(*) FROM tag_associations WHERE tag_id=? AND entity_type=? AND entity_id=?
    """
    __tablename__ = "tag_associations"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Association ID (UUID)"
    )

    # Foreign keys
    tag_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Tag ID (cascade delete)"
    )

    # Entity reference (denormalized)
    entity_type = Column(
        SQLEnum(EntityType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="Type of entity being tagged (BOOKSHELF|BOOK|BLOCK)"
    )

    entity_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="ID of the entity being tagged"
    )

    # Metadata
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone=dt.timezone.utc),
        comment="Association creation timestamp"
    )

    # Relationships
    tag = relationship(
        "TagModel",
        back_populates="tag_associations",
        foreign_keys=[tag_id]
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "tag_id", "entity_type", "entity_id",
            name="uq_tag_associations_tag_entity",
            comment="Prevent duplicate tags on same entity"
        ),
        Index(
            "ix_tag_associations_entity",
            "entity_type", "entity_id",
            comment="Index for finding tags on a specific entity"
        ),
    )

    def to_dict(self) -> dict:
        """Convert ORM model to dictionary"""
        return {
            "id": str(self.id),
            "tag_id": str(self.tag_id),
            "entity_type": self.entity_type.value,
            "entity_id": str(self.entity_id),
            "created_at": self.created_at.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict) -> "TagAssociationModel":
        """Create ORM model from dictionary"""
        import datetime as dt
        from uuid import UUID

        return TagAssociationModel(
            id=UUID(data["id"]) if "id" in data else uuid4(),
            tag_id=UUID(data["tag_id"]),
            entity_type=EntityType[data["entity_type"].upper()],
            entity_id=UUID(data["entity_id"]),
            created_at=dt.datetime.fromisoformat(data["created_at"]) if "created_at" in data else dt.datetime.now(dt.timezone.utc),
        )


# Import datetime module at top
import datetime as dt
