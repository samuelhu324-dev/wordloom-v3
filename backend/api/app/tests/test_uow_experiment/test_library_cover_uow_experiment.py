import pytest
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.modules.library.application.use_cases.get_library import GetLibraryUseCase
from api.app.modules.library.application.use_cases.upload_library_cover import (
    UploadLibraryCoverOutcome,
    UploadLibraryCoverRequest,
    UploadLibraryCoverUseCase,
)
from api.app.modules.media.application.use_cases.upload_image import UploadImageUseCase

from infra.database.models.bookshelf_models import BookshelfModel
from infra.database.models.library_models import LibraryModel
from infra.database.models.media_models import MediaModel
from infra.storage.library_repository_impl import SQLAlchemyLibraryRepository
from infra.storage.media_repository_impl import SQLAlchemyMediaRepository


pytestmark = pytest.mark.anyio


class RecordingStorage:
    def __init__(self):
        self.saved: list[str] = []
        self.deleted: list[str] = []

    async def save_library_cover(self, content: bytes, library_id: UUID, original_filename: str) -> str:
        storage_key = f"tests://library/{library_id}/covers/{uuid4()}-{original_filename}"
        self.saved.append(storage_key)
        return storage_key

    async def delete_file(self, file_path: str) -> None:
        self.deleted.append(file_path)


class FailingUpdateLibraryUseCase:
    async def execute(self, request):
        raise RuntimeError("db update failed (simulated)")


async def _create_library_with_basement(session: AsyncSession, *, library_id: UUID, owner_id: UUID) -> UUID:
    session.add(
        LibraryModel(
            id=library_id,
            user_id=owner_id,
            name="Test Library",
            description=None,
            basement_bookshelf_id=None,
            cover_media_id=None,
        )
    )
    await session.commit()

    basement_id = uuid4()
    session.add(
        BookshelfModel(
            id=basement_id,
            library_id=library_id,
            name="Basement",
            description=None,
            is_basement=True,
        )
    )
    await session.commit()

    model = (await session.execute(select(LibraryModel).where(LibraryModel.id == library_id))).scalar_one()
    model.basement_bookshelf_id = basement_id
    await session.commit()

    return basement_id


async def _get_library_cover_media_id(session: AsyncSession, library_id: UUID) -> UUID | None:
    model = (await session.execute(select(LibraryModel).where(LibraryModel.id == library_id))).scalar_one()
    return model.cover_media_id


async def _media_exists(session: AsyncSession, media_id: UUID) -> bool:
    model = (await session.execute(select(MediaModel).where(MediaModel.id == media_id))).scalar_one_or_none()
    return model is not None


async def test_route_b_observation_without_uow_allows_partial_state(db_session: AsyncSession):
    """Route B observation: without an explicit UoW boundary, a multi-step use case can leave partial state.

    We simulate a failure after Media is created (DB write) but before Library is updated.
    Expectation (current/default design):
    - use case returns UPDATE_FAILED
    - library.cover_media_id remains unchanged
    - media row EXISTS (orphan)
    - storage file is NOT deleted (no compensation on update failure)
    """

    library_id = uuid4()
    owner_id = uuid4()
    await _create_library_with_basement(db_session, library_id=library_id, owner_id=owner_id)

    storage = RecordingStorage()

    get_library = GetLibraryUseCase(SQLAlchemyLibraryRepository(db_session))
    upload_image = UploadImageUseCase(SQLAlchemyMediaRepository(db_session))
    update_library = FailingUpdateLibraryUseCase()

    use_case = UploadLibraryCoverUseCase(
        get_library_use_case=get_library,
        upload_image_use_case=upload_image,
        update_library_use_case=update_library,
        storage=storage,
        allow_dev_library_owner_override=False,
    )

    before_cover_media_id = await _get_library_cover_media_id(db_session, library_id)

    result = await use_case.execute(
        UploadLibraryCoverRequest(
            library_id=library_id,
            actor_user_id=owner_id,
            file_bytes=b"fake-image-bytes",
            original_filename="cover.jpg",
            content_type="image/jpeg",
        )
    )

    assert result.outcome == UploadLibraryCoverOutcome.UPDATE_FAILED
    assert result.storage_key in storage.saved
    assert storage.deleted == []

    after_cover_media_id = await _get_library_cover_media_id(db_session, library_id)
    assert after_cover_media_id == before_cover_media_id

    assert result.media_id is not None
    assert await _media_exists(db_session, result.media_id) is True


async def test_route_b_expected_atomicity_requires_uow_and_compensation(db_session: AsyncSession):
    """Route B target behavior: on failure, DB + storage should be consistent."""

    library_id = uuid4()
    owner_id = uuid4()
    await _create_library_with_basement(db_session, library_id=library_id, owner_id=owner_id)

    storage = RecordingStorage()

    get_library = GetLibraryUseCase(SQLAlchemyLibraryRepository(db_session))
    upload_image = UploadImageUseCase(SQLAlchemyMediaRepository(db_session))
    update_library = FailingUpdateLibraryUseCase()

    use_case = UploadLibraryCoverUseCase(
        get_library_use_case=get_library,
        upload_image_use_case=upload_image,
        update_library_use_case=update_library,
        storage=storage,
        allow_dev_library_owner_override=False,
    )

    result = await use_case.execute(
        UploadLibraryCoverRequest(
            library_id=library_id,
            actor_user_id=owner_id,
            file_bytes=b"fake-image-bytes",
            original_filename="cover.jpg",
            content_type="image/jpeg",
        ),
        db_session=db_session,
    )

    assert result.outcome == UploadLibraryCoverOutcome.UPDATE_FAILED

    # Desired behavior:
    # 1) delete saved file
    assert storage.deleted == [result.storage_key]
    # 2) media row rolled back / not persisted
    assert result.media_id is not None
    assert await _media_exists(db_session, result.media_id) is False
