"""
Media 模块事件处理器

处理 Media 聚合根产生的领域事件。
"""

from typing import List

from ..domain.events import (
    MediaUploaded,
    MediaDeleted,
    MediaRestored,
    MediaPurged,
    MediaAssociated,
    MediaDisassociated,
)


class MediaEventHandlers:
    """Media 事件处理器集合"""

    @staticmethod
    async def handle_media_uploaded(event: MediaUploaded) -> None:
        """
        处理媒体上传事件

        可以在这里：
        - 生成缩略图
        - 更新搜索索引
        - 触发病毒扫描
        """
        print(f"✓ MediaUploaded: {event.filename} ({event.mime_type})")

    @staticmethod
    async def handle_media_deleted(event: MediaDeleted) -> None:
        """处理媒体删除事件（移到垃圾箱）"""
        print(f"✓ MediaDeleted: {event.aggregate_id}")

    @staticmethod
    async def handle_media_restored(event: MediaRestored) -> None:
        """处理媒体恢复事件（从垃圾箱恢复）"""
        print(f"✓ MediaRestored: {event.aggregate_id}")

    @staticmethod
    async def handle_media_purged(event: MediaPurged) -> None:
        """处理媒体彻底删除事件"""
        print(f"✓ MediaPurged: {event.aggregate_id}")

    @staticmethod
    async def handle_media_associated(event: MediaAssociated) -> None:
        """处理媒体关联事件"""
        print(f"✓ MediaAssociated: media={event.aggregate_id}, entity={event.entity_type}:{event.entity_id}")

    @staticmethod
    async def handle_media_disassociated(event: MediaDisassociated) -> None:
        """处理媒体取消关联事件"""
        print(f"✓ MediaDisassociated: media={event.aggregate_id}, entity={event.entity_type}:{event.entity_id}")


def get_media_event_handlers() -> List:
    """获取 Media 事件处理器列表"""
    return [
        MediaEventHandlers.handle_media_uploaded,
        MediaEventHandlers.handle_media_deleted,
        MediaEventHandlers.handle_media_restored,
        MediaEventHandlers.handle_media_purged,
        MediaEventHandlers.handle_media_associated,
        MediaEventHandlers.handle_media_disassociated,
    ]


__all__ = [
    "MediaEventHandlers",
    "get_media_event_handlers",
]
