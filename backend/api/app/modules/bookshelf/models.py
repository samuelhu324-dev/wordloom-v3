"""
Bookshelf Models - SQLAlchemy ORM models for persistence

Maps Bookshelf Domain aggregate to database table.
"""

from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4

from core.database import Base


class BookshelfModel(Base):
    """
    Bookshelf ORM Model

    Table: bookshelves
    - One or more Bookshelves per Library
    - Unique name per Library (RULE-006)
    - Special "Basement" bookshelf for soft-deleted books (RULE-010)

    Mapping Strategy (ADR-009):
    - Primary Key: id (UUID)
    - Business Keys: (library_id, name) UNIQUE per RULE-006
    - Parent: library_id (FK, NOT NULL, per RULE-005)
    - Special: is_basement (per RULE-010, Basement Pattern)

    Round-Trip Validation:
    Use to_dict() for ORM → dict conversion
    Use from_dict() for dict → ORM conversion
    """
    __tablename__ = "bookshelves"

    # ✅ RULE-006: Unique bookshelf name per library
    __table_args__ = (
        UniqueConstraint('library_id', 'name', name='uq_library_bookshelf_name'),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    library_id = Column(
        UUID(as_uuid=True),
        ForeignKey("libraries.id"),
        nullable=False,
        index=True,
        comment="Parent Library",
    )
    name = Column(
        String(255),
        nullable=False,
        comment="Bookshelf name",
    )
    description = Column(
        Text,
        nullable=True,
        comment="Bookshelf description",
    )
    is_basement = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Basement bookshelf (soft delete container, per RULE-010)",
    )
    is_pinned = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Bookshelf is pinned",
    )
    pinned_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When bookshelf was pinned",
    )
    is_favorite = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Bookshelf is favorite",
    )
    status = Column(
        String(50),
        default="active",
        nullable=False,
        comment="Bookshelf status (active, archived, etc.)",
    )
    book_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Cached book count",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="When bookshelf was created",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="When bookshelf was last updated",
    )

    def __repr__(self) -> str:
        return f"<BookshelfModel(id={self.id}, library_id={self.library_id}, name={self.name}, is_basement={self.is_basement})>"

    # ========================================================================
    # Round-Trip Mapping Methods (for testing and repository conversion)
    # ========================================================================

    def to_dict(self) -> dict:
        """
        Convert ORM model to dictionary for serialization or testing.

        Returns:
            dict with all fields

        Usage:
            model = bookshelf_model_factory()
            data = model.to_dict()
            assert data["id"] == model.id
        """
        return {
            "id": self.id,
            "library_id": self.library_id,
            "name": self.name,
            "description": self.description,
            "is_basement": self.is_basement,
            "is_pinned": self.is_pinned,
            "pinned_at": self.pinned_at,
            "is_favorite": self.is_favorite,
            "status": self.status,
            "book_count": self.book_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "BookshelfModel":
        """
        Create ORM model from dictionary.

        Inverse of to_dict(). Used for testing and data migration.

        Args:
            data: Dictionary with model fields

        Returns:
            BookshelfModel instance

        Usage:
            model = BookshelfModel.from_dict({
                "id": uuid4(),
                "library_id": uuid4(),
                "name": "Test"
            })
        """
        return BookshelfModel(
            id=data.get("id"),
            library_id=data.get("library_id"),
            name=data.get("name"),
            description=data.get("description"),
            is_basement=data.get("is_basement", False),
            is_pinned=data.get("is_pinned", False),
            pinned_at=data.get("pinned_at"),
            is_favorite=data.get("is_favorite", False),
            status=data.get("status", "active"),
            book_count=data.get("book_count", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
