"""
Block Test Fixtures - Domain Layer Tests

Provides domain object factories and test data for Block aggregate testing.

Note: Application/Infrastructure layer tests planned for Phase 2.6
"""

import pytest
from uuid import uuid4
from decimal import Decimal

from api.app.modules.block.domain import (
    Block,
    BlockType,
    BlockContent,
)


# ============================================================================
# Basic Fixtures
# ============================================================================

@pytest.fixture
def book_id():
    """Generate a test book UUID"""
    return uuid4()


@pytest.fixture
def block_id():
    """Generate a test block UUID"""
    return uuid4()


@pytest.fixture
def user_id():
    """Generate a test user UUID"""
    return uuid4()


# ============================================================================
# Domain Object Factories
# ============================================================================

@pytest.fixture
def text_block(book_id):
    """Factory: Create a TEXT block"""
    return Block.create(
        book_id=book_id,
        block_type=BlockType.TEXT,
        content="Sample text content",
        order=Decimal("10"),
    )


@pytest.fixture
def heading_block(book_id):
    """Factory: Create a HEADING block"""
    return Block.create(
        book_id=book_id,
        block_type=BlockType.HEADING,
        content="Section Title",
        order=Decimal("5"),
        heading_level=1,
    )


@pytest.fixture
def code_block(book_id):
    """Factory: Create a CODE block"""
    return Block.create(
        book_id=book_id,
        block_type=BlockType.CODE,
        content='def hello():\n    print("Hello")',
        order=Decimal("20"),
    )


@pytest.fixture
def image_block(book_id):
    """Factory: Create an IMAGE block"""
    return Block.create(
        book_id=book_id,
        block_type=BlockType.IMAGE,
        content="https://example.com/image.jpg",
        order=Decimal("15"),
    )


@pytest.fixture
def quote_block(book_id):
    """Factory: Create a QUOTE block"""
    return Block.create(
        book_id=book_id,
        block_type=BlockType.QUOTE,
        content="To be or not to be",
        order=Decimal("25"),
    )


@pytest.fixture
def list_block(book_id):
    """Factory: Create a LIST block"""
    return Block.create(
        book_id=book_id,
        block_type=BlockType.LIST,
        content="- Item 1\n- Item 2\n- Item 3",
        order=Decimal("30"),
    )


@pytest.fixture
def table_block(book_id):
    """Factory: Create a TABLE block"""
    return Block.create(
        book_id=book_id,
        block_type=BlockType.TABLE,
        content="|Col1|Col2|\n|---|---|\n|A|B|",
        order=Decimal("35"),
    )


@pytest.fixture
def divider_block(book_id):
    """Factory: Create a DIVIDER block"""
    return Block.create(
        book_id=book_id,
        block_type=BlockType.DIVIDER,
        content="---",
        order=Decimal("40"),
    )


# ============================================================================
# Test Data
# ============================================================================

@pytest.fixture
def fractional_indices():
    """Pre-calculated Fractional Index values"""
    return {
        "start": Decimal("0"),
        "first": Decimal("1"),
        "mid": Decimal("1.5"),
        "second": Decimal("2"),
        "large": Decimal("1000000"),
    }


@pytest.fixture
def paperballs_recovery_context():
    """Paperballs 3-level recovery test data"""
    return {
        "deleted_prev_id": uuid4(),
        "deleted_next_id": uuid4(),
        "deleted_section_path": "/chapter-1/section-2",
    }


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Register custom pytest markers"""
    config.addinivalue_line(
        "markers",
        "domain: Block domain layer unit tests"
    )
    config.addinivalue_line(
        "markers",
        "paperballs: Paperballs 3-level recovery tests"
    )
    config.addinivalue_line(
        "markers",
        "fractional_index: Fractional Index ordering tests"
    )

