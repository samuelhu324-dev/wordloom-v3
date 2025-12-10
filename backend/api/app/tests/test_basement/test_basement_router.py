"""Unit tests for Basement router endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from api.app.modules.basement.routers import basement_router
from api.app.modules.basement.schemas import MoveBookToBasementRequest
from api.app.modules.book.exceptions import BookNotFoundError, BookOperationError


class _StubDIContainer:
    """Minimal DI container replacement exposing the required use cases."""

    def __init__(
        self,
        *,
        move_use_case: Optional[object] = None,
        list_use_case: Optional[object] = None,
    ) -> None:
        self._move_use_case = move_use_case
        self._list_use_case = list_use_case

    def get_move_book_to_basement_use_case(self):  # pragma: no cover - simple proxy
        return self._move_use_case

    def get_list_basement_books_use_case(self):  # pragma: no cover - simple proxy
        return self._list_use_case


class _StubMoveBookToBasementUseCase:
    def __init__(self, *, snapshot: "_Snapshot", exception: Optional[Exception] = None) -> None:
        self._snapshot = snapshot
        self._exception = exception
        self.recorded_commands = []

    async def execute(self, command):
        self.recorded_commands.append(command)
        if self._exception:
            raise self._exception
        return self._snapshot


class _StubListBasementBooksUseCase:
    def __init__(
        self,
        *,
        snapshots: list["_Snapshot"],
        total: int,
        exception: Optional[Exception] = None,
    ) -> None:
        self._snapshots = snapshots
        self._total = total
        self._exception = exception
        self.recorded_queries = []

    async def execute(self, query):
        self.recorded_queries.append(query)
        if self._exception:
            raise self._exception
        return self._snapshots, self._total


@dataclass
class _Snapshot:
    id: UUID
    library_id: UUID
    bookshelf_id: UUID
    previous_bookshelf_id: Optional[UUID]
    title: str
    summary: Optional[str]
    status: str
    block_count: int
    moved_to_basement_at: Optional[datetime]
    soft_deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


def _make_snapshot(
    *,
    book_id: Optional[UUID] = None,
    library_id: Optional[UUID] = None,
    bookshelf_id: Optional[UUID] = None,
    previous_bookshelf_id: Optional[UUID] = None,
    title: str = "Archived book",
    summary: str = "Soft deleted",
    status: str = "archived",
    block_count: int = 5,
) -> _Snapshot:
    timestamp = datetime.utcnow()
    return _Snapshot(
        id=book_id or uuid4(),
        library_id=library_id or uuid4(),
        bookshelf_id=bookshelf_id or uuid4(),
        previous_bookshelf_id=previous_bookshelf_id,
        title=title,
        summary=summary,
        status=status,
        block_count=block_count,
        moved_to_basement_at=timestamp,
        soft_deleted_at=timestamp,
        created_at=timestamp,
        updated_at=timestamp,
    )


@pytest.mark.asyncio
async def test_move_book_to_basement_returns_snapshot_response():
    book_id = uuid4()
    request = MoveBookToBasementRequest(basement_bookshelf_id=uuid4(), reason="cleanup")
    snapshot = _make_snapshot(book_id=book_id, bookshelf_id=request.basement_bookshelf_id)
    use_case = _StubMoveBookToBasementUseCase(snapshot=snapshot)
    di = _StubDIContainer(move_use_case=use_case)

    response = await basement_router.move_book_to_basement(book_id, request, di)

    assert response.id == snapshot.id
    assert response.bookshelf_id == request.basement_bookshelf_id
    command = use_case.recorded_commands[-1]
    assert command.book_id == book_id
    assert command.basement_bookshelf_id == request.basement_bookshelf_id
    assert command.reason == "cleanup"


@pytest.mark.asyncio
async def test_move_book_to_basement_raises_http_exception_on_domain_error():
    book_id = uuid4()
    request = MoveBookToBasementRequest(basement_bookshelf_id=uuid4())
    expected_error = BookNotFoundError(str(book_id))
    use_case = _StubMoveBookToBasementUseCase(snapshot=_make_snapshot(), exception=expected_error)
    di = _StubDIContainer(move_use_case=use_case)

    with pytest.raises(HTTPException) as exc:
        await basement_router.move_book_to_basement(book_id, request, di)

    assert exc.value.status_code == expected_error.http_status_code
    assert exc.value.detail["code"] == expected_error.code


@pytest.mark.asyncio
async def test_list_basement_books_returns_paginated_response_with_metadata():
    library_id = uuid4()
    snapshots = [_make_snapshot(library_id=library_id) for _ in range(2)]
    use_case = _StubListBasementBooksUseCase(snapshots=snapshots, total=4)
    di = _StubDIContainer(list_use_case=use_case)

    response = await basement_router.list_basement_books(library_id, di, skip=2, limit=2)

    assert [item.id for item in response.items] == [snap.id for snap in snapshots]
    assert response.total == 4
    assert response.page == 2  # skip=2, limit=2 => page 2
    assert response.page_size == 2
    assert response.has_more is False
    query = use_case.recorded_queries[-1]
    assert query.library_id == library_id
    assert query.skip == 2
    assert query.limit == 2


@pytest.mark.asyncio
async def test_list_basement_books_converts_operation_errors_to_http_exception():
    library_id = uuid4()
    expected_error = BookOperationError("Failed to list Basement")
    use_case = _StubListBasementBooksUseCase(snapshots=[], total=0, exception=expected_error)
    di = _StubDIContainer(list_use_case=use_case)

    with pytest.raises(HTTPException) as exc:
        await basement_router.list_basement_books(library_id, di)

    assert exc.value.status_code == expected_error.http_status_code
    assert exc.value.detail["code"] == expected_error.code
