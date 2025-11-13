"""
Media 模块领域事件定义

定义 Media 聚合根产生的所有领域事件。
"""

from dataclasses import dataclass, field
from uuid import UUID
from typing import Optional

from ....infra.event_bus import DomainEvent, EventType


@dataclass
class MediaUploaded(DomainEvent):
    """媒体上传事件"""

    filename: str = ""
    mime_type: str = ""
    file_size: int = 0
    media_type: str = ""  # image, video, etc.
    storage_path: str = ""

    def __post_init__(self):
        self.event_type = EventType.MEDIA_UPLOADED
        self.aggregate_type = "media"


@dataclass
class MediaDeleted(DomainEvent):
    """媒体删除事件（移到垃圾箱）"""

    soft_deleted: bool = True
    deleted_at: Optional[str] = None

    def __post_init__(self):
        self.event_type = EventType.MEDIA_DELETED
        self.aggregate_type = "media"


@dataclass
class MediaRestored(DomainEvent):
    """媒体恢复事件（从垃圾箱恢复）"""

    def __post_init__(self):
        self.event_type = EventType.MEDIA_RESTORED
        self.aggregate_type = "media"


@dataclass
class MediaPurged(DomainEvent):
    """媒体彻底删除事件（从垃圾箱永久删除）"""

    purged_at: Optional[str] = None

    def __post_init__(self):
        self.event_type = EventType.MEDIA_PURGED
        self.aggregate_type = "media"


@dataclass
class MediaAssociated(DomainEvent):
    """媒体关联事件"""

    entity_type: str = ""  # block, book, media_library, etc.
    entity_id: UUID = field(default_factory=lambda: UUID('00000000-0000-0000-0000-000000000000'))

    def __post_init__(self):
        self.event_type = EventType.MEDIA_ASSOCIATED
        self.aggregate_type = "media"


@dataclass
class MediaDisassociated(DomainEvent):
    """媒体取消关联事件"""

    entity_type: str = ""
    entity_id: UUID = field(default_factory=lambda: UUID('00000000-0000-0000-0000-000000000000'))

    def __post_init__(self):
        self.event_type = EventType.MEDIA_DISASSOCIATED
        self.aggregate_type = "media"


__all__ = [
    "MediaUploaded",
    "MediaDeleted",
    "MediaRestored",
    "MediaPurged",
    "MediaAssociated",
    "MediaDisassociated",
]
