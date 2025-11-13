"""
EventBus 事件处理器注册表

在应用启动时，将所有事件处理器注册到 EventBus 中。
"""

from typing import Dict, List

from .event_bus import EventBus, EventType


class EventHandlerRegistry:
    """事件处理器注册表"""

    def __init__(self, event_bus: EventBus):
        """
        初始化事件处理器注册表

        Args:
            event_bus: EventBus 实例
        """
        self.event_bus = event_bus
        self._registered_handlers: Dict[EventType, List] = {}

    def register_handler(self, event_type: EventType, handler) -> None:
        """
        注册事件处理器

        Args:
            event_type: 事件类型
            handler: 处理器函数
        """
        self.event_bus.subscribe(event_type, handler)

        if event_type not in self._registered_handlers:
            self._registered_handlers[event_type] = []
        self._registered_handlers[event_type].append(handler)

    def register_handlers(self, handlers_map: Dict[EventType, List]) -> None:
        """
        批量注册事件处理器

        Args:
            handlers_map: {EventType: [handler1, handler2, ...]}
        """
        for event_type, handlers in handlers_map.items():
            for handler in handlers:
                self.register_handler(event_type, handler)

    def get_registered_handlers(self, event_type: EventType = None) -> Dict[EventType, List] | List:
        """获取已注册的处理器"""
        if event_type is None:
            return self._registered_handlers
        return self._registered_handlers.get(event_type, [])

    def clear(self) -> None:
        """清空所有注册"""
        self._registered_handlers.clear()
        self.event_bus.clear()


def setup_event_handlers(event_bus: EventBus) -> EventHandlerRegistry:
    """
    设置所有事件处理器

    这是应用启动时调用的主要函数。
    它导入所有模块的事件处理器并将它们注册到 EventBus。

    Args:
        event_bus: EventBus 实例

    Returns:
        EventHandlerRegistry 实例

    Example:
        from infra.event_bus import get_event_bus
        from infra.event_handler_registry import setup_event_handlers

        bus = get_event_bus()
        registry = setup_event_handlers(bus)
    """
    registry = EventHandlerRegistry(event_bus)

    # 注册 Tag 事件处理器
    try:
        from modules.tag.application.event_handlers import (
            TagEventHandlers,
        )
        from infra.event_bus import EventType

        registry.register_handler(EventType.TAG_CREATED, TagEventHandlers.handle_tag_created)
        registry.register_handler(EventType.TAG_UPDATED, TagEventHandlers.handle_tag_updated)
        registry.register_handler(EventType.TAG_DELETED, TagEventHandlers.handle_tag_deleted)
        registry.register_handler(EventType.TAG_RESTORED, TagEventHandlers.handle_tag_restored)
        registry.register_handler(EventType.TAG_ASSOCIATED, TagEventHandlers.handle_tag_associated)
        registry.register_handler(EventType.TAG_DISASSOCIATED, TagEventHandlers.handle_tag_disassociated)
    except Exception as e:
        print(f"Warning: Could not register Tag event handlers: {e}")

    # 注册 Media 事件处理器
    try:
        from modules.media.application.event_handlers import (
            MediaEventHandlers,
        )

        registry.register_handler(EventType.MEDIA_UPLOADED, MediaEventHandlers.handle_media_uploaded)
        registry.register_handler(EventType.MEDIA_DELETED, MediaEventHandlers.handle_media_deleted)
        registry.register_handler(EventType.MEDIA_RESTORED, MediaEventHandlers.handle_media_restored)
        registry.register_handler(EventType.MEDIA_PURGED, MediaEventHandlers.handle_media_purged)
        registry.register_handler(EventType.MEDIA_ASSOCIATED, MediaEventHandlers.handle_media_associated)
        registry.register_handler(EventType.MEDIA_DISASSOCIATED, MediaEventHandlers.handle_media_disassociated)
    except Exception as e:
        print(f"Warning: Could not register Media event handlers: {e}")

    # 注册 Bookshelf 事件处理器
    try:
        from modules.bookshelf.application.event_handlers import (
            BookshelfEventHandlers,
        )

        registry.register_handler(EventType.BOOKSHELF_CREATED, BookshelfEventHandlers.handle_bookshelf_created)
        registry.register_handler(EventType.BOOKSHELF_UPDATED, BookshelfEventHandlers.handle_bookshelf_updated)
        registry.register_handler(EventType.BOOKSHELF_DELETED, BookshelfEventHandlers.handle_bookshelf_deleted)
    except Exception as e:
        print(f"Warning: Could not register Bookshelf event handlers: {e}")

    # 注册 Book 事件处理器
    try:
        from modules.book.application.event_handlers import (
            BookEventHandlers,
        )

        registry.register_handler(EventType.BOOK_CREATED, BookEventHandlers.handle_book_created)
        registry.register_handler(EventType.BOOK_UPDATED, BookEventHandlers.handle_book_updated)
        registry.register_handler(EventType.BOOK_DELETED, BookEventHandlers.handle_book_deleted)
        registry.register_handler(EventType.BOOK_RESTORED, BookEventHandlers.handle_book_restored)
    except Exception as e:
        print(f"Warning: Could not register Book event handlers: {e}")

    # 注册 Block 事件处理器
    try:
        from modules.block.application.event_handlers import (
            BlockEventHandlers,
        )

        registry.register_handler(EventType.BLOCK_CREATED, BlockEventHandlers.handle_block_created)
        registry.register_handler(EventType.BLOCK_UPDATED, BlockEventHandlers.handle_block_updated)
        registry.register_handler(EventType.BLOCK_REORDERED, BlockEventHandlers.handle_block_reordered)
        registry.register_handler(EventType.BLOCK_DELETED, BlockEventHandlers.handle_block_deleted)
        registry.register_handler(EventType.BLOCK_RESTORED, BlockEventHandlers.handle_block_restored)
    except Exception as e:
        print(f"Warning: Could not register Block event handlers: {e}")

    # 注册 Library 事件处理器
    try:
        from modules.library.application.event_handlers import (
            LibraryEventHandlers,
        )

        registry.register_handler(EventType.LIBRARY_CREATED, LibraryEventHandlers.handle_library_created)
        registry.register_handler(EventType.LIBRARY_DELETED, LibraryEventHandlers.handle_library_deleted)
    except Exception as e:
        print(f"Warning: Could not register Library event handlers: {e}")

    return registry


__all__ = [
    "EventHandlerRegistry",
    "setup_event_handlers",
]
