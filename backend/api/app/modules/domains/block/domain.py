"""
Block Domain - Business logic for smallest content units

Purpose:
- Represents smallest content units under a Book
- Flat structure with BlockType as independent types (including HEADING as type)
- Supports multiple block types: TEXT, HEADING, CODE, IMAGE, TABLE, QUOTE, LIST
- Uses Fractional Index (DECIMAL ordering) for O(1) drag/drop operations
- Does NOT manage: preview_image for IMAGE blocks (→ Media)

Architecture:
- Pure domain layer with zero infrastructure dependencies
- Flat structure (NOT nested - simpler, supports O(1) drag/drop)
- HEADING is a BlockType, not a title field
- Order field uses Fractional Index (Decimal) for sparse sorting
- Type-specific factory methods (create_text, create_heading, etc.)
- Emits DomainEvents on state changes
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from enum import Enum
from decimal import Decimal

from shared.base import AggregateRoot, DomainEvent, ValueObject


# ============================================================================
# Enums
# ============================================================================

class BlockType(str, Enum):
    """Type of content Block"""
    TEXT = "text"
    HEADING = "heading"      # HEADING replaces HEADING_1/2/3 + title_level concept
    IMAGE = "image"
    CODE = "code"
    TABLE = "table"
    QUOTE = "quote"
    LIST = "list"
    DIVIDER = "divider"


# ============================================================================
# Domain Events
# ============================================================================

@dataclass
class BlockCreated(DomainEvent):
    """Emitted when a new Block is created"""
    block_id: UUID
    book_id: UUID
    block_type: BlockType
    order: Decimal
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.block_id


@dataclass
class BlockContentChanged(DomainEvent):
    """Emitted when Block content is modified"""
    block_id: UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.block_id


@dataclass
class BlockReordered(DomainEvent):
    """Emitted when Block order changes (drag/drop with fractional index)"""
    block_id: UUID
    old_order: Decimal
    new_order: Decimal
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.block_id


@dataclass
class BlockDeleted(DomainEvent):
    """Emitted when Block is deleted"""
    block_id: UUID
    book_id: UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.block_id


# ============================================================================
# Value Objects
# ============================================================================

@dataclass(frozen=True)
class BlockContent(ValueObject):
    """Value object for Block content"""
    value: str

    def __post_init__(self):
        if len(self.value) > 10000:
            raise ValueError("Block content cannot exceed 10000 characters")

    def __str__(self) -> str:
        return self.value


# ============================================================================
# Aggregate Root
# ============================================================================

class Block(AggregateRoot):
    """
    Block Aggregate Root

    Invariants:
    - Block must have a Book (parent aggregate)
    - Block has a type (one of BlockType enum)
    - Content must be non-empty and ≤ 10000 characters
    - Order uses Fractional Index (Decimal) for O(1) drag/drop
    - HEADING is a BlockType with optional level (1-3) in metadata
    - Block structure is FLAT (not nested)
    - Media (for IMAGE blocks) managed by Media Domain

    Design Decision: HEADING as BlockType + Fractional Index ordering
    - HEADING replaces title_text/title_level concept (independent type)
    - Simpler data model with clear type semantics
    - Fractional index (Decimal) enables O(1) reordering without batch updates
    - Still supports heading levels via heading_level property
    - Query-friendly (no recursive queries needed)

    Business Rules:
    - Created with type, content, and order (via factory methods)
    - Content can be updated (BlockContentChanged event)
    - Order can change via fractional index (BlockReordered event)
    """

    def __init__(
        self,
        block_id: UUID,
        book_id: UUID,
        block_type: BlockType,
        content: BlockContent,
        order: Decimal = Decimal("0"),
        heading_level: Optional[int] = None,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self.id = block_id
        self.book_id = book_id
        self.type = block_type
        self.content = content
        self.order = order
        self.heading_level = heading_level if block_type == BlockType.HEADING else None
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.events: List[DomainEvent] = []

    # ========================================================================
    # Factory Methods - Type-Specific Constructors
    # ========================================================================

    @classmethod
    def create_text(
        cls,
        book_id: UUID,
        content: str,
        order: Decimal = Decimal("0"),
    ) -> Block:
        """Create a TEXT block"""
        block_id = uuid4()
        block_content = BlockContent(value=content)
        now = datetime.utcnow()

        block = cls(
            block_id=block_id,
            book_id=book_id,
            block_type=BlockType.TEXT,
            content=block_content,
            order=order,
            created_at=now,
            updated_at=now,
        )

        block.emit(
            BlockCreated(
                block_id=block_id,
                book_id=book_id,
                block_type=BlockType.TEXT,
                order=order,
                occurred_at=now,
            )
        )

        return block

    @classmethod
    def create_heading(
        cls,
        book_id: UUID,
        content: str,
        level: int = 1,
        order: Decimal = Decimal("0"),
    ) -> Block:
        """Create a HEADING block (level 1-3)"""
        if level not in (1, 2, 3):
            raise ValueError("Heading level must be 1, 2, or 3")

        block_id = uuid4()
        block_content = BlockContent(value=content)
        now = datetime.utcnow()

        block = cls(
            block_id=block_id,
            book_id=book_id,
            block_type=BlockType.HEADING,
            content=block_content,
            order=order,
            heading_level=level,
            created_at=now,
            updated_at=now,
        )

        block.emit(
            BlockCreated(
                block_id=block_id,
                book_id=book_id,
                block_type=BlockType.HEADING,
                order=order,
                occurred_at=now,
            )
        )

        return block

    @classmethod
    def create_code(
        cls,
        book_id: UUID,
        content: str,
        language: str = "text",
        order: Decimal = Decimal("0"),
    ) -> Block:
        """Create a CODE block"""
        # Language metadata can be stored in a metadata field if needed
        # For now, include in content comment or as separate field
        block_id = uuid4()
        block_content = BlockContent(value=content)
        now = datetime.utcnow()

        block = cls(
            block_id=block_id,
            book_id=book_id,
            block_type=BlockType.CODE,
            content=block_content,
            order=order,
            created_at=now,
            updated_at=now,
        )

        block.emit(
            BlockCreated(
                block_id=block_id,
                book_id=book_id,
                block_type=BlockType.CODE,
                order=order,
                occurred_at=now,
            )
        )

        return block

    @classmethod
    def create_image(
        cls,
        book_id: UUID,
        order: Decimal = Decimal("0"),
    ) -> Block:
        """Create an IMAGE block (placeholder content)"""
        block_id = uuid4()
        block_content = BlockContent(value="[image]")
        now = datetime.utcnow()

        block = cls(
            block_id=block_id,
            book_id=book_id,
            block_type=BlockType.IMAGE,
            content=block_content,
            order=order,
            created_at=now,
            updated_at=now,
        )

        block.emit(
            BlockCreated(
                block_id=block_id,
                book_id=book_id,
                block_type=BlockType.IMAGE,
                order=order,
                occurred_at=now,
            )
        )

        return block

    @classmethod
    def create_quote(
        cls,
        book_id: UUID,
        content: str,
        order: Decimal = Decimal("0"),
    ) -> Block:
        """Create a QUOTE block"""
        block_id = uuid4()
        block_content = BlockContent(value=content)
        now = datetime.utcnow()

        block = cls(
            block_id=block_id,
            book_id=book_id,
            block_type=BlockType.QUOTE,
            content=block_content,
            order=order,
            created_at=now,
            updated_at=now,
        )

        block.emit(
            BlockCreated(
                block_id=block_id,
                book_id=book_id,
                block_type=BlockType.QUOTE,
                order=order,
                occurred_at=now,
            )
        )

        return block

    @classmethod
    def create_list(
        cls,
        book_id: UUID,
        content: str,
        order: Decimal = Decimal("0"),
    ) -> Block:
        """Create a LIST block"""
        block_id = uuid4()
        block_content = BlockContent(value=content)
        now = datetime.utcnow()

        block = cls(
            block_id=block_id,
            book_id=book_id,
            block_type=BlockType.LIST,
            content=block_content,
            order=order,
            created_at=now,
            updated_at=now,
        )

        block.emit(
            BlockCreated(
                block_id=block_id,
                book_id=book_id,
                block_type=BlockType.LIST,
                order=order,
                occurred_at=now,
            )
        )

        return block

    # ========================================================================
    # Business Methods
    # ========================================================================

    def set_content(self, new_content: str) -> None:
        """Update Block content"""
        new_block_content = BlockContent(value=new_content)

        if self.content.value == new_block_content.value:
            return

        self.content = new_block_content
        self.updated_at = datetime.utcnow()

        self.emit(
            BlockContentChanged(
                block_id=self.id,
                occurred_at=self.updated_at,
            )
        )

    def set_order_fractional(self, new_order: Decimal) -> None:
        """Update Block order using fractional index (for drag/drop)"""
        if new_order < Decimal("0"):
            raise ValueError("Order must be non-negative")

        if self.order == new_order:
            return

        old_order = self.order
        self.order = new_order
        self.updated_at = datetime.utcnow()

        self.emit(
            BlockReordered(
                block_id=self.id,
                old_order=old_order,
                new_order=new_order,
                occurred_at=self.updated_at,
            )
        )

    def mark_deleted(self) -> None:
        """Mark Block as deleted (soft delete)"""
        now = datetime.utcnow()
        self.updated_at = now

        self.emit(
            BlockDeleted(
                block_id=self.id,
                book_id=self.book_id,
                occurred_at=now,
            )
        )

    # ========================================================================
    # Query Methods
    # ========================================================================

    def is_heading(self) -> bool:
        """Check if Block is a heading"""
        return self.type == BlockType.HEADING

    def is_code(self) -> bool:
        """Check if Block is a code block"""
        return self.type == BlockType.CODE

    def is_image(self) -> bool:
        """Check if Block is an image"""
        return self.type == BlockType.IMAGE

    def is_quote(self) -> bool:
        """Check if Block is a quote"""
        return self.type == BlockType.QUOTE

    def is_list(self) -> bool:
        """Check if Block is a list"""
        return self.type == BlockType.LIST

    def __repr__(self) -> str:
        return f"<Block(id={self.id}, book_id={self.book_id}, type={self.type}, order={self.order})>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Block):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
