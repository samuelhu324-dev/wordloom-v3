"""infra.event_bus.event_handler_registry 模块测试 - 事件处理器注册表

These tests track the *current* implementation:
- class-level registry via @EventHandlerRegistry.register
- bootstrap subscribes a single dispatcher per event type
"""

import pytest

from api.app.shared.base import DomainEvent
from infra.event_bus.event_handler_registry import EventHandlerRegistry


class MockEvent(DomainEvent):
    """模拟事件."""

    def __init__(self, data: str = "test"):
        super().__init__()
        self.data = data


@pytest.fixture(autouse=True)
def _clear_registry():
    EventHandlerRegistry.clear()
    yield
    EventHandlerRegistry.clear()


def test_register_and_get_handlers_for_event():
    calls = []

    @EventHandlerRegistry.register(MockEvent)
    async def handler(event: MockEvent):
        calls.append(event.data)

    handlers = EventHandlerRegistry.get_handlers_for_event(MockEvent)
    assert [h.__name__ for h in handlers] == [handler.__name__]


def test_registration_summary_counts():
    @EventHandlerRegistry.register(MockEvent)
    async def handler1(event: MockEvent):
        pass

    @EventHandlerRegistry.register(MockEvent)
    async def handler2(event: MockEvent):
        pass

    summary = EventHandlerRegistry.get_registration_summary()
    assert summary["total_event_types"] == 1
    assert summary["total_handlers"] == 2
    assert summary["events"]["MockEvent"] == 2


@pytest.mark.anyio
async def test_bootstrap_subscribes_single_dispatcher(monkeypatch):
    monkeypatch.setenv("WORDLOOM_EVENT_BUS_TX_MODE", "none")

    called = []

    @EventHandlerRegistry.register(MockEvent)
    async def handler(event: MockEvent):
        called.append(event.data)

    class FakeEventBus:
        def __init__(self):
            self.subscriptions = []

        def subscribe(self, event_type, subscriber):
            self.subscriptions.append((event_type, subscriber))

    fake_bus = FakeEventBus()

    # Patch the global get_event_bus used by bootstrap()
    import api.app.shared.events as events_module

    monkeypatch.setattr(events_module, "get_event_bus", lambda: fake_bus, raising=True)

    EventHandlerRegistry.bootstrap()

    assert len(fake_bus.subscriptions) == 1
    event_type, subscriber = fake_bus.subscriptions[0]
    assert event_type is MockEvent

    # Should be a dispatcher (single subscriber per event type)
    assert subscriber.__name__.startswith("dispatch_")

    await subscriber(MockEvent("hello"))
    assert called == ["hello"]
