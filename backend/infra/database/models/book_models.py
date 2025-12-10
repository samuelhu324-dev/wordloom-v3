"""Book Models - SQLAlchemy ORM models

Mapping Strategy (ADR-010: Book Models & Testing Layer):
==========================================================
- Primary Key: id (UUID)
- Business Keys: bookshelf_id + library_id (冗余 FK for RULE-011 权限检查)
- Soft Delete: soft_deleted_at (per RULE-012 Basement Pattern)
- Metadata: title, summary, is_pinned, due_at, status, maturity, block_count

Invariants Enforced:
✅ RULE-009: 无限创建（仅验证 bookshelf_id 存在）
✅ RULE-011: bookshelf_id + library_id 权限检查（同库转移）
✅ RULE-012: soft_deleted_at 标记软删除（Basement Pattern）
✅ RULE-013: soft_deleted_at IS NULL 过滤显示

Round-Trip Validation:
Use to_dict() for ORM → dict conversion
Use from_dict() for dict → ORM conversion (13 fields total)
"""
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from uuid import uuid4
from .base import Base


class BookModel(Base):
    """Book ORM Model

    Represents a Book aggregate root in the system.

    Key Features:
    - Independent aggregate root (not nested under Bookshelf)
    - Supports cross-Bookshelf movement (RULE-011)
    - Supports soft delete via Basement pattern (RULE-012)
    - Automatically filtered to exclude soft-deleted items (RULE-013)

    Database Constraints:
    - PK: id (UUID, auto-generated)
    - FK: bookshelf_id (NOT NULL, indexed for list queries)
    - FK: library_id (NOT NULL, indexed for permission checks)
    - Soft Delete: soft_deleted_at (nullable, indexed for filtering)

    Query Patterns:
    - Active books: WHERE soft_deleted_at IS NULL
    - Deleted books (in Basement): WHERE soft_deleted_at IS NOT NULL
    - By shelf: WHERE bookshelf_id = ? AND soft_deleted_at IS NULL
    - By library: WHERE library_id = ? AND soft_deleted_at IS NULL
    """
    __tablename__ = "books"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Foreign keys (RULE-011: Two-level permission check)
    bookshelf_id = Column(
        UUID(as_uuid=True),
        ForeignKey("bookshelves.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Library ID (redundant FK for RULE-011 permission validation)
    library_id = Column(
        UUID(as_uuid=True),
        ForeignKey("libraries.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Core fields
    title = Column(
        String(255),
        nullable=False
    )

    summary = Column(
        Text,
        nullable=True
    )

    cover_icon = Column(
        String(64),
        nullable=True,
        comment="POLICY-BOOK-COVER-ICON-LUCIDE: Optional Lucide icon name"
    )

    cover_media_id = Column(
        UUID(as_uuid=True),
        ForeignKey("media.id", ondelete="SET NULL"),
        nullable=True,
        comment="POLICY-BOOK-COVER-MEDIA-STABLE-ONLY: Optional Media UUID for custom covers"
    )

    is_pinned = Column(
        Boolean,
        default=False,
        nullable=False
    )

    due_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    status = Column(
        String(50),
        default="draft",
        nullable=False
    )

    maturity = Column(
        String(16),
        default="seed",
        nullable=False
    )

    block_count = Column(
        Integer,
        default=0,
        nullable=False
    )

    maturity_score = Column(
        Integer,
        default=0,
        nullable=False
    )

    legacy_flag = Column(
        Boolean,
        default=False,
        nullable=False
    )

    manual_maturity_override = Column(
        Boolean,
        default=False,
        nullable=False
    )

    manual_maturity_reason = Column(
        Text,
        nullable=True
    )

    last_visited_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    visit_count_90d = Column(
        Integer,
        default=0,
        nullable=False
    )

    previous_bookshelf_id = Column(
        UUID(as_uuid=True),
        ForeignKey("bookshelves.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Stores the last active bookshelf before moving to Basement"
    )

    moved_to_basement_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Timestamp of latest move into Basement"
    )

    # Soft delete support (RULE-012: Basement Pattern)
    soft_deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )

    # Audit timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self) -> str:
        """Debug representation"""
        return (
            f"BookModel(id={self.id}, title={self.title!r}, "
            f"bookshelf_id={self.bookshelf_id}, soft_deleted_at={self.soft_deleted_at})"
        )

    def to_dict(self) -> dict:
        """
        Serialize to dictionary (13 fields total)

        Usage:
        - REST API responses
        - Test serialization verification
        - Data export

        Returns:
        dict with keys: id, bookshelf_id, library_id, title, summary,
                       status, maturity, is_pinned, due_at, block_count,
                       soft_deleted_at, created_at, updated_at
        """
        return {
            "id": str(self.id) if self.id else None,
            "bookshelf_id": str(self.bookshelf_id) if self.bookshelf_id else None,
            "library_id": str(self.library_id) if self.library_id else None,
            "title": self.title,
            "summary": self.summary,
            "cover_icon": self.cover_icon,
            "cover_media_id": str(self.cover_media_id) if self.cover_media_id else None,
            "status": self.status,
            "maturity": self.maturity,
            "maturity_score": self.maturity_score,
            "legacy_flag": self.legacy_flag,
            "manual_maturity_override": self.manual_maturity_override,
            "manual_maturity_reason": self.manual_maturity_reason,
            "last_visited_at": self.last_visited_at.isoformat() if self.last_visited_at else None,
            "visit_count_90d": self.visit_count_90d,
            "previous_bookshelf_id": str(self.previous_bookshelf_id) if self.previous_bookshelf_id else None,
            "moved_to_basement_at": self.moved_to_basement_at.isoformat() if self.moved_to_basement_at else None,
            "is_pinned": self.is_pinned,
            "due_at": self.due_at.isoformat() if self.due_at else None,
            "block_count": self.block_count,
            "soft_deleted_at": self.soft_deleted_at.isoformat() if self.soft_deleted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def from_dict(data: dict) -> "BookModel":
        """
        Deserialize from dictionary

        Usage:
        - Data migration
        - Test data import
        - API request handling

        Args:
        data: dict with keys matching to_dict() output

        Returns:
        BookModel instance
        """
        return BookModel(
            id=UUID(data.get("id")) if data.get("id") else None,
            bookshelf_id=UUID(data.get("bookshelf_id")) if data.get("bookshelf_id") else None,
            library_id=UUID(data.get("library_id")) if data.get("library_id") else None,
            title=data.get("title"),
            summary=data.get("summary"),
            cover_icon=data.get("cover_icon"),
            cover_media_id=UUID(data.get("cover_media_id")) if data.get("cover_media_id") else None,
            status=data.get("status", "draft"),
            maturity=data.get("maturity", "seed"),
            maturity_score=data.get("maturity_score", 0),
            legacy_flag=data.get("legacy_flag", False),
            manual_maturity_override=data.get("manual_maturity_override", False),
            manual_maturity_reason=data.get("manual_maturity_reason"),
            last_visited_at=data.get("last_visited_at"),
            visit_count_90d=data.get("visit_count_90d", 0),
            previous_bookshelf_id=UUID(data.get("previous_bookshelf_id")) if data.get("previous_bookshelf_id") else None,
            moved_to_basement_at=data.get("moved_to_basement_at"),
            is_pinned=data.get("is_pinned", False),
            due_at=data.get("due_at"),
            block_count=data.get("block_count", 0),
            soft_deleted_at=data.get("soft_deleted_at"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


# Need UUID import for from_dict
from uuid import UUID
