"""Tests for Chronicle application services."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from modules.chronicle.application.services import (
    ChronicleRecorderService,
    ChronicleQueryService,
    RECENT_EVENT_TYPES,
)
from modules.chronicle.domain import ChronicleEventType, ChronicleEvent


def assert_payload_contains(payload: dict, expected: dict) -> None:
    for key, value in expected.items():
        assert payload.get(key) == value


def assert_payload_has_default_envelope(payload: dict) -> None:
    assert payload.get("schema_version") == 1
    assert payload.get("provenance") == "live"
    # Tests run without request context by default.
    assert payload.get("source") == "unknown"
    assert payload.get("actor_kind") == "unknown"


class InMemoryChronicleRepo:
    """Minimal repository stub that captures saved events."""

    def __init__(self):
        self.saved_events = []
        self.list_calls = []
        self._list_response: tuple[list[ChronicleEvent], int] = ([], 0)

    async def save(self, event):
        self.saved_events.append(event)
        return event

    async def list_by_book(self, *, book_id, event_types=None, limit=50, offset=0, order_desc=True):
        self.list_calls.append(
            {
                "book_id": book_id,
                "event_types": tuple(event_types) if event_types else None,
                "limit": limit,
                "offset": offset,
                "order_desc": order_desc,
            }
        )
        return self._list_response

    def set_list_response(self, events: list[ChronicleEvent]):
        self._list_response = (events, len(events))


@pytest.mark.asyncio
async def test_record_book_created_tracks_bookshelf_payload():
    repo = InMemoryChronicleRepo()
    service = ChronicleRecorderService(repo)
    book_id = uuid4()
    shelf_id = uuid4()

    event = await service.record_book_created(
        book_id=book_id,
        bookshelf_id=shelf_id,
        occurred_at=datetime.now(timezone.utc),
    )

    assert event.event_type == ChronicleEventType.BOOK_CREATED
    assert_payload_has_default_envelope(event.payload)
    assert_payload_contains(event.payload, {"bookshelf_id": str(shelf_id)})
    assert repo.saved_events[-1] == event


@pytest.mark.asyncio
async def test_record_book_moved_persists_payload():
    repo = InMemoryChronicleRepo()
    service = ChronicleRecorderService(repo)
    book_id = uuid4()
    from_id = uuid4()
    to_id = uuid4()
    moved_at = datetime.now(timezone.utc)

    event = await service.record_book_moved(
        book_id=book_id,
        from_bookshelf_id=from_id,
        to_bookshelf_id=to_id,
        moved_at=moved_at,
    )

    assert event.event_type == ChronicleEventType.BOOK_MOVED
    assert_payload_has_default_envelope(event.payload)
    assert_payload_contains(
        event.payload,
        {
            "from_bookshelf_id": str(from_id),
            "to_bookshelf_id": str(to_id),
        },
    )
    assert repo.saved_events[-1] == event


@pytest.mark.asyncio
async def test_record_book_moved_to_basement_sets_expected_fields():
    repo = InMemoryChronicleRepo()
    service = ChronicleRecorderService(repo)
    book_id = uuid4()
    from_id = uuid4()
    basement_id = uuid4()
    deleted_at = datetime.now(timezone.utc)

    event = await service.record_book_moved_to_basement(
        book_id=book_id,
        from_bookshelf_id=from_id,
        basement_bookshelf_id=basement_id,
        deleted_at=deleted_at,
    )

    assert event.event_type == ChronicleEventType.BOOK_SOFT_DELETED
    assert_payload_has_default_envelope(event.payload)
    assert_payload_contains(
        event.payload,
        {
            "from_bookshelf_id": str(from_id),
            "basement_bookshelf_id": str(basement_id),
        },
    )
    assert repo.saved_events[-1] == event


@pytest.mark.asyncio
async def test_record_content_snapshot_taken_payload_normalized():
    repo = InMemoryChronicleRepo()
    service = ChronicleRecorderService(repo)
    book_id = uuid4()

    event = await service.record_content_snapshot_taken(
        book_id=book_id,
        block_count=12,
        block_type_counts={"text": 10, "heading": 2},
        total_word_count=3456,
        trigger="maturity_refresh",
    )

    assert event.event_type == ChronicleEventType.CONTENT_SNAPSHOT_TAKEN
    assert_payload_has_default_envelope(event.payload)
    assert event.payload["block_count"] == 12
    assert event.payload["block_type_counts"] == {"text": 10, "heading": 2}
    assert event.payload["total_word_count"] == 3456
    assert repo.saved_events[-1] == event


@pytest.mark.asyncio
async def test_record_wordcount_milestone_reached_contains_totals():
    repo = InMemoryChronicleRepo()
    service = ChronicleRecorderService(repo)
    book_id = uuid4()

    event = await service.record_wordcount_milestone_reached(
        book_id=book_id,
        milestone=5000,
        total_word_count=5123,
        previous_word_count=4100,
    )

    assert event.event_type == ChronicleEventType.WORDCOUNT_MILESTONE_REACHED
    assert_payload_has_default_envelope(event.payload)
    assert_payload_contains(
        event.payload,
        {
            "milestone": 5000,
            "total_word_count": 5123,
            "previous_word_count": 4100,
        },
    )
    assert repo.saved_events[-1] == event


@pytest.mark.asyncio
async def test_record_book_restored_and_deleted_cover_payloads():
    repo = InMemoryChronicleRepo()
    service = ChronicleRecorderService(repo)
    book_id = uuid4()
    basement_id = uuid4()
    restored_to = uuid4()
    bookshelf_id = uuid4()
    restored_at = datetime.now(timezone.utc)
    deleted_at = datetime.now(timezone.utc)

    restored_event = await service.record_book_restored(
        book_id=book_id,
        from_basement_id=basement_id,
        restored_to_bookshelf_id=restored_to,
        restored_at=restored_at,
    )

    deleted_event = await service.record_book_deleted(
        book_id=book_id,
        bookshelf_id=bookshelf_id,
        occurred_at=deleted_at,
    )

    assert restored_event.event_type == ChronicleEventType.BOOK_RESTORED
    assert_payload_has_default_envelope(restored_event.payload)
    assert_payload_contains(
        restored_event.payload,
        {
            "basement_bookshelf_id": str(basement_id),
            "restored_to_bookshelf_id": str(restored_to),
        },
    )

    assert deleted_event.event_type == ChronicleEventType.BOOK_DELETED
    assert_payload_has_default_envelope(deleted_event.payload)
    assert_payload_contains(deleted_event.payload, {"bookshelf_id": str(bookshelf_id)})
    # Ensure both events are stored
    assert repo.saved_events[-2:] == [restored_event, deleted_event]


@pytest.mark.asyncio
async def test_record_book_maturity_recomputed_payload_contains_delta():
    repo = InMemoryChronicleRepo()
    service = ChronicleRecorderService(repo)
    book_id = uuid4()
    occurred_at = datetime.now(timezone.utc)

    event = await service.record_book_maturity_recomputed(
        book_id=book_id,
        previous_score=40,
        new_score=55,
        stage="growing",
        trigger="recalculate",
        occurred_at=occurred_at,
    )

    assert event.event_type == ChronicleEventType.BOOK_MATURITY_RECOMPUTED
    assert_payload_has_default_envelope(event.payload)
    assert_payload_contains(
        event.payload,
        {
            "previous_score": 40,
            "new_score": 55,
            "delta": 15,
            "stage": "growing",
            "trigger": "recalculate",
            "initial": False,
        },
    )
    assert repo.saved_events[-1] == event


@pytest.mark.asyncio
async def test_record_structure_task_completed_payload():
    repo = InMemoryChronicleRepo()
    service = ChronicleRecorderService(repo)
    book_id = uuid4()

    event = await service.record_structure_task_completed(
        book_id=book_id,
        task_code="add_summary",
        title="写摘要",
        points=15,
        stage="seed",
        trigger="recalculate",
    )

    assert event.event_type == ChronicleEventType.STRUCTURE_TASK_COMPLETED
    assert_payload_has_default_envelope(event.payload)
    assert_payload_contains(
        event.payload,
        {
            "task_id": "add_summary",
            "title": "写摘要",
            "points": 15,
            "stage": "seed",
            "trigger": "recalculate",
        },
    )
    assert repo.saved_events[-1] == event


@pytest.mark.asyncio
async def test_record_structure_task_regressed_payload_points_negative():
    repo = InMemoryChronicleRepo()
    service = ChronicleRecorderService(repo)
    book_id = uuid4()

    event = await service.record_structure_task_regressed(
        book_id=book_id,
        task_code="add_summary",
        title="写摘要",
        points=15,
        stage="seed",
        trigger="recalculate",
    )

    assert event.event_type == ChronicleEventType.STRUCTURE_TASK_REGRESSED
    assert_payload_has_default_envelope(event.payload)
    assert_payload_contains(
        event.payload,
        {
            "task_id": "add_summary",
            "title": "写摘要",
            "points": -15,
            "stage": "seed",
            "trigger": "recalculate",
        },
    )
    assert repo.saved_events[-1] == event


@pytest.mark.asyncio
async def test_query_service_delegates_to_repository():
    repo = InMemoryChronicleRepo()
    service = ChronicleQueryService(repo)
    book_id = uuid4()
    events = [
        ChronicleEvent.create(
            event_type=ChronicleEventType.BOOK_CREATED,
            book_id=book_id,
            payload={"bookshelf_id": "test"},
        )
    ]
    repo.set_list_response(events)

    items, total = await service.list_book_events(book_id=book_id, limit=10, offset=5)

    assert items == events
    assert total == len(events)
    assert repo.list_calls == [
        {
            "book_id": book_id,
            "event_types": None,
            "limit": 10,
            "offset": 5,
            "order_desc": True,
        }
    ]


@pytest.mark.asyncio
async def test_query_service_recent_events_applies_preconfigured_filter():
    repo = InMemoryChronicleRepo()
    service = ChronicleQueryService(repo)
    book_id = uuid4()
    events = [
        ChronicleEvent.create(
            event_type=ChronicleEventType.BOOK_STAGE_CHANGED,
            book_id=book_id,
            payload={},
        )
    ]
    repo.set_list_response(events)

    items, total = await service.list_recent_book_events(book_id=book_id, limit=6)

    assert items == events
    assert total == len(events)
    assert repo.list_calls[-1] == {
        "book_id": book_id,
        "event_types": RECENT_EVENT_TYPES,
        "limit": 6,
        "offset": 0,
        "order_desc": True,
    }
