"""
Block 模块领域事件定义

定义 Block 聚合根产生的所有领域事件。
"""

from dataclasses import dataclass
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone

from api.app.shared.base import DomainEvent


@dataclass
class BlockCreated(DomainEvent):
    """块创建事件"""

    book_id: UUID = None
    block_type: str = ""  # TEXT, IMAGE, VIDEO, etc.
    content: str = ""

    def __post_init__(self):
        self.aggregate_type = "block"
        self.occurred_at = datetime.now(timezone.utc)


@dataclass
class BlockUpdated(DomainEvent):
    """块更新事件"""

    content: Optional[str] = None

    def __post_init__(self):
        self.aggregate_type = "block"
        self.occurred_at = datetime.now(timezone.utc)


@dataclass
class BlockReordered(DomainEvent):
    """块重新排序事件"""

    new_order: Optional[object] = None

    def __post_init__(self):
        self.aggregate_type = "block"
        self.occurred_at = datetime.now(timezone.utc)


@dataclass
class BlockDeleted(DomainEvent):
    """块删除事件（逻辑删除）"""

    soft_deleted: bool = True

    def __post_init__(self):
        self.aggregate_type = "block"
        self.occurred_at = datetime.now(timezone.utc)


@dataclass
class BlockRestored(DomainEvent):
    """块恢复事件（从逻辑删除恢复）"""

    def __post_init__(self):
        self.aggregate_type = "block"
        self.occurred_at = datetime.now(timezone.utc)


__all__ = [
    "BlockCreated",
    "BlockUpdated",
    "BlockReordered",
    "BlockDeleted",
    "BlockRestored",
]
