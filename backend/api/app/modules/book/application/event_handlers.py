"""
Book 模块事件处理器

处理 Book 聚合根产生的领域事件。
"""

from typing import List

from ..domain.events import (
    BookCreated,
    BookUpdated,
    BookDeleted,
    BookRestored,
)


class BookEventHandlers:
    """Book 事件处理器集合"""

    @staticmethod
    async def handle_book_created(event: BookCreated) -> None:
        """
        处理书籍创建事件

        可以在这里：
        - 创建初始块
        - 更新书架统计
        """
        print(f"✓ BookCreated: {event.title}")

    @staticmethod
    async def handle_book_updated(event: BookUpdated) -> None:
        """处理书籍更新事件"""
        print(f"✓ BookUpdated: {event.aggregate_id}")

    @staticmethod
    async def handle_book_deleted(event: BookDeleted) -> None:
        """处理书籍删除事件（逻辑删除）"""
        print(f"✓ BookDeleted: {event.aggregate_id}")

    @staticmethod
    async def handle_book_restored(event: BookRestored) -> None:
        """处理书籍恢复事件"""
        print(f"✓ BookRestored: {event.aggregate_id}")


def get_book_event_handlers() -> List:
    """获取 Book 事件处理器列表"""
    return [
        BookEventHandlers.handle_book_created,
        BookEventHandlers.handle_book_updated,
        BookEventHandlers.handle_book_deleted,
        BookEventHandlers.handle_book_restored,
    ]


__all__ = [
    "BookEventHandlers",
    "get_book_event_handlers",
]
