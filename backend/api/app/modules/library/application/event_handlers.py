"""
Library 模块事件处理器

处理 Library 聚合根产生的领域事件。
"""

from typing import List

from ..domain.events import (
    LibraryCreated,
    LibraryDeleted,
)


class LibraryEventHandlers:
    """Library 事件处理器集合"""

    @staticmethod
    async def handle_library_created(event: LibraryCreated) -> None:
        """
        处理库创建事件

        可以在这里：
        - 初始化默认书架
        - 创建 Basement
        """
        print(f"✓ LibraryCreated: {event.user_id}")

    @staticmethod
    async def handle_library_deleted(event: LibraryDeleted) -> None:
        """处理库删除事件"""
        print(f"✓ LibraryDeleted: {event.user_id}")


def get_library_event_handlers() -> List:
    """获取 Library 事件处理器列表"""
    return [
        LibraryEventHandlers.handle_library_created,
        LibraryEventHandlers.handle_library_deleted,
    ]


__all__ = [
    "LibraryEventHandlers",
    "get_library_event_handlers",
]
