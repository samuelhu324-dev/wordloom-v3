"""Tests for the BookAggregateMaturityDataProvider fallback behaviour."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List
from uuid import UUID, uuid4

import pytest

from api.app.modules.book.domain.book import Book
from api.app.modules.book.domain.book_summary import BookSummary
from api.app.modules.book.domain.book_title import BookTitle
from api.app.modules.maturity.application.adapters import BookAggregateMaturityDataProvider
from api.app.modules.tag.domain import EntityType as TagEntityType


@dataclass
class _StubBookRepository:
    book: Book

    async def get_by_id(self, book_id: UUID) -> Book | None:
        if book_id != self.book.id:
            return None
        return self.book


@dataclass
class _StubTagRepository:
    tag_counts: List[int]
    calls: List[tuple[TagEntityType, UUID]]

    def __init__(self, tag_count: int) -> None:
        self.tag_counts = [tag_count]
        self.calls = []

    async def find_by_entity(self, entity_type: TagEntityType, entity_id: UUID):
        self.calls.append((entity_type, entity_id))
        return [object() for _ in range(self.tag_counts[0])]


@dataclass
class _StubBlockRepository:
    count: int
    type_count: int
    calls: List[UUID]

    def __init__(self, count: int, type_count: int) -> None:
        self.count = count
        self.type_count = type_count
        self.calls = []

    async def count_active_blocks(self, book_id: UUID) -> tuple[int, int]:
        self.calls.append(book_id)
        return self.count, self.type_count


def _make_book(*, snapshot: int) -> Book:
    book = Book.create(
        bookshelf_id=uuid4(),
        library_id=uuid4(),
        title="Test",
        summary="Summary",
    )
    book.tag_count_snapshot = snapshot
    book.summary = BookSummary(value="Summary")
    book.title = BookTitle(value="Test")
    return book


@pytest.mark.asyncio
async def test_provider_uses_live_tag_count_when_snapshot_missing():
    book = _make_book(snapshot=0)
    book_repo = _StubBookRepository(book)
    tag_repo = _StubTagRepository(tag_count=3)

    provider = BookAggregateMaturityDataProvider(book_repo, tag_repository=tag_repo)

    profile = await provider.load_book_profile(book.id)

    assert profile.tag_count_snapshot == 3
    assert tag_repo.calls == [(TagEntityType.BOOK, book.id)]


@pytest.mark.asyncio
async def test_provider_respects_snapshot_when_present():
    book = _make_book(snapshot=4)
    book_repo = _StubBookRepository(book)
    tag_repo = _StubTagRepository(tag_count=7)

    provider = BookAggregateMaturityDataProvider(book_repo, tag_repository=tag_repo)


@pytest.mark.asyncio
async def test_provider_uses_live_block_metrics_when_missing():
    book = _make_book(snapshot=2)
    book.block_count = 0
    book.block_type_count = 0
    book_repo = _StubBookRepository(book)
    block_repo = _StubBlockRepository(count=5, type_count=3)

    provider = BookAggregateMaturityDataProvider(book_repo, block_repository=block_repo)

    profile = await provider.load_book_profile(book.id)

    assert profile.block_count == 5
    assert profile.block_type_count == 3
    assert block_repo.calls == [book.id]


    book = _make_book(snapshot=2)
    book.block_count = 7
    book.block_type_count = 4
    book_repo = _StubBookRepository(book)
    block_repo = _StubBlockRepository(count=10, type_count=5)

    provider = BookAggregateMaturityDataProvider(book_repo, block_repository=block_repo)

    profile = await provider.load_book_profile(book.id)

    assert profile.block_count == 7
    assert profile.block_type_count == 4
    assert block_repo.calls == []

