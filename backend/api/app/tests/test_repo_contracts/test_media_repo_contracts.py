import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4
import json
from contextlib import contextmanager

import pytest

from api.app.modules.media.domain import Media, MediaMimeType, MediaState
from api.app.shared.request_context import RequestContext
from infra.storage.media_repository_impl import SQLAlchemyMediaRepository


def _make_media(*, storage_key: str) -> Media:
    # NOTE: Second-knife contract: construct Media directly, do NOT involve UploadImageUseCase.
    return Media.create_image(
        filename="contract.png",
        mime_type=MediaMimeType.PNG,
        file_size=1234,
        storage_key=storage_key,
        user_id=uuid4(),
        width=640,
        height=480,
    )


class FakeMediaRepository:
    def __init__(self) -> None:
        self._rows: dict[UUID, dict] = {}
        # Use the same logger name as the real repository so caplog can capture
        # both implementations consistently.
        self._logger = logging.getLogger("infra.storage.media_repository_impl")

    async def save(self, media: Media) -> None:
        # Snapshot storage (avoid reference-mutation false positives)
        self._rows[media.id] = {
            "id": media.id,
            "user_id": media.user_id,
            "filename": media.filename,
            "media_type": media.media_type,
            "mime_type": media.mime_type,
            "file_size": media.file_size,
            "storage_key": media.storage_key,
            "width": media.width,
            "height": media.height,
            "duration_ms": media.duration_ms,
            "state": media.state,
            "trash_at": media.trash_at,
            "deleted_at": media.deleted_at,
            "created_at": media.created_at,
            "updated_at": media.updated_at,
        }

    async def get_by_id(self, media_id: UUID, *, ctx: RequestContext | None = None):
        correlation_id = getattr(ctx, "correlation_id", None)
        row = self._rows.get(media_id)

        self._logger.info(
            {
                "event": "media.repo.get_by_id",
                "operation": "media.get",
                "layer": "repo",
                "correlation_id": correlation_id,
                "media_id": str(media_id),
                "row_count": 1 if row else 0,
            }
        )

        if not row:
            return None

        return Media(
            id=row["id"],
            user_id=row["user_id"],
            filename=row["filename"],
            media_type=row["media_type"],
            mime_type=row["mime_type"],
            file_size=row["file_size"],
            storage_key=row["storage_key"],
            width=row["width"],
            height=row["height"],
            duration_ms=row["duration_ms"],
            state=row["state"],
            trash_at=row["trash_at"],
            deleted_at=row["deleted_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@pytest.mark.asyncio
async def test_media_repo_save_get_by_id_contract_fake():
    storage_key = f"contract/media/{uuid4()}.png"
    media = _make_media(storage_key=storage_key)

    repo = FakeMediaRepository()

    await repo.save(media)

    loaded = await repo.get_by_id(media.id)
    assert loaded is not None

    # Contract (business-level fields)
    assert loaded.id == media.id
    assert loaded.storage_key == media.storage_key
    assert loaded.mime_type == media.mime_type
    assert loaded.file_size == media.file_size
    assert loaded.state == media.state


@pytest.mark.asyncio
async def test_media_repo_save_get_by_id_contract_sqlalchemy(db_session):
    storage_key = f"contract/media/{uuid4()}.png"
    media = _make_media(storage_key=storage_key)

    repo = SQLAlchemyMediaRepository(db_session)

    await repo.save(media)

    loaded = await repo.get_by_id(media.id)
    assert loaded is not None

    # Contract (business-level fields)
    assert loaded.id == media.id
    assert loaded.storage_key == media.storage_key
    assert loaded.mime_type == media.mime_type
    assert loaded.file_size == media.file_size
    assert loaded.state == media.state


@pytest.mark.asyncio
async def test_media_repo_mutation_requires_save_contract_fake():
    storage_key = f"contract/media/{uuid4()}.png"
    media = _make_media(storage_key=storage_key)

    repo = FakeMediaRepository()

    await repo.save(media)

    # Mutate in memory without saving
    media.state = MediaState.TRASH
    media.trash_at = datetime.now(timezone.utc)

    loaded_without_save = await repo.get_by_id(media.id)
    assert loaded_without_save is not None
    assert loaded_without_save.state == MediaState.ACTIVE

    # Save and verify
    await repo.save(media)
    loaded_after_save = await repo.get_by_id(media.id)
    assert loaded_after_save is not None
    assert loaded_after_save.state == MediaState.TRASH


@pytest.mark.asyncio
async def test_media_repo_mutation_requires_save_contract_sqlalchemy(db_session):
    storage_key = f"contract/media/{uuid4()}.png"
    media = _make_media(storage_key=storage_key)

    repo = SQLAlchemyMediaRepository(db_session)

    await repo.save(media)

    # Mutate in memory without saving
    media.state = MediaState.TRASH
    media.trash_at = datetime.now(timezone.utc)

    loaded_without_save = await repo.get_by_id(media.id)
    assert loaded_without_save is not None
    assert loaded_without_save.state == MediaState.ACTIVE

    # Save and verify
    await repo.save(media)
    loaded_after_save = await repo.get_by_id(media.id)
    assert loaded_after_save is not None
    assert loaded_after_save.state == MediaState.TRASH


def _extract_structured_payload(record: logging.LogRecord) -> dict | None:
    if isinstance(record.msg, dict):
        return record.msg
    if record.args and len(record.args) == 1 and isinstance(record.args[0], dict):
        return record.args[0]
    if isinstance(record.msg, str):
        s = record.msg.strip()
        if s.startswith("{") and s.endswith("}"):
            try:
                val = json.loads(s)
                if isinstance(val, dict):
                    return val
            except Exception:
                return None
    return None


class _ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@contextmanager
def _capture_logger_records(logger_name: str):
    logger = logging.getLogger(logger_name)
    handler = _ListHandler()

    old_disable = logging.getLogger().manager.disable
    old_level = logger.level
    old_propagate = logger.propagate
    old_disabled = logger.disabled

    logging.disable(logging.NOTSET)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = True
    logger.disabled = False
    try:
        yield handler.records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)
        logger.propagate = old_propagate
        logger.disabled = old_disabled
        logging.disable(old_disable)


@pytest.mark.asyncio
async def test_media_repo_get_by_id_logs_correlation_id_contract_fake():
    storage_key = f"contract/media/{uuid4()}.png"
    media = _make_media(storage_key=storage_key)

    repo = FakeMediaRepository()

    await repo.save(media)

    ctx = RequestContext(correlation_id="cid-media-contract")

    with _capture_logger_records("infra.storage.media_repository_impl") as records:
        loaded = await repo.get_by_id(media.id, ctx=ctx)
        assert loaded is not None

    # Align with repo-labs note: assert only business/observability contract, not db_duration_ms.
    for record in records:
        payload = _extract_structured_payload(record)
        if payload and payload.get("event") == "media.repo.get_by_id" and payload.get("media_id") == str(media.id):
            assert payload.get("correlation_id") == "cid-media-contract"
            return

    raise AssertionError("Expected structured log event 'media.repo.get_by_id' was not emitted")


@pytest.mark.asyncio
async def test_media_repo_get_by_id_logs_correlation_id_contract_sqlalchemy(db_session):
    storage_key = f"contract/media/{uuid4()}.png"
    media = _make_media(storage_key=storage_key)

    repo = SQLAlchemyMediaRepository(db_session)

    await repo.save(media)

    ctx = RequestContext(correlation_id="cid-media-contract")

    with _capture_logger_records("infra.storage.media_repository_impl") as records:
        loaded = await repo.get_by_id(media.id, ctx=ctx)
        assert loaded is not None

    for record in records:
        payload = _extract_structured_payload(record)
        if payload and payload.get("event") == "media.repo.get_by_id" and payload.get("media_id") == str(media.id):
            assert payload.get("correlation_id") == "cid-media-contract"
            return

    raise AssertionError("Expected structured log event 'media.repo.get_by_id' was not emitted")
