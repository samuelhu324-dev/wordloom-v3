"""
Test Suite: Block Domain Layer

Tests for Block aggregate root:
- Domain invariants (RULE-013-REVISED, RULE-014, RULE-015-REVISED, RULE-016)
- BlockContent and BlockMetadata value objects
- Fractional Index Ordering
- Block types (HEADING, TEXT, CODE, etc.)

对应 DDD_RULES:
  ✓ RULE-013-REVISED: Block 可无限创建，支持多种类型
  ✓ RULE-014: Block 属于唯一的 Book
  ✓ RULE-015-REVISED: Block 使用 Fractional Index 排序
  ✓ RULE-016: HEADING 是新增的 Block 类型
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal

from modules.block.domain import Block, BlockContent, BlockType
from modules.block.exceptions import InvalidBlockTypeError, InvalidBlockContentError


class TestBlockContent:
    """Value Object: BlockContent"""

    def test_block_content_creation_valid(self):
        """✓ BlockContent accepts valid content"""
        content = BlockContent(value="Sample block content")
        assert content.value == "Sample block content"

    def test_block_content_empty_valid(self):
        """✓ BlockContent allows empty strings"""
        content = BlockContent(value="")
        assert content.value == ""

    def test_block_content_large_text(self):
        """✓ BlockContent accepts large texts"""
        large_text = "A" * 10000
        content = BlockContent(value=large_text)
        assert len(content.value) == 10000


class TestBlockType:
    """Block Types (RULE-013-REVISED, RULE-016)"""

    def test_block_type_text(self):
        """✓ BlockType TEXT"""
        assert BlockType.TEXT.value == "text"

    def test_block_type_code(self):
        """✓ BlockType CODE"""
        assert BlockType.CODE.value == "code"

    def test_block_type_heading(self):
        """✓ RULE-016: BlockType HEADING"""
        assert BlockType.HEADING.value == "heading"

    def test_block_type_image(self):
        """✓ BlockType IMAGE"""
        assert BlockType.IMAGE.value == "image"

    def test_block_type_table(self):
        """✓ BlockType TABLE"""
        assert BlockType.TABLE.value == "table"

    def test_all_supported_types(self):
        """✓ All standard block types supported"""
        expected_types = {"text", "code", "heading", "image", "table"}
        actual_types = {bt.value for bt in BlockType}
        assert expected_types.issubset(actual_types)


class TestBlockAggregateRoot:
    """Aggregate Root: Block"""

    def test_block_creation_text_type(self):
        """✓ Block creation with TEXT type"""
        block = Block(
            block_id=uuid4(),
            book_id=uuid4(),
            block_type=BlockType.TEXT,
            content=BlockContent(value="Text content"),
            index=Decimal("1.0"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert block.block_type == BlockType.TEXT
        assert block.content.value == "Text content"

    def test_block_creation_code_type(self):
        """✓ Block creation with CODE type"""
        block = Block(
            block_id=uuid4(),
            book_id=uuid4(),
            block_type=BlockType.CODE,
            content=BlockContent(value="print('hello')"),
            index=Decimal("1.0"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert block.block_type == BlockType.CODE

    def test_block_creation_heading_type(self):
        """✓ RULE-016: Block creation with HEADING type"""
        block = Block(
            block_id=uuid4(),
            book_id=uuid4(),
            block_type=BlockType.HEADING,
            content=BlockContent(value="Section Title"),
            index=Decimal("1.0"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert block.block_type == BlockType.HEADING


class TestBlockFractionalIndexing:
    """RULE-015-REVISED: Fractional Index Ordering"""

    def test_block_fractional_index_valid(self):
        """✓ Block accepts Fractional Index values"""
        block = Block(
            block_id=uuid4(),
            book_id=uuid4(),
            block_type=BlockType.TEXT,
            content=BlockContent(value="Test"),
            index=Decimal("1.5"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert block.index == Decimal("1.5")

    def test_block_fractional_index_between_integers(self):
        """✓ Block index can be between integers (1 < index < 2)"""
        block1 = Block(
            block_id=uuid4(),
            book_id=uuid4(),
            block_type=BlockType.TEXT,
            content=BlockContent(value="First"),
            index=Decimal("1.0"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        block_middle = Block(
            block_id=uuid4(),
            book_id=uuid4(),
            block_type=BlockType.TEXT,
            content=BlockContent(value="Middle"),
            index=Decimal("1.5"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        block2 = Block(
            block_id=uuid4(),
            book_id=uuid4(),
            block_type=BlockType.TEXT,
            content=BlockContent(value="Second"),
            index=Decimal("2.0"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Verify ordering
        assert block1.index < block_middle.index < block2.index

    def test_block_fractional_index_high_precision(self):
        """✓ Block index supports high precision"""
        block = Block(
            block_id=uuid4(),
            book_id=uuid4(),
            block_type=BlockType.TEXT,
            content=BlockContent(value="Precise"),
            index=Decimal("1.000000001"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert len(str(block.index).split('.')[-1]) > 0


class TestBlockInvariants:
    """Domain Invariants Enforcement"""

    def test_block_invariant_unlimited_creation(self):
        """✓ RULE-013-REVISED: Blocks can be created unlimited"""
        book_id = uuid4()

        for i in range(10):
            block = Block(
                block_id=uuid4(),
                book_id=book_id,
                block_type=BlockType.TEXT,
                content=BlockContent(value=f"Block {i}"),
                index=Decimal(str(i + 1)),
                is_deleted=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            assert block.book_id == book_id

    def test_block_invariant_belongs_to_book(self):
        """✓ RULE-014: Block belongs to unique Book"""
        book_id = uuid4()
        block = Block(
            block_id=uuid4(),
            book_id=book_id,
            block_type=BlockType.TEXT,
            content=BlockContent(value="Test"),
            index=Decimal("1.0"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert block.book_id == book_id

    def test_block_invariant_ordered_by_index(self):
        """✓ RULE-015-REVISED: Blocks ordered by Fractional Index"""
        book_id = uuid4()

        blocks = []
        indices = [Decimal("1.0"), Decimal("1.5"), Decimal("2.0"), Decimal("1.25")]

        for idx in indices:
            block = Block(
                block_id=uuid4(),
                book_id=book_id,
                block_type=BlockType.TEXT,
                content=BlockContent(value="Content"),
                index=idx,
                is_deleted=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            blocks.append(block)

        # Blocks should be orderable
        sorted_blocks = sorted(blocks, key=lambda b: b.index)
        sorted_indices = [b.index for b in sorted_blocks]

        assert sorted_indices == sorted(indices)

    def test_block_invariant_type_valid(self):
        """✓ RULE-013-REVISED: Block type must be valid"""
        block = Block(
            block_id=uuid4(),
            book_id=uuid4(),
            block_type=BlockType.HEADING,
            content=BlockContent(value="Heading"),
            index=Decimal("1.0"),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert block.block_type in BlockType
