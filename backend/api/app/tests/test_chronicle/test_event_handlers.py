"""Tests for Chronicle event bus handlers."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from modules.book.domain.events import (
    BookCreated,
    BookDeleted,
    BookMovedToBasement,
    BookMovedToBookshelf,
    BookRestoredFromBasement,
)
from infra.event_bus.handlers import chronicle_handler


class RecorderSpy:
    """Helper that records which recorder method was invoked."""

    def __init__(self):
        self.calls = []

    async def record_book_created(self, **kwargs):
        self.calls.append(("book_created", kwargs))

    async def record_book_moved(self, **kwargs):
        self.calls.append(("book_moved", kwargs))

    async def record_book_moved_to_basement(self, **kwargs):
        self.calls.append(("book_basement", kwargs))

    async def record_book_restored(self, **kwargs):
        self.calls.append(("book_restored", kwargs))

    async def record_book_deleted(self, **kwargs):
        self.calls.append(("book_deleted", kwargs))


@pytest.fixture
def recorder_spy():
    return RecorderSpy()


async def _run_handler(monkeypatch, recorder_spy, expected_name, handler_coro):
    async def fake_record(op, *, event_name):
        assert event_name == expected_name
        await op(recorder_spy)

    monkeypatch.setattr(chronicle_handler, "_record", fake_record)
    await handler_coro


@pytest.mark.asyncio
async def test_book_created_handler_records_event(monkeypatch, recorder_spy):
    event = BookCreated(book_id=uuid4(), bookshelf_id=uuid4(), title="A")

    async def invoke():
        await chronicle_handler.chronicle_book_created(event)

    await _run_handler(monkeypatch, recorder_spy, "BookCreated", invoke())
    assert recorder_spy.calls[-1][0] == "book_created"
    assert recorder_spy.calls[-1][1]["book_id"] == event.book_id


@pytest.mark.asyncio
async def test_book_moved_handler_records_payload(monkeypatch, recorder_spy):
    event = BookMovedToBookshelf(
        book_id=uuid4(),
        old_bookshelf_id=uuid4(),
        new_bookshelf_id=uuid4(),
        moved_at=datetime.now(timezone.utc),
    )

    async def invoke():
        await chronicle_handler.chronicle_book_moved(event)

    await _run_handler(monkeypatch, recorder_spy, "BookMovedToBookshelf", invoke())
    call = recorder_spy.calls[-1]
    assert call[0] == "book_moved"
    assert call[1]["from_bookshelf_id"] == event.old_bookshelf_id
    assert call[1]["to_bookshelf_id"] == event.new_bookshelf_id


@pytest.mark.asyncio
async def test_book_moved_to_basement_handler(monkeypatch, recorder_spy):
    event = BookMovedToBasement(
        book_id=uuid4(),
        old_bookshelf_id=uuid4(),
        basement_bookshelf_id=uuid4(),
        deleted_at=datetime.now(timezone.utc),
    )

    async def invoke():
        await chronicle_handler.chronicle_book_moved_to_basement(event)

    await _run_handler(monkeypatch, recorder_spy, "BookMovedToBasement", invoke())
    call = recorder_spy.calls[-1]
    assert call[0] == "book_basement"
    assert call[1]["basement_bookshelf_id"] == event.basement_bookshelf_id


@pytest.mark.asyncio
async def test_book_restored_handler(monkeypatch, recorder_spy):
    event = BookRestoredFromBasement(
        book_id=uuid4(),
        basement_bookshelf_id=uuid4(),
        restored_to_bookshelf_id=uuid4(),
        restored_at=datetime.now(timezone.utc),
    )

    async def invoke():
        await chronicle_handler.chronicle_book_restored(event)

    await _run_handler(monkeypatch, recorder_spy, "BookRestoredFromBasement", invoke())
    call = recorder_spy.calls[-1]
    assert call[0] == "book_restored"
    assert call[1]["restored_to_bookshelf_id"] == event.restored_to_bookshelf_id


@pytest.mark.asyncio
async def test_book_deleted_handler(monkeypatch, recorder_spy):
    event = BookDeleted(
        book_id=uuid4(),
        bookshelf_id=uuid4(),
        occurred_at=datetime.now(timezone.utc),
    )

    async def invoke():
        await chronicle_handler.chronicle_book_deleted(event)

    await _run_handler(monkeypatch, recorder_spy, "BookDeleted", invoke())
    call = recorder_spy.calls[-1]
    assert call[0] == "book_deleted"
    assert call[1]["bookshelf_id"] == event.bookshelf_id
