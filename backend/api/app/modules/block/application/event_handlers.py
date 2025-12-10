"""
Block 模块事件处理器

处理 Block 聚合根产生的领域事件。
"""

from typing import List

from ..domain.events import (
    BlockCreated,
    BlockUpdated,
    BlockReordered,
    BlockDeleted,
    BlockRestored,
)


class BlockEventHandlers:
    """Block 事件处理器集合"""

    @staticmethod
    async def handle_block_created(event: BlockCreated) -> None:
        """
        处理块创建事件

        可以在这里：
        - 更新书籍块数统计
        - 生成版本记录
        """
        print(f"✓ BlockCreated: {event.block_type}")

    @staticmethod
    async def handle_block_updated(event: BlockUpdated) -> None:
        """处理块更新事件"""
        print(f"✓ BlockUpdated: {event.aggregate_id}")

    @staticmethod
    async def handle_block_reordered(event: BlockReordered) -> None:
        """处理块重新排序事件"""
        print(f"✓ BlockReordered: {event.aggregate_id} to {event.new_index}")

    @staticmethod
    async def handle_block_deleted(event: BlockDeleted) -> None:
        """处理块删除事件（逻辑删除）"""
        print(f"✓ BlockDeleted: {event.aggregate_id}")

    @staticmethod
    async def handle_block_restored(event: BlockRestored) -> None:
        """处理块恢复事件"""
        print(f"✓ BlockRestored: {event.aggregate_id}")


def get_block_event_handlers() -> List:
    """获取 Block 事件处理器列表"""
    return [
        BlockEventHandlers.handle_block_created,
        BlockEventHandlers.handle_block_updated,
        BlockEventHandlers.handle_block_reordered,
        BlockEventHandlers.handle_block_deleted,
        BlockEventHandlers.handle_block_restored,
    ]


__all__ = [
    "BlockEventHandlers",
    "get_block_event_handlers",
]
