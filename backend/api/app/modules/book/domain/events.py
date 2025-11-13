"""
Book 模块领域事件定义

定义 Book 聚合根产生的所有领域事件。
"""

from dataclasses import dataclass
from uuid import UUID

from ....infra.event_bus import DomainEvent, EventType


@dataclass
class BookCreated(DomainEvent):
    """书籍创建事件"""

    bookshelf_id: UUID = None
    title: str = ""
    description: str = ""

    def __post_init__(self):
        self.event_type = EventType.BOOK_CREATED
        self.aggregate_type = "book"


@dataclass
class BookUpdated(DomainEvent):
    """书籍更新事件"""

    title: str = None
    description: str = None

    def __post_init__(self):
        self.event_type = EventType.BOOK_UPDATED
        self.aggregate_type = "book"


@dataclass
class BookDeleted(DomainEvent):
    """书籍删除事件（逻辑删除）"""

    soft_deleted: bool = True

    def __post_init__(self):
        self.event_type = EventType.BOOK_DELETED
        self.aggregate_type = "book"


@dataclass
class BookRestored(DomainEvent):
    """书籍恢复事件（从逻辑删除恢复）"""

    def __post_init__(self):
        self.event_type = EventType.BOOK_RESTORED
        self.aggregate_type = "book"


__all__ = [
    "BookCreated",
    "BookUpdated",
    "BookDeleted",
    "BookRestored",
]
