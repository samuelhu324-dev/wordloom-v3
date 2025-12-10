"""
Block 模块领域事件定义

定义 Block 聚合根产生的所有领域事件。
"""

from dataclasses import dataclass, field
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone

from api.app.shared.base import DomainEvent


@dataclass
class BlockCreated(DomainEvent):
    """块创建事件 (包含必要上下文字段)

    字段说明:
    - block_id: 新块 ID (作为 aggregate_id)
    - book_id: 所属书籍 ID
    - block_type: 类型字符串 (text, heading, ...)
    - content: 内容前若干字符 (避免事件过大)
    - order: 排序索引 (Fractional Index 当前值, 仅用于日志/监听)
    """
    block_id: UUID
    book_id: UUID
    block_type: str
    content: str
    order: float
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:  # 与其他事件保持一致接口
        return self.block_id


@dataclass
class BlockUpdated(DomainEvent):
    """块更新事件"""
    block_id: UUID
    book_id: UUID
    content: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.block_id


@dataclass
class BlockReordered(DomainEvent):
    """块重新排序事件"""
    block_id: UUID
    book_id: UUID
    old_order: float
    new_order: float
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.block_id


@dataclass
class BlockDeleted(DomainEvent):
    """块删除事件（逻辑删除）"""
    block_id: UUID
    book_id: UUID
    prev_sibling_id: Optional[str]
    next_sibling_id: Optional[str]
    section_path: Optional[str]
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.block_id


@dataclass
class BlockRestored(DomainEvent):
    """块恢复事件（从逻辑删除恢复）"""
    block_id: UUID
    book_id: UUID
    new_order: float
    recovery_level: int
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.block_id


__all__ = [
    "BlockCreated",
    "BlockUpdated",
    "BlockReordered",
    "BlockDeleted",
    "BlockRestored",
]
