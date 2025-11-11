"""
Block Domain - Business logic for smallest content units

Purpose:
- Represents smallest content units under a Book
- Flat structure with optional title hierarchy (title_level 1-3)
- Supports multiple block types: TEXT, HEADING_1-3, IMAGE, CODE, TABLE, QUOTE, LIST
- Does NOT manage: preview_image for IMAGE blocks (→ Media)

Architecture:
- Pure domain layer with zero infrastructure dependencies
- Flat structure (NOT nested Markers - simpler, supports drag/drop)
- Title hierarchy support via title_level (1-3 or None)
- Order field for drag/drop reordering support
- Emits DomainEvents on state changes
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from enum import Enum

from shared.base import AggregateRoot, DomainEvent, ValueObject


# ============================================================================
# Enums
# ============================================================================

class BlockType(str, Enum):
    """Type of content Block"""
    TEXT = "text"
    HEADING_1 = "heading_1"
    HEADING_2 = "heading_2"
    HEADING_3 = "heading_3"
    IMAGE = "image"
    CODE = "code"
    TABLE = "table"
    QUOTE = "quote"
    LIST = "list"


class TitleLevel(int, Enum):
    """Hierarchy level for Block with title_level"""
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3


# ============================================================================
# Domain Events
# ============================================================================

@dataclass
class BlockCreated(DomainEvent):
    """Emitted when a new Block is created"""
    block_id: UUID
    book_id: UUID
    block_type: BlockType
    order: int
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
    """Emitted when Block order changes"""
    block_id: UUID
    old_order: int
    new_order: int
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.block_id


@dataclass
class BlockTitleSet(DomainEvent):
    """Emitted when Block title/hierarchy is set"""
    block_id: UUID
    title_level: Optional[int]
    title_text: Optional[str]
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


@dataclass(frozen=True)
class BlockTitle(ValueObject):
    """Value object for Block title (with hierarchy level)"""
    text: Optional[str] = None
    level: Optional[int] = None

    def __post_init__(self):
        if self.level is not None and self.level not in (1, 2, 3):
            raise ValueError("Title level must be 1, 2, or 3")
        if self.text is not None and len(self.text) > 255:
            raise ValueError("Title text cannot exceed 255 characters")
        # Either both set or both None
        if (self.text is None) != (self.level is None):
            raise ValueError("Title text and level must both be set or both be None")

    def __str__(self) -> str:
        return self.text or ""


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
    - Order must be non-negative (for drag/drop support)
    - Title is optional with hierarchy level (1-3) or None
    - Block structure is FLAT (not nested)
    - Media (for IMAGE blocks) managed by Media Domain

    Design Decision: Flat structure with title_level instead of nested Markers
    - Simpler data model
    - Supports drag/drop reordering
    - Still supports title hierarchy via title_level (1-3)
    - Query-friendly (no recursive queries needed)

    Business Rules:
    - Created with type, content, and order
    - Content can be updated (BlockContentChanged event)
    - Order can change for drag/drop (BlockReordered event)
    - Title can be added/removed (BlockTitleSet event)
    """

    def __init__(
        self,
        block_id: UUID,
        book_id: UUID,
        block_type: BlockType,
        content: BlockContent,
        order: int = 0,
        title: Optional[BlockTitle] = None,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self.id = block_id
        self.book_id = book_id
        self.block_type = block_type
        self.content = content
        self.order = order
        self.title = title
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.events: List[DomainEvent] = []

    # ========================================================================
    # Factory Methods
    # ========================================================================

    @classmethod
    def create(
        cls,
        book_id: UUID,
        block_type: BlockType,
        content: str,
        order: int = 0,
    ) -> Block:
        """
        Factory method to create a new Block

        Args:
            book_id: ID of the parent Book
            block_type: Type of Block (TEXT, HEADING_1, etc.)
            content: Content string (≤ 10000 chars)
            order: Position in Book (for drag/drop)

        Returns:
            New Block instance with BlockCreated event

        Raises:
            ValueError: If content or type invalid
        """
        block_id = uuid4()
        block_content = BlockContent(value=content)
        now = datetime.utcnow()

        block = cls(
            block_id=block_id,
            book_id=book_id,
            block_type=block_type,
            content=block_content,
            order=order,
            created_at=now,
            updated_at=now,
        )

        block.emit(
            BlockCreated(
                block_id=block_id,
                book_id=book_id,
                block_type=block_type,
                order=order,
                occurred_at=now,
            )
        )

        return block

    # ========================================================================
    # Factory Methods - Block Type Constructors
    # ========================================================================

    @classmethod
    def create_text_block(cls, book_id: UUID, content: str, order: int = 0) -> Block:
        """Create a TEXT block"""
        return cls.create(book_id, BlockType.TEXT, content, order)

    @classmethod
    def create_heading_block(
        cls,
        book_id: UUID,
        level: int,
        content: str,
        order: int = 0,
    ) -> Block:
        """Create a HEADING block (level 1-3)"""
        if level not in (1, 2, 3):
            raise ValueError("Heading level must be 1, 2, or 3")
        block_type = {1: BlockType.HEADING_1, 2: BlockType.HEADING_2, 3: BlockType.HEADING_3}[level]
        return cls.create(book_id, block_type, content, order)

    @classmethod
    def create_image_block(cls, book_id: UUID, order: int = 0) -> Block:
        """Create an IMAGE block (placeholder content)"""
        return cls.create(book_id, BlockType.IMAGE, "[image]", order)

    @classmethod
    def create_code_block(cls, book_id: UUID, content: str, order: int = 0) -> Block:
        """Create a CODE block"""
        return cls.create(book_id, BlockType.CODE, content, order)

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

    def set_order(self, new_order: int) -> None:
        """Update Block order (for drag/drop)"""
        if new_order < 0:
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

    def set_title(self, text: str, level: int) -> None:
        """
        Set Block title with hierarchy level

        Args:
            text: Title text (≤ 255 chars)
            level: Hierarchy level (1, 2, or 3)

        Raises:
            ValueError: If text or level invalid
        """
        new_title = BlockTitle(text=text, level=level)
        self.title = new_title
        self.updated_at = datetime.utcnow()

        self.emit(
            BlockTitleSet(
                block_id=self.id,
                title_level=level,
                title_text=text,
                occurred_at=self.updated_at,
            )
        )

    def remove_title(self) -> None:
        """Remove Block title"""
        if self.title is None:
            return

        self.title = None
        self.updated_at = datetime.utcnow()

        self.emit(
            BlockTitleSet(
                block_id=self.id,
                title_level=None,
                title_text=None,
                occurred_at=self.updated_at,
            )
        )

    def mark_deleted(self) -> None:
        """Mark Block as deleted"""
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
        return self.block_type in (BlockType.HEADING_1, BlockType.HEADING_2, BlockType.HEADING_3)

    def heading_level(self) -> Optional[int]:
        """Get heading level if this is a heading block"""
        level_map = {
            BlockType.HEADING_1: 1,
            BlockType.HEADING_2: 2,
            BlockType.HEADING_3: 3,
        }
        return level_map.get(self.block_type)

    def is_image(self) -> bool:
        """Check if Block is an image"""
        return self.block_type == BlockType.IMAGE

    def __repr__(self) -> str:
        return f"<Block(id={self.id}, book_id={self.book_id}, type={self.block_type}, order={self.order})>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Block):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
