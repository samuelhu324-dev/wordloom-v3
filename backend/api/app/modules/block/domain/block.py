"""
Block Aggregate Root

Core business logic for content blocks within Books.

Purpose:
- Represents smallest editable unit (paragraph, heading, code, image, etc.)
- Manages ordered positioning via Fractional Index (O(1) drag/drop)
- Manages soft deletion via Basement pattern (POLICY-008)
- Supports 3-level Paperballs recovery strategy (Doc 8)

Architecture:
- Pure domain layer with zero infrastructure dependencies
- Emits DomainEvents on state changes
- Uses Repository pattern for persistence abstraction

Invariants:
- Block associated to Book through book_id FK (not embedded)
- Type must be one of 8 valid BlockType values (TEXT, HEADING, CODE, IMAGE, QUOTE, LIST, TABLE, DIVIDER)
- Content must be ≤ 10000 characters
- order field stores Fractional Index value (DECIMAL(19,10) precision)
- heading_level only valid for HEADING type (1-3 for H1-H3)
- soft_deleted_at marks Blocks in Basement view
- Paperballs fields (deleted_prev_id, deleted_next_id, deleted_section_path) enable recovery
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4
from decimal import Decimal

from api.app.shared.base import AggregateRoot, DomainEvent
from .events import (
    BlockCreated,
    BlockUpdated,
    BlockReordered,
    BlockDeleted,
    BlockRestored,
)


class BlockType(str, Enum):
    """
    Block Type Enumeration (RULE-014)

    Defines all supported block types in the system.
    Must match ORM BlockType enum for type safety.

    Value Distribution:
    - TEXT: Plain text paragraphs (most common, ~70%)
    - HEADING: Section headers with level (H1-H3, ~10%)
    - CODE: Code blocks with syntax highlighting (~5%)
    - IMAGE: Image references (~5%)
    - QUOTE: Blockquotes (~5%)
    - LIST: Bullet/numbered lists (~3%)
    - TABLE: Tabular data (<1%)
    - DIVIDER: Visual separators (<1%)
    """
    TEXT = "text"          # Plain text paragraph
    HEADING = "heading"    # Heading (H1, H2, H3 per RULE-013-REVISED)
    CODE = "code"          # Code block with language
    IMAGE = "image"        # Image reference
    QUOTE = "quote"        # Blockquote
    LIST = "list"          # Bullet/numbered list
    TABLE = "table"        # Table structure
    DIVIDER = "divider"    # Horizontal divider


class BlockContent:
    """
    Block Content ValueObject

    Validates content constraints.
    - Min: 0 characters (empty allowed for placeholders)
    - Max: 10000 characters
    """

    def __init__(self, value: str):
        if not isinstance(value, str):
            raise ValueError("Content must be a string")
        if len(value) > 10000:
            raise ValueError("Content exceeds maximum length of 10000 characters")
        self.value = value

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"BlockContent({len(self.value)} chars)"


class Block(AggregateRoot):
    """
    Block Aggregate Root (独立聚合根)

    Design Decision: Independent aggregate
    - Does NOT directly contain nested objects (only value objects)
    - Uses order field for positioning (Fractional Index strategy)
    - Service layer responsible for reordering and deletion handling

    Business Rules:
    - Created with type, content, and book_id
    - Type determines valid additional fields (e.g., heading_level for HEADING)
    - Reordering changes order via Fractional Index (O(1) operation)
    - Deletion = transfer to Basement (BlockDeleted event)
    - Restoration from Basement uses 3-level Paperballs strategy
    - Maximum content length: 10000 characters (VALUE OBJECT constraint)

    Soft Delete Pattern (RULE-012):
    - Active blocks: soft_deleted_at IS NULL
    - Deleted blocks (Basement): soft_deleted_at IS NOT NULL
    - Query filter: WHERE book_id = ? AND soft_deleted_at IS NULL

    Paperballs Recovery (Doc 8 - 3-level strategy):
    - Level 1: Restore after previous sibling (deleted_prev_id)
    - Level 2: Restore before next sibling (deleted_next_id)
    - Level 3: Restore at section end (deleted_section_path)
    - Level 4: Restore at book end (fallback guarantee)
    """

    def __init__(
        self,
        block_id: UUID,
        book_id: UUID,
        block_type: BlockType,
        content: BlockContent,
        order: Decimal = Decimal('0'),
        heading_level: Optional[int] = None,
        soft_deleted_at: Optional[datetime] = None,
        deleted_prev_id: Optional[UUID] = None,
        deleted_next_id: Optional[UUID] = None,
        deleted_section_path: Optional[str] = None,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        """Initialize Block aggregate root"""
        self.id = block_id
        self.book_id = book_id
        self.type = block_type
        self.content = content if isinstance(content, BlockContent) else BlockContent(content)
        self.order = order
        self.heading_level = heading_level
        self.soft_deleted_at = soft_deleted_at  # ← Marks if in Basement
        self.deleted_prev_id = deleted_prev_id  # ← Paperballs Level 1
        self.deleted_next_id = deleted_next_id  # ← Paperballs Level 2
        self.deleted_section_path = deleted_section_path  # ← Paperballs Level 3
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.events: List[DomainEvent] = []

        # Type-specific validation
        if self.type == BlockType.HEADING and self.heading_level is None:
            raise ValueError("HEADING blocks must have heading_level (1-3)")

    # ========================================================================
    # Factory Methods
    # ========================================================================

    @classmethod
    def create(
        cls,
        book_id: UUID,
        block_type: BlockType,
        content: str,
        order: Decimal = Decimal('1'),
        heading_level: Optional[int] = None,
    ) -> Block:
        """
        Factory method to create new Block

        Args:
            book_id: Parent book ID
            block_type: Type of block (TEXT, HEADING, CODE, etc.)
            content: Block content (string)
            order: Fractional index for positioning (default: 1)
            heading_level: For HEADING type only (1-3 for H1-H3)

        Returns:
            New Block instance

        Raises:
            ValueError: If type=HEADING but heading_level not provided
        """
        block_id = uuid4()
        block = cls(
            block_id=block_id,
            book_id=book_id,
            block_type=block_type,
            content=BlockContent(content),
            order=order,
            heading_level=heading_level,
        )

        # Emit creation event
        block.events.append(
            BlockCreated(
                aggregate_id=block_id,
                book_id=book_id,
                block_type=block_type.value,
                content=content[:100],  # First 100 chars for event
                order=float(order),
            )
        )

        return block

    # ========================================================================
    # Business Methods
    # ========================================================================

    def update_content(self, new_content: str) -> None:
        """
        Update block content

        Args:
            new_content: New content string (≤ 10000 chars)

        Emits: BlockUpdated event
        """
        self.content = BlockContent(new_content)
        self.updated_at = datetime.now(timezone.utc)

        self.events.append(
            BlockUpdated(
                aggregate_id=self.id,
                book_id=self.book_id,
                new_content=new_content[:100],
            )
        )

    def reorder(self, new_order: Decimal, prev_block_order: Optional[Decimal] = None, next_block_order: Optional[Decimal] = None) -> None:
        """
        Reorder block via Fractional Index

        Args:
            new_order: New order value (calculated via Fractional Index)
            prev_block_order: Previous block's order (for context)
            next_block_order: Next block's order (for context)

        Emits: BlockReordered event
        """
        old_order = self.order
        self.order = new_order
        self.updated_at = datetime.now(timezone.utc)

        self.events.append(
            BlockReordered(
                aggregate_id=self.id,
                book_id=self.book_id,
                old_order=float(old_order),
                new_order=float(new_order),
            )
        )

    def mark_deleted(
        self,
        prev_sibling_id: Optional[UUID] = None,
        next_sibling_id: Optional[UUID] = None,
        section_path: Optional[str] = None,
    ) -> None:
        """
        Soft-delete block to Basement

        Captures Paperballs recovery context:
        - prev_sibling_id: Previous active block (Level 1 recovery)
        - next_sibling_id: Next active block (Level 2 recovery)
        - section_path: Section path (Level 3 recovery)

        Args:
            prev_sibling_id: Previous sibling block ID (optional)
            next_sibling_id: Next sibling block ID (optional)
            section_path: Section path string (optional)

        Emits: BlockDeleted event
        """
        self.soft_deleted_at = datetime.now(timezone.utc)
        self.deleted_prev_id = prev_sibling_id
        self.deleted_next_id = next_sibling_id
        self.deleted_section_path = section_path
        self.updated_at = self.soft_deleted_at

        self.events.append(
            BlockDeleted(
                aggregate_id=self.id,
                book_id=self.book_id,
                prev_sibling_id=str(prev_sibling_id) if prev_sibling_id else None,
                next_sibling_id=str(next_sibling_id) if next_sibling_id else None,
                section_path=section_path,
            )
        )

    def restore_from_basement(self, new_order: Decimal, recovery_level: int = 1) -> None:
        """
        Restore block from Basement

        Clears soft_deleted_at and Paperballs recovery fields.

        Args:
            new_order: New order after restoration
            recovery_level: Which recovery strategy was used (1-4)

        Emits: BlockRestored event
        """
        self.soft_deleted_at = None
        self.deleted_prev_id = None
        self.deleted_next_id = None
        self.deleted_section_path = None
        self.order = new_order
        self.updated_at = datetime.now(timezone.utc)

        self.events.append(
            BlockRestored(
                aggregate_id=self.id,
                book_id=self.book_id,
                new_order=float(new_order),
                recovery_level=recovery_level,
            )
        )

    # ========================================================================
    # Query Methods
    # ========================================================================

    def is_deleted(self) -> bool:
        """Check if block is in Basement (soft-deleted)"""
        return self.soft_deleted_at is not None

    def is_active(self) -> bool:
        """Check if block is active (not in Basement)"""
        return self.soft_deleted_at is None

    def __repr__(self) -> str:
        """Debug representation"""
        status = "DELETED" if self.is_deleted() else "ACTIVE"
        return (
            f"Block(id={self.id}, book_id={self.book_id}, type={self.type.value}, "
            f"order={self.order}, status={status})"
        )

    def __str__(self) -> str:
        """Human-readable representation"""
        content_preview = str(self.content)[:50]
        return f"Block#{str(self.id)[:8]}({self.type.value}): {content_preview}..."
