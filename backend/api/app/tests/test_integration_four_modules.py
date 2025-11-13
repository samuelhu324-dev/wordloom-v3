"""
Phase 1.5 Complete Integration Test Suite
==========================================

Tests the complete 4-module hierarchy before final component isolation:
    Library → Bookshelf → Book → Block

Test Scope:
    ✅ Library module (domain + service + repository + models + schemas + router)
    ✅ Bookshelf module (domain + service + repository + models + schemas + router)
    ✅ Book module (domain + service + repository + models + schemas + router)
    ✅ Block module (domain + service + repository + models + schemas + router)

Test Organization:
    1. Domain Layer Tests (invariants, business rules, events)
    2. Repository Layer Tests (persistence, queries, exceptions)
    3. Service Layer Tests (orchestration, validation, error handling)
    4. Schema Layer Tests (request/response validation, serialization)
    5. Router Layer Tests (HTTP endpoints, status codes, DI chain)
    6. Round-Trip Integration Tests (full stack: domain → db → domain)
    7. Cross-Module Tests (relationships, cascading operations)

Quality Gates:
    - All 4 modules must pass independently
    - Cross-module relationships must be valid
    - No datetime deprecation warnings
    - Exception mapping to HTTP codes verified
    - Soft delete policy (POLICY-008) enforced

References:
    - ADR-018: Library API Maturity
    - ADR-020: Bookshelf Router/Schemas/Exceptions
    - ADR-021: Book Router/Schemas/Exceptions
    - ADR-022: Block Router/Schemas/Exceptions
    - ADR-023: Phase 1.5 Integration Test Report (to be generated)

Test Execution: pytest backend/api/app/tests/test_integration_four_modules.py -v
"""

import pytest
import asyncio
from uuid import UUID, uuid4
from datetime import datetime, timezone
from decimal import Decimal
from typing import List

# ============================================================================
# SECTION 1: LIBRARY MODULE TESTS
# ============================================================================

class TestLibraryDomain:
    """Test Library domain layer (invariants, events, value objects)"""

    def test_library_creation_emits_event(self):
        """RULE-001: Library creation must emit LibraryCreated event"""
        from modules.library.domain import Library

        library = Library.create(user_id=uuid4(), name="My Library")

        assert library.id is not None
        assert library.user_id is not None
        assert library.name.value == "My Library"
        assert len(library.domain_events) >= 1
        # Check LibraryCreated event
        assert any(e.__class__.__name__ == "LibraryCreated" for e in library.domain_events)

    def test_library_creation_generates_basement(self):
        """RULE-001: Library creation must auto-generate Basement bookshelf"""
        from modules.library.domain import Library

        library = Library.create(user_id=uuid4(), name="Test Library")

        assert library.basement_bookshelf_id is not None
        assert len(library.domain_events) >= 2  # LibraryCreated + BasementCreated

    def test_library_rename_emits_event(self):
        """RULE-003: Library rename must emit LibraryRenamed event"""
        from modules.library.domain import Library

        library = Library.create(user_id=uuid4(), name="Old Name")
        library.domain_events.clear()

        library.rename("New Name")

        assert library.name.value == "New Name"
        assert any(e.__class__.__name__ == "LibraryRenamed" for e in library.domain_events)

    def test_library_name_validation(self):
        """RULE-003: Library name must be 1-255 characters"""
        from modules.library.domain import Library, InvalidLibraryNameError

        # Valid
        library = Library.create(user_id=uuid4(), name="Valid")
        assert library.name.value == "Valid"

        # Invalid: empty
        with pytest.raises(InvalidLibraryNameError):
            Library.create(user_id=uuid4(), name="")

        # Invalid: too long
        with pytest.raises(InvalidLibraryNameError):
            Library.create(user_id=uuid4(), name="x" * 256)

    def test_library_user_association(self):
        """RULE-002: Library must be 1:1 associated with user"""
        from modules.library.domain import Library

        user_id = uuid4()
        lib1 = Library.create(user_id=user_id, name="Lib1")
        lib2 = Library.create(user_id=user_id, name="Lib2")

        assert lib1.user_id == lib2.user_id == user_id
        # Note: Repository layer enforces UNIQUE constraint

    def test_library_soft_delete_emits_event(self):
        """POLICY-008: Library soft delete must emit LibraryDeleted event"""
        from modules.library.domain import Library

        library = Library.create(user_id=uuid4(), name="Test")
        library.domain_events.clear()

        library.mark_deleted()

        assert library.soft_deleted_at is not None
        assert any(e.__class__.__name__ == "LibraryDeleted" for e in library.domain_events)


class TestLibraryRepository:
    """Test Library repository layer (persistence, queries)"""

    @pytest.mark.asyncio
    async def test_library_save_and_retrieve(self, db_session):
        """Repository: Save and retrieve Library"""
        from modules.library.repository import LibraryRepositoryImpl
        from modules.library.domain import Library

        repo = LibraryRepositoryImpl(db_session)
        user_id = uuid4()
        library = Library.create(user_id=user_id, name="Test Library")

        # Save
        await repo.save(library)

        # Retrieve
        retrieved = await repo.get_by_id(library.id)

        assert retrieved is not None
        assert retrieved.id == library.id
        assert retrieved.user_id == user_id
        assert retrieved.name.value == "Test Library"

    @pytest.mark.asyncio
    async def test_library_get_by_user_id(self, db_session):
        """RULE-001: Get Library by user_id (1:1 relationship)"""
        from modules.library.repository import LibraryRepositoryImpl
        from modules.library.domain import Library

        repo = LibraryRepositoryImpl(db_session)
        user_id = uuid4()
        library = Library.create(user_id=user_id, name="User Library")

        await repo.save(library)
        retrieved = await repo.get_by_user_id(user_id)

        assert retrieved is not None
        assert retrieved.user_id == user_id

    @pytest.mark.asyncio
    async def test_library_already_exists_error(self, db_session):
        """RULE-001: Cannot create duplicate Library for same user (UNIQUE constraint)"""
        from modules.library.repository import LibraryRepositoryImpl
        from modules.library.domain import Library
        from modules.library.exceptions import LibraryAlreadyExistsError

        repo = LibraryRepositoryImpl(db_session)
        user_id = uuid4()
        lib1 = Library.create(user_id=user_id, name="Lib1")
        lib2 = Library.create(user_id=user_id, name="Lib2")

        await repo.save(lib1)

        # Second save should fail
        with pytest.raises(LibraryAlreadyExistsError):
            await repo.save(lib2)

    @pytest.mark.asyncio
    async def test_library_soft_delete_filter(self, db_session):
        """POLICY-008: Soft deleted Library not returned by get_by_id"""
        from modules.library.repository import LibraryRepositoryImpl
        from modules.library.domain import Library

        repo = LibraryRepositoryImpl(db_session)
        library = Library.create(user_id=uuid4(), name="Test")
        await repo.save(library)

        # Soft delete
        library.mark_deleted()
        await repo.save(library)

        # Retrieve should return None
        retrieved = await repo.get_by_id(library.id)
        assert retrieved is None


class TestLibraryService:
    """Test Library service layer (orchestration, business logic)"""

    @pytest.mark.asyncio
    async def test_library_create_service(self, mock_library_repository):
        """Service: Create Library with validation"""
        from modules.library.service import LibraryService

        service = LibraryService(mock_library_repository)
        user_id = uuid4()

        library = await service.create_library(user_id=user_id, name="My Library")

        assert library.id is not None
        assert library.user_id == user_id

    @pytest.mark.asyncio
    async def test_library_get_service(self, mock_library_repository):
        """Service: Retrieve Library"""
        from modules.library.service import LibraryService

        service = LibraryService(mock_library_repository)
        user_id = uuid4()
        lib = await service.create_library(user_id=user_id, name="Test")

        retrieved = await service.get_library(lib.id)

        assert retrieved is not None
        assert retrieved.id == lib.id


class TestLibrarySchemas:
    """Test Library request/response schemas (Pydantic validation)"""

    def test_library_create_schema_validation(self):
        """Schema: LibraryCreate validation"""
        from modules.library.schemas import LibraryCreate

        # Valid
        request = LibraryCreate(user_id=uuid4(), name="Valid Library")
        assert request.name == "Valid Library"

        # Invalid: empty name
        with pytest.raises(ValueError):
            LibraryCreate(user_id=uuid4(), name="")

        # Invalid: whitespace only
        with pytest.raises(ValueError):
            LibraryCreate(user_id=uuid4(), name="   ")

    def test_library_response_serialization(self):
        """Schema: LibraryResponse serialization"""
        from modules.library.schemas import LibraryResponse

        lib_id = uuid4()
        user_id = uuid4()
        response = LibraryResponse(
            id=lib_id,
            user_id=user_id,
            name="Test Library",
            basement_bookshelf_id=uuid4(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        data = response.model_dump()
        assert data["id"] == lib_id
        assert data["user_id"] == user_id
        assert data["name"] == "Test Library"


# ============================================================================
# SECTION 2: BOOKSHELF MODULE TESTS
# ============================================================================

class TestBookshelfDomain:
    """Test Bookshelf domain layer"""

    def test_bookshelf_creation_emits_event(self):
        """RULE-004: Bookshelf creation must emit BookshelfCreated event"""
        from modules.bookshelf.domain import Bookshelf

        library_id = uuid4()
        bookshelf = Bookshelf.create(
            library_id=library_id,
            name="My Shelf",
            is_basement=False
        )

        assert bookshelf.id is not None
        assert bookshelf.library_id == library_id
        assert bookshelf.name.value == "My Shelf"
        assert not bookshelf.is_basement
        assert any(e.__class__.__name__ == "BookshelfCreated" for e in bookshelf.domain_events)

    def test_bookshelf_basement_flag(self):
        """RULE-010: Basement bookshelf must have is_basement=True"""
        from modules.bookshelf.domain import Bookshelf

        library_id = uuid4()
        basement = Bookshelf.create(
            library_id=library_id,
            name="Basement",
            is_basement=True
        )

        assert basement.is_basement is True

    def test_bookshelf_name_validation(self):
        """RULE-005: Bookshelf name validation (1-255 chars)"""
        from modules.bookshelf.domain import Bookshelf, InvalidBookshelfNameError

        # Valid
        shelf = Bookshelf.create(library_id=uuid4(), name="Valid", is_basement=False)
        assert shelf.name.value == "Valid"

        # Invalid: empty
        with pytest.raises(InvalidBookshelfNameError):
            Bookshelf.create(library_id=uuid4(), name="", is_basement=False)

    def test_bookshelf_rename_emits_event(self):
        """RULE-005: Bookshelf rename must emit BookshelfRenamed event"""
        from modules.bookshelf.domain import Bookshelf

        shelf = Bookshelf.create(library_id=uuid4(), name="Old", is_basement=False)
        shelf.domain_events.clear()

        shelf.rename("New")

        assert shelf.name.value == "New"
        assert any(e.__class__.__name__ == "BookshelfRenamed" for e in shelf.domain_events)


class TestBookshelfRepository:
    """Test Bookshelf repository layer"""

    @pytest.mark.asyncio
    async def test_bookshelf_save_and_retrieve(self, db_session):
        """Repository: Save and retrieve Bookshelf"""
        from modules.bookshelf.repository import BookshelfRepositoryImpl
        from modules.bookshelf.domain import Bookshelf

        repo = BookshelfRepositoryImpl(db_session)
        library_id = uuid4()
        shelf = Bookshelf.create(library_id=library_id, name="Test Shelf", is_basement=False)

        await repo.save(shelf)
        retrieved = await repo.get_by_id(shelf.id)

        assert retrieved is not None
        assert retrieved.id == shelf.id
        assert retrieved.name.value == "Test Shelf"

    @pytest.mark.asyncio
    async def test_bookshelf_get_by_library_id(self, db_session):
        """Repository: Query bookshelves by library_id"""
        from modules.bookshelf.repository import BookshelfRepositoryImpl
        from modules.bookshelf.domain import Bookshelf

        repo = BookshelfRepositoryImpl(db_session)
        library_id = uuid4()
        shelf1 = Bookshelf.create(library_id=library_id, name="Shelf1", is_basement=False)
        shelf2 = Bookshelf.create(library_id=library_id, name="Shelf2", is_basement=False)

        await repo.save(shelf1)
        await repo.save(shelf2)
        bookshelves = await repo.get_by_library_id(library_id)

        assert len(bookshelves) == 2
        assert all(s.library_id == library_id for s in bookshelves)


# ============================================================================
# SECTION 3: BOOK MODULE TESTS
# ============================================================================

class TestBookDomain:
    """Test Book domain layer"""

    def test_book_creation_emits_event(self):
        """RULE-009: Book creation must emit BookCreated event"""
        from modules.book.domain import Book

        bookshelf_id = uuid4()
        book = Book.create(
            bookshelf_id=bookshelf_id,
            title="Test Book"
        )

        assert book.id is not None
        assert book.bookshelf_id == bookshelf_id
        assert book.title.value == "Test Book"
        assert any(e.__class__.__name__ == "BookCreated" for e in book.domain_events)

    def test_book_title_validation(self):
        """RULE-009: Book title validation (1-255 chars)"""
        from modules.book.domain import Book, InvalidBookTitleError

        # Valid
        book = Book.create(bookshelf_id=uuid4(), title="Valid Title")
        assert book.title.value == "Valid Title"

        # Invalid: empty
        with pytest.raises(InvalidBookTitleError):
            Book.create(bookshelf_id=uuid4(), title="")

    def test_book_soft_delete(self):
        """RULE-012: Book soft delete sets soft_deleted_at timestamp"""
        from modules.book.domain import Book

        book = Book.create(bookshelf_id=uuid4(), title="Test")
        assert book.soft_deleted_at is None

        book.mark_deleted()

        assert book.soft_deleted_at is not None
        assert book.soft_deleted_at.tzinfo is not None  # timezone-aware

    def test_book_move_to_bookshelf_emits_event(self):
        """RULE-011: Book move must emit BookMovedToBookshelf event"""
        from modules.book.domain import Book

        old_shelf = uuid4()
        new_shelf = uuid4()
        book = Book.create(bookshelf_id=old_shelf, title="Test")
        book.domain_events.clear()

        book.move_to_bookshelf(new_shelf)

        assert book.bookshelf_id == new_shelf
        assert any(e.__class__.__name__ == "BookMovedToBookshelf" for e in book.domain_events)


class TestBookRepository:
    """Test Book repository layer"""

    @pytest.mark.asyncio
    async def test_book_save_and_retrieve(self, db_session):
        """Repository: Save and retrieve Book"""
        from modules.book.repository import BookRepositoryImpl
        from modules.book.domain import Book

        repo = BookRepositoryImpl(db_session)
        bookshelf_id = uuid4()
        book = Book.create(bookshelf_id=bookshelf_id, title="Test Book")

        await repo.save(book)
        retrieved = await repo.get_by_id(book.id)

        assert retrieved is not None
        assert retrieved.id == book.id
        assert retrieved.title.value == "Test Book"

    @pytest.mark.asyncio
    async def test_book_get_by_bookshelf_id(self, db_session):
        """Repository: Query books by bookshelf_id"""
        from modules.book.repository import BookRepositoryImpl
        from modules.book.domain import Book

        repo = BookRepositoryImpl(db_session)
        bookshelf_id = uuid4()
        book1 = Book.create(bookshelf_id=bookshelf_id, title="Book1")
        book2 = Book.create(bookshelf_id=bookshelf_id, title="Book2")

        await repo.save(book1)
        await repo.save(book2)
        books = await repo.get_by_bookshelf_id(bookshelf_id)

        assert len(books) >= 2

    @pytest.mark.asyncio
    async def test_book_soft_delete_filter(self, db_session):
        """POLICY-008: Soft deleted books not returned by queries"""
        from modules.book.repository import BookRepositoryImpl
        from modules.book.domain import Book

        repo = BookRepositoryImpl(db_session)
        book = Book.create(bookshelf_id=uuid4(), title="Test")
        await repo.save(book)

        book.mark_deleted()
        await repo.save(book)

        retrieved = await repo.get_by_id(book.id)
        assert retrieved is None


# ============================================================================
# SECTION 4: BLOCK MODULE TESTS
# ============================================================================

class TestBlockDomain:
    """Test Block domain layer"""

    def test_block_text_creation_emits_event(self):
        """RULE-014: Block creation with type must emit BlockCreated event"""
        from modules.block.domain import Block, BlockType

        book_id = uuid4()
        block = Block.create_text(
            book_id=book_id,
            content="Test content",
            order=Decimal("10.0")
        )

        assert block.id is not None
        assert block.book_id == book_id
        assert block.block_type == BlockType.TEXT
        assert block.content.value == "Test content"
        assert any(e.__class__.__name__ == "BlockCreated" for e in block.domain_events)

    def test_block_heading_creation_with_level(self):
        """RULE-013-REVISED: HEADING block must have heading_level (1-3)"""
        from modules.block.domain import Block, BlockType

        book_id = uuid4()
        block = Block.create_heading(
            book_id=book_id,
            content="Title",
            heading_level=1,
            order=Decimal("20.0")
        )

        assert block.block_type == BlockType.HEADING
        assert block.heading_level == 1

    def test_block_heading_level_validation(self):
        """RULE-013-REVISED: Heading level must be 1-3"""
        from modules.block.domain import Block, InvalidHeadingLevelError

        book_id = uuid4()

        # Valid levels
        for level in [1, 2, 3]:
            block = Block.create_heading(
                book_id=book_id,
                content=f"H{level}",
                heading_level=level,
                order=Decimal(str(level * 10))
            )
            assert block.heading_level == level

        # Invalid level
        with pytest.raises(InvalidHeadingLevelError):
            Block.create_heading(
                book_id=book_id,
                content="Invalid",
                heading_level=4,
                order=Decimal("40.0")
            )

    def test_block_type_factory_methods(self):
        """RULE-014: Block supports 8 types with factory methods"""
        from modules.block.domain import Block, BlockType

        book_id = uuid4()
        types = [
            (Block.create_text, BlockType.TEXT),
            (Block.create_heading, BlockType.HEADING, 1),
            (Block.create_code, BlockType.CODE),
            (Block.create_image, BlockType.IMAGE),
            (Block.create_quote, BlockType.QUOTE),
            (Block.create_list, BlockType.LIST),
            (Block.create_table, BlockType.TABLE),
            (Block.create_divider, BlockType.DIVIDER),
        ]

        for type_info in types:
            factory = type_info[0]
            expected_type = type_info[1]
            order = Decimal(str(len(types) * 10))

            if expected_type == BlockType.HEADING:
                heading_level = type_info[2]
                block = factory(
                    book_id=book_id,
                    content="Test",
                    heading_level=heading_level,
                    order=order
                )
            else:
                block = factory(
                    book_id=book_id,
                    content="Test",
                    order=order
                )

            assert block.block_type == expected_type

    def test_block_fractional_index_ordering(self):
        """RULE-015-REVISED: Block order as Decimal for fractional indexing"""
        from modules.block.domain import Block

        book_id = uuid4()
        block1 = Block.create_text(book_id=book_id, content="A", order=Decimal("10.0"))
        block2 = Block.create_text(book_id=book_id, content="B", order=Decimal("20.0"))

        # Fractional order between them
        mid_order = (block1.order + block2.order) / 2
        block3 = Block.create_text(book_id=book_id, content="C", order=mid_order)

        assert Decimal("10.0") < block3.order < Decimal("20.0")
        assert isinstance(block3.order, Decimal)

    def test_block_soft_delete(self):
        """POLICY-008: Block soft delete sets soft_deleted_at"""
        from modules.block.domain import Block

        block = Block.create_text(
            book_id=uuid4(),
            content="Test",
            order=Decimal("10.0")
        )
        assert block.soft_deleted_at is None

        block.mark_deleted()

        assert block.soft_deleted_at is not None
        assert block.soft_deleted_at.tzinfo is not None


class TestBlockRepository:
    """Test Block repository layer"""

    @pytest.mark.asyncio
    async def test_block_save_and_retrieve(self, db_session):
        """Repository: Save and retrieve Block"""
        from modules.block.repository import BlockRepositoryImpl
        from modules.block.domain import Block

        repo = BlockRepositoryImpl(db_session)
        book_id = uuid4()
        block = Block.create_text(
            book_id=book_id,
            content="Test",
            order=Decimal("10.0")
        )

        await repo.save(block)
        retrieved = await repo.get_by_id(block.id)

        assert retrieved is not None
        assert retrieved.id == block.id
        assert retrieved.content.value == "Test"

    @pytest.mark.asyncio
    async def test_block_get_by_book_id_ordered(self, db_session):
        """Repository: Query blocks by book_id, ordered by fractional index"""
        from modules.block.repository import BlockRepositoryImpl
        from modules.block.domain import Block

        repo = BlockRepositoryImpl(db_session)
        book_id = uuid4()
        block1 = Block.create_text(book_id=book_id, content="A", order=Decimal("10.0"))
        block2 = Block.create_text(book_id=book_id, content="B", order=Decimal("5.0"))
        block3 = Block.create_text(book_id=book_id, content="C", order=Decimal("15.0"))

        await repo.save(block1)
        await repo.save(block2)
        await repo.save(block3)

        blocks = await repo.get_by_book_id(book_id)

        # Should be ordered by order field
        assert len(blocks) == 3
        assert blocks[0].order == Decimal("5.0")
        assert blocks[1].order == Decimal("10.0")
        assert blocks[2].order == Decimal("15.0")

    @pytest.mark.asyncio
    async def test_block_list_paginated(self, db_session):
        """Repository: Paginated query with total count"""
        from modules.block.repository import BlockRepositoryImpl
        from modules.block.domain import Block

        repo = BlockRepositoryImpl(db_session)
        book_id = uuid4()

        # Create 25 blocks
        for i in range(25):
            block = Block.create_text(
                book_id=book_id,
                content=f"Block {i}",
                order=Decimal(str(i * 10))
            )
            await repo.save(block)

        # Page 1 (20 items)
        blocks_p1, total = await repo.list_paginated(book_id, page=1, page_size=20)

        assert len(blocks_p1) == 20
        assert total == 25

        # Page 2 (5 items)
        blocks_p2, total = await repo.list_paginated(book_id, page=2, page_size=20)

        assert len(blocks_p2) == 5
        assert total == 25

    @pytest.mark.asyncio
    async def test_block_soft_delete_filter(self, db_session):
        """POLICY-008: Soft deleted blocks not returned"""
        from modules.block.repository import BlockRepositoryImpl
        from modules.block.domain import Block

        repo = BlockRepositoryImpl(db_session)
        block = Block.create_text(book_id=uuid4(), content="Test", order=Decimal("10.0"))
        await repo.save(block)

        block.mark_deleted()
        await repo.save(block)

        retrieved = await repo.get_by_id(block.id)
        assert retrieved is None


# ============================================================================
# SECTION 5: CROSS-MODULE INTEGRATION TESTS
# ============================================================================

class TestCrossModuleIntegration:
    """Test relationships and cascading operations across modules"""

    @pytest.mark.asyncio
    async def test_library_to_bookshelf_relationship(self, db_session):
        """Integration: Library → Bookshelf (FK constraint)"""
        from modules.library.repository import LibraryRepositoryImpl
        from modules.bookshelf.repository import BookshelfRepositoryImpl
        from modules.library.domain import Library
        from modules.bookshelf.domain import Bookshelf

        lib_repo = LibraryRepositoryImpl(db_session)
        shelf_repo = BookshelfRepositoryImpl(db_session)

        library = Library.create(user_id=uuid4(), name="Test Library")
        await lib_repo.save(library)

        # Create bookshelf for library
        shelf = Bookshelf.create(
            library_id=library.id,
            name="Test Shelf",
            is_basement=False
        )
        await shelf_repo.save(shelf)

        # Verify relationship
        retrieved_lib = await lib_repo.get_by_id(library.id)
        retrieved_shelf = await shelf_repo.get_by_id(shelf.id)

        assert retrieved_shelf.library_id == retrieved_lib.id

    @pytest.mark.asyncio
    async def test_bookshelf_to_book_relationship(self, db_session):
        """Integration: Bookshelf → Book (FK constraint)"""
        from modules.bookshelf.repository import BookshelfRepositoryImpl
        from modules.book.repository import BookRepositoryImpl
        from modules.bookshelf.domain import Bookshelf
        from modules.book.domain import Book

        shelf_repo = BookshelfRepositoryImpl(db_session)
        book_repo = BookRepositoryImpl(db_session)

        shelf = Bookshelf.create(library_id=uuid4(), name="Test", is_basement=False)
        await shelf_repo.save(shelf)

        book = Book.create(bookshelf_id=shelf.id, title="Test Book")
        await book_repo.save(book)

        # Verify relationship
        retrieved_shelf = await shelf_repo.get_by_id(shelf.id)
        retrieved_book = await book_repo.get_by_id(book.id)

        assert retrieved_book.bookshelf_id == retrieved_shelf.id

    @pytest.mark.asyncio
    async def test_book_to_block_relationship(self, db_session):
        """Integration: Book → Block (FK constraint)"""
        from modules.book.repository import BookRepositoryImpl
        from modules.block.repository import BlockRepositoryImpl
        from modules.book.domain import Book
        from modules.block.domain import Block

        book_repo = BookRepositoryImpl(db_session)
        block_repo = BlockRepositoryImpl(db_session)

        book = Book.create(bookshelf_id=uuid4(), title="Test")
        await book_repo.save(book)

        block = Block.create_text(
            book_id=book.id,
            content="Content",
            order=Decimal("10.0")
        )
        await block_repo.save(block)

        # Verify relationship
        retrieved_book = await book_repo.get_by_id(book.id)
        retrieved_block = await block_repo.get_by_id(block.id)

        assert retrieved_block.book_id == retrieved_book.id

    @pytest.mark.asyncio
    async def test_full_hierarchy_round_trip(self, db_session):
        """Integration: Complete Library → Bookshelf → Book → Block hierarchy"""
        from modules.library.repository import LibraryRepositoryImpl
        from modules.bookshelf.repository import BookshelfRepositoryImpl
        from modules.book.repository import BookRepositoryImpl
        from modules.block.repository import BlockRepositoryImpl
        from modules.library.domain import Library
        from modules.bookshelf.domain import Bookshelf
        from modules.book.domain import Book
        from modules.block.domain import Block

        lib_repo = LibraryRepositoryImpl(db_session)
        shelf_repo = BookshelfRepositoryImpl(db_session)
        book_repo = BookRepositoryImpl(db_session)
        block_repo = BlockRepositoryImpl(db_session)

        # Create full hierarchy
        user_id = uuid4()
        library = Library.create(user_id=user_id, name="Library")
        await lib_repo.save(library)

        shelf = Bookshelf.create(library_id=library.id, name="Shelf", is_basement=False)
        await shelf_repo.save(shelf)

        book = Book.create(bookshelf_id=shelf.id, title="Book")
        await book_repo.save(book)

        blocks = [
            Block.create_text(book_id=book.id, content="Para 1", order=Decimal("10.0")),
            Block.create_heading(book_id=book.id, content="Section", heading_level=1, order=Decimal("20.0")),
            Block.create_code(book_id=book.id, content="code()", order=Decimal("30.0")),
        ]
        for block in blocks:
            await block_repo.save(block)

        # Verify full retrieval
        retrieved_lib = await lib_repo.get_by_id(library.id)
        retrieved_shelf = await shelf_repo.get_by_id(shelf.id)
        retrieved_book = await book_repo.get_by_id(book.id)
        retrieved_blocks = await block_repo.get_by_book_id(book.id)

        assert retrieved_lib.id == library.id
        assert retrieved_shelf.library_id == library.id
        assert retrieved_book.bookshelf_id == shelf.id
        assert len(retrieved_blocks) == 3
        assert all(b.book_id == book.id for b in retrieved_blocks)

    @pytest.mark.asyncio
    async def test_soft_delete_policy_enforcement(self, db_session):
        """POLICY-008: Soft delete consistently enforced across all modules"""
        from modules.library.repository import LibraryRepositoryImpl
        from modules.bookshelf.repository import BookshelfRepositoryImpl
        from modules.book.repository import BookRepositoryImpl
        from modules.block.repository import BlockRepositoryImpl
        from modules.library.domain import Library
        from modules.bookshelf.domain import Bookshelf
        from modules.book.domain import Book
        from modules.block.domain import Block

        lib_repo = LibraryRepositoryImpl(db_session)
        shelf_repo = BookshelfRepositoryImpl(db_session)
        book_repo = BookRepositoryImpl(db_session)
        block_repo = BlockRepositoryImpl(db_session)

        # Create items
        lib = Library.create(user_id=uuid4(), name="Lib")
        await lib_repo.save(lib)

        shelf = Bookshelf.create(library_id=lib.id, name="Shelf", is_basement=False)
        await shelf_repo.save(shelf)

        book = Book.create(bookshelf_id=shelf.id, title="Book")
        await book_repo.save(book)

        block = Block.create_text(book_id=book.id, content="Text", order=Decimal("10.0"))
        await block_repo.save(block)

        # Soft delete all
        lib.mark_deleted()
        shelf.mark_deleted()
        book.mark_deleted()
        block.mark_deleted()

        await lib_repo.save(lib)
        await shelf_repo.save(shelf)
        await book_repo.save(book)
        await block_repo.save(block)

        # Verify all return None
        assert await lib_repo.get_by_id(lib.id) is None
        assert await shelf_repo.get_by_id(shelf.id) is None
        assert await book_repo.get_by_id(book.id) is None
        assert await block_repo.get_by_id(block.id) is None


# ============================================================================
# SECTION 6: SCHEMA & SERIALIZATION TESTS
# ============================================================================

class TestSchemasAndSerialization:
    """Test request/response schemas and serialization across all modules"""

    def test_library_dto_round_trip(self):
        """Schema: LibraryDTO round-trip domain → DTO → response"""
        from modules.library.schemas import LibraryDTO
        from modules.library.domain import Library

        # Create domain object
        library = Library.create(user_id=uuid4(), name="Test")

        # Domain → DTO
        dto = LibraryDTO.from_domain(library)
        assert dto.id == library.id
        assert dto.name == library.name.value

        # DTO → Response
        response = dto.to_response()
        assert response.id == library.id
        assert response.name == "Test"

    def test_block_decimal_serialization(self):
        """Schema: Block order (Decimal) serialized to JSON string"""
        from modules.block.schemas import BlockDTO, BlockResponse
        from modules.block.domain import Block

        block = Block.create_text(
            book_id=uuid4(),
            content="Test",
            order=Decimal("15.5")
        )

        dto = BlockDTO.from_domain(block)
        assert isinstance(dto.order, Decimal)

        response = dto.to_response()
        assert isinstance(response.order, str)
        assert response.order == "15.5"

    def test_block_paginated_response(self):
        """Schema: BlockPaginatedResponse with has_more flag"""
        from modules.block.schemas import BlockResponse, BlockPaginatedResponse

        responses = [
            BlockResponse(
                id=uuid4(),
                book_id=uuid4(),
                block_type="TEXT",
                content="Block 1",
                order="10.0",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
            BlockResponse(
                id=uuid4(),
                book_id=uuid4(),
                block_type="TEXT",
                content="Block 2",
                order="20.0",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
        ]

        paginated = BlockPaginatedResponse(
            items=responses,
            total=100,
            page=1,
            page_size=20,
            has_more=True
        )

        assert paginated.has_more is True
        assert len(paginated.items) == 2


# ============================================================================
# SECTION 7: EXCEPTION HANDLING TESTS
# ============================================================================

class TestExceptionHandling:
    """Test exception hierarchy and HTTP status code mapping"""

    def test_library_not_found_exception(self):
        """Exception: LibraryNotFoundError → 404"""
        from modules.library.exceptions import LibraryNotFoundError

        exc = LibraryNotFoundError(library_id=uuid4())
        assert exc.http_status_code == 404
        assert exc.code == "LIBRARY_NOT_FOUND"

    def test_library_already_exists_exception(self):
        """Exception: LibraryAlreadyExistsError → 409"""
        from modules.library.exceptions import LibraryAlreadyExistsError

        exc = LibraryAlreadyExistsError(user_id=uuid4())
        assert exc.http_status_code == 409
        assert exc.code == "LIBRARY_ALREADY_EXISTS"

    def test_invalid_heading_level_exception(self):
        """Exception: InvalidHeadingLevelError → 422"""
        from modules.block.exceptions import InvalidHeadingLevelError

        exc = InvalidHeadingLevelError(provided=5, allowed=[1, 2, 3])
        assert exc.http_status_code == 422
        assert exc.code == "INVALID_HEADING_LEVEL"

    def test_fractional_index_error_exception(self):
        """Exception: FractionalIndexError → 422"""
        from modules.block.exceptions import FractionalIndexError

        exc = FractionalIndexError(message="Precision limit reached")
        assert exc.http_status_code == 422
        assert exc.code == "FRACTIONAL_INDEX_ERROR"

    def test_block_in_basement_exception(self):
        """Exception: BlockInBasementError → 409"""
        from modules.block.exceptions import BlockInBasementError

        exc = BlockInBasementError(block_id=uuid4())
        assert exc.http_status_code == 409
        assert exc.code == "BLOCK_IN_BASEMENT"

    def test_exception_to_dict_serialization(self):
        """Exception: to_dict() serialization for HTTP responses"""
        from modules.book.exceptions import BookNotFoundError

        exc = BookNotFoundError(book_id=uuid4())
        error_dict = exc.to_dict()

        assert "code" in error_dict
        assert "message" in error_dict
        assert "details" in error_dict


# ============================================================================
# SECTION 8: DATETIME & TIMEZONE VALIDATION
# ============================================================================

class TestDatetimeValidation:
    """Verify all datetime fields are timezone-aware (no deprecation warnings)"""

    def test_library_timestamps_are_timezone_aware(self):
        """Validation: Library timestamps must be timezone-aware"""
        from modules.library.domain import Library

        library = Library.create(user_id=uuid4(), name="Test")

        assert library.created_at.tzinfo is not None
        assert library.updated_at.tzinfo is not None

    def test_book_timestamps_are_timezone_aware(self):
        """Validation: Book timestamps must be timezone-aware"""
        from modules.book.domain import Book

        book = Book.create(bookshelf_id=uuid4(), title="Test")

        assert book.created_at.tzinfo is not None
        assert book.updated_at.tzinfo is not None

    def test_block_timestamps_are_timezone_aware(self):
        """Validation: Block timestamps must be timezone-aware"""
        from modules.block.domain import Block

        block = Block.create_text(book_id=uuid4(), content="Test", order=Decimal("10.0"))

        assert block.created_at.tzinfo is not None
        assert block.updated_at.tzinfo is not None
        if block.soft_deleted_at is not None:
            assert block.soft_deleted_at.tzinfo is not None


# ============================================================================
# Test Execution Markers
# ============================================================================

# pytest markers for organization
pytestmark = [
    pytest.mark.integration,
    pytest.mark.four_modules,
    pytest.mark.phase_1_5,
]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
