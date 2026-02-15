import pytest
from types import SimpleNamespace
from uuid import uuid4

from api.app.modules.book.application.use_cases.create_book import CreateBookUseCase
from api.app.modules.book.application.use_cases.get_book import GetBookUseCase
from api.app.modules.book.application.use_cases.list_books import ListBooksUseCase
from api.app.modules.book.application.ports.input import GetBookRequest, ListBooksRequest
from api.app.modules.book.exceptions import BookForbiddenError


class _StubLibraryRepository:
    def __init__(self, owners_by_library_id):
        self._owners_by_library_id = owners_by_library_id

    async def get_by_id(self, library_id):
        owner_id = self._owners_by_library_id.get(library_id)
        if owner_id is None:
            return None
        return SimpleNamespace(id=library_id, user_id=owner_id)


class _StubBookRepository:
    def __init__(self, *, book_by_id=None):
        self._book_by_id = book_by_id or {}

    async def save(self, book):  # pragma: no cover
        return book

    async def get_by_id(self, book_id):
        return self._book_by_id.get(book_id)

    async def get_by_bookshelf_id(self, bookshelf_id, skip, limit, *, include_deleted=False):  # pragma: no cover
        return ([], 0)

    async def get_by_library_id(self, library_id, skip, limit, *, include_deleted=False):  # pragma: no cover
        return ([], 0)


class _StubBookshelfRepository:
    def __init__(self, *, shelf_by_id=None):
        self._shelf_by_id = shelf_by_id or {}

    async def get_by_id(self, bookshelf_id):
        return self._shelf_by_id.get(bookshelf_id)


@pytest.mark.asyncio
async def test_create_book_forbidden_when_not_owner():
    library_id = uuid4()
    actor_user_id = uuid4()
    owner_user_id = uuid4()

    library_repo = _StubLibraryRepository({library_id: owner_user_id})
    book_repo = _StubBookRepository()

    use_case = CreateBookUseCase(book_repo, library_repository=library_repo)

    with pytest.raises(BookForbiddenError):
        await use_case.execute(
            bookshelf_id=uuid4(),
            library_id=library_id,
            title="x",
            description=None,
            cover_icon=None,
            actor_user_id=actor_user_id,
            enforce_owner_check=True,
        )


@pytest.mark.asyncio
async def test_get_book_forbidden_when_not_owner():
    library_id = uuid4()
    actor_user_id = uuid4()
    owner_user_id = uuid4()
    book_id = uuid4()

    library_repo = _StubLibraryRepository({library_id: owner_user_id})
    book_repo = _StubBookRepository(
        book_by_id={book_id: SimpleNamespace(id=book_id, library_id=library_id)}
    )

    use_case = GetBookUseCase(book_repo, library_repository=library_repo)

    with pytest.raises(BookForbiddenError):
        await use_case.execute(
            GetBookRequest(
                book_id=book_id,
                actor_user_id=actor_user_id,
                enforce_owner_check=True,
            )
        )


@pytest.mark.asyncio
async def test_list_books_forbidden_when_not_owner_by_library_id():
    library_id = uuid4()
    actor_user_id = uuid4()
    owner_user_id = uuid4()

    library_repo = _StubLibraryRepository({library_id: owner_user_id})
    book_repo = _StubBookRepository()

    use_case = ListBooksUseCase(book_repo, library_repository=library_repo)

    with pytest.raises(BookForbiddenError):
        await use_case.execute(
            ListBooksRequest(
                library_id=library_id,
                actor_user_id=actor_user_id,
                enforce_owner_check=True,
            )
        )


@pytest.mark.asyncio
async def test_list_books_forbidden_when_not_owner_resolves_library_from_bookshelf():
    library_id = uuid4()
    bookshelf_id = uuid4()
    actor_user_id = uuid4()
    owner_user_id = uuid4()

    library_repo = _StubLibraryRepository({library_id: owner_user_id})
    shelf_repo = _StubBookshelfRepository(
        shelf_by_id={bookshelf_id: SimpleNamespace(id=bookshelf_id, library_id=library_id)}
    )
    book_repo = _StubBookRepository()

    use_case = ListBooksUseCase(
        book_repo,
        library_repository=library_repo,
        bookshelf_repository=shelf_repo,
    )

    with pytest.raises(BookForbiddenError):
        await use_case.execute(
            ListBooksRequest(
                bookshelf_id=bookshelf_id,
                actor_user_id=actor_user_id,
                enforce_owner_check=True,
            )
        )


@pytest.mark.asyncio
async def test_get_book_allows_when_owner_check_disabled():
    library_id = uuid4()
    actor_user_id = uuid4()
    owner_user_id = uuid4()
    book_id = uuid4()

    library_repo = _StubLibraryRepository({library_id: owner_user_id})
    book_repo = _StubBookRepository(
        book_by_id={book_id: SimpleNamespace(id=book_id, library_id=library_id)}
    )

    use_case = GetBookUseCase(book_repo, library_repository=library_repo)

    book = await use_case.execute(
        GetBookRequest(
            book_id=book_id,
            actor_user_id=actor_user_id,
            enforce_owner_check=False,
        )
    )

    assert getattr(book, "id", None) == book_id
