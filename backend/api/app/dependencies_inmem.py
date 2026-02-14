"""
In-Memory Repository Implementation - Temporary for E2E Testing
直接在内存中存储数据，不依赖数据库/Mock
"""
from uuid import UUID
from typing import Dict, List, Optional
from datetime import datetime, timezone

from api.app.modules.chronicle.domain import ChronicleEvent, ChronicleEventType
from api.app.modules.chronicle.application.services import (
    ChronicleRecorderService,
    ChronicleQueryService,
)
from api.app.modules.book.domain.services import BookMaturityScoreService


class InMemoryLibraryRepository:
    """Minimal in-memory Library repository.

    Used by authorization checks when enforce_owner_check is enabled.
    """

    def __init__(self):
        self.storage: Dict[UUID, object] = {}

    async def save(self, library):
        self.storage[library.id] = library
        return library

    async def get_by_id(self, library_id: UUID):
        return self.storage.get(library_id)

    async def exists(self, library_id: UUID):
        return library_id in self.storage


class InMemoryBookshelfRepository:
    """In-Memory Bookshelf Repository"""
    def __init__(self):
        self.storage: Dict[UUID, object] = {}

    async def save(self, bookshelf):
        self.storage[bookshelf.id] = bookshelf
        return bookshelf

    async def get_by_id(self, bookshelf_id: UUID):
        return self.storage.get(bookshelf_id)

    async def exists_by_name(self, lib_id: UUID, name: str):
        return False

    async def delete(self, bookshelf_id: UUID):
        self.storage.pop(bookshelf_id, None)

    async def exists(self, bookshelf_id: UUID):
        return bookshelf_id in self.storage

    async def find_deleted_by_library(self, lib_id: UUID, limit=100, offset=0):
        return []

    async def list_by_library(self, lib_id: UUID, limit=100, offset=0):
        return list(self.storage.values())


class InMemoryBookRepository:
    """In-Memory Book Repository"""
    def __init__(self):
        self.storage: Dict[UUID, object] = {}

    async def save(self, book):
        self.storage[book.id] = book
        return book

    async def get_by_id(self, book_id: UUID):
        return self.storage.get(book_id)

    async def exists_by_title(self, shelf_id: UUID, title: str):
        return False

    async def list_by_bookshelf(self, shelf_id: UUID, limit=50, offset=0):
        return [b for b in self.storage.values() if b.bookshelf_id == shelf_id]

    async def delete(self, book_id: UUID):
        self.storage.pop(book_id, None)

    async def exists(self, book_id: UUID):
        return book_id in self.storage


class InMemoryBlockRepository:
    """In-Memory Block Repository"""
    def __init__(self):
        self.storage: Dict[UUID, object] = {}

    async def save(self, block):
        self.storage[block.id] = block
        return block

    async def get_by_id(self, block_id: UUID):
        block = self.storage.get(block_id)
        if block is None:
            return None
        if getattr(block, "soft_deleted_at", None) is not None:
            return None
        return block

    async def get_any_by_id(self, block_id: UUID):
        return self.storage.get(block_id)

    async def list_paginated(
        self,
        book_id: UUID,
        page: int = 1,
        page_size: int = 20,
        include_deleted: bool = False,
    ):
        all_blocks = [b for b in self.storage.values() if getattr(b, "book_id", None) == book_id]
        if not include_deleted:
            all_blocks = [b for b in all_blocks if getattr(b, "soft_deleted_at", None) is None]
        total = len(all_blocks)
        start = max(0, (page - 1) * page_size)
        end = start + page_size
        return all_blocks[start:end], total

    async def get_deleted_blocks(self, book_id: UUID):
        return [
            b
            for b in self.storage.values()
            if getattr(b, "book_id", None) == book_id and getattr(b, "soft_deleted_at", None) is not None
        ]

    async def list_by_book(self, book_id: UUID, limit=100, offset=0):
        return [b for b in self.storage.values() if b.book_id == book_id]

    async def delete(self, block_id: UUID):
        self.storage.pop(block_id, None)

    async def exists(self, block_id: UUID):
        return block_id in self.storage

    async def count_active_blocks(self, book_id: UUID):
        blocks = [b for b in self.storage.values() if getattr(b, "book_id", None) == book_id]
        block_types = {getattr(b, "type", None) for b in blocks if getattr(b, "type", None)}
        return len(blocks), len(block_types)

    async def get_prev_sibling(self, block_id: UUID, book_id: UUID):
        return None

    async def get_next_sibling(self, block_id: UUID, book_id: UUID):
        return None

    def new_key_between(self, prev_sort_key, next_sort_key):
        # Minimal implementation for in-memory: no real fractional indexing.
        return 1

    async def restore_from_paperballs(
        self,
        block_id: UUID,
        book_id: UUID,
        deleted_prev_id,
        deleted_next_id,
        deleted_section_path,
    ):
        block = self.storage.get(block_id)
        if block is None:
            raise ValueError("Block not found")
        if getattr(block, "book_id", None) != book_id:
            raise ValueError("Book mismatch")
        setattr(block, "soft_deleted_at", None)
        setattr(block, "deleted_prev_id", None)
        setattr(block, "deleted_next_id", None)
        setattr(block, "deleted_section_path", None)
        self.storage[block_id] = block
        return block


class InMemoryChronicleRepository:
    """In-Memory Chronicle Repository"""

    def __init__(self):
        self.events: List[ChronicleEvent] = []

    async def save(self, event: ChronicleEvent) -> ChronicleEvent:
        self.events.append(event)
        return event

    async def list_by_book(
        self,
        book_id: UUID,
        event_types: Optional[List[ChronicleEventType]] = None,
        limit: int = 50,
        offset: int = 0,
        order_desc: bool = True,
    ):
        filtered = [
            e
            for e in self.events
            if e.book_id == book_id and (not event_types or e.event_type in event_types)
        ]
        filtered.sort(key=lambda e: e.occurred_at, reverse=order_desc)
        total = len(filtered)
        items = filtered[offset : offset + limit]
        return items, total

    async def list_by_time_range(
        self,
        start: datetime,
        end: datetime,
        event_types: Optional[List[ChronicleEventType]] = None,
        limit: int = 100,
        offset: int = 0,
    ):
        filtered = [
            e
            for e in self.events
            if start <= e.occurred_at <= end
            and (not event_types or e.event_type in event_types)
        ]
        filtered.sort(key=lambda e: e.occurred_at, reverse=True)
        total = len(filtered)
        items = filtered[offset : offset + limit]
        return items, total


class DIContainerInMem:
    """DI Container with In-Memory Repositories - for E2E testing"""

    def __init__(self, session=None):
        """session is ignored, using in-memory storage"""
        self.session = session
        self.library_repo = InMemoryLibraryRepository()
        self.bookshelf_repo = InMemoryBookshelfRepository()
        self.book_repo = InMemoryBookRepository()
        self.block_repo = InMemoryBlockRepository()
        self.chronicle_repo = InMemoryChronicleRepository()
        self.book_maturity_score_service = BookMaturityScoreService()

    def get_session(self):
        """Return the placeholder session for API compatibility."""
        return self.session

    # ========== Bookshelf UseCases ==========
    def get_create_bookshelf_use_case(self):
        from api.app.modules.bookshelf.application.use_cases.create_bookshelf import CreateBookshelfUseCase
        return CreateBookshelfUseCase(self.bookshelf_repo)

    def get_list_bookshelves_use_case(self):
        from api.app.modules.bookshelf.application.use_cases.list_bookshelves import ListBookshelvesUseCase
        return ListBookshelvesUseCase(self.bookshelf_repo)

    def get_get_bookshelf_use_case(self):
        from api.app.modules.bookshelf.application.use_cases.get_bookshelf import GetBookshelfUseCase
        return GetBookshelfUseCase(self.bookshelf_repo)

    def get_get_basement_use_case(self):
        from api.app.modules.bookshelf.application.use_cases.get_basement import GetBasementUseCase
        return GetBasementUseCase(self.bookshelf_repo)

    def get_delete_bookshelf_use_case(self):
        from api.app.modules.bookshelf.application.use_cases.delete_bookshelf import DeleteBookshelfUseCase
        return DeleteBookshelfUseCase(self.bookshelf_repo)

    def get_restore_bookshelf_use_case(self):
        from api.app.modules.bookshelf.application.use_cases.restore_bookshelf import RestoreBookshelfUseCase
        return RestoreBookshelfUseCase(self.bookshelf_repo)

    def get_rename_bookshelf_use_case(self):
        from api.app.modules.bookshelf.application.use_cases.rename_bookshelf import RenameBookshelfUseCase
        return RenameBookshelfUseCase(self.bookshelf_repo)

    # ========== Book UseCases ==========
    def get_create_book_use_case(self):
        from api.app.modules.book.application.use_cases.create_book import CreateBookUseCase
        return CreateBookUseCase(self.book_repo)

    def get_list_books_use_case(self):
        from api.app.modules.book.application.use_cases.list_books import ListBooksUseCase
        return ListBooksUseCase(self.book_repo)

    def get_get_book_use_case(self):
        from api.app.modules.book.application.use_cases.get_book import GetBookUseCase
        return GetBookUseCase(self.book_repo)

    def get_update_book_use_case(self):
        from api.app.modules.book.application.use_cases.update_book import UpdateBookUseCase
        return UpdateBookUseCase(self.book_repo)

    def get_delete_book_use_case(self):
        from api.app.modules.book.application.use_cases.delete_book import DeleteBookUseCase
        return DeleteBookUseCase(self.book_repo, self.bookshelf_repo)

    def get_move_book_use_case(self):
        from api.app.modules.book.application.use_cases.move_book import MoveBookUseCase
        return MoveBookUseCase(self.book_repo, bookshelf_repository=self.bookshelf_repo)

    def get_restore_book_use_case(self):
        from api.app.modules.book.application.use_cases.restore_book import RestoreBookUseCase
        return RestoreBookUseCase(self.book_repo, bookshelf_repository=self.bookshelf_repo)

    def get_calculate_book_maturity_use_case(self):
        from api.app.modules.maturity.application.adapters import BookAggregateMaturityDataProvider
        from api.app.modules.maturity.application.use_cases import CalculateBookMaturityUseCase

        data_provider = BookAggregateMaturityDataProvider(
            self.book_repo,
            block_repository=self.block_repo,
        )
        # In-memory setup: skip persistence layer
        return CalculateBookMaturityUseCase(data_provider=data_provider, snapshot_repository=None)

    def get_recalculate_book_maturity_use_case(self):
        from api.app.modules.book.application.use_cases.recalculate_book_maturity import RecalculateBookMaturityUseCase

        return RecalculateBookMaturityUseCase(
            repository=self.book_repo,
            maturity_calculator=self.get_calculate_book_maturity_use_case(),
            chronicle_service=ChronicleRecorderService(self.chronicle_repo),
        )

    def get_update_book_maturity_use_case(self):
        from api.app.modules.book.application.use_cases.update_book_maturity import UpdateBookMaturityUseCase

        return UpdateBookMaturityUseCase(
            repository=self.book_repo,
            score_service=self.book_maturity_score_service,
            chronicle_service=ChronicleRecorderService(self.chronicle_repo),
        )

    def get_list_deleted_books_use_case(self):
        from api.app.modules.book.application.use_cases.list_deleted_books import ListDeletedBooksUseCase
        return ListDeletedBooksUseCase(self.book_repo)

    # ========== Block UseCases ==========
    def get_create_block_use_case(self):
        from api.app.modules.block.application.use_cases.create_block import CreateBlockUseCase
        return CreateBlockUseCase(
            self.block_repo,
            book_repository=self.book_repo,
            library_repository=self.library_repo,
        )

    def get_list_blocks_use_case(self):
        from api.app.modules.block.application.use_cases.list_blocks import ListBlocksUseCase
        return ListBlocksUseCase(
            self.block_repo,
            book_repository=self.book_repo,
            library_repository=self.library_repo,
        )

    def get_get_block_use_case(self):
        from api.app.modules.block.application.use_cases.get_block import GetBlockUseCase
        return GetBlockUseCase(
            self.block_repo,
            book_repository=self.book_repo,
            library_repository=self.library_repo,
        )

    def get_update_block_use_case(self):
        from api.app.modules.block.application.use_cases.update_block import UpdateBlockUseCase
        return UpdateBlockUseCase(
            self.block_repo,
            book_repository=self.book_repo,
            library_repository=self.library_repo,
        )

    def get_reorder_blocks_use_case(self):
        from api.app.modules.block.application.use_cases.reorder_blocks import ReorderBlocksUseCase
        return ReorderBlocksUseCase(
            self.block_repo,
            book_repository=self.book_repo,
            library_repository=self.library_repo,
        )

    def get_delete_block_use_case(self):
        from api.app.modules.block.application.use_cases.delete_block import DeleteBlockUseCase
        return DeleteBlockUseCase(
            self.block_repo,
            book_repository=self.book_repo,
            library_repository=self.library_repo,
        )

    def get_restore_block_use_case(self):
        from api.app.modules.block.application.use_cases.restore_block import RestoreBlockUseCase
        return RestoreBlockUseCase(
            self.block_repo,
            book_repository=self.book_repo,
            library_repository=self.library_repo,
        )

    def get_list_deleted_blocks_use_case(self):
        from api.app.modules.block.application.use_cases.list_deleted_blocks import ListDeletedBlocksUseCase
        return ListDeletedBlocksUseCase(
            self.block_repo,
            book_repository=self.book_repo,
            library_repository=self.library_repo,
        )

    # ========== Chronicle Services ==========
    def get_chronicle_recorder_service(self):
        return ChronicleRecorderService(self.chronicle_repo)

    def get_chronicle_query_service(self):
        return ChronicleQueryService(self.chronicle_repo)
