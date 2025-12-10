import pytest
from uuid import uuid4
from datetime import datetime, timezone

from api.app.modules.book.domain import Book, BookTitle
from api.app.modules.book.application.use_cases.update_book import UpdateBookUseCase
from api.app.modules.book.application.ports.input import UpdateBookRequest


class FakeBookRepository:
    """Minimal repository to exercise UpdateBookUseCase cover_icon flow."""

    def __init__(self):
        self._store = {}

    async def save(self, book: Book) -> Book:
        self._store[book.id] = book
        return book

    async def get_by_id(self, book_id):
        return self._store.get(book_id)


def _build_book():
    book = Book(
        book_id=uuid4(),
        bookshelf_id=uuid4(),
        library_id=uuid4(),
        title=BookTitle(value="Cover Icon Book"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    return book


@pytest.mark.asyncio
async def test_update_book_use_case_sets_cover_icon():
    repo = FakeBookRepository()
    book = _build_book()
    await repo.save(book)

    use_case = UpdateBookUseCase(repository=repo, event_bus=None)

    request = UpdateBookRequest(
        book_id=book.id,
        cover_icon="book-open",
        cover_icon_provided=True,
    )

    updated = await use_case.execute(request)

    assert updated.cover_icon == "book-open"


@pytest.mark.asyncio
async def test_update_book_use_case_clears_cover_icon():
    repo = FakeBookRepository()
    book = _build_book()
    book.update_cover_icon("bookmark")
    await repo.save(book)

    use_case = UpdateBookUseCase(repository=repo, event_bus=None)

    request = UpdateBookRequest(
        book_id=book.id,
        cover_icon=None,
        cover_icon_provided=True,
    )

    updated = await use_case.execute(request)

    assert updated.cover_icon is None
