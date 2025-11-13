"""
Bookshelf 模块领域事件定义

定义 Bookshelf 聚合根产生的所有领域事件。
"""

from dataclasses import dataclass
from uuid import UUID

from ....infra.event_bus import DomainEvent, EventType


@dataclass
class BookshelfCreated(DomainEvent):
    """书架创建事件"""

    library_id: UUID = None
    name: str = ""
    description: str = ""
    is_basement: bool = False

    def __post_init__(self):
        self.event_type = EventType.BOOKSHELF_CREATED
        self.aggregate_type = "bookshelf"


@dataclass
class BookshelfUpdated(DomainEvent):
    """书架更新事件"""

    name: str = None
    description: str = None

    def __post_init__(self):
        self.event_type = EventType.BOOKSHELF_UPDATED
        self.aggregate_type = "bookshelf"


@dataclass
class BookshelfDeleted(DomainEvent):
    """书架删除事件"""

    def __post_init__(self):
        self.event_type = EventType.BOOKSHELF_DELETED
        self.aggregate_type = "bookshelf"


__all__ = [
    "BookshelfCreated",
    "BookshelfUpdated",
    "BookshelfDeleted",
]
