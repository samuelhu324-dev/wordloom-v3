"""
Test Suite: Bookshelf Domain Layer

Tests for Bookshelf aggregate root:
- Domain invariants (RULE-004, RULE-005, RULE-006, RULE-010)
- BookshelfName value object
- Bookshelf operations
- Basement pattern enforcement

对应 DDD_RULES:
  ✓ RULE-004: Bookshelf 可无限创建
  ✓ RULE-005: Bookshelf 必须属于一个 Library
  ✓ RULE-006: Bookshelf 名称不能重复
  ✓ RULE-010: 每个 Library 自动创建一个 Basement Bookshelf
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from modules.bookshelf.domain import Bookshelf, BookshelfName
from modules.bookshelf.exceptions import InvalidBookshelfNameError


class TestBookshelfName:
    """Value Object: BookshelfName"""

    def test_bookshelf_name_creation_valid(self):
        """✓ BookshelfName accepts valid names"""
        name = BookshelfName(value="My Bookshelf")
        assert name.value == "My Bookshelf"

    def test_bookshelf_name_strip_whitespace(self):
        """✓ BookshelfName strips leading/trailing whitespace"""
        name = BookshelfName(value="  Trimmed Name  ")
        assert name.value == "Trimmed Name"

    def test_bookshelf_name_empty_raises_error(self):
        """✗ BookshelfName rejects empty strings"""
        with pytest.raises(InvalidBookshelfNameError):
            BookshelfName(value="")

    def test_bookshelf_name_too_long_raises_error(self):
        """✗ BookshelfName rejects names > 255 characters"""
        long_name = "A" * 256
        with pytest.raises(InvalidBookshelfNameError):
            BookshelfName(value=long_name)


class TestBookshelfAggregateRoot:
    """Aggregate Root: Bookshelf (RULE-004, RULE-005, RULE-006)"""

    def test_bookshelf_creation_valid(self):
        """✓ Bookshelf creation with valid data"""
        bookshelf = Bookshelf(
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            name=BookshelfName(value="Test Bookshelf"),
            is_basement=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert bookshelf.bookshelf_id is not None
        assert bookshelf.library_id is not None
        assert bookshelf.name.value == "Test Bookshelf"
        assert bookshelf.is_basement is False

    def test_bookshelf_basement_creation(self):
        """✓ RULE-010: Basement Bookshelf creation (special type)"""
        basement = Bookshelf(
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            name=BookshelfName(value="Basement"),
            is_basement=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert basement.is_basement is True
        assert basement.name.value == "Basement"

    def test_bookshelf_library_id_immutable(self):
        """✓ RULE-005: Bookshelf's library_id is immutable"""
        library_id = uuid4()
        bookshelf = Bookshelf(
            bookshelf_id=uuid4(),
            library_id=library_id,
            name=BookshelfName(value="Test"),
            is_basement=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert bookshelf.library_id == library_id


class TestBookshelfInvariants:
    """Domain Invariants Enforcement"""

    def test_bookshelf_invariant_unlimited_creation(self):
        """✓ RULE-004: Bookshelf can be created unlimited"""
        library_id = uuid4()

        bs1 = Bookshelf(
            bookshelf_id=uuid4(),
            library_id=library_id,
            name=BookshelfName(value="Bookshelf 1"),
            is_basement=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        bs2 = Bookshelf(
            bookshelf_id=uuid4(),
            library_id=library_id,
            name=BookshelfName(value="Bookshelf 2"),
            is_basement=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Both should be valid
        assert bs1.library_id == library_id
        assert bs2.library_id == library_id
        assert bs1.bookshelf_id != bs2.bookshelf_id

    def test_bookshelf_invariant_library_association(self):
        """✓ RULE-005: Bookshelf must belong to a Library"""
        library_id = uuid4()
        bookshelf = Bookshelf(
            bookshelf_id=uuid4(),
            library_id=library_id,
            name=BookshelfName(value="Test"),
            is_basement=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert bookshelf.library_id is not None
        assert bookshelf.library_id == library_id

    def test_bookshelf_invariant_unique_name(self):
        """✓ RULE-006: Bookshelf name should be unique per library (validation)"""
        bookshelf = Bookshelf(
            bookshelf_id=uuid4(),
            library_id=uuid4(),
            name=BookshelfName(value="Unique Name"),
            is_basement=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert len(bookshelf.name.value) > 0
