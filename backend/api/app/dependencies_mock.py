"""
Mock DIContainer for rapid testing

This is a temporary implementation to bypass Repository async/sync issues.
Used to verify DI injection and routing integration work correctly.

TODO: Replace with proper async Repository implementations.
"""

from typing import Dict, Any, Type, TypeVar, Callable, List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.modules.chronicle.domain import ChronicleEvent, ChronicleEventType
from api.app.modules.chronicle.application.services import (
    ChronicleRecorderService,
    ChronicleQueryService,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class MockChronicleRepository:
    """Simple in-memory Chronicle repository for mock DI container."""

    def __init__(self):
        self.events: List[ChronicleEvent] = []

    async def save(self, event: ChronicleEvent) -> ChronicleEvent:
        self.events.append(event)
        return event

    async def list_by_book(
        self,
        book_id,
        event_types: Optional[List[ChronicleEventType]] = None,
        limit: int = 50,
        offset: int = 0,
        order_desc: bool = True,
    ):
        filtered = [
            e for e in self.events
            if e.book_id == book_id and (not event_types or e.event_type in event_types)
        ]
        filtered.sort(key=lambda e: e.occurred_at, reverse=order_desc)
        total = len(filtered)
        return filtered[offset: offset + limit], total

    async def list_by_time_range(
        self,
        start,
        end,
        event_types: Optional[List[ChronicleEventType]] = None,
        limit: int = 100,
        offset: int = 0,
    ):
        filtered = [
            e for e in self.events
            if start <= e.occurred_at <= end and (not event_types or e.event_type in event_types)
        ]
        filtered.sort(key=lambda e: e.occurred_at, reverse=True)
        total = len(filtered)
        return filtered[offset: offset + limit], total


class MockDIContainer:
    """Lightweight DI container with mock implementations"""

    def __init__(self, session: AsyncSession = None):
        self._session = session
        self._chronicle_repo = MockChronicleRepository()

    def get_session(self) -> Optional[AsyncSession]:
        """Expose mock session so router helpers don't fail."""
        return self._session

    # ==================== Bookshelf UseCase 宸ュ巶鏂规硶 ====================

    def get_create_bookshelf_use_case(self):
        """鑾峰彇鍒涘缓涔︽灦鐢ㄤ緥 (Mock)"""
        from api.app.modules.bookshelf.application.use_cases.create_bookshelf import CreateBookshelfUseCase
        from api.app.modules.bookshelf.domain import Bookshelf, BookshelfName, BookshelfStatus
        from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository
        from uuid import uuid4
        from datetime import datetime, timezone

        class MockBookshelfRepository(IBookshelfRepository):
            async def save(self, bookshelf):
                logger.info(f"Mock save: {bookshelf.name.value}")

            async def get_by_id(self, id):
                return None

            async def get_by_library_id(self, id):
                return []

            async def get_basement_by_library_id(self, id):
                return None

            async def exists_by_name(self, lib_id, name):
                return False

            async def delete(self, id):
                pass

            async def exists(self, id):
                return False

            async def find_deleted_by_library(self, lib_id, limit=100, offset=0):
                return []

        repo = MockBookshelfRepository()
        return CreateBookshelfUseCase(repo)

    def get_list_bookshelves_use_case(self):
        """鑾峰彇鍒楄〃涔︽灦鐢ㄤ緥 (Mock)"""
        from api.app.modules.bookshelf.application.use_cases.list_bookshelves import ListBookshelvesUseCase
        from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository

        class MockBookshelfRepository(IBookshelfRepository):
            async def save(self, bookshelf):
            return bookshelf

            async def get_by_id(self, id):
                return None

            async def get_by_library_id(self, id):
                return []

            async def get_basement_by_library_id(self, id):
                return None

            async def exists_by_name(self, lib_id, name):
                return False

            async def delete(self, id):
                pass

            async def exists(self, id):
                return False

            async def find_deleted_by_library(self, lib_id, limit=100, offset=0):
                return []

        repo = MockBookshelfRepository()
        return ListBookshelvesUseCase(repo)

    def get_get_bookshelf_use_case(self):
        """鑾峰彇鍗曚釜涔︽灦鐢ㄤ緥 (Mock)"""
        from api.app.modules.bookshelf.application.use_cases.get_bookshelf import GetBookshelfUseCase
        from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository

        class MockBookshelfRepository(IBookshelfRepository):
            async def save(self, bookshelf):
            return bookshelf

            async def get_by_id(self, id):
                return None

            async def get_by_library_id(self, id):
                return []

            async def get_basement_by_library_id(self, id):
                return None

            async def exists_by_name(self, lib_id, name):
                return False

            async def delete(self, id):
                pass

            async def exists(self, id):
                return False

            async def find_deleted_by_library(self, lib_id, limit=100, offset=0):
                return []

        repo = MockBookshelfRepository()
        return GetBookshelfUseCase(repo)

    def get_update_bookshelf_use_case(self):
        """鑾峰彇鏇存柊涔︽灦鐢ㄤ緥 (Mock)"""
        from api.app.modules.bookshelf.application.use_cases.update_bookshelf import UpdateBookshelfUseCase
        from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository

        class MockBookshelfRepository(IBookshelfRepository):
            async def save(self, bookshelf):
            return bookshelf

            async def get_by_id(self, id):
                return None

            async def get_by_library_id(self, id):
                return []

            async def get_basement_by_library_id(self, id):
                return None

            async def exists_by_name(self, lib_id, name):
                return False

            async def delete(self, id):
                pass

            async def exists(self, id):
                return False

            async def find_deleted_by_library(self, lib_id, limit=100, offset=0):
                return []

        repo = MockBookshelfRepository()
        return UpdateBookshelfUseCase(repo)

    def get_delete_bookshelf_use_case(self):
        """鑾峰彇鍒犻櫎涔︽灦鐢ㄤ緥 (Mock)"""
        from api.app.modules.bookshelf.application.use_cases.delete_bookshelf import DeleteBookshelfUseCase
        from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository

        class MockBookshelfRepository(IBookshelfRepository):
            async def save(self, bookshelf):
            return bookshelf

            async def get_by_id(self, id):
                return None

            async def get_by_library_id(self, id):
                return []

            async def get_basement_by_library_id(self, id):
                return None

            async def exists_by_name(self, lib_id, name):
                return False

            async def delete(self, id):
                pass

            async def exists(self, id):
                return False

            async def find_deleted_by_library(self, lib_id, limit=100, offset=0):
                return []

        repo = MockBookshelfRepository()
        return DeleteBookshelfUseCase(repo)

    def get_get_basement_use_case(self):
        """鑾峰彇鍦颁笅瀹ょ敤渚?(Mock)"""
        from api.app.modules.bookshelf.application.use_cases.get_basement import GetBasementUseCase
        from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository

        class MockBookshelfRepository(IBookshelfRepository):
            async def save(self, bookshelf):
            return bookshelf

            async def get_by_id(self, id):
                return None

            async def get_by_library_id(self, id):
                return []

            async def get_basement_by_library_id(self, id):
                return None

            async def exists_by_name(self, lib_id, name):
                return False

            async def delete(self, id):
                pass

            async def exists(self, id):
                return False

            async def find_deleted_by_library(self, lib_id, limit=100, offset=0):
                return []

        repo = MockBookshelfRepository()
        return GetBasementUseCase(repo)

    # ==================== Book UseCase 宸ュ巶鏂规硶 ====================

    def get_create_book_use_case(self):
        """鑾峰彇鍒涘缓涔︾敤渚?(Mock)"""
        from api.app.modules.book.application.use_cases.create_book import CreateBookUseCase
        from api.app.modules.book.application.ports.output import IBookRepository

        class MockBookRepository(IBookRepository):
            async def save(self, book):
                # Return the book with ID set
                return book

            async def get_by_id(self, id):
                return None

            async def exists_by_title(self, shelf_id, title):
                return False

            async def list_by_bookshelf(self, shelf_id, limit=50, offset=0):
                return []

            async def delete(self, id):
                pass

            async def exists(self, id):
                return False

        repo = MockBookRepository()
        return CreateBookUseCase(repo)

    def get_list_books_use_case(self):
        """鑾峰彇鍒楄〃涔︾敤渚?(Mock)"""
        from api.app.modules.book.application.use_cases.list_books import ListBooksUseCase
        from api.app.modules.book.application.ports.output import IBookRepository

        class MockBookRepository(IBookRepository):
            async def save(self, book):
            return book

            async def get_by_id(self, id):
                return None

            async def exists_by_title(self, shelf_id, title):
                return False

            async def list_by_bookshelf(self, shelf_id, limit=50, offset=0):
                return []

            async def delete(self, id):
                pass

            async def exists(self, id):
                return False

        repo = MockBookRepository()
        return ListBooksUseCase(repo)

    def get_get_book_use_case(self):
        """鑾峰彇鍗曚釜涔︾敤渚?(Mock)"""
        from api.app.modules.book.application.use_cases.get_book import GetBookUseCase
        from api.app.modules.book.application.ports.output import IBookRepository

        class MockBookRepository(IBookRepository):
            async def save(self, book):
            return book

            async def get_by_id(self, id):
                return None

            async def exists_by_title(self, shelf_id, title):
                return False

            async def list_by_bookshelf(self, shelf_id, limit=50, offset=0):
                return []

            async def delete(self, id):
                pass

            async def exists(self, id):
                return False

        repo = MockBookRepository()
        return GetBookUseCase(repo)

    def get_update_book_use_case(self):
        """鑾峰彇鏇存柊涔︾敤渚?(Mock)"""
        from api.app.modules.book.application.use_cases.update_book import UpdateBookUseCase
        from api.app.modules.book.application.ports.output import IBookRepository

        class MockBookRepository(IBookRepository):
            async def save(self, book):
            return book

            async def get_by_id(self, id):
                return None

            async def exists_by_title(self, shelf_id, title):
                return False

            async def list_by_bookshelf(self, shelf_id, limit=50, offset=0):
                return []

            async def delete(self, id):
                pass

            async def exists(self, id):
                return False

        repo = MockBookRepository()
        return UpdateBookUseCase(repo)

    def get_delete_book_use_case(self):
        """鑾峰彇鍒犻櫎涔︾敤渚?(Mock)"""
        from api.app.modules.book.application.use_cases.delete_book import DeleteBookUseCase
        from api.app.modules.book.application.ports.output import IBookRepository

        class MockBookRepository(IBookRepository):
            async def save(self, book):
            return book

            async def get_by_id(self, id):
                return None

            async def exists_by_title(self, shelf_id, title):
                return False

            async def list_by_bookshelf(self, shelf_id, limit=50, offset=0):
                return []

            async def delete(self, id):
                pass

            async def exists(self, id):
                return False

        repo = MockBookRepository()
        return DeleteBookUseCase(repo)

    def get_move_book_use_case(self):
        """鑾峰彇绉诲姩涔︾敤渚?(Mock)"""
        from api.app.modules.book.application.use_cases.move_book import MoveBookUseCase
        from api.app.modules.book.application.ports.output import IBookRepository

        class MockBookRepository(IBookRepository):
            async def save(self, book):
            return book

            async def get_by_id(self, id):
                return None

            async def exists_by_title(self, shelf_id, title):
                return False

            async def list_by_bookshelf(self, shelf_id, limit=50, offset=0):
                return []

            async def delete(self, id):
                pass

            async def exists(self, id):
                return False

        repo = MockBookRepository()
        return MoveBookUseCase(repo)

    def get_restore_book_use_case(self):
        """鑾峰彇鎭㈠涔︾敤渚?(Mock)"""
        from api.app.modules.book.application.use_cases.restore_book import RestoreBookUseCase
        from api.app.modules.book.application.ports.output import IBookRepository

        class MockBookRepository(IBookRepository):
            async def save(self, book):
            return book

            async def get_by_id(self, id):
                return None

            async def exists_by_title(self, shelf_id, title):
                return False

            async def list_by_bookshelf(self, shelf_id, limit=50, offset=0):
                return []

            async def delete(self, id):
                pass

            async def exists(self, id):
                return False

        repo = MockBookRepository()
        return RestoreBookUseCase(repo)

    def get_list_deleted_books_use_case(self):
        """鑾峰彇鍒楄〃宸插垹闄や功鐢ㄤ緥 (Mock)"""
        from api.app.modules.book.application.use_cases.list_deleted_books import ListDeletedBooksUseCase
        from api.app.modules.book.application.ports.output import IBookRepository

        class MockBookRepository(IBookRepository):
            async def save(self, book):
            return book

            async def get_by_id(self, id):
                return None

            async def exists_by_title(self, shelf_id, title):
                return False

            async def list_by_bookshelf(self, shelf_id, limit=50, offset=0):
                return []

            async def delete(self, id):
                pass

            async def exists(self, id):
                return False

        repo = MockBookRepository()
        return ListDeletedBooksUseCase(repo)

    # ==================== Block UseCase 宸ュ巶鏂规硶 ====================

    def get_create_block_use_case(self):
        """鑾峰彇鍒涘缓鍧楃敤渚?(Mock)"""
        from api.app.modules.block.application.use_cases.create_block import CreateBlockUseCase
        from api.app.modules.block.application.ports.output import IBlockRepository

        class MockBlockRepository(IBlockRepository):
            async def save(self, block):
            return block

            async def get_by_id(self, id):
                return None

            async def delete(self, id):
                pass

            async def list_by_book(self, book_id, limit=100, offset=0):
                return []

            async def exists(self, id):
                return False

        repo = MockBlockRepository()
        return CreateBlockUseCase(repo)

    def get_list_blocks_use_case(self):
        """鑾峰彇鍒楄〃鍧楃敤渚?(Mock)"""
        from api.app.modules.block.application.use_cases.list_blocks import ListBlocksUseCase
        from api.app.modules.block.application.ports.output import IBlockRepository

        class MockBlockRepository(IBlockRepository):
            async def save(self, block):
            return block

            async def get_by_id(self, id):
                return None

            async def delete(self, id):
                pass

            async def list_by_book(self, book_id, limit=100, offset=0):
                return []

            async def exists(self, id):
                return False

        repo = MockBlockRepository()
        return ListBlocksUseCase(repo)

    def get_get_block_use_case(self):
        """鑾峰彇鍗曚釜鍧楃敤渚?(Mock)"""
        from api.app.modules.block.application.use_cases.get_block import GetBlockUseCase
        from api.app.modules.block.application.ports.output import IBlockRepository

        class MockBlockRepository(IBlockRepository):
            async def save(self, block):
            return block

            async def get_by_id(self, id):
                return None

            async def delete(self, id):
                pass

            async def list_by_book(self, book_id, limit=100, offset=0):
                return []

            async def exists(self, id):
                return False

        repo = MockBlockRepository()
        return GetBlockUseCase(repo)

    def get_update_block_use_case(self):
        """鑾峰彇鏇存柊鍧楃敤渚?(Mock)"""
        from api.app.modules.block.application.use_cases.update_block import UpdateBlockUseCase
        from api.app.modules.block.application.ports.output import IBlockRepository

        class MockBlockRepository(IBlockRepository):
            async def save(self, block):
            return block

            async def get_by_id(self, id):
                return None

            async def delete(self, id):
                pass

            async def list_by_book(self, book_id, limit=100, offset=0):
                return []

            async def exists(self, id):
                return False

        repo = MockBlockRepository()
        return UpdateBlockUseCase(repo)

    def get_reorder_blocks_use_case(self):
        """鑾峰彇閲嶆柊鎺掑簭鍧楃敤渚?(Mock)"""
        from api.app.modules.block.application.use_cases.reorder_blocks import ReorderBlocksUseCase
        from api.app.modules.block.application.ports.output import IBlockRepository

        class MockBlockRepository(IBlockRepository):
            async def save(self, block):
            return block

            async def get_by_id(self, id):
                return None

            async def delete(self, id):
                pass

            async def list_by_book(self, book_id, limit=100, offset=0):
                return []

            async def exists(self, id):
                return False

        repo = MockBlockRepository()
        return ReorderBlocksUseCase(repo)

    def get_delete_block_use_case(self):
        """鑾峰彇鍒犻櫎鍧楃敤渚?(Mock)"""
        from api.app.modules.block.application.use_cases.delete_block import DeleteBlockUseCase
        from api.app.modules.block.application.ports.output import IBlockRepository

        class MockBlockRepository(IBlockRepository):
            async def save(self, block):
            return block

            async def get_by_id(self, id):
                return None

            async def delete(self, id):
                pass

            async def list_by_book(self, book_id, limit=100, offset=0):
                return []

            async def exists(self, id):
                return False

        repo = MockBlockRepository()
        return DeleteBlockUseCase(repo)

    def get_restore_block_use_case(self):
        """鑾峰彇鎭㈠鍧楃敤渚?(Mock)"""
        from api.app.modules.block.application.use_cases.restore_block import RestoreBlockUseCase
        from api.app.modules.block.application.ports.output import IBlockRepository

        class MockBlockRepository(IBlockRepository):
            async def save(self, block):
            return block

            async def get_by_id(self, id):
                return None

            async def delete(self, id):
                pass

            async def list_by_book(self, book_id, limit=100, offset=0):
                return []

            async def exists(self, id):
                return False

        repo = MockBlockRepository()
        return RestoreBlockUseCase(repo)

    def get_list_deleted_blocks_use_case(self):
        """鑾峰彇鍒楄〃宸插垹闄ゅ潡鐢ㄤ緥 (Mock)"""
        from api.app.modules.block.application.use_cases.list_deleted_blocks import ListDeletedBlocksUseCase
        from api.app.modules.block.application.ports.output import IBlockRepository

        class MockBlockRepository(IBlockRepository):
            async def save(self, block):
            return block

            async def get_by_id(self, id):
                return None

            async def delete(self, id):
                pass

            async def list_by_book(self, book_id, limit=100, offset=0):
                return []

            async def exists(self, id):
                return False

        repo = MockBlockRepository()
        return ListDeletedBlocksUseCase(repo)

    # ========== Chronicle Services ==========
    def get_chronicle_recorder_service(self):
        return ChronicleRecorderService(self._chronicle_repo)

    def get_chronicle_query_service(self):
        return ChronicleQueryService(self._chronicle_repo)

