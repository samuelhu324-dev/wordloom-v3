"""
Block Models - SQLAlchemy ORM definitions

Mapping Strategy (ADR-015: Block Models & Testing Layer):
==========================================================
- Primary Key: id (UUID)
- Parent: book_id (FK, NOT NULL)
- Type System: type (BlockType Enum, per RULE-014)
- Ordering: order (DECIMAL(19,10) Fractional Index, per RULE-015-REVISED)
- Special: heading_level (nullable, only for HEADING type per RULE-013-REVISED)
- Soft Delete: soft_deleted_at (per POLICY-008)

Invariants Enforced:
✅ RULE-013: 无限创建（无 count 限制）
✅ RULE-014: type 必须是有效的 BlockType enum（数据库级别）
✅ RULE-015-REVISED: order DECIMAL(19,10) 支持分数索引（O(1) 拖拽操作）
✅ RULE-013-REVISED: HEADING 类型时 heading_level 必须设置
✅ RULE-016: book_id NOT NULL + FK 约束
✅ POLICY-008: soft_deleted_at 支持软删除

Round-Trip Validation:
Use to_dict() for ORM → dict conversion
Use from_dict() for dict → ORM conversion (9 fields total)

Query Patterns:
- Active blocks: WHERE book_id = ? AND soft_deleted_at IS NULL ORDER BY order
- Deleted blocks: WHERE book_id = ? AND soft_deleted_at IS NOT NULL
- Between blocks (for insertion): WHERE order BETWEEN ? AND ? AND soft_deleted_at IS NULL
"""

from enum import Enum
from sqlalchemy import Column, String, DateTime, Text, Numeric, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from uuid import uuid4
from .base import Base
from decimal import Decimal


class BlockType(str, Enum):
    """
    Block Type Enumeration (RULE-014)

    Defines all supported block types in the system.
    Must match Domain BlockType enum for type safety.
    """
    TEXT = "text"          # Plain text paragraph
    HEADING = "heading"    # Heading (H1, H2, H3 per RULE-013-REVISED)
    CODE = "code"          # Code block with language
    IMAGE = "image"        # Image reference
    QUOTE = "quote"        # Blockquote
    LIST = "list"          # Bullet/numbered list
    TODO_LIST = "todo_list"  # Checkbox todo list
    TABLE = "table"        # Table structure
    DIVIDER = "divider"    # Horizontal divider


class BlockModel(Base):
    """
    Block ORM Model

    Represents a Block aggregate root in the system.

    Key Features:
    - Independent aggregate root (not nested under Book)
    - Supports fractional index ordering for O(1) drag/drop operations
    - Supports soft delete via Basement pattern
    - Supports type-specific fields (e.g., heading_level for HEADING)

    Database Constraints:
    - PK: id (UUID, auto-generated)
    - FK: book_id (NOT NULL, indexed)
    - Type: type (Enum, enforced at DB level per RULE-014)
    - Ordering: order (DECIMAL(19,10) for fractional indexing per RULE-015-REVISED)
    - Soft Delete: soft_deleted_at (nullable, indexed for filtering)

    Type-Specific Fields:
    - heading_level: Only used for HEADING type blocks (H1=1, H2=2, H3=3)
    """

    __tablename__ = "blocks"

    # Primary key and foreign keys
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    book_id = Column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Block type and content
    # Use plain VARCHAR + CHECK constraint (migration sets valid_block_type) to avoid enum type mismatch
    type = Column(
        String(32),
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )

    # Fractional index ordering (O(1) drag/drop operations per RULE-015-REVISED)
    # Precision upgraded to NUMERIC(36,18) via Migration 012 for higher insertion density
    order = Column(
        Numeric(precision=36, scale=18),
        nullable=False,
        default=Decimal('0')
    )

    # HEADING-specific field (only set when type='heading' per RULE-013-REVISED)
    heading_level = Column(
        Integer,
        nullable=True
    )

    # Soft delete support (POLICY-008: Basement Pattern)
    soft_deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )

    # ========== NEW: Paperballs Recovery Position Information (Doc 8 Integration) ==========
    # These fields store the deletion context to enable 3-level recovery strategy
    deleted_prev_id = Column(
        UUID(as_uuid=True),
        ForeignKey("blocks.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    deleted_next_id = Column(
        UUID(as_uuid=True),
        ForeignKey("blocks.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    deleted_section_path = Column(
        String(500),
        nullable=True,
        index=True
    )

    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Timestamp of soft delete"
    )

    # ========== NEW: Meta (Phase 0 reserved) ==========
    # Lightweight JSON/string metadata (e.g., cached render hints) - not yet used by domain
    meta = Column(
        Text,
        nullable=True
    )

    # Audit timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        """Debug representation"""
        return (
            f"BlockModel(id={self.id}, book_id={self.book_id}, type={self.type}, "
            f"order={self.order}, soft_deleted_at={self.soft_deleted_at})"
        )

    def to_dict(self) -> dict:
        """
        Serialize to dictionary (12 fields total including Paperballs fields)

        Usage:
        - REST API responses
        - Test serialization verification
        - Data export

        Returns:
        dict with keys: id, book_id, type, content, order, heading_level,
                       soft_deleted_at, deleted_prev_id, deleted_next_id,
                       deleted_section_path, created_at, updated_at
        """
        return {
            "id": str(self.id) if self.id else None,
            "book_id": str(self.book_id) if self.book_id else None,
            "type": self.type.value if isinstance(self.type, BlockType) else self.type,
            "content": self.content,
            "order": float(self.order) if self.order else 0.0,  # DECIMAL → float
            "heading_level": self.heading_level,
            "soft_deleted_at": self.soft_deleted_at.isoformat() if self.soft_deleted_at else None,
            # === NEW: Paperballs fields ===
            "deleted_prev_id": str(self.deleted_prev_id) if self.deleted_prev_id else None,
            "deleted_next_id": str(self.deleted_next_id) if self.deleted_next_id else None,
            "deleted_section_path": self.deleted_section_path,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            # === Audit timestamps ===
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def from_dict(data: dict) -> "BlockModel":
        """
        Deserialize from dictionary

        Usage:
        - Data migration
        - Test data import
        - API request handling

        Args:
        data: dict with keys matching to_dict() output

        Returns:
        BlockModel instance
        """
        block_type = data.get("type")
        if isinstance(block_type, str):
            # Convert string to BlockType enum
            block_type = BlockType(block_type)

        return BlockModel(
            id=UUID(data.get("id")) if data.get("id") else None,
            book_id=UUID(data.get("book_id")) if data.get("book_id") else None,
            type=block_type,
            content=data.get("content"),
            order=Decimal(str(data.get("order", 0))),
            heading_level=data.get("heading_level"),
            soft_deleted_at=data.get("soft_deleted_at"),
            # === NEW: Paperballs fields ===
            deleted_prev_id=UUID(data.get("deleted_prev_id")) if data.get("deleted_prev_id") else None,
            deleted_next_id=UUID(data.get("deleted_next_id")) if data.get("deleted_next_id") else None,
            deleted_section_path=data.get("deleted_section_path"),
            deleted_at=data.get("deleted_at"),
            # === Audit timestamps ===
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


# Need UUID import for from_dict
from uuid import UUID
