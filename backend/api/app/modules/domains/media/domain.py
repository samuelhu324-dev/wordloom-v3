"""
Media Domain - Unified media resource management

Purpose:
- Independent Domain managing all file resources
- Supports multiple entity types: BOOKSHELF_COVER, BOOK_COVER, BLOCK_IMAGE, CHRONICLE_ATTACHMENT
- Tracks: file_url, file_size, mime_type, file_hash, dimensions (for images)
- Soft delete support (deleted_at)

Architecture:
- Pure domain layer with zero infrastructure dependencies
- Entity-based (not aggregate) - Media serves other aggregates
- Storage path logic moved to Infra layer
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum

from shared.base import AggregateRoot, DomainEvent, ValueObject


# ============================================================================
# Enums
# ============================================================================

class MediaEntityType(str, Enum):
    """Type of entity this media belongs to"""
    BOOKSHELF_COVER = "bookshelf_cover"
    BOOK_COVER = "book_cover"
    BLOCK_IMAGE = "block_image"
    CHRONICLE_ATTACHMENT = "chronicle_attachment"


# ============================================================================
# Domain Events
# ============================================================================

@dataclass
class MediaUploaded(DomainEvent):
    """Emitted when media is uploaded"""
    media_id: UUID
    entity_type: MediaEntityType
    entity_id: UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.media_id


@dataclass
class MediaDeleted(DomainEvent):
    """Emitted when media is deleted"""
    media_id: UUID
    entity_type: MediaEntityType
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.media_id


# ============================================================================
# Value Objects
# ============================================================================

@dataclass(frozen=True)
class MediaMetadata(ValueObject):
    """Value object for media metadata"""
    file_size: int
    mime_type: str
    file_hash: str
    width: Optional[int] = None
    height: Optional[int] = None

    def __post_init__(self):
        if self.file_size < 0:
            raise ValueError("File size cannot be negative")
        if not self.mime_type:
            raise ValueError("MIME type is required")


# ============================================================================
# Aggregate Root
# ============================================================================

class Media(AggregateRoot):
    """
    Media Aggregate Root

    Invariants:
    - Media must have entity_type and entity_id
    - File hash must be unique per entity (no duplicate files)
    - File size, MIME type are required
    - Width/height optional (for images)
    - Soft delete support (deleted_at)

    Business Rules:
    - Media is uploaded with metadata
    - Media can be deleted (soft delete)
    - Media can be associated with: Bookshelf covers, Book covers, Block images, Chronicle attachments
    """

    def __init__(
        self,
        media_id: UUID,
        entity_type: MediaEntityType,
        entity_id: UUID,
        file_url: str,
        file_size: int,
        mime_type: str,
        file_hash: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        created_at: datetime = None,
        updated_at: datetime = None,
        deleted_at: Optional[datetime] = None,
    ):
        self.id = media_id
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.file_url = file_url
        self.file_size = file_size
        self.mime_type = mime_type
        self.file_hash = file_hash
        self.width = width
        self.height = height
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.deleted_at = deleted_at
        self.events = []

    # ========================================================================
    # Factory Methods
    # ========================================================================

    @classmethod
    def create(
        cls,
        entity_type: MediaEntityType,
        entity_id: UUID,
        file_url: str,
        file_size: int,
        mime_type: str,
        file_hash: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> Media:
        """
        Factory method to create new Media

        Args:
            entity_type: Type of entity this media belongs to
            entity_id: ID of the entity
            file_url: URL to access the file
            file_size: File size in bytes
            mime_type: MIME type of file
            file_hash: SHA256 hash of file
            width: Image width (optional)
            height: Image height (optional)

        Returns:
            New Media instance with MediaUploaded event
        """
        media_id = uuid4()
        now = datetime.utcnow()

        media = cls(
            media_id=media_id,
            entity_type=entity_type,
            entity_id=entity_id,
            file_url=file_url,
            file_size=file_size,
            mime_type=mime_type,
            file_hash=file_hash,
            width=width,
            height=height,
            created_at=now,
            updated_at=now,
        )

        media.emit(
            MediaUploaded(
                media_id=media_id,
                entity_type=entity_type,
                entity_id=entity_id,
                occurred_at=now,
            )
        )

        return media

    # ========================================================================
    # Business Methods
    # ========================================================================

    def mark_deleted(self) -> None:
        """Soft delete media"""
        if self.deleted_at is not None:
            return

        now = datetime.utcnow()
        self.deleted_at = now
        self.updated_at = now

        self.emit(
            MediaDeleted(
                media_id=self.id,
                entity_type=self.entity_type,
                occurred_at=now,
            )
        )

    # ========================================================================
    # Query Methods
    # ========================================================================

    def is_deleted(self) -> bool:
        """Check if media is soft deleted"""
        return self.deleted_at is not None

    def is_image(self) -> bool:
        """Check if media is an image"""
        return self.mime_type.startswith("image/")

    def __repr__(self) -> str:
        return f"<Media(id={self.id}, entity_type={self.entity_type}, entity_id={self.entity_id})>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Media):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
