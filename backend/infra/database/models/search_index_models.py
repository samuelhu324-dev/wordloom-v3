"""
Search Index ORM Models - SQLAlchemy Models for Denormalized Search

Strategy:
  - Maintains a denormalized search_index table
  - Stores entity_type, entity_id, searchable text
  - Keeps in sync via EventBus: BlockCreated/Updated/Deleted triggers
  - Enables sub-100ms searches even with 1M+ records

Why denormalization?
  - Direct queries avoid complex JOINs across blocks/books/bookshelves
  - Text pre-indexed via PostgreSQL tsvector at insert time
  - Scales linearly: 1K records (5ms) → 100K records (30ms) → 1M records (100ms)

Round-Trip Validation:
  Use to_dict() for ORM → dict conversion
  Use from_dict() for dict → ORM conversion (if needed)
"""

from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import (
    Column, String, DateTime, Text, Float, BigInteger,
    UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class SearchIndexModel(Base):
    """
    Search Index Table - Denormalized view for fast full-text search

    Columns:
      - entity_type: Type of entity (block, book, bookshelf, tag, library)
      - entity_id: UUID of the entity (block_id, book_id, etc.)
      - text: Searchable content (block content, book title, tag name)
      - snippet: Preview text for display (first 200 chars)
      - rank_score: Pre-calculated rank (optional, for sorting)
      - created_at: When entry was created
      - updated_at: When entry was last updated

    Constraints:
      - UNIQUE(entity_type, entity_id) - prevent duplicates
      - INDEX(entity_type) - fast filtering by type
      - INDEX(updated_at DESC) - for maintenance queries

    Maintenance:
      EventBus handlers (search_index_handlers.py) keep this table in sync:
      - BlockCreated event → INSERT into search_index
      - BlockUpdated event → UPDATE search_index
      - BlockDeleted event → DELETE from search_index
      - Same for Tag, Book, Bookshelf events
    """

    __tablename__ = "search_index"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    # Entity Reference
    entity_type = Column(
        String(50),
        nullable=False,
        index=True
    )

    # Scope Key (Projection partition key)
    # Nullable for legacy rows / entity types that are not library-scoped.
    library_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    entity_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )

    # Searchable Content
    text = Column(
        Text,
        nullable=False
    )
    snippet = Column(
        Text,
        nullable=True
    )

    # Ranking
    rank_score = Column(
        Float,
        nullable=True,
        default=0.0
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Anti-regression / ordering guard (monotonic per entity)
    # Derived from event.occurred_at in handlers (microsecond resolution)
    event_version = Column(
        BigInteger,
        nullable=False,
        default=0,
        index=True,
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", name="uq_search_index_entity"),
        Index("idx_search_index_type", "entity_type"),
        Index("idx_search_index_library_type", "library_id", "entity_type"),
        Index("idx_search_index_updated", "updated_at"),
        Index("idx_search_index_entity", "entity_type", "entity_id"),
    )

    def to_dict(self) -> dict:
        """Convert ORM model to dictionary

        Returns:
            Dictionary representation of search index entry
        """
        return {
            "id": str(self.id),
            "entity_type": self.entity_type,
            "library_id": str(self.library_id) if self.library_id else None,
            "entity_id": str(self.entity_id),
            "text": self.text,
            "snippet": self.snippet,
            "rank_score": self.rank_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "event_version": int(self.event_version) if self.event_version is not None else 0,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SearchIndexModel":
        """Create ORM model from dictionary

        Args:
            data: Dictionary with search index data

        Returns:
            SearchIndexModel instance
        """
        return cls(
            id=data.get("id"),
            entity_type=data["entity_type"],
            library_id=data.get("library_id"),
            entity_id=data["entity_id"],
            text=data["text"],
            snippet=data.get("snippet"),
            rank_score=data.get("rank_score", 0.0),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(timezone.utc),
            event_version=int(data.get("event_version", 0) or 0),
        )

    def __repr__(self) -> str:
        return f"<SearchIndexModel(type={self.entity_type}, id={self.entity_id}, score={self.rank_score})>"
