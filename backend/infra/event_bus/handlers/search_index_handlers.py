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
from sqlalchemy.orm import Session
from sqlalchemy import insert, update, delete

from app.infra.database.models.search_index_models import SearchIndexModel
from app.modules.block.domain.events import BlockCreated, BlockUpdated, BlockDeleted
from app.modules.tag.domain.events import TagCreated, TagUpdated, TagDeleted
from app.infra.event_bus.event_handler import event_handler

logger = logging.getLogger(__name__)


# ============================================================================
# Block Event Handlers (3个)
# ============================================================================

@event_handler(BlockCreated)
async def on_block_created(event: BlockCreated, db: Session) -> None:
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
    try:
        stmt = insert(SearchIndexModel).values(
            entity_type="block",
            entity_id=event.block_id,
            text=event.content or "",
            snippet=(event.content or "")[:200],
            rank_score=0.0,
        )
        db.execute(stmt)
        db.commit()
        logger.info(f"Search index: inserted block {event.block_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to index block {event.block_id}: {str(e)}")
        raise


@event_handler(BlockUpdated)
async def on_block_updated(event: BlockUpdated, db: Session) -> None:
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
    try:
        stmt = (
            update(SearchIndexModel)
            .where(
                SearchIndexModel.entity_type == "block",
                SearchIndexModel.entity_id == event.block_id,
            )
            .values(
                text=event.content or "",
                snippet=(event.content or "")[:200],
            )
        )
        db.execute(stmt)
        db.commit()
        logger.info(f"Search index: updated block {event.block_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update search index for block {event.block_id}: {str(e)}")
        raise


@event_handler(BlockDeleted)
async def on_block_deleted(event: BlockDeleted, db: Session) -> None:
    """
    Block 删除事件处理器 → DELETE search_index

    操作:
    - 从 search_index 删除对应记录
    - 确保搜索结果不再包含已删除的 block
    """
    try:
        stmt = delete(SearchIndexModel).where(
            SearchIndexModel.entity_type == "block",
            SearchIndexModel.entity_id == event.block_id,
        )
        db.execute(stmt)
        db.commit()
        logger.info(f"Search index: deleted block {event.block_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete search index for block {event.block_id}: {str(e)}")
        raise


# ============================================================================
# Tag Event Handlers (3个)
# ============================================================================

@event_handler(TagCreated)
async def on_tag_created(event: TagCreated, db: Session) -> None:
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
    try:
        stmt = insert(SearchIndexModel).values(
            entity_type="tag",
            entity_id=event.tag_id,
            text=event.name or "",
            snippet=event.name or "",
            rank_score=0.0,
        )
        db.execute(stmt)
        db.commit()
        logger.info(f"Search index: inserted tag {event.tag_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to index tag {event.tag_id}: {str(e)}")
        raise


@event_handler(TagUpdated)
async def on_tag_updated(event: TagUpdated, db: Session) -> None:
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
    try:
        stmt = (
            update(SearchIndexModel)
            .where(
                SearchIndexModel.entity_type == "tag",
                SearchIndexModel.entity_id == event.tag_id,
            )
            .values(
                text=event.name or "",
                snippet=event.name or "",
            )
        )
        db.execute(stmt)
        db.commit()
        logger.info(f"Search index: updated tag {event.tag_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update search index for tag {event.tag_id}: {str(e)}")
        raise


@event_handler(TagDeleted)
async def on_tag_deleted(event: TagDeleted, db: Session) -> None:
    """
    Tag 删除事件处理器 → DELETE search_index

    操作:
    - 从 search_index 删除对应记录
    - 确保搜索结果不再包含已删除的 tag
    """
    try:
        stmt = delete(SearchIndexModel).where(
            SearchIndexModel.entity_type == "tag",
            SearchIndexModel.entity_id == event.tag_id,
        )
        db.execute(stmt)
        db.commit()
        logger.info(f"Search index: deleted tag {event.tag_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete search index for tag {event.tag_id}: {str(e)}")
        raise


__all__ = [
    "on_block_created",
    "on_block_updated",
    "on_block_deleted",
    "on_tag_created",
    "on_tag_updated",
    "on_tag_deleted",
]


# ============================================================================
# Block Event Handlers
# ============================================================================

@event_handler(BlockCreated)
async def on_block_created(event: BlockCreated, db: Session) -> None:
    """
    Block 创建事件处理器

    操作: INSERT into search_index

    字段映射:
    - entity_type: "block"
    - entity_id: event.block_id
    - text: event.content
    - snippet: event.content[:200]
    """
    try:
        stmt = insert(SearchIndexModel).values(
            entity_type="block",
            entity_id=event.block_id,
            text=event.content or "",
            snippet=(event.content or "")[:200],
            rank_score=0.0,
        )
        db.execute(stmt)
        db.commit()
        logger.info(f"Search index: inserted block {event.block_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to index block {event.block_id}: {str(e)}")
        raise


@event_handler(BlockUpdated)
async def on_block_updated(event: BlockUpdated, db: Session) -> None:
    """
    Block 更新事件处理器

    操作: UPDATE search_index

    字段更新:
    - text: event.content
    - snippet: event.content[:200]
    - updated_at: now()
    """
    try:
        stmt = (
            update(SearchIndexModel)
            .where(
                SearchIndexModel.entity_type == "block",
                SearchIndexModel.entity_id == event.block_id,
            )
            .values(
                text=event.content or "",
                snippet=(event.content or "")[:200],
            )
        )
        db.execute(stmt)
        db.commit()
        logger.info(f"Search index: updated block {event.block_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update search index for block {event.block_id}: {str(e)}")
        raise


@event_handler(BlockDeleted)
async def on_block_deleted(event: BlockDeleted, db: Session) -> None:
    """
    Block 删除事件处理器

    操作: DELETE from search_index
    """
    try:
        stmt = delete(SearchIndexModel).where(
            SearchIndexModel.entity_type == "block",
            SearchIndexModel.entity_id == event.block_id,
        )
        db.execute(stmt)
        db.commit()
        logger.info(f"Search index: deleted block {event.block_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete search index for block {event.block_id}: {str(e)}")
        raise


# ============================================================================
# Tag Event Handlers
# ============================================================================

@event_handler(TagCreated)
async def on_tag_created(event: TagCreated, db: Session) -> None:
    """
    Tag 创建事件处理器

    操作: INSERT into search_index

    字段映射:
    - entity_type: "tag"
    - entity_id: event.tag_id
    - text: event.name
    - snippet: event.name
    """
    try:
        stmt = insert(SearchIndexModel).values(
            entity_type="tag",
            entity_id=event.tag_id,
            text=event.name or "",
            snippet=event.name or "",
            rank_score=0.0,
        )
        db.execute(stmt)
        db.commit()
        logger.info(f"Search index: inserted tag {event.tag_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to index tag {event.tag_id}: {str(e)}")
        raise


@event_handler(TagUpdated)
async def on_tag_updated(event: TagUpdated, db: Session) -> None:
    """
    Tag 更新事件处理器

    操作: UPDATE search_index

    字段更新:
    - text: event.name
    - snippet: event.name
    - updated_at: now()
    """
    try:
        stmt = (
            update(SearchIndexModel)
            .where(
                SearchIndexModel.entity_type == "tag",
                SearchIndexModel.entity_id == event.tag_id,
            )
            .values(
                text=event.name or "",
                snippet=event.name or "",
            )
        )
        db.execute(stmt)
        db.commit()
        logger.info(f"Search index: updated tag {event.tag_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update search index for tag {event.tag_id}: {str(e)}")
        raise


@event_handler(TagDeleted)
async def on_tag_deleted(event: TagDeleted, db: Session) -> None:
    """
    Tag 删除事件处理器

    操作: DELETE from search_index
    """
    try:
        stmt = delete(SearchIndexModel).where(
            SearchIndexModel.entity_type == "tag",
            SearchIndexModel.entity_id == event.tag_id,
        )
        db.execute(stmt)
        db.commit()
        logger.info(f"Search index: deleted tag {event.tag_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete search index for tag {event.tag_id}: {str(e)}")
        raise


__all__ = [
    "on_block_created",
    "on_block_updated",
    "on_block_deleted",
    "on_tag_created",
    "on_tag_updated",
    "on_tag_deleted",
]
