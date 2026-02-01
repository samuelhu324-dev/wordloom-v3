import pytest

from infra.event_bus.event_handler_registry import EventHandlerRegistry


class _FakeSession:
    def __init__(self):
        self.executed = []
        self.committed = False
        self.rolled_back = False

    async def execute(self, stmt):
        self.executed.append(stmt)

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


class _FakeSessionContextManager:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeSessionFactory:
    def __init__(self):
        self.sessions = []

    def __call__(self):
        session = _FakeSession()
        self.sessions.append(session)
        return _FakeSessionContextManager(session)


@pytest.mark.anyio
async def test_wrap_for_event_bus_commits_on_success(monkeypatch):
    factory = _FakeSessionFactory()

    async def _fake_get_session_factory():
        return factory

    monkeypatch.setattr(
        "infra.database.session.get_session_factory", _fake_get_session_factory, raising=True
    )

    class Event:
        fail = False

    async def handler(event, db):
        await db.execute("ok")

    wrapped = EventHandlerRegistry._wrap_for_event_bus(handler)
    await wrapped(Event())

    assert factory.sessions[-1].committed is True
    assert factory.sessions[-1].rolled_back is False


@pytest.mark.anyio
async def test_wrap_for_event_bus_rolls_back_on_error(monkeypatch):
    factory = _FakeSessionFactory()

    async def _fake_get_session_factory():
        return factory

    monkeypatch.setattr(
        "infra.database.session.get_session_factory", _fake_get_session_factory, raising=True
    )

    class Event:
        fail = True

    async def handler(event, db):
        await db.execute("boom")
        raise RuntimeError("nope")

    wrapped = EventHandlerRegistry._wrap_for_event_bus(handler)

    with pytest.raises(RuntimeError):
        await wrapped(Event())

    assert factory.sessions[-1].committed is False
    assert factory.sessions[-1].rolled_back is True
