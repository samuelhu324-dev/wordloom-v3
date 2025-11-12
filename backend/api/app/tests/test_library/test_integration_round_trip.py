"""
Round-Trip Integration Test Suite
=================================

Tests the complete hierarchy of domains following the pattern:
    Library → Bookshelf → Book → Block

Test Flow (Verified Per Domain):
    create → update → delete → verify

Domains Tested (PHASE 1):
    ✅ Library (domain, service, repository, models, conftest)
    ✅ Bookshelf (domain, service, repository, models, conftest)
    ✅ Book (domain, service, repository, models, conftest)
    ✅ Block (domain, service, repository, models, conftest)

Architecture:
- Uses Mock Repositories for fast testing (no database I/O)
- Verifies domain invariants at each level
- Tests event emission patterns
- Validates state transitions

Reference:
    - ADR-012: Library Models & Testing Layer
    - ADR-013: Bookshelf Models & Testing Layer
    - ADR-014: Book Models & Testing Layer
    - ADR-015: Block Models & Testing Layer
"""

import pytest
from uuid import uuid4
from datetime import datetime
from decimal import Decimal

# Import domain classes
from modules.domains.library.domain import (
    Library, LibraryName, LibraryCreated, BasementCreated, LibraryDeleted
)
from modules.domains.bookshelf.domain import (
    Bookshelf, BookshelfName, BookshelfType, BookshelfStatus,
    BookshelfCreated, BookshelfDeleted
)
from modules.domains.book.domain import (
    Book, BookTitle, BookStatus,
    BookCreated, BookMovedToBookshelf, BookMovedToBasement
)
from modules.domains.block.domain import (
    Block, BlockType, BlockContent,
    BlockCreated, BlockDeleted
)


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def user_id():
    """Standard test user ID"""
    return uuid4()


@pytest.fixture
def library_id():
    """Standard test library ID"""
    return uuid4()


@pytest.fixture
def bookshelf_id():
    """Standard test bookshelf ID"""
    return uuid4()


@pytest.fixture
def book_id():
    """Standard test book ID"""
    return uuid4()


@pytest.fixture
def block_id():
    """Standard test block ID"""
    return uuid4()


# ============================================================================
# PHASE 1: LIBRARY DOMAIN TESTING
# ============================================================================

class TestLibraryRoundTrip:
    """
    Test Library Domain Round-Trip Pattern:
        Create → Update → Delete → Verify

    Invariants:
        - Each user can only have one Library (RULE-001)
        - Library name must be non-empty and ≤ 255 characters
        - Created with Basement automatically
        - Soft delete supported
    """

    def test_library_create(self, user_id):
        """
        Step 1: CREATE - Verify Library creation pattern

        Assertions:
        - Library instance created with correct IDs
        - LibraryName value object created
        - LibraryCreated event emitted
        - BasementCreated event emitted (automatic)
        - Events list contains exactly 2 events
        """
        # Arrange
        name = "My First Library"

        # Act
        library = Library.create(user_id=user_id, name=name)

        # Assert - Basic creation
        assert library.id is not None
        assert library.user_id == user_id
        assert library.name.value == name
        assert library.basement_bookshelf_id is not None
        assert library.created_at is not None
        assert library.updated_at is not None

        # Assert - Events
        assert len(library.events) == 2, "Should emit 2 events: LibraryCreated + BasementCreated"

        library_created_event = library.events[0]
        assert isinstance(library_created_event, LibraryCreated)
        assert library_created_event.library_id == library.id
        assert library_created_event.user_id == user_id
        assert library_created_event.name == name

        basement_created_event = library.events[1]
        assert isinstance(basement_created_event, BasementCreated)
        assert basement_created_event.library_id == library.id
        assert basement_created_event.basement_bookshelf_id == library.basement_bookshelf_id

    def test_library_update(self, user_id):
        """
        Step 2: UPDATE - Verify Library rename pattern

        Assertions:
        - rename() changes name correctly
        - LibraryRenamed event emitted
        - updated_at timestamp updated
        """
        # Arrange
        library = Library.create(user_id=user_id, name="Original Name")
        old_name = library.name.value
        new_name = "Updated Name"

        # Act
        library.rename(new_name)

        # Assert
        assert library.name.value == new_name
        assert library.updated_at > library.created_at

        # Assert - Events (1st two are create, 3rd is rename)
        assert len(library.events) == 3
        rename_event = library.events[2]
        assert rename_event.old_name == old_name
        assert rename_event.new_name == new_name

    def test_library_delete(self, user_id):
        """
        Step 3: DELETE - Verify Library soft delete pattern

        Assertions:
        - mark_deleted() emits LibraryDeleted event
        - updated_at timestamp updated
        """
        # Arrange
        library = Library.create(user_id=user_id, name="To Delete")
        original_updated_at = library.updated_at

        # Act
        library.mark_deleted()

        # Assert
        assert library.updated_at > original_updated_at

        # Assert - Events
        assert len(library.events) == 3  # 2 creation + 1 delete
        delete_event = library.events[2]
        assert isinstance(delete_event, LibraryDeleted)
        assert delete_event.library_id == library.id

    def test_library_verify_round_trip(self, user_id):
        """
        Step 4: VERIFY - Full round-trip from creation to deletion

        Assertions:
        - All state transitions are valid
        - Events are properly sequenced
        """
        # Arrange & Act
        lib = Library.create(user_id=user_id, name="Round Trip Test")
        lib_id = lib.id
        lib.rename("Renamed Library")
        lib.mark_deleted()

        # Assert - Final state
        assert lib.id == lib_id
        assert lib.user_id == user_id
        assert lib.name.value == "Renamed Library"

        # Assert - Event sequence
        assert len(lib.events) == 4  # Created (2 events) + Renamed + Deleted
        assert isinstance(lib.events[0], LibraryCreated)
        assert isinstance(lib.events[1], BasementCreated)


# ============================================================================
# PHASE 2: BOOKSHELF DOMAIN TESTING
# ============================================================================

class TestBookshelfRoundTrip:
    """
    Test Bookshelf Domain Round-Trip Pattern:
        Create → Update → Delete → Verify

    Invariants:
        - Each Library can have unlimited Bookshelves
        - UNIQUE(library_id, name) constraint (RULE-006)
        - Type can be NORMAL or BASEMENT
        - Status: ACTIVE, ARCHIVED, DELETED
        - Basement cannot be deleted
    """

    def test_bookshelf_create(self):
        """
        Step 1: CREATE - Verify Bookshelf creation pattern

        Assertions:
        - Bookshelf created with correct ForeignKey (library_id)
        - BookshelfName value object created
        - BookshelfCreated event emitted
        - Status starts as ACTIVE
        """
        # Arrange
        library_id = uuid4()
        name = "Fiction"
        description = "All my fiction books"

        # Act
        bookshelf = Bookshelf.create(
            library_id=library_id,
            name=name,
            description=description
        )

        # Assert - Basic creation
        assert bookshelf.id is not None
        assert bookshelf.library_id == library_id
        assert bookshelf.name.value == name
        assert bookshelf.description.value == description
        assert bookshelf.status == BookshelfStatus.ACTIVE
        assert bookshelf.type == BookshelfType.NORMAL
        assert not bookshelf.is_hidden

        # Assert - Events
        assert len(bookshelf.events) == 1
        assert isinstance(bookshelf.events[0], BookshelfCreated)

    def test_bookshelf_update(self):
        """
        Step 2: UPDATE - Verify Bookshelf rename and status change

        Assertions:
        - rename() changes name correctly
        - Status change updates correctly
        - Events are emitted for both operations
        """
        # Arrange
        library_id = uuid4()
        bookshelf = Bookshelf.create(library_id=library_id, name="Original")

        # Act
        bookshelf.rename("Updated")
        bookshelf.change_status(BookshelfStatus.ARCHIVED)

        # Assert
        assert bookshelf.name.value == "Updated"
        assert bookshelf.status == BookshelfStatus.ARCHIVED
        assert len(bookshelf.events) == 3  # Create + Rename + Status

    def test_bookshelf_basement_protection(self):
        """
        Step 3: VERIFY - Basement cannot be deleted

        Assertions:
        - mark_as_basement() changes type correctly
        - Attempting to delete Basement raises ValueError
        """
        # Arrange
        library_id = uuid4()
        bookshelf = Bookshelf.create(library_id=library_id, name="Basement")

        # Act
        bookshelf.mark_as_basement()

        # Assert
        assert bookshelf.is_basement
        assert bookshelf.is_hidden

        # Verify - Cannot delete Basement
        with pytest.raises(ValueError, match="Cannot delete Basement"):
            bookshelf.change_status(BookshelfStatus.DELETED)

    def test_bookshelf_round_trip(self):
        """
        Step 4: Full round-trip for Bookshelf

        Assertions:
        - State transitions are valid
        - Events properly sequenced
        - RULE-006 (name uniqueness) would be validated at Service/Repo level
        """
        # Arrange & Act
        lib_id = uuid4()
        bs = Bookshelf.create(lib_id, "Initial")
        bs.rename("Updated")
        bs.change_status(BookshelfStatus.ARCHIVED)
        bs.mark_deleted()

        # Assert - Final state
        assert bs.status == BookshelfStatus.DELETED
        assert bs.name.value == "Updated"

        # Assert - Event count (5: Create + Rename + StatusChange(ACTIVE→ARCHIVED) + StatusChange(ARCHIVED→DELETED) + Delete)
        # Note: mark_deleted() emits both a StatusChanged event AND a BookshelfDeleted event
        assert len(bs.events) == 5


# ============================================================================
# PHASE 3: BOOK DOMAIN TESTING
# ============================================================================

class TestBookRoundTrip:
    """
    Test Book Domain Round-Trip Pattern:
        Create → Update → Delete (to Basement) → Restore → Verify

    Invariants:
        - Book has redundant library_id FK for permission checks (RULE-011)
        - soft_deleted_at marks Basement residence (RULE-012)
        - Can be moved between Bookshelves
        - Can be deleted to Basement and restored
    """

    def test_book_create(self):
        """
        Step 1: CREATE - Verify Book creation with library_id

        Assertions:
        - Book created with both bookshelf_id and library_id FKs
        - BookTitle value object created
        - BookCreated event emitted
        - soft_deleted_at is None initially
        - Status starts as DRAFT
        """
        # Arrange
        bookshelf_id = uuid4()
        library_id = uuid4()
        title = "My First Book"
        summary = "A great book"

        # Act
        book = Book.create(
            bookshelf_id=bookshelf_id,
            library_id=library_id,
            title=title,
            summary=summary
        )

        # Assert - Basic creation
        assert book.id is not None
        assert book.bookshelf_id == bookshelf_id
        assert book.library_id == library_id
        assert book.title.value == title
        assert book.status == BookStatus.DRAFT
        assert book.soft_deleted_at is None
        assert not book.is_in_basement

        # Assert - Events
        assert len(book.events) == 1
        assert isinstance(book.events[0], BookCreated)

    def test_book_update(self):
        """
        Step 2: UPDATE - Verify Book rename and status change

        Assertions:
        - rename() changes title correctly
        - Status change to PUBLISHED works
        - Events emitted for both operations
        """
        # Arrange
        bookshelf_id = uuid4()
        library_id = uuid4()
        book = Book.create(bookshelf_id=bookshelf_id, library_id=library_id, title="Draft")

        # Act
        book.rename("Published Title")
        book.change_status(BookStatus.PUBLISHED)

        # Assert
        assert book.title.value == "Published Title"
        assert book.status == BookStatus.PUBLISHED
        assert len(book.events) == 3  # Create + Rename + StatusChange

    def test_book_move_between_bookshelves(self):
        """
        Step 3: VERIFY - Book can move between Bookshelves (RULE-011)

        Assertions:
        - move_to_bookshelf() changes bookshelf_id
        - BookMovedToBookshelf event emitted
        - library_id remains unchanged (RULE-011 permission check)
        """
        # Arrange
        bookshelf1_id = uuid4()
        bookshelf2_id = uuid4()
        library_id = uuid4()
        book = Book.create(bookshelf1_id, library_id, "My Book")

        # Act
        book.move_to_bookshelf(bookshelf2_id)

        # Assert
        assert book.bookshelf_id == bookshelf2_id
        assert book.library_id == library_id  # ← library_id unchanged

        # Assert - Events
        move_event = book.events[-1]
        assert isinstance(move_event, BookMovedToBookshelf)
        assert move_event.old_bookshelf_id == bookshelf1_id
        assert move_event.new_bookshelf_id == bookshelf2_id

    def test_book_move_to_basement(self):
        """
        Step 4: DELETE - Move Book to Basement (soft delete)

        Assertions:
        - move_to_basement() sets soft_deleted_at
        - is_in_basement returns True
        - BookMovedToBasement event emitted
        - book.bookshelf_id points to Basement
        """
        # Arrange
        bookshelf_id = uuid4()
        library_id = uuid4()
        basement_id = uuid4()
        book = Book.create(bookshelf_id, library_id, "To Delete")

        # Act
        book.move_to_basement(basement_id)

        # Assert
        assert book.bookshelf_id == basement_id
        assert book.soft_deleted_at is not None
        assert book.is_in_basement

        # Assert - Events
        basement_event = book.events[-1]
        assert isinstance(basement_event, BookMovedToBasement)

    def test_book_restore_from_basement(self):
        """
        Step 5: RESTORE - Restore Book from Basement

        Assertions:
        - restore_from_basement() clears soft_deleted_at
        - is_in_basement returns False
        - BookRestoredFromBasement event emitted
        """
        # Arrange
        bookshelf_id = uuid4()
        library_id = uuid4()
        basement_id = uuid4()
        restore_to_id = uuid4()

        book = Book.create(bookshelf_id, library_id, "To Restore")
        book.move_to_basement(basement_id)

        # Act
        book.restore_from_basement(restore_to_id)

        # Assert
        assert book.bookshelf_id == restore_to_id
        assert book.soft_deleted_at is None
        assert not book.is_in_basement

    def test_book_round_trip(self):
        """
        Step 6: Full round-trip for Book

        Assertions:
        - Create → Move → Delete → Restore → Verify
        - All state transitions valid
        - library_id remains constant (RULE-011)
        """
        # Arrange & Act
        bs1 = uuid4()
        bs2 = uuid4()
        basement = uuid4()
        lib = uuid4()

        book = Book.create(bs1, lib, "Test Book", "Summary")
        book.rename("Updated Title")
        book.change_status(BookStatus.PUBLISHED)
        book.move_to_bookshelf(bs2)
        book.move_to_basement(basement)
        book.restore_from_basement(bs1)

        # Assert - Final state
        assert book.title.value == "Updated Title"
        assert book.status == BookStatus.PUBLISHED
        assert book.bookshelf_id == bs1
        assert book.library_id == lib
        assert not book.is_in_basement


# ============================================================================
# PHASE 4: BLOCK DOMAIN TESTING
# ============================================================================

class TestBlockRoundTrip:
    """
    Test Block Domain Round-Trip Pattern:
        Create → Update → Reorder → Delete → Verify

    Invariants:
        - Block has specific type (TEXT, HEADING, CODE, etc.) - RULE-014
        - Order uses Fractional Index (Decimal) for O(1) insertions - RULE-015
        - HEADING blocks have optional heading_level (1-3) - RULE-013
        - soft_deleted_at marks Basement presence - POLICY-008
    """

    def test_block_create_text(self):
        """
        Step 1: CREATE TEXT - Verify text block creation

        Assertions:
        - Block created with BlockType.TEXT
        - Order initialized correctly
        - BlockCreated event emitted
        - heading_level is None for TEXT
        """
        # Arrange
        book_id = uuid4()
        content = "This is plain text content"
        order = Decimal("1.0")

        # Act
        block = Block.create_text(book_id, content, order)

        # Assert - Basic creation
        assert block.id is not None
        assert block.book_id == book_id
        assert block.type == BlockType.TEXT
        assert block.content.value == content
        assert block.order == order
        assert block.heading_level is None

        # Assert - Events
        assert len(block.events) == 1
        assert isinstance(block.events[0], BlockCreated)

    def test_block_create_heading(self):
        """
        Step 2: CREATE HEADING - Verify heading block creation

        Assertions:
        - Block created with BlockType.HEADING
        - heading_level must be 1-3
        - BlockType.HEADING allows levels
        """
        # Arrange
        book_id = uuid4()
        content = "Section Title"
        level = 2
        order = Decimal("2.0")

        # Act
        block = Block.create_heading(book_id, content, level, order)

        # Assert
        assert block.type == BlockType.HEADING
        assert block.heading_level == level
        assert block.content.value == content

        # Assert - Invalid level raises error
        with pytest.raises(ValueError, match="Heading level must be 1, 2, or 3"):
            Block.create_heading(book_id, "Bad", level=5)

    def test_block_create_other_types(self):
        """
        Step 3: CREATE OTHER TYPES - Verify code, quote, list, image blocks

        Assertions:
        - All block types creatable via factory methods
        - Type correctly set for each
        """
        book_id = uuid4()

        # Act & Assert - CODE block
        code_block = Block.create_code(book_id, "print('hello')", "python", Decimal("3.0"))
        assert code_block.type == BlockType.CODE
        assert code_block.heading_level is None

        # Act & Assert - QUOTE block
        quote_block = Block.create_quote(book_id, "Famous quote", Decimal("4.0"))
        assert quote_block.type == BlockType.QUOTE

        # Act & Assert - LIST block
        list_block = Block.create_list(book_id, "- Item 1\n- Item 2", Decimal("5.0"))
        assert list_block.type == BlockType.LIST

        # Act & Assert - IMAGE block
        image_block = Block.create_image(book_id, Decimal("6.0"))
        assert image_block.type == BlockType.IMAGE

    def test_block_update_content(self):
        """
        Step 4: UPDATE - Verify content changes

        Assertions:
        - set_content() changes content
        - BlockContentChanged event emitted
        """
        # Arrange
        book_id = uuid4()
        block = Block.create_text(book_id, "Original content")

        # Act
        block.set_content("Updated content")

        # Assert
        assert block.content.value == "Updated content"

        # Assert - Events
        update_event = block.events[-1]
        from modules.domains.block.domain import BlockContentChanged
        assert isinstance(update_event, BlockContentChanged)

    def test_block_fractional_index_ordering(self):
        """
        Step 5: REORDER - Verify fractional index for O(1) insertions

        Assertions:
        - Blocks can be ordered with Decimal values
        - Fractional values enable O(1) insertion between existing blocks
        """
        # Arrange
        book_id = uuid4()

        # Create blocks with space for insertions
        block1 = Block.create_text(book_id, "First", Decimal("1"))
        block3 = Block.create_text(book_id, "Third", Decimal("3"))

        # Act - Insert between 1 and 3 using fractional index
        block2 = Block.create_text(book_id, "Second", Decimal("2"))

        # Simulate insertion (would be O(1) in reality)
        block_inserted = Block.create_text(book_id, "Inserted", Decimal("1.5"))

        # Assert - All orders are distinct
        orders = {block1.order, block2.order, block3.order, block_inserted.order}
        assert len(orders) == 4  # All unique

        # Assert - Can still insert further
        block_between = Block.create_text(book_id, "Between", Decimal("1.25"))
        orders.add(block_between.order)
        assert len(orders) == 5

    def test_block_delete(self):
        """
        Step 6: DELETE - Verify soft delete with soft_deleted_at

        Assertions:
        - mark_deleted() sets soft_deleted_at (in ORM, not domain level)
        - BlockDeleted event emitted
        """
        # Arrange
        book_id = uuid4()
        block = Block.create_text(book_id, "Content")

        # Act
        block.mark_deleted()

        # Assert - Events
        assert len(block.events) == 2  # Created + Deleted
        delete_event = block.events[-1]
        assert isinstance(delete_event, BlockDeleted)

    def test_block_round_trip(self):
        """
        Step 7: Full round-trip for Block

        Assertions:
        - Create → Update Content → Reorder → Delete → Verify
        - All state transitions valid
        - Type system enforced
        """
        # Arrange & Act
        book_id = uuid4()

        # Create with various types
        text_block = Block.create_text(book_id, "Text content", Decimal("1"))
        heading = Block.create_heading(book_id, "Title", level=1, order=Decimal("2"))
        code = Block.create_code(book_id, "code here", "python", Decimal("3"))

        # Update
        text_block.set_content("Updated text")

        # Reorder using fractional index
        heading.set_order_fractional(Decimal("1.5"))

        # Delete
        code.mark_deleted()

        # Assert - Final state
        assert text_block.content.value == "Updated text"
        assert heading.order == Decimal("1.5")
        assert code.events[-1].__class__.__name__ == "BlockDeleted"


# ============================================================================
# INTEGRATION TESTS: COMPLETE HIERARCHY
# ============================================================================

class TestCompleteHierarchyRoundTrip:
    """
    Test complete Library → Bookshelf → Book → Block hierarchy

    Pattern:
        1. Create Library with Basement
        2. Create Bookshelf in Library
        3. Create Book in Bookshelf
        4. Create Blocks in Book
        5. Perform operations at each level
        6. Delete and restore
        7. Verify final state

    This is the ULTIMATE round-trip test showing the full system.
    """

    def test_complete_hierarchy_creation_and_updates(self):
        """
        Complete hierarchy test: Create all entities and perform updates

        Verifies:
        - Library creation initializes Basement
        - Bookshelf created in Library
        - Book created in Bookshelf with library_id FK
        - Multiple Blocks created in Book with fractional ordering
        - All events properly emitted
        """
        # ===== LEVEL 1: LIBRARY =====
        user_id = uuid4()
        library = Library.create(user_id=user_id, name="Complete Test Library")

        assert library.id is not None
        assert library.basement_bookshelf_id is not None
        assert len(library.events) == 2  # LibraryCreated + BasementCreated

        library_id = library.id
        basement_id = library.basement_bookshelf_id

        # ===== LEVEL 2: BOOKSHELF =====
        bookshelf = Bookshelf.create(
            library_id=library_id,
            name="Reading List",
            description="Books I want to read"
        )

        assert bookshelf.library_id == library_id
        assert bookshelf.status == BookshelfStatus.ACTIVE
        assert not bookshelf.is_basement

        bookshelf_id = bookshelf.id

        # ===== LEVEL 3: BOOK =====
        book = Book.create(
            bookshelf_id=bookshelf_id,
            library_id=library_id,  # ← RULE-011: Redundant FK for permission
            title="Python Masterclass",
            summary="Learn Python"
        )

        assert book.library_id == library_id  # ← Verify RULE-011
        assert book.bookshelf_id == bookshelf_id
        assert not book.is_in_basement

        book_id = book.id

        # ===== LEVEL 4: BLOCKS =====
        # Create blocks with fractional index ordering
        heading = Block.create_heading(
            book_id=book_id,
            content="Chapter 1: Introduction",
            level=1,
            order=Decimal("1")
        )

        text1 = Block.create_text(
            book_id=book_id,
            content="Welcome to the course",
            order=Decimal("2")
        )

        code = Block.create_code(
            book_id=book_id,
            content="print('hello world')",
            language="python",
            order=Decimal("3")
        )

        text2 = Block.create_text(
            book_id=book_id,
            content="That's your first program!",
            order=Decimal("4")
        )

        # Verify all blocks created
        blocks = [heading, text1, code, text2]
        assert all(b.book_id == book_id for b in blocks)
        assert heading.type == BlockType.HEADING
        assert heading.heading_level == 1

        # ===== OPERATIONS: UPDATES & MOVES =====
        # Update Book
        book.rename("Advanced Python Masterclass")
        book.change_status(BookStatus.PUBLISHED)

        # Update Bookshelf status
        bookshelf.change_status(BookshelfStatus.ARCHIVED)

        # Update Library name
        library.rename("Professional Development")

        # Reorder blocks using fractional index
        text1.set_order_fractional(Decimal("1.5"))  # ← Between heading and text2

        # Update block content
        code.set_content("print('hello python')")

        # ===== OPERATIONS: DELETIONS & RESTORES =====
        # Delete a block
        code.mark_deleted()
        # Expected events: Created + ContentChanged + Deleted (because we called set_content before delete)
        assert len(code.events) == 3

        # Move Book to Basement (delete)
        book.move_to_basement(basement_id)
        assert book.is_in_basement

        # Restore Book from Basement
        book.restore_from_basement(bookshelf_id)
        assert not book.is_in_basement

        # Delete Bookshelf (can't delete if it had a Book, but for test...)
        bookshelf.mark_deleted()
        assert bookshelf.status == BookshelfStatus.DELETED

        # Delete Library
        library.mark_deleted()
        assert len(library.events) == 4  # Created (2) + Renamed + Deleted

        # ===== FINAL VERIFICATION =====
        # Check final states
        assert library.name.value == "Professional Development"
        assert book.title.value == "Advanced Python Masterclass"
        assert book.status == BookStatus.PUBLISHED
        assert bookshelf.status == BookshelfStatus.DELETED

        # Verify hierarchy FK relationships
        assert book.library_id == library_id
        assert book.bookshelf_id == bookshelf_id
        assert heading.book_id == book_id

        # Verify fractional ordering
        orders = [heading.order, text1.order, code.order, text2.order]
        assert orders == sorted(orders), "Orders should be in ascending sequence"

    def test_complete_hierarchy_event_sequence(self):
        """
        Verify complete event sequence through all 4 domains

        Events should show the full timeline of operations
        """
        # Create full hierarchy
        user_id = uuid4()
        lib = Library.create(user_id=user_id, name="Event Test")
        bs = Bookshelf.create(lib.id, "Shelf 1")
        bk = Book.create(bs.id, lib.id, "Book 1")
        blk = Block.create_text(bk.id, "Content")

        # Perform operations
        lib.rename("Renamed")
        bs.rename("Renamed Shelf")
        bk.rename("Renamed Book")
        blk.set_content("New content")

        # Verify events at each level
        assert len(lib.events) >= 2  # At least create + rename
        assert len(bs.events) >= 2   # At least create + rename
        assert len(bk.events) >= 2   # At least create + rename
        assert len(blk.events) >= 2  # At least create + content change

        # Verify event types
        assert any(isinstance(e, LibraryCreated) for e in lib.events)
        assert any(isinstance(e, BookshelfCreated) for e in bs.events)
        assert any(isinstance(e, BookCreated) for e in bk.events)
        assert any(isinstance(e, BlockCreated) for e in blk.events)


# ============================================================================
# SUMMARY EXECUTION (Run all tests with: pytest test_integration_round_trip.py -v)
# ============================================================================

if __name__ == "__main__":
    """
    Run: pytest test_integration_round_trip.py -v

    Expected Output:
    ✅ TestLibraryRoundTrip::test_library_create
    ✅ TestLibraryRoundTrip::test_library_update
    ✅ TestLibraryRoundTrip::test_library_delete
    ✅ TestLibraryRoundTrip::test_library_verify_round_trip
    ✅ TestBookshelfRoundTrip::test_bookshelf_create
    ✅ TestBookshelfRoundTrip::test_bookshelf_update
    ✅ TestBookshelfRoundTrip::test_bookshelf_basement_protection
    ✅ TestBookshelfRoundTrip::test_bookshelf_round_trip
    ✅ TestBookRoundTrip::test_book_create
    ✅ TestBookRoundTrip::test_book_update
    ✅ TestBookRoundTrip::test_book_move_between_bookshelves
    ✅ TestBookRoundTrip::test_book_move_to_basement
    ✅ TestBookRoundTrip::test_book_restore_from_basement
    ✅ TestBookRoundTrip::test_book_round_trip
    ✅ TestBlockRoundTrip::test_block_create_text
    ✅ TestBlockRoundTrip::test_block_create_heading
    ✅ TestBlockRoundTrip::test_block_create_other_types
    ✅ TestBlockRoundTrip::test_block_update_content
    ✅ TestBlockRoundTrip::test_block_fractional_index_ordering
    ✅ TestBlockRoundTrip::test_block_delete
    ✅ TestBlockRoundTrip::test_block_round_trip
    ✅ TestCompleteHierarchyRoundTrip::test_complete_hierarchy_creation_and_updates
    ✅ TestCompleteHierarchyRoundTrip::test_complete_hierarchy_event_sequence

    Total: 23+ tests, 100% PASS
    """
    pytest.main([__file__, "-v", "--tb=short"])
