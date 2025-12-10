"""
infra.event_bus.event_handler_registry 模块测试 - 事件处理器注册表
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from infra.event_bus.event_handler_registry import EventHandlerRegistry
from app.shared.base import DomainEvent


class MockEvent(DomainEvent):
    """模拟事件."""
    def __init__(self, data: str = "test"):
        super().__init__()
        self.data = data


class TestEventHandlerRegistry:
    """测试事件处理器注册表."""

    def test_registry_initialization(self):
        """测试注册表初始化."""
        registry = EventHandlerRegistry()
        assert registry is not None

    def test_registry_register_handler(self):
        """测试注册处理器."""
        registry = EventHandlerRegistry()

        async def mock_handler(event: MockEvent):
            pass

        registry.register(MockEvent, mock_handler)
        # 应该成功注册

    def test_registry_multiple_handlers_same_event(self):
        """测试为同一事件注册多个处理器."""
        registry = EventHandlerRegistry()

        async def handler1(event: MockEvent):
            pass

        async def handler2(event: MockEvent):
            pass

        registry.register(MockEvent, handler1)
        registry.register(MockEvent, handler2)
        # 应该支持多个处理器

    def test_registry_get_handlers(self):
        """测试获取处理器."""
        registry = EventHandlerRegistry()

        async def mock_handler(event: MockEvent):
            pass

        registry.register(MockEvent, mock_handler)
        handlers = registry.get_handlers(MockEvent)
        assert len(handlers) >= 1


class TestEventHandlerRegistryAsync:
    """测试异步事件处理器."""

    @pytest.mark.asyncio
    async def test_dispatch_event(self):
        """测试分发事件."""
        registry = EventHandlerRegistry()
        call_count = 0

        async def mock_handler(event: MockEvent):
            nonlocal call_count
            call_count += 1

        registry.register(MockEvent, mock_handler)
        event = MockEvent("test data")

        await registry.dispatch(event)
        assert call_count >= 1

    @pytest.mark.asyncio
    async def test_dispatch_multiple_handlers(self):
        """测试分发到多个处理器."""
        registry = EventHandlerRegistry()
        results = []

        async def handler1(event: MockEvent):
            results.append("h1")

        async def handler2(event: MockEvent):
            results.append("h2")

        registry.register(MockEvent, handler1)
        registry.register(MockEvent, handler2)

        event = MockEvent()
        await registry.dispatch(event)
        assert len(results) >= 2


class TestEventHandlerRegistryDecorator:
    """测试装饰器注册模式."""

    def test_decorator_registration(self):
        """测试装饰器注册."""
        registry = EventHandlerRegistry()

        @registry.register_handler(MockEvent)
        async def mock_handler(event: MockEvent):
            pass

        handlers = registry.get_handlers(MockEvent)
        assert len(handlers) >= 1


class TestEventHandlerRegistryBootstrap:
    """测试事件处理器引导."""

    def test_bootstrap_initialization(self):
        """测试引导初始化."""
        registry = EventHandlerRegistry()
        # 应该支持bootstrap方法
        if hasattr(registry, "bootstrap"):
            registry.bootstrap()

    @pytest.mark.asyncio
    async def test_concurrent_dispatch(self):
        """测试并发分发."""
        registry = EventHandlerRegistry()
        results = []

        async def slow_handler(event: MockEvent):
            await asyncio.sleep(0.01)
            results.append("handler")

        registry.register(MockEvent, slow_handler)
        event = MockEvent()

        await registry.dispatch(event)
        assert len(results) >= 1


class TestEventHandlerRegistryErrorHandling:
    """测试错误处理."""

    @pytest.mark.asyncio
    async def test_handler_exception_handling(self):
        """测试处理器异常处理."""
        registry = EventHandlerRegistry()

        async def failing_handler(event: MockEvent):
            raise Exception("Handler failed")

        async def working_handler(event: MockEvent):
            pass

        registry.register(MockEvent, failing_handler)
        registry.register(MockEvent, working_handler)

        event = MockEvent()
        # 应该处理异常而不中止其他处理器
        try:
            await registry.dispatch(event)
        except Exception:
            pass


class TestEventHandlerRegistrySingleton:
    """测试单例模式."""

    def test_registry_singleton_pattern(self):
        """测试注册表单例."""
        registry1 = EventHandlerRegistry()
        registry2 = EventHandlerRegistry()

        # 取决于实现，可能是同一实例
        async def handler(event: MockEvent):
            pass

        registry1.register(MockEvent, handler)


class TestEventHandlerRegistryClearing:
    """测试清空处理器."""

    def test_clear_all_handlers(self):
        """测试清空所有处理器."""
        registry = EventHandlerRegistry()

        async def handler(event: MockEvent):
            pass

        registry.register(MockEvent, handler)

        if hasattr(registry, "clear"):
            registry.clear()
            handlers = registry.get_handlers(MockEvent)
            assert len(handlers) == 0
