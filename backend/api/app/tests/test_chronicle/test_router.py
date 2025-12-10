"""Router-level tests for Chronicle endpoints (function-level)."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from modules.chronicle.domain import ChronicleEvent, ChronicleEventType
from modules.chronicle.schemas import ChronicleBookOpenedRequest
from modules.chronicle.routers.chronicle_router import record_book_opened, list_book_events


class StubRecorderService:
    def __init__(self, event: ChronicleEvent):
        self.event = event
        self.calls = []

    async def record_book_opened(self, *, book_id, actor_id=None):
        self.calls.append({"book_id": book_id, "actor_id": actor_id})
        return self.event


class StubQueryService:
    def __init__(self, events, total):
        self.events = events
        self.total = total
        self.calls = []

    async def list_book_events(self, **kwargs):
        self.calls.append(kwargs)
        return self.events, self.total


class StubDI:
    def __init__(self, recorder_service, query_service):
        self._recorder = recorder_service
        self._query = query_service

    def get_chronicle_recorder_service(self):
        return self._recorder

    def get_chronicle_query_service(self):
        return self._query


@pytest.mark.asyncio
async def test_record_book_opened_returns_serialized_event():
    book_id = uuid4()
    actor_id = uuid4()
    event = ChronicleEvent.create(
        event_type=ChronicleEventType.BOOK_OPENED,
        book_id=book_id,
        actor_id=actor_id,
        occurred_at=datetime.now(timezone.utc),
    )
    recorder = StubRecorderService(event)
    di = StubDI(recorder, query_service=None)

    request = ChronicleBookOpenedRequest(book_id=book_id, actor_id=actor_id)
    response = await record_book_opened(request, di=di)

    assert recorder.calls == [{"book_id": book_id, "actor_id": actor_id}]
    assert response.event_type == ChronicleEventType.BOOK_OPENED
    assert response.book_id == book_id
    assert response.actor_id == actor_id
    assert response.payload == {}


@pytest.mark.asyncio
async def test_list_book_events_applies_pagination_and_has_more():
    book_id = uuid4()
    events = [
        ChronicleEvent.create(
            event_type=ChronicleEventType.BOOK_CREATED,
            book_id=book_id,
            occurred_at=datetime.now(timezone.utc),
        )
        for _ in range(2)
    ]
    query_service = StubQueryService(events, total=5)
    di = StubDI(recorder_service=None, query_service=query_service)

    response = await list_book_events(
        book_id=book_id,
        page=2,
        size=2,
        event_types=None,
        di=di,
    )

    assert query_service.calls[-1]["book_id"] == book_id
    assert query_service.calls[-1]["limit"] == 2
    assert query_service.calls[-1]["offset"] == 2
    assert response.total == 5
    assert response.page == 2
    assert response.size == 2
    assert response.has_more is True
    assert len(response.items) == 2
    assert all(item.book_id == book_id for item in response.items)
