import logging
from io import BytesIO
from types import SimpleNamespace
from typing import Optional
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from starlette.datastructures import Headers, UploadFile

from api.app.dependencies import get_di_container
from api.app.modules.library.exceptions import LibraryNotFoundError
from api.app.modules.media.exceptions import MediaOperationError


def _make_upload(*, filename: str, content: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        file=BytesIO(content),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


def _find_outcome(caplog, *, operation: str) -> dict:
    for record in caplog.records:
        if isinstance(record.msg, dict) and record.msg.get("event") == "usecase.outcome":
            if record.msg.get("operation") == operation:
                return record.msg
    raise AssertionError(f"No usecase.outcome log found for operation={operation}")


class _FakeAsyncSession:
    pass


class _FakeStorage:
    def __init__(self, *, save_raises: Optional[Exception] = None):
        self.save_raises = save_raises
        self.deleted = []

    async def save_library_cover(self, content: bytes, library_id: UUID, filename: str) -> str:
        if self.save_raises:
            raise self.save_raises
        return f"library/{library_id}/{filename}"

    async def save_book_cover(self, content: bytes, book_id: UUID, filename: str) -> str:
        if self.save_raises:
            raise self.save_raises
        return f"book/{book_id}/{filename}"

    async def delete_file(self, storage_key: str) -> None:
        self.deleted.append(storage_key)


class _FakeGetLibraryUseCase:
    def __init__(self, *, snapshot=None, raises: Optional[Exception] = None):
        self.snapshot = snapshot
        self.raises = raises

    async def execute(self, request):
        if self.raises:
            raise self.raises
        return self.snapshot


class _FakeUpdateLibraryUseCase:
    def __init__(self, *, response=None):
        self.response = response

    async def execute(self, request):
        return self.response


class _FakeUploadImageUseCase:
    def __init__(self, *, media=None, raises: Optional[Exception] = None):
        self.media = media
        self.raises = raises

    async def execute(self, filename, mime_type, file_size, storage_key, user_id=None):
        if self.raises:
            raise self.raises
        return self.media


class _FakeBookUseCase:
    def __init__(self, *, book=None, raises: Optional[Exception] = None):
        self.book = book
        self.raises = raises

    async def execute(self, request):
        if self.raises:
            raise self.raises
        return self.book


class _FakeUpdateBookUseCase:
    def __init__(self, *, book=None, raises: Optional[Exception] = None):
        self.book = book
        self.raises = raises

    async def execute(self, request):
        if self.raises:
            raise self.raises
        return self.book


class _FakeDI:
    def __init__(
        self,
        *,
        get_library_uc=None,
        update_library_uc=None,
        get_book_uc=None,
        update_book_uc=None,
        upload_image_uc=None,
    ):
        self._get_library_uc = get_library_uc
        self._update_library_uc = update_library_uc
        self._get_book_uc = get_book_uc
        self._update_book_uc = update_book_uc
        self._upload_image_uc = upload_image_uc

    def get_get_library_use_case(self):
        return self._get_library_uc

    def get_update_library_use_case(self):
        return self._update_library_uc

    def get_get_book_use_case(self):
        return self._get_book_uc

    def get_update_book_use_case(self):
        return self._update_book_uc

    def get_upload_image_use_case(self):
        return self._upload_image_uc


@pytest.mark.asyncio
async def test_library_cover_bind_contract_not_found_emits_outcome(monkeypatch, caplog):
    from api.app.modules.library.routers import library_router as module

    caplog.set_level(logging.INFO)

    library_id = uuid4()
    request = SimpleNamespace(state=SimpleNamespace(correlation_id="cid-test"))

    monkeypatch.setattr(module, "_settings", SimpleNamespace(allow_dev_library_owner_override=False), raising=False)

    di = _FakeDI(
        get_library_uc=_FakeGetLibraryUseCase(raises=LibraryNotFoundError("missing")),
        upload_image_uc=_FakeUploadImageUseCase(media=SimpleNamespace(id=uuid4())),
        update_library_uc=_FakeUpdateLibraryUseCase(response=SimpleNamespace(user_id=uuid4(), library_id=library_id)),
    )

    with pytest.raises(HTTPException) as exc:
        await module.upload_library_cover(
            library_id=library_id,
            request=request,
            file=_make_upload(filename="c.png", content=b"123", content_type="image/png"),
            user_id=uuid4(),
            di=di,
            session=_FakeAsyncSession(),
        )

    assert exc.value.status_code == 404
    outcome = _find_outcome(caplog, operation="library.cover.bind")
    assert outcome["outcome"] == "not_found"
    assert outcome["status_code"] == 404
    assert outcome["correlation_id"] == "cid-test"


@pytest.mark.asyncio
async def test_library_cover_bind_contract_forbidden_emits_outcome(monkeypatch, caplog):
    from api.app.modules.library.routers import library_router as module

    caplog.set_level(logging.INFO)

    library_id = uuid4()
    current_user_id = uuid4()
    library_owner_id = uuid4()
    request = SimpleNamespace(state=SimpleNamespace(correlation_id="cid-test"))

    monkeypatch.setattr(module, "_settings", SimpleNamespace(allow_dev_library_owner_override=False), raising=False)

    di = _FakeDI(
        get_library_uc=_FakeGetLibraryUseCase(snapshot=SimpleNamespace(user_id=library_owner_id)),
        upload_image_uc=_FakeUploadImageUseCase(media=SimpleNamespace(id=uuid4())),
        update_library_uc=_FakeUpdateLibraryUseCase(response=SimpleNamespace(user_id=library_owner_id, library_id=library_id)),
    )

    with pytest.raises(HTTPException) as exc:
        await module.upload_library_cover(
            library_id=library_id,
            request=request,
            file=_make_upload(filename="c.png", content=b"123", content_type="image/png"),
            user_id=current_user_id,
            di=di,
            session=_FakeAsyncSession(),
        )

    assert exc.value.status_code == 403
    outcome = _find_outcome(caplog, operation="library.cover.bind")
    assert outcome["outcome"] == "forbidden"
    assert outcome["status_code"] == 403


@pytest.mark.asyncio
async def test_library_cover_bind_contract_validation_failed_empty_file_emits_outcome(monkeypatch, caplog):
    from api.app.modules.library.routers import library_router as module

    caplog.set_level(logging.INFO)

    library_id = uuid4()
    owner_id = uuid4()
    request = SimpleNamespace(state=SimpleNamespace(correlation_id="cid-test"))

    monkeypatch.setattr(module, "_settings", SimpleNamespace(allow_dev_library_owner_override=False), raising=False)

    di = _FakeDI(
        get_library_uc=_FakeGetLibraryUseCase(snapshot=SimpleNamespace(user_id=owner_id)),
        upload_image_uc=_FakeUploadImageUseCase(media=SimpleNamespace(id=uuid4())),
        update_library_uc=_FakeUpdateLibraryUseCase(response=SimpleNamespace(user_id=owner_id, library_id=library_id)),
    )

    with pytest.raises(HTTPException) as exc:
        await module.upload_library_cover(
            library_id=library_id,
            request=request,
            file=_make_upload(filename="c.png", content=b"", content_type="image/png"),
            user_id=owner_id,
            di=di,
            session=_FakeAsyncSession(),
        )

    assert exc.value.status_code == 400
    outcome = _find_outcome(caplog, operation="library.cover.bind")
    assert outcome["outcome"] == "validation_failed"
    assert outcome["status_code"] == 400


@pytest.mark.asyncio
async def test_library_cover_bind_contract_error_storage_failure_emits_outcome(monkeypatch, caplog):
    from api.app.modules.library.routers import library_router as module

    caplog.set_level(logging.INFO)

    library_id = uuid4()
    owner_id = uuid4()
    request = SimpleNamespace(state=SimpleNamespace(correlation_id="cid-test"))

    monkeypatch.setattr(module, "_settings", SimpleNamespace(allow_dev_library_owner_override=False), raising=False)
    monkeypatch.setattr(module, "_library_cover_storage", _FakeStorage(save_raises=RuntimeError("disk down")), raising=False)

    di = _FakeDI(
        get_library_uc=_FakeGetLibraryUseCase(snapshot=SimpleNamespace(user_id=owner_id)),
        upload_image_uc=_FakeUploadImageUseCase(media=SimpleNamespace(id=uuid4())),
        update_library_uc=_FakeUpdateLibraryUseCase(response=SimpleNamespace(user_id=owner_id, library_id=library_id)),
    )

    with pytest.raises(HTTPException) as exc:
        await module.upload_library_cover(
            library_id=library_id,
            request=request,
            file=_make_upload(filename="c.png", content=b"123", content_type="image/png"),
            user_id=owner_id,
            di=di,
            session=_FakeAsyncSession(),
        )

    assert exc.value.status_code == 500
    outcome = _find_outcome(caplog, operation="library.cover.bind")
    assert outcome["outcome"] == "error"
    assert outcome["status_code"] == 500


@pytest.mark.asyncio
async def test_library_cover_bind_contract_success_emits_outcome(monkeypatch, caplog):
    from api.app.modules.library.routers import library_router as module

    caplog.set_level(logging.INFO)

    library_id = uuid4()
    owner_id = uuid4()
    media_id = uuid4()
    request = SimpleNamespace(state=SimpleNamespace(correlation_id="cid-test"))

    monkeypatch.setattr(module, "_settings", SimpleNamespace(allow_dev_library_owner_override=False), raising=False)
    monkeypatch.setattr(module, "_library_cover_storage", _FakeStorage(), raising=False)

    async def _fake_load_tags(session, library_ids):
        return {}, {}

    def _fake_build_detail_response(uc_response, tags=None, tag_total_count=0):
        return {
            "library_id": str(getattr(uc_response, "library_id", library_id)),
            "user_id": str(getattr(uc_response, "user_id", owner_id)),
            "cover_media_id": str(getattr(uc_response, "cover_media_id", None)),
        }

    monkeypatch.setattr(module, "_load_library_tags", _fake_load_tags, raising=False)
    monkeypatch.setattr(module, "_build_library_detail_response", _fake_build_detail_response, raising=False)

    upload_uc = _FakeUploadImageUseCase(media=SimpleNamespace(id=media_id))
    update_uc = _FakeUpdateLibraryUseCase(response=SimpleNamespace(user_id=owner_id, library_id=library_id, cover_media_id=media_id))

    di = _FakeDI(
        get_library_uc=_FakeGetLibraryUseCase(snapshot=SimpleNamespace(user_id=owner_id)),
        upload_image_uc=upload_uc,
        update_library_uc=update_uc,
    )

    result = await module.upload_library_cover(
        library_id=library_id,
        request=request,
        file=_make_upload(filename="c.png", content=b"123", content_type="image/png"),
        user_id=owner_id,
        di=di,
        session=_FakeAsyncSession(),
    )

    assert result["library_id"] == str(library_id)
    assert result["cover_media_id"] == str(media_id)

    outcome = _find_outcome(caplog, operation="library.cover.bind")
    assert outcome["outcome"] == "success"
    assert outcome["status_code"] == 201
    assert outcome["media_id"] == str(media_id)


@pytest.mark.asyncio
async def test_book_cover_bind_contract_not_found_emits_outcome(monkeypatch, caplog):
    from api.app.modules.book.routers import book_router as module

    caplog.set_level(logging.INFO)

    book_id = uuid4()
    request = SimpleNamespace(state=SimpleNamespace(correlation_id="cid-test"))

    di = _FakeDI(
        get_book_uc=_FakeBookUseCase(raises=module.BookNotFoundError(book_id)),
        upload_image_uc=_FakeUploadImageUseCase(media=SimpleNamespace(id=uuid4())),
        update_book_uc=_FakeUpdateBookUseCase(book=SimpleNamespace(id=book_id)),
    )

    with pytest.raises(HTTPException) as exc:
        await module.upload_book_cover(
            book_id=book_id,
            request=request,
            file=_make_upload(filename="c.png", content=b"123", content_type="image/png"),
            di=di,
        )

    assert exc.value.status_code == 404
    outcome = _find_outcome(caplog, operation="book.cover.bind")
    assert outcome["outcome"] == "not_found"
    assert outcome["status_code"] == 404
    assert outcome["correlation_id"] == "cid-test"


@pytest.mark.asyncio
async def test_book_cover_bind_contract_validation_failed_not_stable_emits_outcome(monkeypatch, caplog):
    from api.app.modules.book.routers import book_router as module

    caplog.set_level(logging.INFO)

    book_id = uuid4()
    request = SimpleNamespace(state=SimpleNamespace(correlation_id="cid-test"))

    book = SimpleNamespace(id=book_id, maturity=module.BookMaturity.SEED, legacy_flag=False)

    di = _FakeDI(
        get_book_uc=_FakeBookUseCase(book=book),
        upload_image_uc=_FakeUploadImageUseCase(media=SimpleNamespace(id=uuid4())),
        update_book_uc=_FakeUpdateBookUseCase(book=book),
    )

    with pytest.raises(HTTPException) as exc:
        await module.upload_book_cover(
            book_id=book_id,
            request=request,
            file=_make_upload(filename="c.png", content=b"123", content_type="image/png"),
            di=di,
        )

    assert exc.value.status_code == 422
    outcome = _find_outcome(caplog, operation="book.cover.bind")
    assert outcome["outcome"] == "validation_failed"
    assert outcome["status_code"] == 422
    assert outcome["correlation_id"] == "cid-test"


@pytest.mark.asyncio
async def test_book_cover_bind_contract_validation_failed_empty_file_emits_outcome(monkeypatch, caplog):
    from api.app.modules.book.routers import book_router as module

    caplog.set_level(logging.INFO)

    book_id = uuid4()
    request = SimpleNamespace(state=SimpleNamespace(correlation_id="cid-test"))

    book = SimpleNamespace(id=book_id, maturity=module.BookMaturity.STABLE, legacy_flag=False)

    di = _FakeDI(
        get_book_uc=_FakeBookUseCase(book=book),
        upload_image_uc=_FakeUploadImageUseCase(media=SimpleNamespace(id=uuid4())),
        update_book_uc=_FakeUpdateBookUseCase(book=book),
    )

    with pytest.raises(HTTPException) as exc:
        await module.upload_book_cover(
            book_id=book_id,
            request=request,
            file=_make_upload(filename="c.png", content=b"", content_type="image/png"),
            di=di,
        )

    assert exc.value.status_code == 400
    outcome = _find_outcome(caplog, operation="book.cover.bind")
    assert outcome["outcome"] == "validation_failed"
    assert outcome["status_code"] == 400


@pytest.mark.asyncio
async def test_book_cover_bind_contract_error_storage_failure_emits_outcome(monkeypatch, caplog):
    from api.app.modules.book.routers import book_router as module

    caplog.set_level(logging.INFO)

    book_id = uuid4()
    request = SimpleNamespace(state=SimpleNamespace(correlation_id="cid-test"))

    monkeypatch.setattr(module, "_book_cover_storage", _FakeStorage(save_raises=RuntimeError("disk down")), raising=False)

    book = SimpleNamespace(id=book_id, maturity=module.BookMaturity.STABLE, legacy_flag=False)

    di = _FakeDI(
        get_book_uc=_FakeBookUseCase(book=book),
        upload_image_uc=_FakeUploadImageUseCase(media=SimpleNamespace(id=uuid4())),
        update_book_uc=_FakeUpdateBookUseCase(book=book),
    )

    with pytest.raises(HTTPException) as exc:
        await module.upload_book_cover(
            book_id=book_id,
            request=request,
            file=_make_upload(filename="c.png", content=b"123", content_type="image/png"),
            di=di,
        )

    assert exc.value.status_code == 500
    outcome = _find_outcome(caplog, operation="book.cover.bind")
    assert outcome["outcome"] == "error"
    assert outcome["status_code"] == 500


@pytest.mark.asyncio
async def test_book_cover_bind_contract_success_emits_outcome(monkeypatch, caplog):
    from api.app.modules.book.routers import book_router as module

    caplog.set_level(logging.INFO)

    book_id = uuid4()
    media_id = uuid4()
    request = SimpleNamespace(state=SimpleNamespace(correlation_id="cid-test"))

    monkeypatch.setattr(module, "_book_cover_storage", _FakeStorage(), raising=False)

    async def _fake_serialize_book_with_theme(book, di):
        return {
            "id": str(getattr(book, "id", book_id)),
            "cover_media_id": str(getattr(book, "cover_media_id", media_id)),
        }

    monkeypatch.setattr(module, "_serialize_book_with_theme", _fake_serialize_book_with_theme, raising=False)

    book = SimpleNamespace(id=book_id, maturity=module.BookMaturity.STABLE, legacy_flag=False)
    updated_book = SimpleNamespace(id=book_id, maturity=module.BookMaturity.STABLE, legacy_flag=False, cover_media_id=media_id)

    di = _FakeDI(
        get_book_uc=_FakeBookUseCase(book=book),
        upload_image_uc=_FakeUploadImageUseCase(media=SimpleNamespace(id=media_id)),
        update_book_uc=_FakeUpdateBookUseCase(book=updated_book),
    )

    result = await module.upload_book_cover(
        book_id=book_id,
        request=request,
        file=_make_upload(filename="c.png", content=b"123", content_type="image/png"),
        di=di,
    )

    assert result["id"] == str(book_id)
    assert result["cover_media_id"] == str(media_id)

    outcome = _find_outcome(caplog, operation="book.cover.bind")
    assert outcome["outcome"] == "success"
    assert outcome["status_code"] == 201
    assert outcome["media_id"] == str(media_id)


def test_step0_step4_book_cover_bind_smoke(monkeypatch, caplog):
    from api.app.modules.book.routers import book_router as module

    caplog.set_level(logging.INFO)

    book_id = uuid4()
    media_id = uuid4()

    # step0: 准备 app + 依赖覆盖 + CID middleware
    app = FastAPI()

    @app.middleware("http")
    async def _cid_middleware(request, call_next):
        request.state.correlation_id = request.headers.get("X-Request-Id")
        return await call_next(request)

    monkeypatch.setattr(module, "_book_cover_storage", _FakeStorage(), raising=False)

    async def _fake_serialize_book_with_theme(book, di):
        return {"id": str(getattr(book, "id", book_id)), "cover_media_id": str(getattr(book, "cover_media_id", media_id))}

    monkeypatch.setattr(module, "_serialize_book_with_theme", _fake_serialize_book_with_theme, raising=False)

    book = SimpleNamespace(id=book_id, maturity=module.BookMaturity.STABLE, legacy_flag=False, library_id=uuid4())
    updated_book = SimpleNamespace(id=book_id, cover_media_id=media_id, maturity=module.BookMaturity.STABLE, legacy_flag=False, library_id=uuid4())

    di = _FakeDI(
        get_book_uc=_FakeBookUseCase(book=book),
        update_book_uc=_FakeUpdateBookUseCase(book=updated_book),
        upload_image_uc=_FakeUploadImageUseCase(media=SimpleNamespace(id=media_id)),
    )

    app.dependency_overrides[get_di_container] = lambda: di
    app.include_router(module.router, prefix="/api/v1/books")

    client = TestClient(app)

    # step1: 调用 endpoint
    response = client.post(
        f"/api/v1/books/{book_id}/cover",
        files={"file": ("c.png", b"123", "image/png")},
        headers={"X-Request-Id": "cid-xyz"},
    )

    # step2: 断言 HTTP 响应
    assert response.status_code == 201

    # step3: 断言 usecase.outcome 日志
    outcome = _find_outcome(caplog, operation="book.cover.bind")
    assert outcome["outcome"] == "success"
    assert outcome["correlation_id"] == "cid-xyz"

    # step4: 断言最小输出 shape
    body = response.json()
    assert body["id"] == str(book_id)
