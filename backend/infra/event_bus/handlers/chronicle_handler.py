"""Chronicle Event Handlers

将关键领域事件写入 Chronicle 事件存储。

当前处理范围：BookCreated / BookMovedToBookshelf / BookMovedToBasement /
BookRestoredFromBasement / BookDeleted。
Block 状态事件将于后续 Block 状态机完成后补充。
"""

import logging
from typing import Awaitable, Callable

from api.app.modules.book.domain.events import (
    BookCreated,
    BookDeleted,
    BookMovedToBasement,
    BookMovedToBookshelf,
    BookRenamed,
    BookRestoredFromBasement,
)
from api.app.modules.chronicle.application.services import ChronicleRecorderService
from api.app.modules.chronicle.domain import ChronicleEventType  # noqa: F401 (预留使用)
from infra.event_bus.event_handler_registry import EventHandlerRegistry
from infra.database.session import get_session_factory
from infra.storage.chronicle_repository_impl import SQLAlchemyChronicleRepository

logger = logging.getLogger(__name__)

RecorderOp = Callable[[ChronicleRecorderService], Awaitable[None]]


async def _record(op: RecorderOp, *, event_name: str) -> None:
    try:
        session_factory = await get_session_factory()
        async with session_factory() as session:
            repo = SQLAlchemyChronicleRepository(session)
            service = ChronicleRecorderService(repo)
            await op(service)
    except Exception as exc:  # pragma: no cover - 记录日志
        logger.error(
            "Failed to persist %s event to chronicle: %s", event_name, exc,
            exc_info=True,
        )


@EventHandlerRegistry.register(BookCreated)
async def chronicle_book_created(event: BookCreated) -> None:
    """将 BookCreated 写入 chronicle_events 表。"""

    await _record(
        lambda service: service.record_book_created(
            book_id=event.book_id,
            bookshelf_id=event.bookshelf_id,
            occurred_at=event.occurred_at,
        ),
        event_name="BookCreated",
    )


@EventHandlerRegistry.register(BookRenamed)
async def chronicle_book_renamed(event: BookRenamed) -> None:
    """将 BookRenamed 写入 chronicle_events 表。"""

    await _record(
        lambda service: service.record_book_renamed(
            book_id=event.book_id,
            from_title=event.old_title,
            to_title=event.new_title,
            occurred_at=event.occurred_at,
        ),
        event_name="BookRenamed",
    )


@EventHandlerRegistry.register(BookMovedToBookshelf)
async def chronicle_book_moved(event: BookMovedToBookshelf) -> None:
    """记录书籍跨书架移动事件。"""

    await _record(
        lambda service: service.record_book_moved(
            book_id=event.book_id,
            from_bookshelf_id=event.old_bookshelf_id,
            to_bookshelf_id=event.new_bookshelf_id,
            moved_at=event.moved_at,
        ),
        event_name="BookMovedToBookshelf",
    )


@EventHandlerRegistry.register(BookMovedToBasement)
async def chronicle_book_moved_to_basement(event: BookMovedToBasement) -> None:
    """记录书籍进入 Basement (软删除) 事件。"""

    await _record(
        lambda service: service.record_book_moved_to_basement(
            book_id=event.book_id,
            from_bookshelf_id=event.old_bookshelf_id,
            basement_bookshelf_id=event.basement_bookshelf_id,
            deleted_at=event.deleted_at,
        ),
        event_name="BookMovedToBasement",
    )


@EventHandlerRegistry.register(BookRestoredFromBasement)
async def chronicle_book_restored(event: BookRestoredFromBasement) -> None:
    """记录书籍从 Basement 恢复的事件。"""

    await _record(
        lambda service: service.record_book_restored(
            book_id=event.book_id,
            from_basement_id=event.basement_bookshelf_id,
            restored_to_bookshelf_id=event.restored_to_bookshelf_id,
            restored_at=event.restored_at,
        ),
        event_name="BookRestoredFromBasement",
    )


@EventHandlerRegistry.register(BookDeleted)
async def chronicle_book_deleted(event: BookDeleted) -> None:
    """记录书籍标记删除事件。"""

    await _record(
        lambda service: service.record_book_deleted(
            book_id=event.book_id,
            bookshelf_id=event.bookshelf_id,
            occurred_at=event.occurred_at,
        ),
        event_name="BookDeleted",
    )
