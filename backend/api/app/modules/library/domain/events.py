"""
Library 模块领域事件定义

定义 Library 聚合根产生的所有领域事件。
"""

from dataclasses import dataclass
from uuid import UUID

from ....infra.event_bus import DomainEvent, EventType


@dataclass
class LibraryCreated(DomainEvent):
    """库创建事件"""

    user_id: UUID = None

    def __post_init__(self):
        self.event_type = EventType.LIBRARY_CREATED
        self.aggregate_type = "library"


@dataclass
class LibraryDeleted(DomainEvent):
    """库删除事件"""

    user_id: UUID = None

    def __post_init__(self):
        self.event_type = EventType.LIBRARY_DELETED
        self.aggregate_type = "library"


__all__ = [
    "LibraryCreated",
    "LibraryDeleted",
]
