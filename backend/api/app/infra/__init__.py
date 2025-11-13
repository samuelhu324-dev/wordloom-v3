"""
Infrastructure 层

包含所有跨模块的基础设施代码：
- 数据库连接和 ORM 配置
- EventBus 事件系统
- 日志、缓存、存储等
"""

from .event_bus import (
    DomainEvent,
    EventType,
    IEventBus,
    EventBus,
    EventHandler,
    AsyncEventHandler,
    get_event_bus,
    reset_event_bus,
)

from .event_handler_registry import (
    EventHandlerRegistry,
    setup_event_handlers,
)

__all__ = [
    # EventBus
    "DomainEvent",
    "EventType",
    "IEventBus",
    "EventBus",
    "EventHandler",
    "AsyncEventHandler",
    "get_event_bus",
    "reset_event_bus",
    # Event Handler Registry
    "EventHandlerRegistry",
    "setup_event_handlers",
]
