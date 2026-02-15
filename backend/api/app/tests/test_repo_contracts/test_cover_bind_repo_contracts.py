import pytest
from uuid import uuid4, UUID

from api.app.modules.book.domain import Book
from api.app.modules.bookshelf.domain import Bookshelf
from api.app.modules.library.domain import Library
from api.app.modules.media.domain import Media, MediaMimeType

from infra.storage.book_repository_impl import SQLAlchemyBookRepository
from infra.storage.bookshelf_repository_impl import SQLAlchemyBookshelfRepository
from infra.storage.library_repository_impl import SQLAlchemyLibraryRepository
from infra.storage.media_repository_impl import SQLAlchemyMediaRepository


class FakeBookRepository:
    def __init__(self) -> None:
        self._rows: dict[UUID, dict] = {}

    async def save(self, book: Book) -> Book:
        self._rows[book.id] = {
            "id": book.id,
            "bookshelf_id": book.bookshelf_id,
            "library_id": book.library_id,
            "title": book.title.value,
            "summary": book.summary.value if book.summary else None,
            "cover_icon": book.cover_icon,
            "cover_media_id": book.cover_media_id,
            "is_pinned": book.is_pinned,
            "due_at": book.due_at,
            "status": book.status,
            "maturity": book.maturity,
            "block_count": book.block_count,
            "soft_deleted_at": book.soft_deleted_at,
            "created_at": book.created_at,
            "updated_at": book.updated_at,
        }
        return book

    async def get_by_id(self, book_id: UUID):
        row = self._rows.get(book_id)
        if not row:
            return None
        from api.app.modules.book.domain import BookTitle, BookSummary

        return Book(
            book_id=row["id"],
            bookshelf_id=row["bookshelf_id"],
            library_id=row["library_id"],
            title=BookTitle(value=row["title"]),
            summary=BookSummary(value=row["summary"]),
            cover_icon=row["cover_icon"],
            cover_media_id=row["cover_media_id"],
            is_pinned=row["is_pinned"],
            due_at=row["due_at"],
            status=row["status"],
            maturity=row["maturity"],
            block_count=row["block_count"],
            soft_deleted_at=row["soft_deleted_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class FakeLibraryRepository:
    def __init__(self) -> None:
        self._rows: dict[UUID, dict] = {}

    async def save(self, library: Library) -> None:
        self._rows[library.id] = {
            "id": library.id,
            "user_id": library.user_id,
            "name": library.name.value,
            "basement_bookshelf_id": library.basement_bookshelf_id,
            "description": library.description,
            "cover_media_id": library.cover_media_id,
            "theme_color": library.theme_color,
            "pinned": library.pinned,
            "pinned_order": library.pinned_order,
            "archived_at": library.archived_at,
            "last_activity_at": library.last_activity_at,
            "views_count": library.views_count,
            "last_viewed_at": library.last_viewed_at,
            "created_at": library.created_at,
            "updated_at": library.updated_at,
            "soft_deleted_at": library.soft_deleted_at,
        }

    async def get_by_id(self, library_id: UUID):
        row = self._rows.get(library_id)
        if not row:
            return None
        # Reuse domain factory style by constructing directly.
        from api.app.modules.library.domain import LibraryName

        return Library(
            library_id=row["id"],
            user_id=row["user_id"],
            name=LibraryName(value=row["name"]),
            basement_bookshelf_id=row["basement_bookshelf_id"],
            description=row["description"],
            cover_media_id=row["cover_media_id"],
            theme_color=row["theme_color"],
            pinned=row["pinned"],
            pinned_order=row["pinned_order"],
            archived_at=row["archived_at"],
            last_activity_at=row["last_activity_at"],
            views_count=row["views_count"],
            last_viewed_at=row["last_viewed_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            soft_deleted_at=row["soft_deleted_at"],
        )


class FakeMediaRepository:
    def __init__(self) -> None:
        self._rows: dict[UUID, Media] = {}

    async def save(self, media: Media) -> Media:
        self._rows[media.id] = media
        return media

    async def get_by_id(self, media_id: UUID) -> Media | None:
        return self._rows.get(media_id)


@pytest.mark.asyncio
async def test_book_repo_cover_media_id_bind_contract_fake():
    media_repo = FakeMediaRepository()
    media = Media.create_image(
        filename="contract.png",
        mime_type=MediaMimeType.PNG,
        file_size=1,
        storage_key=f"contract/{uuid4()}.png",
    )
    await media_repo.save(media)
    new_media_id = media.id

    book_repo = FakeBookRepository()
    bookshelf_id = uuid4()
    library_id = uuid4()

    book = Book.create(
        bookshelf_id=bookshelf_id,
        library_id=library_id,
        title="contract-book",
    )
    await book_repo.save(book)

    # 1) initial state persisted
    loaded = await book_repo.get_by_id(book.id)
    assert loaded is not None
    assert getattr(loaded, "cover_media_id", None) is None

    # 2) mutate in-memory, but do NOT save: should not change persisted state
    book.cover_media_id = new_media_id
    loaded_without_save = await book_repo.get_by_id(book.id)
    assert loaded_without_save is not None
    assert getattr(loaded_without_save, "cover_media_id", None) is None

    # 3) save and verify
    await book_repo.save(book)
    loaded_after_save = await book_repo.get_by_id(book.id)
    assert loaded_after_save is not None
    assert loaded_after_save.cover_media_id == new_media_id


@pytest.mark.asyncio
async def test_book_repo_cover_media_id_bind_contract_sqlalchemy(db_session):
    library_repo = SQLAlchemyLibraryRepository(db_session)
    bookshelf_repo = SQLAlchemyBookshelfRepository(db_session)
    book_repo = SQLAlchemyBookRepository(db_session)
    media_repo = SQLAlchemyMediaRepository(db_session)

    library = Library.create(user_id=uuid4(), name="contract-library")
    # Bootstrap Library + Basement bookshelf (circular FK) the same way the
    # CreateLibrary use case does: save a "shell" row first, then create the
    # Basement bookshelf, then persist the FK back onto the Library row.
    basement_id = library.basement_bookshelf_id
    library.basement_bookshelf_id = None
    await library_repo.save(library)
    library.basement_bookshelf_id = basement_id

    basement = Bookshelf.create_basement(
        library_id=library.id,
        bookshelf_id=basement_id,
    )
    await bookshelf_repo.save(basement)
    await library_repo.save(library)

    bookshelf = Bookshelf.create(library_id=library.id, name="contract-shelf")
    await bookshelf_repo.save(bookshelf)

    book = Book.create(
        bookshelf_id=bookshelf.id,
        library_id=library.id,
        title="contract-book",
    )
    await book_repo.save(book)

    media = Media.create_image(
        filename="contract.png",
        mime_type=MediaMimeType.PNG,
        file_size=1,
        storage_key=f"contract/{uuid4()}.png",
    )
    await media_repo.save(media)
    new_media_id = media.id

    # 1) initial state persisted
    loaded = await book_repo.get_by_id(book.id)
    assert loaded is not None
    assert getattr(loaded, "cover_media_id", None) is None

    # 2) mutate in-memory, but do NOT save: should not change persisted state
    book.cover_media_id = new_media_id
    loaded_without_save = await book_repo.get_by_id(book.id)
    assert loaded_without_save is not None
    assert getattr(loaded_without_save, "cover_media_id", None) is None

    # 3) save and verify
    await book_repo.save(book)
    loaded_after_save = await book_repo.get_by_id(book.id)
    assert loaded_after_save is not None
    assert loaded_after_save.cover_media_id == new_media_id


@pytest.mark.asyncio
async def test_library_repo_cover_media_id_bind_contract_fake():
    new_media_id = uuid4()

    library_repo = FakeLibraryRepository()
    library = Library.create(user_id=uuid4(), name="contract-library")
    await library_repo.save(library)

    loaded = await library_repo.get_by_id(library.id)
    assert loaded is not None
    assert getattr(loaded, "cover_media_id", None) is None

    library.cover_media_id = new_media_id
    loaded_without_save = await library_repo.get_by_id(library.id)
    assert loaded_without_save is not None
    assert getattr(loaded_without_save, "cover_media_id", None) is None

    await library_repo.save(library)
    loaded_after_save = await library_repo.get_by_id(library.id)
    assert loaded_after_save is not None
    assert loaded_after_save.cover_media_id == new_media_id


@pytest.mark.asyncio
async def test_library_repo_cover_media_id_bind_contract_sqlalchemy(db_session):
    new_media_id = uuid4()

    library_repo = SQLAlchemyLibraryRepository(db_session)
    bookshelf_repo = SQLAlchemyBookshelfRepository(db_session)

    library = Library.create(user_id=uuid4(), name="contract-library")
    # Bootstrap Library + Basement bookshelf (circular FK) the same way the
    # CreateLibrary use case does: save a "shell" row first, then create the
    # Basement bookshelf, then persist the FK back onto the Library row.
    basement_id = library.basement_bookshelf_id
    library.basement_bookshelf_id = None
    await library_repo.save(library)
    library.basement_bookshelf_id = basement_id

    basement = Bookshelf.create_basement(
        library_id=library.id,
        bookshelf_id=basement_id,
    )
    await bookshelf_repo.save(basement)
    await library_repo.save(library)

    loaded = await library_repo.get_by_id(library.id)
    assert loaded is not None
    assert getattr(loaded, "cover_media_id", None) is None

    library.cover_media_id = new_media_id
    loaded_without_save = await library_repo.get_by_id(library.id)
    assert loaded_without_save is not None
    assert getattr(loaded_without_save, "cover_media_id", None) is None

    await library_repo.save(library)
    loaded_after_save = await library_repo.get_by_id(library.id)
    assert loaded_after_save is not None
    assert loaded_after_save.cover_media_id == new_media_id
