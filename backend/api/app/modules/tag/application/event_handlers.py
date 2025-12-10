"""
Tag 模块事件处理器

处理 Tag 聚合根产生的领域事件。
"""

from typing import List

from ..domain.events import (
    TagCreated,
    SubtagCreated,
    TagUpdated,
    TagDeleted,
    TagRestored,
    TagAssociated,
    TagDisassociated,
)


class TagEventHandlers:
    """Tag 事件处理器集合"""

    @staticmethod
    async def handle_tag_created(event: TagCreated) -> None:
        """
        处理 Tag 创建事件

        可以在这里：
        - 更新搜索索引
        - 发送通知
        - 更新缓存
        """
        print(f"✓ TagCreated: {event.tag_name}")

    @staticmethod
    async def handle_subtag_created(event: SubtagCreated) -> None:
        """处理 Subtag 创建事件"""
        print(f"✓ SubtagCreated: {event.subtag_name}")

    @staticmethod
    async def handle_tag_updated(event: TagUpdated) -> None:
        """处理 Tag 更新事件"""
        print(f"✓ TagUpdated: {event.aggregate_id}")

    @staticmethod
    async def handle_tag_deleted(event: TagDeleted) -> None:
        """处理 Tag 删除事件"""
        print(f"✓ TagDeleted: {event.aggregate_id}")

    @staticmethod
    async def handle_tag_restored(event: TagRestored) -> None:
        """处理 Tag 恢复事件"""
        print(f"✓ TagRestored: {event.aggregate_id}")

    @staticmethod
    async def handle_tag_associated(event: TagAssociated) -> None:
        """处理 Tag 关联事件"""
        print(f"✓ TagAssociated: tag={event.aggregate_id}, entity={event.entity_type}:{event.entity_id}")

    @staticmethod
    async def handle_tag_disassociated(event: TagDisassociated) -> None:
        """处理 Tag 取消关联事件"""
        print(f"✓ TagDisassociated: tag={event.aggregate_id}, entity={event.entity_type}:{event.entity_id}")


def get_tag_event_handlers() -> List:
    """获取 Tag 事件处理器列表"""
    return [
        TagEventHandlers.handle_tag_created,
        TagEventHandlers.handle_subtag_created,
        TagEventHandlers.handle_tag_updated,
        TagEventHandlers.handle_tag_deleted,
        TagEventHandlers.handle_tag_restored,
        TagEventHandlers.handle_tag_associated,
        TagEventHandlers.handle_tag_disassociated,
    ]


__all__ = [
    "TagEventHandlers",
    "get_tag_event_handlers",
]
