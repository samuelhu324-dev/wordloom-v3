import pytest
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from api.app.modules.library.application.ports.input import GetLibraryRequest, GetLibraryResponse
from api.app.modules.library.application.use_cases.update_library import UpdateLibraryRequest, UpdateLibraryResponse
from api.app.modules.library.application.use_cases.upload_library_cover import (
    UploadLibraryCoverOutcome,
    UploadLibraryCoverRequest,
    UploadLibraryCoverUseCase,
)
from api.app.modules.library.exceptions import LibraryNotFoundError
from api.app.modules.media.domain import Media, MediaMimeType
from api.app.modules.media.exceptions import (
    InvalidMimeTypeError,
    StorageQuotaExceededError,
)


@dataclass
class _MediaStub:
    id: UUID


class FakeGetLibraryUseCase:
    def __init__(self, response: GetLibraryResponse | None = None, *, raise_not_found: bool = False):
        self._response = response
        self._raise_not_found = raise_not_found

    async def execute(self, request: GetLibraryRequest) -> GetLibraryResponse:
        if self._raise_not_found or self._response is None:
            raise LibraryNotFoundError(str(request.library_id))
        return self._response


class FakeUpdateLibraryUseCase:
    def __init__(self, *, user_id: UUID | None = None, force_error: Exception | None = None):
        self.user_id = user_id
        self.force_error = force_error
        self.last_request: UpdateLibraryRequest | None = None

    async def execute(self, request: UpdateLibraryRequest) -> UpdateLibraryResponse:
        self.last_request = request
        if self.force_error:
            raise self.force_error

        now = datetime.now(timezone.utc)
        return UpdateLibraryResponse(
            library_id=request.library_id,
            user_id=self.user_id or uuid4(),
            name="lib",
            description=None,
            cover_media_id=request.cover_media_id if request.cover_media_id_provided else None,
            created_at=now,
            updated_at=now,
            basement_bookshelf_id=None,
            pinned=False,
            pinned_order=None,
            archived_at=None,
            last_activity_at=now,
            views_count=0,
            last_viewed_at=None,
            theme_color=None,
        )


class FakeStorage:
    def __init__(self, *, fail_save: bool = False):
        self.fail_save = fail_save
        self.saved: list[tuple[UUID, str, int]] = []
        self.deleted: list[str] = []

    async def save_library_cover(self, content: bytes, library_id: UUID, original_filename: str) -> str:
        if self.fail_save:
            raise RuntimeError("disk full")
        key = f"library_covers/{library_id}/{uuid4()}.png"
        self.saved.append((library_id, original_filename, len(content)))
        return key

    async def delete_file(self, file_path: str) -> None:
        self.deleted.append(file_path)


class FakeUploadImageUseCase:
    def __init__(self, *, to_raise: Exception | None = None, fixed_media_id: UUID | None = None):
        self.to_raise = to_raise
        self.fixed_media_id = fixed_media_id
        self.calls: list[dict] = []

    async def execute(self, *, filename: str, mime_type: MediaMimeType, file_size: int, storage_key: str, user_id=None, width=None, height=None):
        self.calls.append(
            {
                "filename": filename,
                "mime_type": mime_type,
                "file_size": file_size,
                "storage_key": storage_key,
                "user_id": user_id,
            }
        )
        if self.to_raise:
            raise self.to_raise
        media = Media.create_image(
            filename=filename,
            mime_type=mime_type,
            file_size=file_size,
            storage_key=storage_key,
            user_id=user_id,
        )
        if self.fixed_media_id is not None:
            return _MediaStub(id=self.fixed_media_id)
        return media


def _sample_library_response(*, owner_id: UUID, library_id: UUID | None = None, cover_media_id: UUID | None = None) -> GetLibraryResponse:
    now = datetime.now(timezone.utc)
    return GetLibraryResponse(
        library_id=library_id or uuid4(),
        user_id=owner_id,
        name="lib",
        description=None,
        cover_media_id=cover_media_id,
        basement_bookshelf_id=None,
        created_at=now,
        updated_at=now,
        is_deleted=False,
        pinned=False,
        pinned_order=None,
        archived_at=None,
        last_activity_at=now,
        views_count=0,
        last_viewed_at=None,
        theme_color=None,
    )


@pytest.mark.asyncio
async def test_outcome_not_found():
    storage = FakeStorage()
    uc = UploadLibraryCoverUseCase(
        get_library_use_case=FakeGetLibraryUseCase(raise_not_found=True),
        upload_image_use_case=FakeUploadImageUseCase(),
        update_library_use_case=FakeUpdateLibraryUseCase(),
        storage=storage,
        allow_dev_library_owner_override=False,
    )

    res = await uc.execute(
        UploadLibraryCoverRequest(
            library_id=uuid4(),
            actor_user_id=uuid4(),
            file_bytes=b"x",
            original_filename="a.png",
            content_type="image/png",
        )
    )

    assert res.outcome == UploadLibraryCoverOutcome.NOT_FOUND
    assert storage.saved == []


@pytest.mark.asyncio
async def test_outcome_forbidden_when_not_owner():
    owner_id = uuid4()
    actor_id = uuid4()
    storage = FakeStorage()
    uc = UploadLibraryCoverUseCase(
        get_library_use_case=FakeGetLibraryUseCase(response=_sample_library_response(owner_id=owner_id)),
        upload_image_use_case=FakeUploadImageUseCase(),
        update_library_use_case=FakeUpdateLibraryUseCase(),
        storage=storage,
        allow_dev_library_owner_override=False,
    )

    res = await uc.execute(
        UploadLibraryCoverRequest(
            library_id=uuid4(),
            actor_user_id=actor_id,
            file_bytes=b"x",
            original_filename="a.png",
            content_type="image/png",
        )
    )

    assert res.outcome == UploadLibraryCoverOutcome.FORBIDDEN
    assert storage.saved == []


@pytest.mark.asyncio
async def test_outcome_rejected_empty_file():
    owner_id = uuid4()
    storage = FakeStorage()
    uc = UploadLibraryCoverUseCase(
        get_library_use_case=FakeGetLibraryUseCase(response=_sample_library_response(owner_id=owner_id)),
        upload_image_use_case=FakeUploadImageUseCase(),
        update_library_use_case=FakeUpdateLibraryUseCase(),
        storage=storage,
        allow_dev_library_owner_override=True,
    )

    res = await uc.execute(
        UploadLibraryCoverRequest(
            library_id=uuid4(),
            actor_user_id=owner_id,
            file_bytes=b"",
            original_filename="a.png",
            content_type="image/png",
        )
    )

    assert res.outcome == UploadLibraryCoverOutcome.REJECTED_EMPTY
    assert storage.saved == []


@pytest.mark.asyncio
async def test_outcome_rejected_mime_before_storage():
    owner_id = uuid4()
    storage = FakeStorage()
    uc = UploadLibraryCoverUseCase(
        get_library_use_case=FakeGetLibraryUseCase(response=_sample_library_response(owner_id=owner_id)),
        upload_image_use_case=FakeUploadImageUseCase(),
        update_library_use_case=FakeUpdateLibraryUseCase(),
        storage=storage,
        allow_dev_library_owner_override=True,
    )

    res = await uc.execute(
        UploadLibraryCoverRequest(
            library_id=uuid4(),
            actor_user_id=owner_id,
            file_bytes=b"x",
            original_filename="a.pdf",
            content_type="application/pdf",
        )
    )

    assert res.outcome == UploadLibraryCoverOutcome.REJECTED_MIME
    assert storage.saved == []


@pytest.mark.asyncio
async def test_outcome_rejected_too_large_before_storage():
    owner_id = uuid4()
    storage = FakeStorage()
    uc = UploadLibraryCoverUseCase(
        get_library_use_case=FakeGetLibraryUseCase(response=_sample_library_response(owner_id=owner_id)),
        upload_image_use_case=FakeUploadImageUseCase(),
        update_library_use_case=FakeUpdateLibraryUseCase(),
        storage=storage,
        allow_dev_library_owner_override=True,
    )

    res = await uc.execute(
        UploadLibraryCoverRequest(
            library_id=uuid4(),
            actor_user_id=owner_id,
            file_bytes=b"x" * (UploadLibraryCoverUseCase.MAX_IMAGE_SIZE + 1),
            original_filename="a.png",
            content_type="image/png",
        )
    )

    assert res.outcome == UploadLibraryCoverOutcome.REJECTED_TOO_LARGE
    assert storage.saved == []


@pytest.mark.asyncio
async def test_outcome_storage_save_failed():
    owner_id = uuid4()
    storage = FakeStorage(fail_save=True)
    uc = UploadLibraryCoverUseCase(
        get_library_use_case=FakeGetLibraryUseCase(response=_sample_library_response(owner_id=owner_id)),
        upload_image_use_case=FakeUploadImageUseCase(),
        update_library_use_case=FakeUpdateLibraryUseCase(),
        storage=storage,
        allow_dev_library_owner_override=True,
    )

    res = await uc.execute(
        UploadLibraryCoverRequest(
            library_id=uuid4(),
            actor_user_id=owner_id,
            file_bytes=b"x",
            original_filename="a.png",
            content_type="image/png",
        )
    )

    assert res.outcome == UploadLibraryCoverOutcome.STORAGE_SAVE_FAILED
    assert storage.saved == []


@pytest.mark.asyncio
async def test_outcome_quota_exceeded_deletes_saved_file():
    owner_id = uuid4()
    storage = FakeStorage()
    upload = FakeUploadImageUseCase(to_raise=StorageQuotaExceededError(used_bytes=0, quota_bytes=0, needed_bytes=1))
    uc = UploadLibraryCoverUseCase(
        get_library_use_case=FakeGetLibraryUseCase(response=_sample_library_response(owner_id=owner_id)),
        upload_image_use_case=upload,
        update_library_use_case=FakeUpdateLibraryUseCase(),
        storage=storage,
        allow_dev_library_owner_override=True,
    )

    res = await uc.execute(
        UploadLibraryCoverRequest(
            library_id=uuid4(),
            actor_user_id=owner_id,
            file_bytes=b"x",
            original_filename="a.png",
            content_type="image/png",
        )
    )

    assert res.outcome == UploadLibraryCoverOutcome.QUOTA_EXCEEDED
    assert len(storage.saved) == 1
    assert len(storage.deleted) == 1
    assert storage.deleted[0] == res.storage_key


@pytest.mark.asyncio
async def test_success_calls_update_with_cover_media_id():
    owner_id = uuid4()
    lib_id = uuid4()
    storage = FakeStorage()
    update = FakeUpdateLibraryUseCase(user_id=owner_id)
    upload = FakeUploadImageUseCase(fixed_media_id=uuid4())

    uc = UploadLibraryCoverUseCase(
        get_library_use_case=FakeGetLibraryUseCase(response=_sample_library_response(owner_id=owner_id, library_id=lib_id)),
        upload_image_use_case=upload,
        update_library_use_case=update,
        storage=storage,
        allow_dev_library_owner_override=False,
    )

    res = await uc.execute(
        UploadLibraryCoverRequest(
            library_id=lib_id,
            actor_user_id=owner_id,
            file_bytes=b"x",
            original_filename="a.png",
            content_type="image/png",
        )
    )

    assert res.outcome == UploadLibraryCoverOutcome.SUCCESS
    assert update.last_request is not None
    assert update.last_request.library_id == lib_id
    assert update.last_request.cover_media_id_provided is True
    assert update.last_request.cover_media_id == res.media_id
    assert storage.deleted == []


@pytest.mark.asyncio
async def test_success_exposes_previous_cover_media_id_when_replacing():
    owner_id = uuid4()
    lib_id = uuid4()
    previous = uuid4()

    storage = FakeStorage()
    upload = FakeUploadImageUseCase(fixed_media_id=uuid4())

    uc = UploadLibraryCoverUseCase(
        get_library_use_case=FakeGetLibraryUseCase(
            response=_sample_library_response(owner_id=owner_id, library_id=lib_id, cover_media_id=previous)
        ),
        upload_image_use_case=upload,
        update_library_use_case=FakeUpdateLibraryUseCase(user_id=owner_id),
        storage=storage,
        allow_dev_library_owner_override=True,
    )

    res = await uc.execute(
        UploadLibraryCoverRequest(
            library_id=lib_id,
            actor_user_id=owner_id,
            file_bytes=b"x",
            original_filename="a.png",
            content_type="image/png",
        )
    )

    assert res.outcome == UploadLibraryCoverOutcome.SUCCESS
    assert res.previous_cover_media_id == previous
