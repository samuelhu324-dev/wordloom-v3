"""Media Models - SQLAlchemy ORM models

Mapping Strategy (ADR-026: Media Models & Trash Lifecycle):
===========================================================
- Primary Key: id (UUID)
- Business Keys: storage_key (Unique)
- Soft Delete: state (ACTIVE | TRASH) + trash_at timestamp
- Purge: deleted_at (hard delete marker after 30 days)
- Metadata: filename, mime_type, dimensions, duration
- Association: media can link to Books/Bookshelves/Blocks

Tables:
  - media: Main media file definitions with lifecycle tracking
  - media_associations: N:N relationship with Books/Bookshelves/Blocks

Invariants Enforced:
✅ POLICY-010: state (ACTIVE|TRASH) with trash_at tracking
✅ POLICY-010: 30-day retention before hard delete (via application logic)
✅ Media metadata extracted after upload (width/height for images, duration for videos)
✅ storage_key uniqueness (maps to actual file location)

Round-Trip Validation:
Use to_dict() for ORM → dict conversion
Use from_dict() for dict → ORM conversion
"""

from datetime import datetime, timezone
from uuid import uuid4, UUID
from enum import Enum as PyEnum
import datetime as dt

from sqlalchemy import (
    Column, String, DateTime, Text, Integer, ForeignKey,
    UniqueConstraint, Index, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from .base import Base


# ============================================================================
# Enums
# ============================================================================

class MediaType(PyEnum):
    """Type of media"""
    IMAGE = "image"
    VIDEO = "video"


class MediaMimeType(PyEnum):
    """Supported MIME types"""
    # Images
    JPEG = "image/jpeg"
    PNG = "image/png"
    WEBP = "image/webp"
    GIF = "image/gif"

    # Videos
    MP4 = "video/mp4"
    WEBM = "video/webm"
    OGG = "video/ogg"


class MediaState(PyEnum):
    """Current state of media"""
    ACTIVE = "ACTIVE"
    TRASH = "TRASH"


class EntityTypeForMedia(PyEnum):
    """Entity types that can reference media"""
    BOOKSHELF = "bookshelf"
    BOOK = "book"
    BLOCK = "block"


# ============================================================================
# ORM Models
# ============================================================================

class MediaModel(Base):
    """Media ORM Model

    Represents a Media (Image/Video) file in the system.

    Key Features:
    - Centralized media storage with soft delete to trash
    - 30-day retention in trash before hard delete (POLICY-010)
    - Metadata extraction for images (dimensions) and videos (duration)
    - Storage key denormalization for direct file access
    - Relationships managed through MediaAssociation (not direct foreign keys)

    Database Constraints:
    - PK: id (UUID, auto-generated)
    - UNIQUE: storage_key (maps to actual file location)
    - Soft Delete: state (ACTIVE|TRASH) + trash_at timestamp
    - Hard Delete: deleted_at (only set after 30 days in trash)

    Query Patterns:
    - All active media: WHERE state = 'active' AND deleted_at IS NULL
    - All trash media: WHERE state = 'trash' AND deleted_at IS NULL
    - Media eligible for purge: WHERE state = 'trash' AND trash_at <= (NOW - 30 days)
    - Search by filename: WHERE filename LIKE ? AND state = 'active'
    - Find media by entity: JOIN media_associations WHERE entity_type=? AND entity_id=?
    """
    __tablename__ = "media"

    # Primary key
    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # File information
    filename = Column(
        String(255),
        nullable=False,
        index=True
    )

    storage_key = Column(
        String(512),
        nullable=False,
        unique=True,
        index=True
    )

    user_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True
    )

    media_type = Column(
        String(50),
        nullable=False,
        index=True
    )

    mime_type = Column(
        String(100),
        nullable=False
    )

    file_size = Column(
        Integer,
        nullable=False
    )

    # Image metadata
    width = Column(
        Integer,
        nullable=True
    )

    height = Column(
        Integer,
        nullable=True
    )

    # Video metadata
    duration_ms = Column(
        Integer,
        nullable=True
    )

    # State management (POLICY-010)
    state = Column(
        String(20),
        nullable=False,
        default=MediaState.ACTIVE.value,
        index=True
    )

    trash_at = Column(
        DateTime,
        nullable=True,
        index=True
    )

    deleted_at = Column(
        DateTime,
        nullable=True,
        index=True
    )

    # Metadata
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    media_associations = relationship(
        "MediaAssociationModel",
        cascade="all, delete-orphan",
        back_populates="media",
        foreign_keys="MediaAssociationModel.media_id"
    )

    # Constraints
    __table_args__ = (
        Index(
            "ix_media_user_id",
            "user_id"
        ),
        Index(
            "ix_media_state",
            "state"
        ),
        Index(
            "ix_media_trash_at",
            "trash_at"
        ),
        Index(
            "ix_media_created_at",
            "created_at"
        ),
    )

    def to_dict(self) -> dict:
        """Convert ORM model to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "filename": self.filename,
            "storage_key": self.storage_key,
            "media_type": self.media_type,  # Already a string from DB
            "mime_type": self.mime_type,  # Already a string from DB
            "file_size": self.file_size,
            "width": self.width,
            "height": self.height,
            "duration_ms": self.duration_ms,
            "state": self.state,  # Already a string from DB
            "trash_at": self.trash_at.isoformat() if self.trash_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict) -> "MediaModel":
        """Create ORM model from dictionary"""
        return MediaModel(
            id=UUID(data["id"]) if "id" in data else uuid4(),
            filename=data["filename"],
            storage_key=data["storage_key"],
            user_id=UUID(data["user_id"]) if data.get("user_id") else None,
            media_type=MediaType[data["media_type"].upper()],
            mime_type=MediaMimeType[data["mime_type"].replace("/", "_").upper()],
            file_size=data["file_size"],
            width=data.get("width"),
            height=data.get("height"),
            duration_ms=data.get("duration_ms"),
            state=MediaState[data.get("state", "active").upper()],
            trash_at=datetime.fromisoformat(data["trash_at"]) if data.get("trash_at") else None,
            deleted_at=datetime.fromisoformat(data["deleted_at"]) if data.get("deleted_at") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(timezone.utc),
        )


class MediaAssociationModel(Base):
    """MediaAssociation ORM Model

    Represents the N:N relationship between Media and entities (Books/Bookshelves/Blocks).

    Key Features:
    - Links a Media file to a specific entity (Book/Bookshelf/Block)
    - entity_type determines the target entity class
    - Denormalized model for query performance (avoid separate tables per type)
    - Hard delete (not soft delete) - when entity is deleted, association is cleaned up

    Database Constraints:
    - PK: id (UUID, auto-generated)
    - FK: media_id (references media.id, cascade delete)
    - UNIQUE: (media_id, entity_type, entity_id) - prevent duplicate associations
    - Indexes on (entity_type, entity_id) for fast reverse lookup

    Query Patterns:
    - Get all media for a book: SELECT * FROM media_associations WHERE entity_type='book' AND entity_id=?
    - Get all entities with a media: SELECT * FROM media_associations WHERE media_id=?
    - Check if association exists: SELECT COUNT(*) FROM media_associations WHERE media_id=? AND entity_type=? AND entity_id=?
    """
    __tablename__ = "media_associations"

    # Primary key
    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Foreign keys
    media_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("media.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Entity reference (denormalized)
    entity_type = Column(
        SQLEnum(EntityTypeForMedia, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )

    entity_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=False,
        index=True
    )

    # Metadata
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    media = relationship(
        "MediaModel",
        back_populates="media_associations",
        foreign_keys=[media_id]
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "media_id", "entity_type", "entity_id",
            name="uq_media_associations_media_entity"
        ),
        Index(
            "ix_media_associations_entity",
            "entity_type", "entity_id"
        ),
    )

    def to_dict(self) -> dict:
        """Convert ORM model to dictionary"""
        return {
            "id": str(self.id),
            "media_id": str(self.media_id),
            "entity_type": self.entity_type.value,
            "entity_id": str(self.entity_id),
            "created_at": self.created_at.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict) -> "MediaAssociationModel":
        """Create ORM model from dictionary"""
        return MediaAssociationModel(
            id=UUID(data["id"]) if "id" in data else uuid4(),
            media_id=UUID(data["media_id"]),
            entity_type=EntityTypeForMedia[data["entity_type"].upper()],
            entity_id=UUID(data["entity_id"]),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(timezone.utc),
        )
