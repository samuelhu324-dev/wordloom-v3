"""Phase 0 Block Router (Minimal)

目标：提供最小 CRUD + 分页 V2 接口，不涉及高级 Paperballs UI 与批量重排。

分页契约：Pagination V2 = { items, total, page, page_size, has_more }
内容规则：
  - > 20000 字节：阻止保存 (错误码 BLOCK_CONTENT_TOO_LARGE)
  - 15000~20000 字节：返回 warning 字段提示接近上限 (CONTENT_NEAR_LIMIT)
排序策略 (Phase0 简化)：
  - 新建时取当前最后一个 order + 1 (不足时 = 1)
  - 不做 Fractional Index 插入中间逻辑
恢复逻辑：
  - restore 仅清除 soft_deleted_at，不执行 3-level 复杂定位（后续 Phase 3 再升级）
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from decimal import Decimal
import logging

from infra.database.session import get_db_session
from infra.storage.block_repository_impl import SQLAlchemyBlockRepository
from infra.database.models.book_models import BookModel
from infra.database.models.block_models import BlockModel
from infra.database.models.library_models import LibraryModel
from api.app.shared.actor import Actor
from api.app.config.security import get_current_actor
from api.app.config.setting import get_settings
from api.app.modules.block.domain.block import Block, BlockType
from api.app.modules.chronicle.application.services import ChronicleRecorderService
from api.app.modules.chronicle.application.todo_facts import diff_todo_list_facts
from infra.storage.chronicle_repository_impl import SQLAlchemyChronicleRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/phase0", tags=["Blocks-Phase0"])

_settings = get_settings()

MAX_BYTES = 20000
WARN_BYTES = 15000


async def _assert_book_owner(
    session: AsyncSession,
    *,
    book_id: UUID,
    actor_user_id: UUID,
    enforce_owner_check: bool,
) -> None:
    if not enforce_owner_check:
        return

    result = await session.execute(
        select(BookModel.library_id).where(BookModel.id == book_id)
    )
    library_id = result.scalar_one_or_none()
    if library_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BOOK_NOT_FOUND", "message": "未找到书籍"},
        )

    result = await session.execute(
        select(LibraryModel.user_id).where(LibraryModel.id == library_id)
    )
    owner_user_id = result.scalar_one_or_none()
    if owner_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "LIBRARY_NOT_FOUND", "message": "未找到书库"},
        )

    if owner_user_id != actor_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "无权限访问该书籍/块",
                "details": {
                    "actor_user_id": str(actor_user_id),
                    "library_id": str(library_id),
                    "book_id": str(book_id),
                },
            },
        )


async def _assert_block_owner(
    session: AsyncSession,
    *,
    block_id: UUID,
    actor_user_id: UUID,
    enforce_owner_check: bool,
) -> UUID:
    result = await session.execute(
        select(BlockModel.book_id).where(BlockModel.id == block_id)
    )
    book_id = result.scalar_one_or_none()
    if book_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BLOCK_NOT_FOUND", "message": "未找到块"},
        )
    await _assert_book_owner(
        session,
        book_id=book_id,
        actor_user_id=actor_user_id,
        enforce_owner_check=enforce_owner_check,
    )
    return book_id


def _serialize(block: Block) -> dict:
    return {
        "id": str(block.id),
        "book_id": str(block.book_id),
        "type": block.type.value,
        "content": block.content.value,
        "order": str(block.order),
        "heading_level": block.heading_level,
        "soft_deleted_at": block.soft_deleted_at.isoformat() if block.soft_deleted_at else None,
        "created_at": block.created_at.isoformat(),
        "updated_at": block.updated_at.isoformat(),
    }

@router.post("/books/{book_id}/blocks", status_code=201)
async def create_block_phase0(
    book_id: UUID,
    payload: dict,
    actor: Actor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_db_session),
):
    """Create block (Phase0 minimal). Robust error surfacing added."""
    try:
        await _assert_book_owner(
            session,
            book_id=book_id,
            actor_user_id=actor.user_id,
            enforce_owner_check=(not _settings.allow_dev_library_owner_override),
        )

        block_type_raw = payload.get("type", "text")
        content_raw = payload.get("content", "")
        heading_level = payload.get("heading_level")

        try:
            block_type = BlockType(block_type_raw)
        except ValueError:
            raise HTTPException(400, detail={"code": "BLOCK_UNSUPPORTED_TYPE", "message": "不支持的块类型"})

        byte_len = len(content_raw.encode("utf-8"))
        if byte_len > MAX_BYTES:
            raise HTTPException(400, detail={"code": "BLOCK_CONTENT_TOO_LARGE", "message": f"内容超过 {MAX_BYTES} 字节上限"})

        repo = SQLAlchemyBlockRepository(session)
        existing = await repo.list_by_book(book_id, limit=5000, offset=0)
        last_order = existing[-1].order if existing else Decimal("0")
        new_order = last_order + Decimal("1")

        if block_type == BlockType.HEADING and heading_level not in (1, 2, 3):
            raise HTTPException(422, detail={"code": "BLOCK_HEADING_LEVEL_INVALID", "message": "heading_level 必须是 1|2|3"})

        block = Block.create(
            book_id=book_id,
            block_type=block_type,
            content=content_raw,
            order=new_order,
            heading_level=heading_level,
        )
        await repo.save(block)

        resp = _serialize(block)
        if byte_len >= WARN_BYTES:
            resp["warning"] = {"code": "CONTENT_NEAR_LIMIT", "message": f"内容已达到 {byte_len} 字节 (> {WARN_BYTES})"}
        return resp
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed creating block (book_id={book_id}): {e}")
        raise HTTPException(500, detail={"code": "BLOCK_CREATE_FAILED", "message": str(e)})

@router.get("/books/{book_id}/blocks")
async def list_blocks_phase0(
    book_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    actor: Actor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_db_session),
):
    await _assert_book_owner(
        session,
        book_id=book_id,
        actor_user_id=actor.user_id,
        enforce_owner_check=(not _settings.allow_dev_library_owner_override),
    )

    # Chronicle: treat first page list as opening the book content.
    if page == 1:
        try:
            chronicle_repo = SQLAlchemyChronicleRepository(session)
            chronicle = ChronicleRecorderService(chronicle_repo)
            await chronicle.record_book_opened(book_id=book_id, actor_id=actor.user_id)
        except Exception:
            pass

    repo = SQLAlchemyBlockRepository(session)
    # 简化分页：取全部后切片（Phase0 数据规模可控）
    all_blocks = await repo.list_by_book(book_id, limit=10000, offset=0)
    active = [b for b in all_blocks if b.soft_deleted_at is None]
    total = len(active)
    start = (page - 1) * page_size
    end = start + page_size
    items = active[start:end]
    has_more = end < total
    return {
        "items": [_serialize(b) for b in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": has_more,
    }

@router.patch("/blocks/{block_id}")
async def update_block_content_phase0(
    block_id: UUID,
    payload: dict,
    actor: Actor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_db_session),
):
    await _assert_block_owner(
        session,
        block_id=block_id,
        actor_user_id=actor.user_id,
        enforce_owner_check=(not _settings.allow_dev_library_owner_override),
    )
    content_raw = payload.get("content")
    type_raw = payload.get("type")
    heading_level = payload.get("heading_level")

    if content_raw is None and type_raw is None:
        raise HTTPException(400, detail={"code": "BLOCK_UPDATE_NO_FIELDS", "message": "content 或 type 至少提供一个"})

    byte_len = len(content_raw.encode("utf-8")) if content_raw is not None else 0
    if content_raw is not None and byte_len > MAX_BYTES:
        raise HTTPException(400, detail={"code": "BLOCK_CONTENT_TOO_LARGE", "message": f"内容超过 {MAX_BYTES} 字节上限"})

    new_type = None
    if type_raw is not None:
        try:
            new_type = BlockType(type_raw)
        except ValueError:
            raise HTTPException(400, detail={"code": "BLOCK_UNSUPPORTED_TYPE", "message": "不支持的块类型"})

    repo = SQLAlchemyBlockRepository(session)
    block = await repo.get_by_id(block_id)
    if not block:
        raise HTTPException(404, detail={"code": "BLOCK_NOT_FOUND", "message": "未找到块"})

    old_content = None
    try:
        old_content = str(getattr(block, "content", ""))
    except Exception:
        old_content = None

    old_type = getattr(getattr(block, "type", None), "value", None) or getattr(block, "type", None)

    if content_raw is not None:
        block.update_content(content_raw)

    if new_type is not None:
        try:
            block.update_type(new_type, heading_level=heading_level)
        except ValueError as exc:
            raise HTTPException(422, detail={"code": "BLOCK_TYPE_INVALID", "message": str(exc)})

    await repo.save(block)

    # Chronicle: record stable facts (non-blocking).
    try:
        chronicle_repo = SQLAlchemyChronicleRepository(session)
        chronicle = ChronicleRecorderService(chronicle_repo)

        changed: list[str] = []
        if content_raw is not None:
            changed.append("content")
        if changed:
            await chronicle.record_block_updated(
                book_id=getattr(block, "book_id", None),
                block_id=block_id,
                fields={"changed": changed},
                actor_id=actor.user_id,
            )

        if new_type is not None:
            new_type_value = getattr(new_type, "value", None) or str(new_type)
            if str(old_type) != str(new_type_value):
                await chronicle.record_block_type_changed(
                    book_id=getattr(block, "book_id", None),
                    block_id=block_id,
                    from_type=str(old_type) if old_type is not None else None,
                    to_type=str(new_type_value),
                    actor_id=actor.user_id,
                )

        # TODO facts: derive promoted/completed from todo_list content changes.
        effective_type = (
            getattr(new_type, "value", None)
            if new_type is not None
            else getattr(getattr(block, "type", None), "value", None)
        )
        if content_raw is not None and str(effective_type) == "todo_list":
            promoted_events, completed_events = diff_todo_list_facts(
                old_content=old_content if str(old_type) == "todo_list" else None,
                new_content=content_raw,
            )
            for item in promoted_events:
                await chronicle.record_todo_promoted_from_block(
                    book_id=getattr(block, "book_id", None),
                    block_id=block_id,
                    todo_id=item.get("todo_id"),
                    text=item.get("text"),
                    is_urgent=item.get("is_urgent"),
                    actor_id=actor.user_id,
                )
            for item in completed_events:
                await chronicle.record_todo_completed(
                    book_id=getattr(block, "book_id", None),
                    block_id=block_id,
                    todo_id=item.get("todo_id"),
                    text=item.get("text"),
                    promoted=item.get("promoted"),
                    actor_id=actor.user_id,
                )
    except Exception:
        pass
    resp = _serialize(block)
    if content_raw is not None and byte_len >= WARN_BYTES:
        resp["warning"] = {"code": "CONTENT_NEAR_LIMIT", "message": f"内容已达到 {byte_len} 字节 (>{WARN_BYTES})"}
    return resp

@router.delete("/blocks/{block_id}", status_code=204)
async def delete_block_phase0(
    block_id: UUID,
    actor: Actor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_db_session),
):
    await _assert_block_owner(
        session,
        block_id=block_id,
        actor_user_id=actor.user_id,
        enforce_owner_check=(not _settings.allow_dev_library_owner_override),
    )
    repo = SQLAlchemyBlockRepository(session)
    block = await repo.get_by_id(block_id)
    if not block:
        raise HTTPException(404, detail={"code": "BLOCK_NOT_FOUND", "message": "未找到块"})
    block.mark_deleted()
    await repo.save(block)

    try:
        chronicle_repo = SQLAlchemyChronicleRepository(session)
        chronicle = ChronicleRecorderService(chronicle_repo)
        await chronicle.record_block_soft_deleted(
            book_id=getattr(block, "book_id", None),
            block_id=block_id,
            actor_id=actor.user_id,
        )
    except Exception:
        pass
    return None

@router.post("/blocks/{block_id}/restore")
async def restore_block_phase0(
    block_id: UUID,
    actor: Actor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_db_session),
):
    book_id = await _assert_block_owner(
        session,
        block_id=block_id,
        actor_user_id=actor.user_id,
        enforce_owner_check=(not _settings.allow_dev_library_owner_override),
    )
    repo = SQLAlchemyBlockRepository(session)
    block = await repo.get_any_by_id(block_id)
    if not block:
        raise HTTPException(404, detail={"code": "BLOCK_NOT_FOUND", "message": "未找到块"})
    if block.soft_deleted_at is None:
        raise HTTPException(409, detail={"code": "BLOCK_NOT_DELETED", "message": "块未处于删除状态"})

    # 简化恢复：放到末尾（last order + 1）
    existing = await repo.list_by_book(book_id, limit=10000, offset=0)
    active = [b for b in existing if b.soft_deleted_at is None and b.id != block.id]
    last_order = active[-1].order if active else Decimal("0")
    block.restore_from_basement(last_order + Decimal("1"), recovery_level=4)
    await repo.save(block)

    try:
        chronicle_repo = SQLAlchemyChronicleRepository(session)
        chronicle = ChronicleRecorderService(chronicle_repo)
        await chronicle.record_block_restored(
            book_id=getattr(block, "book_id", None),
            block_id=block_id,
            actor_id=actor.user_id,
        )
    except Exception:
        pass
    return _serialize(block)

__all__ = ["router"]
