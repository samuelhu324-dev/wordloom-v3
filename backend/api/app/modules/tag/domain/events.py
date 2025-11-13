"""
Tag 模块领域事件定义

定义 Tag 聚合根产生的所有领域事件。
"""

from dataclasses import dataclass, field
from uuid import UUID
from typing import Optional, List

# 导入 EventBus 类（在 infra 模块中）
from ....infra.event_bus import DomainEvent, EventType


@dataclass
class TagCreated(DomainEvent):
    """Tag 创建事件"""

    tag_name: str = ""
    color: str = "#666666"
    icon: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        self.event_type = EventType.TAG_CREATED
        self.aggregate_type = "tag"


@dataclass
class SubtagCreated(DomainEvent):
    """Subtag 创建事件"""

    parent_tag_id: UUID = field(default_factory=lambda: UUID('00000000-0000-0000-0000-000000000000'))
    subtag_name: str = ""
    color: str = "#666666"
    icon: Optional[str] = None

    def __post_init__(self):
        self.event_type = EventType.TAG_CREATED
        self.aggregate_type = "tag"


@dataclass
class TagUpdated(DomainEvent):
    """Tag 更新事件"""

    tag_name: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        self.event_type = EventType.TAG_UPDATED
        self.aggregate_type = "tag"


@dataclass
class TagDeleted(DomainEvent):
    """Tag 删除事件（逻辑删除）"""

    soft_deleted: bool = True

    def __post_init__(self):
        self.event_type = EventType.TAG_DELETED
        self.aggregate_type = "tag"


@dataclass
class TagRestored(DomainEvent):
    """Tag 恢复事件（从逻辑删除恢复）"""

    def __post_init__(self):
        self.event_type = EventType.TAG_RESTORED
        self.aggregate_type = "tag"


@dataclass
class TagAssociated(DomainEvent):
    """Tag 关联事件"""

    entity_type: str = ""  # book, block, media, etc.
    entity_id: UUID = field(default_factory=lambda: UUID('00000000-0000-0000-0000-000000000000'))

    def __post_init__(self):
        self.event_type = EventType.TAG_ASSOCIATED
        self.aggregate_type = "tag"


@dataclass
class TagDisassociated(DomainEvent):
    """Tag 取消关联事件"""

    entity_type: str = ""
    entity_id: UUID = field(default_factory=lambda: UUID('00000000-0000-0000-0000-000000000000'))

    def __post_init__(self):
        self.event_type = EventType.TAG_DISASSOCIATED
        self.aggregate_type = "tag"


__all__ = [
    "TagCreated",
    "SubtagCreated",
    "TagUpdated",
    "TagDeleted",
    "TagRestored",
    "TagAssociated",
    "TagDisassociated",
]
