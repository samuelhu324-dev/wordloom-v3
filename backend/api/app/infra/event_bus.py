"""
EventBus 基础设施模块

实现发布-订阅模式，用于发送和处理领域事件。
支持异步事件处理和多个事件处理器。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Set, Type, TypeVar
from uuid import UUID, uuid4
import asyncio
from enum import Enum


# ====== Domain Event Base Classes ======

class EventType(str, Enum):
    """事件类型枚举"""
    # Tag Events
    TAG_CREATED = "tag.created"
    TAG_UPDATED = "tag.updated"
    TAG_DELETED = "tag.deleted"
    TAG_RESTORED = "tag.restored"
    TAG_ASSOCIATED = "tag.associated"
    TAG_DISASSOCIATED = "tag.disassociated"

    # Media Events
    MEDIA_UPLOADED = "media.uploaded"
    MEDIA_DELETED = "media.deleted"
    MEDIA_RESTORED = "media.restored"
    MEDIA_PURGED = "media.purged"
    MEDIA_ASSOCIATED = "media.associated"
    MEDIA_DISASSOCIATED = "media.disassociated"

    # Library Events
    LIBRARY_CREATED = "library.created"
    LIBRARY_DELETED = "library.deleted"

    # Bookshelf Events
    BOOKSHELF_CREATED = "bookshelf.created"
    BOOKSHELF_UPDATED = "bookshelf.updated"
    BOOKSHELF_DELETED = "bookshelf.deleted"

    # Book Events
    BOOK_CREATED = "book.created"
    BOOK_UPDATED = "book.updated"
    BOOK_DELETED = "book.deleted"
    BOOK_RESTORED = "book.restored"

    # Block Events
    BLOCK_CREATED = "block.created"
    BLOCK_UPDATED = "block.updated"
    BLOCK_REORDERED = "block.reordered"
    BLOCK_DELETED = "block.deleted"
    BLOCK_RESTORED = "block.restored"


@dataclass
class DomainEvent(ABC):
    """
    领域事件基类

    所有领域事件应继承此类。
    事件在业务操作完成后发布，其他部分可订阅并响应。
    """

    event_id: UUID = field(default_factory=uuid4)
    event_type: EventType = field(init=False)
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    aggregate_id: UUID = field(default_factory=uuid4)  # 触发事件的聚合根 ID
    aggregate_type: str = ""  # 聚合根类型 (tag, media, book, etc.)
    version: int = 1  # 事件版本

    def __post_init__(self):
        """子类应设置 event_type"""
        pass


# ====== Event Bus Interface ======

EventHandler = Callable[[DomainEvent], Any]
AsyncEventHandler = Callable[[DomainEvent], asyncio.coroutine]

T = TypeVar('T', bound=DomainEvent)


class IEventBus(ABC):
    """事件总线接口"""

    @abstractmethod
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        订阅事件

        Args:
            event_type: 事件类型
            handler: 事件处理函数
        """
        pass

    @abstractmethod
    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        取消订阅

        Args:
            event_type: 事件类型
            handler: 事件处理函数
        """
        pass

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """
        发布事件

        Args:
            event: 要发布的事件
        """
        pass

    @abstractmethod
    async def publish_async(self, event: DomainEvent, handlers: List[AsyncEventHandler]) -> None:
        """
        异步发布事件给多个处理器

        Args:
            event: 要发布的事件
            handlers: 异步处理器列表
        """
        pass

    @abstractmethod
    def get_handlers(self, event_type: EventType) -> List[EventHandler]:
        """获取特定事件类型的所有处理器"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空所有订阅"""
        pass


# ====== Event Bus Implementation ======

class EventBus(IEventBus):
    """
    同步和异步事件总线实现

    支持：
    - 订阅和取消订阅事件
    - 发布事件到所有订阅者
    - 同步和异步事件处理
    - 错误处理和日志记录
    """

    def __init__(self):
        """初始化事件总线"""
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._async_handlers: Dict[EventType, List[AsyncEventHandler]] = {}
        self._published_events: List[DomainEvent] = []

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        订阅事件

        Args:
            event_type: 事件类型
            handler: 事件处理函数

        Example:
            bus = EventBus()

            def on_tag_created(event: TagCreated):
                print(f"Tag created: {event.tag_name}")

            bus.subscribe(EventType.TAG_CREATED, on_tag_created)
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        取消订阅事件

        Args:
            event_type: 事件类型
            handler: 事件处理函数
        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    async def publish(self, event: DomainEvent) -> None:
        """
        发布事件到所有订阅者

        支持同步处理器。

        Args:
            event: 要发布的事件

        Example:
            event = TagCreated(
                aggregate_id=tag_id,
                aggregate_type="tag",
                tag_name="Python"
            )
            await bus.publish(event)
        """
        self._published_events.append(event)

        handlers = self._handlers.get(event.event_type, [])

        for handler in handlers:
            try:
                result = handler(event)
                # 如果处理器返回一个协程，等待它
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                # 记录错误但不影响其他处理器
                print(f"Error in event handler for {event.event_type}: {str(e)}")

    async def publish_async(self, event: DomainEvent, handlers: List[AsyncEventHandler]) -> None:
        """
        异步发布事件给多个异步处理器

        并发执行所有处理器。

        Args:
            event: 要发布的事件
            handlers: 异步处理器列表
        """
        self._published_events.append(event)

        tasks = [handler(event) for handler in handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 检查是否有错误
        for result in results:
            if isinstance(result, Exception):
                print(f"Error in async event handler: {str(result)}")

    def get_handlers(self, event_type: EventType) -> List[EventHandler]:
        """获取特定事件类型的所有处理器"""
        return self._handlers.get(event_type, [])

    def get_published_events(self) -> List[DomainEvent]:
        """获取已发布的所有事件（用于测试）"""
        return self._published_events.copy()

    def clear(self) -> None:
        """清空所有订阅和已发布的事件"""
        self._handlers.clear()
        self._async_handlers.clear()
        self._published_events.clear()

    def __repr__(self) -> str:
        event_types = list(self._handlers.keys())
        handler_count = sum(len(h) for h in self._handlers.values())
        return f"EventBus(event_types={len(event_types)}, handlers={handler_count})"


# ====== Singleton Instance ======

_event_bus_instance: EventBus | None = None


def get_event_bus() -> EventBus:
    """
    获取全局事件总线实例（单例）

    Returns:
        全局 EventBus 实例

    Example:
        bus = get_event_bus()
        bus.subscribe(EventType.TAG_CREATED, on_tag_created)
    """
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance


def reset_event_bus() -> None:
    """重置事件总线（用于测试）"""
    global _event_bus_instance
    if _event_bus_instance is not None:
        _event_bus_instance.clear()
        _event_bus_instance = None


__all__ = [
    "DomainEvent",
    "EventType",
    "IEventBus",
    "EventBus",
    "EventHandler",
    "AsyncEventHandler",
    "get_event_bus",
    "reset_event_bus",
]
