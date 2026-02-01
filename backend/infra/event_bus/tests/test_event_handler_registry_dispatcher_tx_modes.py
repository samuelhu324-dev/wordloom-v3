import pytest

from infra.event_bus.event_handler_registry import EventHandlerRegistry


class _FakeBegin:
    def __init__(self, session, *, is_nested: bool):
        self._session = session
        self._is_nested = is_nested

    async def __aenter__(self):
        if self._is_nested:
            self._session.nested_started += 1
        else:
            self._session.outer_started += 1
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is None:
            if self._is_nested:
                self._session.nested_committed += 1
            else:
                self._session.outer_committed += 1
            return False

        # error path
        if self._is_nested:
            self._session.nested_rolled_back += 1
        else:
            self._session.outer_rolled_back += 1
        return False


class _FakeSession:
    def __init__(self):
        self.outer_started = 0
        self.outer_committed = 0
        self.outer_rolled_back = 0
        self.nested_started = 0
        self.nested_committed = 0
        self.nested_rolled_back = 0
        self.rollback_called = 0
        self.executed = []

    def begin(self):
        return _FakeBegin(self, is_nested=False)

    def begin_nested(self):
        return _FakeBegin(self, is_nested=True)

    async def execute(self, stmt):
        self.executed.append(stmt)

    async def rollback(self):
        self.rollback_called += 1


class _FakeSessionContextManager:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeSessionFactory:
    def __init__(self, session):
        self._session = session
        self.created = 0

    def __call__(self):
        self.created += 1
        return _FakeSessionContextManager(self._session)


@pytest.mark.anyio
async def test_dispatcher_savepoint_mode_continues_and_commits(monkeypatch):
    monkeypatch.setenv("WORDLOOM_EVENT_BUS_TX_MODE", "savepoint")

    session = _FakeSession()
    factory = _FakeSessionFactory(session)

    async def _fake_get_session_factory():
        return factory

    monkeypatch.setattr(
        "infra.database.session.get_session_factory", _fake_get_session_factory, raising=True
    )

    calls = []

    class Event:
        pass

    async def handler_fail(event, db):
        calls.append("fail")
        await db.execute("fail")
        raise RuntimeError("boom")

    async def handler_ok(event, db):
        calls.append("ok")
        await db.execute("ok")

    # Register into registry internal map for this test only
    EventHandlerRegistry._handlers[Event] = [handler_fail, handler_ok]

    dispatcher = EventHandlerRegistry._make_dispatcher(Event)
    await dispatcher(Event())

    assert calls == ["fail", "ok"]
    assert session.outer_started == 1
    assert session.outer_committed == 1
    assert session.outer_rolled_back == 0
    assert session.nested_started == 2
    assert session.nested_rolled_back == 1
    assert session.nested_committed == 1


@pytest.mark.anyio
async def test_dispatcher_atomic_mode_rolls_back_and_stops(monkeypatch):
    monkeypatch.setenv("WORDLOOM_EVENT_BUS_TX_MODE", "atomic")

    session = _FakeSession()
    factory = _FakeSessionFactory(session)

    async def _fake_get_session_factory():
        return factory

    monkeypatch.setattr(
        "infra.database.session.get_session_factory", _fake_get_session_factory, raising=True
    )

    calls = []

    class Event:
        pass

    async def handler_fail(event, db):
        calls.append("fail")
        await db.execute("fail")
        raise RuntimeError("boom")

    async def handler_ok(event, db):
        calls.append("ok")
        await db.execute("ok")

    EventHandlerRegistry._handlers[Event] = [handler_fail, handler_ok]

    dispatcher = EventHandlerRegistry._make_dispatcher(Event)

    with pytest.raises(RuntimeError):
        await dispatcher(Event())

    assert calls == ["fail"]
    assert session.outer_started == 1
    assert session.outer_committed == 0
    assert session.outer_rolled_back == 1
    assert session.rollback_called >= 1
