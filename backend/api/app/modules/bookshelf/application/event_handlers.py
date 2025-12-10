"""
Bookshelf 模块事件处理器

处理 Bookshelf 聚合根产生的领域事件。
"""

from typing import List

from ..domain.events import (
    BookshelfCreated,
    BookshelfUpdated,
    BookshelfDeleted,
)


class BookshelfEventHandlers:
    """Bookshelf 事件处理器集合"""

    @staticmethod
    async def handle_bookshelf_created(event: BookshelfCreated) -> None:
        """
        处理书架创建事件

        可以在这里：
        - 创建初始化数据
        - 发送通知
        """
        print(f"✓ BookshelfCreated: {event.name}")

    @staticmethod
    async def handle_bookshelf_updated(event: BookshelfUpdated) -> None:
        """处理书架更新事件"""
        print(f"✓ BookshelfUpdated: {event.aggregate_id}")

    @staticmethod
    async def handle_bookshelf_deleted(event: BookshelfDeleted) -> None:
        """处理书架删除事件"""
        print(f"✓ BookshelfDeleted: {event.aggregate_id}")


def get_bookshelf_event_handlers() -> List:
    """获取 Bookshelf 事件处理器列表"""
    return [
        BookshelfEventHandlers.handle_bookshelf_created,
        BookshelfEventHandlers.handle_bookshelf_updated,
        BookshelfEventHandlers.handle_bookshelf_deleted,
    ]


__all__ = [
    "BookshelfEventHandlers",
    "get_bookshelf_event_handlers",
]
