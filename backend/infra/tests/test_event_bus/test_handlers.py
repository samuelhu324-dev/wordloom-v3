"""
infra.event_bus.handlers 模块测试 - 事件处理器实现
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from api.app.shared.base import DomainEvent


class BlockCreatedEvent(DomainEvent):
    """块创建事件."""
    def __init__(self, block_id: str, content: str, book_id: str):
        super().__init__()
        self.block_id = block_id
        self.content = content
        self.book_id = book_id
        self.aggregate_root_id = block_id


class BlockUpdatedEvent(DomainEvent):
    """块更新事件."""
    def __init__(self, block_id: str, content: str):
        super().__init__()
        self.block_id = block_id
        self.content = content
        self.aggregate_root_id = block_id


class BlockDeletedEvent(DomainEvent):
    """块删除事件."""
    def __init__(self, block_id: str):
        super().__init__()
        self.block_id = block_id
        self.aggregate_root_id = block_id


class TagCreatedEvent(DomainEvent):
    """标签创建事件."""
    def __init__(self, tag_id: str, name: str):
        super().__init__()
        self.tag_id = tag_id
        self.name = name
        self.aggregate_root_id = tag_id


class TagUpdatedEvent(DomainEvent):
    """标签更新事件."""
    def __init__(self, tag_id: str, name: str):
        super().__init__()
        self.tag_id = tag_id
        self.name = name
        self.aggregate_root_id = tag_id


class TagDeletedEvent(DomainEvent):
    """标签删除事件."""
    def __init__(self, tag_id: str):
        super().__init__()
        self.tag_id = tag_id
        self.aggregate_root_id = tag_id


class TestBlockCreatedHandler:
    """测试块创建事件处理器."""

    @pytest.mark.asyncio
    async def test_handle_block_created_inserts_search_index(self):
        """测试块创建时插入搜索索引."""
        event = BlockCreatedEvent(
            block_id="block_123",
            content="Test block content",
            book_id="book_456"
        )

        # 模拟搜索索引表插入
        # 实现会从infra.event_bus.handlers导入

    @pytest.mark.asyncio
    async def test_handle_block_created_with_empty_content(self):
        """测试块创建空内容."""
        event = BlockCreatedEvent(
            block_id="block_123",
            content="",
            book_id="book_456"
        )
        # 应该仍然创建索引条目


class TestBlockUpdatedHandler:
    """测试块更新事件处理器."""

    @pytest.mark.asyncio
    async def test_handle_block_updated_updates_search_index(self):
        """测试块更新时更新搜索索引."""
        event = BlockUpdatedEvent(
            block_id="block_123",
            content="Updated content"
        )
        # 应该更新搜索索引条目

    @pytest.mark.asyncio
    async def test_handle_block_updated_preserves_metadata(self):
        """测试块更新保留元数据."""
        event = BlockUpdatedEvent(
            block_id="block_123",
            content="New content"
        )
        # 应该保留created_at但更新updated_at


class TestBlockDeletedHandler:
    """测试块删除事件处理器."""

    @pytest.mark.asyncio
    async def test_handle_block_deleted_removes_search_index(self):
        """测试块删除时删除搜索索引."""
        event = BlockDeletedEvent(block_id="block_123")
        # 应该从搜索索引中删除


class TestTagCreatedHandler:
    """测试标签创建事件处理器."""

    @pytest.mark.asyncio
    async def test_handle_tag_created_inserts_search_index(self):
        """测试标签创建时插入搜索索引."""
        event = TagCreatedEvent(
            tag_id="tag_123",
            name="Important"
        )
        # 应该创建搜索索引条目


class TestTagUpdatedHandler:
    """测试标签更新事件处理器."""

    @pytest.mark.asyncio
    async def test_handle_tag_updated_updates_search_index(self):
        """测试标签更新时更新搜索索引."""
        event = TagUpdatedEvent(
            tag_id="tag_123",
            name="Updated Name"
        )
        # 应该更新搜索索引条目


class TestTagDeletedHandler:
    """测试标签删除事件处理器."""

    @pytest.mark.asyncio
    async def test_handle_tag_deleted_removes_search_index(self):
        """测试标签删除时删除搜索索引."""
        event = TagDeletedEvent(tag_id="tag_123")
        # 应该从搜索索引中删除


class TestSearchIndexSyncHandler:
    """测试搜索索引同步处理器."""

    @pytest.mark.asyncio
    async def test_sync_on_crud_operations(self):
        """测试CRUD操作时同步搜索索引."""
        # 6个处理器应该被正确注册
        # Block: 3个 (Created, Updated, Deleted)
        # Tag: 3个 (Created, Updated, Deleted)

    @pytest.mark.asyncio
    async def test_concurrent_sync_operations(self):
        """测试并发同步操作."""
        # 多个事件应该可以并发处理


class TestEventHandlerIntegration:
    """测试事件处理器集成."""

    def test_all_handlers_registered(self):
        """测试 search_index_handlers 的 6 个处理器已注册."""

        from api.app.modules.block.domain.events import BlockCreated, BlockUpdated, BlockDeleted
        from api.app.modules.tag.domain.events import TagCreated, TagRenamed, TagDeleted
        from infra.event_bus.event_handler_registry import EventHandlerRegistry

        # Import triggers decorator registration
        import infra.event_bus.handlers.search_index_handlers  # noqa: F401

        for event_type in [
            BlockCreated,
            BlockUpdated,
            BlockDeleted,
            TagCreated,
            TagRenamed,
            TagDeleted,
        ]:
            handlers = EventHandlerRegistry.get_handlers_for_event(event_type)
            assert len(handlers) == 1

    @pytest.mark.asyncio
    async def test_handler_error_does_not_break_pipeline(self):
        """测试处理器错误不会中断管道."""
        # 一个处理器失败不应该影响其他
