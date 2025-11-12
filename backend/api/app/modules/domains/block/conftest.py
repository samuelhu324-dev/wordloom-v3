"""Block Tests - Fixtures and Mock Repository

Testing Strategy (ADR-015: Block Models & Testing Layer):
========================================================
- Constants: sample_book_id
- Factories: block_domain_factory, block_model_factory
- Mock: MockBlockRepository with RULE-015/POLICY-008 constraint validation
- Helpers: assert_block_fractional_index, assert_block_soft_deleted, assert_heading_level_required
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime, timezone
from decimal import Decimal
from domains.block.domain import Block, BlockType, BlockContent, BlockTitle


# ============================================
# 1️⃣ CONSTANTS
# ============================================

@pytest.fixture
def sample_book_id():
    """Sample book ID (constant for tests)"""
    return UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


# ============================================
# 2️⃣ DOMAIN FACTORIES
# ============================================

@pytest.fixture
def block_domain_factory(sample_book_id):
    """
    Factory for creating Block Domain objects

    Supports all 9 fields customization including soft_deleted_at
    for POLICY-008 soft delete testing and order for RULE-015 testing.

    Usage:
        block = block_domain_factory(block_type=BlockType.HEADING, heading_level=2)
        deleted_block = block_domain_factory(soft_deleted_at=now)
    """
    def _create(
        block_id=None,
        book_id=None,
        block_type=BlockType.TEXT,
        content="Test content",
        order=10.0,
        heading_level=None,
        soft_deleted_at=None,
        created_at=None,
        updated_at=None,
    ):
        from domains.block.domain import Block
        now = datetime.now(timezone.utc)
        return Block(
            id=block_id or uuid4(),
            book_id=book_id or sample_book_id,
            type=block_type,
            content=BlockContent(content),
            order=Decimal(str(order)),
            heading_level=heading_level,
            soft_deleted_at=soft_deleted_at,
            created_at=created_at or now,
            updated_at=updated_at or now,
        )
    return _create


# ============================================
# 3️⃣ ORM MODEL FACTORIES
# ============================================

@pytest.fixture
def block_model_factory(sample_book_id):
    """
    Factory for creating Block ORM models

    Supports all 9 fields including type (as BlockType Enum),
    order (as Decimal), heading_level (nullable), and soft_deleted_at
    for complete round-trip testing.

    Usage:
        model = block_model_factory(type=BlockType.HEADING, heading_level=2)
        deleted_model = block_model_factory(soft_deleted_at=now)
    """
    def _create(
        block_id=None,
        book_id=None,
        block_type=BlockType.TEXT,
        content="Test content",
        order=10.0,
        heading_level=None,
        soft_deleted_at=None,
        created_at=None,
        updated_at=None,
    ):
        from domains.block.models import BlockModel, BlockType as DBBlockType
        now = datetime.now(timezone.utc)
        return BlockModel(
            id=block_id or uuid4(),
            book_id=book_id or sample_book_id,
            type=block_type,
            content=content,
            order=Decimal(str(order)),
            heading_level=heading_level,
            soft_deleted_at=soft_deleted_at,
            created_at=created_at or now,
            updated_at=updated_at or now,
        )
    return _create


# ============================================
# 4️⃣ MOCK REPOSITORY
# ============================================

@pytest.fixture
async def mock_block_repository(sample_book_id):
    """
    Mock BlockRepository with RULE-015 and POLICY-008 constraint validation

    Key Capabilities:
    - ✅ RULE-014: Validates type is valid BlockType enum
    - ✅ RULE-015-REVISED: Supports fractional index ordering
    - ✅ RULE-013-REVISED: Validates HEADING type requires heading_level
    - ✅ POLICY-008: Filters soft-deleted blocks (soft_deleted_at IS NULL)

    Behaviors:
    - save(): Validates type and heading_level constraints
    - get_by_id(): Returns None if block is soft-deleted
    - get_by_book_id(): Excludes soft-deleted blocks, orders by Decimal
    - get_deleted_blocks(): Retrieves only soft-deleted blocks
    """
    class MockBlockRepository:
        def __init__(self):
            self.store = {}  # block_id -> Block

        async def save(self, block: Block) -> None:
            """
            Save block with RULE-014 and RULE-013-REVISED validation

            RULE-014: Verify block.type is valid
            RULE-013-REVISED: HEADING type must have heading_level
            """
            # RULE-014: Validate type
            valid_types = {bt.value for bt in BlockType}
            block_type_str = block.type.value if hasattr(block.type, 'value') else block.type
            if block_type_str not in valid_types:
                raise ValueError(f"Invalid block type: {block_type_str}")

            # RULE-013-REVISED: HEADING blocks need heading_level
            if block_type_str == "heading" and block.heading_level is None:
                raise ValueError("HEADING blocks must have heading_level (1-3)")

            self.store[block.id] = block

        async def get_by_id(self, block_id: UUID):
            """
            Get block by ID (POLICY-008: auto-filter soft-deleted)

            Returns None if block is soft-deleted (soft_deleted_at IS NOT NULL)
            """
            block = self.store.get(block_id)
            if block and block.soft_deleted_at is not None:
                return None  # Block is in Basement, not visible
            return block

        async def get_by_book_id(self, book_id: UUID) -> list:
            """
            Get active blocks by book (RULE-015: ordered by fractional index)

            Returns only blocks where soft_deleted_at IS NULL,
            sorted by order (Decimal) for RULE-015-REVISED support
            """
            blocks = [
                b for b in self.store.values()
                if b.book_id == book_id and b.soft_deleted_at is None
            ]
            # Sort by Decimal order (supports fractional index insertion)
            return sorted(blocks, key=lambda b: float(b.order))

        async def get_deleted_blocks(self, book_id: UUID) -> list:
            """
            Get soft-deleted blocks (POLICY-008: retrieve from Basement)

            Returns only blocks where soft_deleted_at IS NOT NULL
            """
            return [
                b for b in self.store.values()
                if b.book_id == book_id and b.soft_deleted_at is not None
            ]

        async def delete(self, block_id: UUID) -> None:
            """
            Explicitly delete block (NOT RECOMMENDED - use soft delete instead)

            This is for hard delete. Prefer soft delete via:
                block.soft_deleted_at = datetime.now(timezone.utc)
                await repository.save(block)
            """
            # Intentionally not implemented to encourage soft delete pattern
            raise NotImplementedError(
                "Use soft delete pattern: set block.soft_deleted_at and call save()"
            )

    return MockBlockRepository()


# ============================================
# 5️⃣ SERVICE FIXTURES
# ============================================

@pytest.fixture
async def block_service(mock_block_repository):
    """
    BlockService with mock repository (for unit tests)

    Usage:
        async def test_create_block(block_service, sample_book_id):
            block = await block_service.create_block(
                book_id, BlockType.TEXT, "Content"
            )
    """
    from domains.block.service import BlockService
    return BlockService(repository=mock_block_repository)


# ============================================
# 6️⃣ ASSERTION HELPERS
# ============================================

@pytest.fixture
async def assert_block_fractional_index():
    """
    Helper to verify RULE-015-REVISED: Fractional Index ordering

    Ensures:
    - order values are valid Decimal/float
    - blocks are correctly ordered
    - can insert between any two blocks (O(1) operation)
    """
    async def _verify(blocks, repository):
        from decimal import Decimal

        # Verify order is valid Decimal
        for block in blocks:
            assert isinstance(block.order, (Decimal, float, int))

        # Verify blocks ordered by order
        orders = [float(b.order) for b in blocks]
        assert orders == sorted(orders), "Blocks not ordered by fractional index"

        # Verify insertion capability (fractional index property)
        if len(blocks) >= 2:
            block_a = blocks[0]
            block_b = blocks[1]
            # New order should fit between A and B
            new_order = (float(block_a.order) + float(block_b.order)) / 2.0
            assert float(block_a.order) < new_order < float(block_b.order), \
                "Cannot insert between blocks (fractional index failed)"

    return _verify


@pytest.fixture
async def assert_block_soft_deleted():
    """
    Helper to verify POLICY-008: Block soft delete

    Ensures:
    - get_by_id() returns None for soft-deleted blocks
    - get_deleted_blocks() can retrieve soft-deleted blocks
    - soft_deleted_at timestamp is set correctly
    """
    async def _verify(block_id: UUID, book_id: UUID, repository):
        # Soft-deleted block should not be visible via get_by_id()
        block = await repository.get_by_id(block_id)
        assert block is None, "Soft-deleted block should not be visible"

        # But should be retrievable via get_deleted_blocks()
        deleted = await repository.get_deleted_blocks(book_id)
        deleted_ids = [b.id for b in deleted]
        assert block_id in deleted_ids, "Soft-deleted block should be in deleted list"

    return _verify


@pytest.fixture
async def assert_heading_level_required():
    """
    Helper to verify RULE-013-REVISED: HEADING blocks need heading_level

    Ensures:
    - HEADING type blocks must have heading_level (1-3)
    - Non-HEADING blocks can have heading_level=None
    - Validation occurs at Repository level
    """
    async def _verify(repository):
        from domains.block.models import BlockModel, BlockType

        # HEADING block WITH heading_level (should succeed)
        heading_with_level = BlockModel(
            id=uuid4(),
            book_id=uuid4(),
            type=BlockType.HEADING,
            content="Title",
            order=Decimal('10.0'),
            heading_level=2,
        )
        await repository.save(heading_with_level)
        loaded = await repository.get_by_id(heading_with_level.id)
        assert loaded.heading_level == 2

        # HEADING block WITHOUT heading_level (should fail)
        heading_without_level = BlockModel(
            id=uuid4(),
            book_id=uuid4(),
            type=BlockType.HEADING,
            content="Title",
            order=Decimal('20.0'),
            heading_level=None,  # ← Missing!
        )
        with pytest.raises(ValueError):
            await repository.save(heading_without_level)

        # TEXT block with heading_level=None (should succeed)
        text_block = BlockModel(
            id=uuid4(),
            book_id=uuid4(),
            type=BlockType.TEXT,
            content="Text",
            order=Decimal('30.0'),
            heading_level=None,
        )
        await repository.save(text_block)
        loaded = await repository.get_by_id(text_block.id)
        assert loaded.heading_level is None

    return _verify
