"""
Search Index EventBus Handlers

职责:
- 监听 Block/Tag 域事件 (BlockCreated/Updated/Deleted, TagCreated/Updated/Deleted)
- 自动更新 search_index 表
- 保持搜索索引与实体状态同步

Handler 列表 (6个):
1. BlockCreated → INSERT search_index
2. BlockUpdated → UPDATE search_index
3. BlockDeleted → DELETE search_index
4. TagCreated → INSERT search_index
5. TagUpdated → UPDATE search_index
6. TagDeleted → DELETE search_index

POLICY: 事件驱动的索引维护，零延迟同步，自动化处理
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.modules.block.domain.events import BlockCreated, BlockUpdated, BlockDeleted
from api.app.modules.tag.domain.events import TagCreated, TagRenamed, TagDeleted

from infra.event_bus.event_handler_registry import EventHandlerRegistry
from infra.search.search_indexer import get_search_indexer

logger = logging.getLogger(__name__)


# ============================================================================
# Block Event Handlers (3个)
# ============================================================================

@EventHandlerRegistry.register(BlockCreated)
async def on_block_created(event: BlockCreated, db: AsyncSession) -> None:
    """
    Block 创建事件处理器 → INSERT search_index

    操作:
    - 创建新的 search_index 记录
    - 提取 block 内容作为搜索文本
    - 生成片段摘要

    字段映射:
    - entity_type: "block"
    - entity_id: event.block_id
    - text: event.content
    - snippet: event.content[:200] (前200字符)
    - rank_score: 0.0 (初始分数)
    """
    indexer = get_search_indexer(db)
    await indexer.index_block_created(event)


@EventHandlerRegistry.register(BlockUpdated)
async def on_block_updated(event: BlockUpdated, db: AsyncSession) -> None:
    """
    Block 更新事件处理器 → UPDATE search_index

    操作:
    - 更新现有的 search_index 记录
    - 刷新搜索文本和摘要
    - updated_at 自动更新 (ORM 触发器)

    字段更新:
    - text: event.content
    - snippet: event.content[:200]
    """
    indexer = get_search_indexer(db)
    await indexer.index_block_updated(event)


@EventHandlerRegistry.register(BlockDeleted)
async def on_block_deleted(event: BlockDeleted, db: AsyncSession) -> None:
    """
    Block 删除事件处理器 → DELETE search_index

    操作:
    - 从 search_index 删除对应记录
    - 确保搜索结果不再包含已删除的 block
    """
    indexer = get_search_indexer(db)
    await indexer.delete_block(block_id=event.block_id)


# ============================================================================
# Tag Event Handlers (3个)
# ============================================================================

@EventHandlerRegistry.register(TagCreated)
async def on_tag_created(event: TagCreated, db: AsyncSession) -> None:
    """
    Tag 创建事件处理器 → INSERT search_index

    操作:
    - 创建新的 search_index 记录
    - tag name 作为搜索文本
    - tag 是较短的文本，snippet = name

    字段映射:
    - entity_type: "tag"
    - entity_id: event.tag_id
    - text: event.name (tag 名称)
    - snippet: event.name (tag 较短，直接用 name)
    - rank_score: 0.0 (初始分数)
    """
    indexer = get_search_indexer(db)
    await indexer.index_tag_created(event)


@EventHandlerRegistry.register(TagRenamed)
async def on_tag_renamed(event: TagRenamed, db: AsyncSession) -> None:
    """
    Tag 更新事件处理器 → UPDATE search_index

    操作:
    - 更新现有的 search_index 记录
    - 刷新 tag 名称
    - updated_at 自动更新 (ORM 触发器)

    字段更新:
    - text: event.name (新的 tag 名称)
    - snippet: event.name
    """
    indexer = get_search_indexer(db)
    await indexer.index_tag_renamed(event)


@EventHandlerRegistry.register(TagDeleted)
async def on_tag_deleted(event: TagDeleted, db: AsyncSession) -> None:
    """
    Tag 删除事件处理器 → DELETE search_index

    操作:
    - 从 search_index 删除对应记录
    - 确保搜索结果不再包含已删除的 tag
    """
    indexer = get_search_indexer(db)
    await indexer.delete_tag(tag_id=event.tag_id)


__all__ = [
    "on_block_created",
    "on_block_updated",
    "on_block_deleted",
    "on_tag_created",
    "on_tag_renamed",
    "on_tag_deleted",
]
