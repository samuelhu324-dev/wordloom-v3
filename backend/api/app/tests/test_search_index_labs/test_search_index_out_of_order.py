import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infra.database.models.search_index_models import SearchIndexModel
from infra.event_bus.handlers.search_index_handlers import (
    on_block_created,
    on_block_updated,
    on_tag_created,
    on_tag_renamed,
)

from api.app.modules.block.domain.events import BlockCreated, BlockUpdated
from api.app.modules.tag.domain.events import TagCreated, TagRenamed


pytestmark = pytest.mark.anyio


async def _get_search_index_text(session: AsyncSession, *, entity_type: str, entity_id) -> str | None:
    row = (
        await session.execute(
            select(SearchIndexModel)
            .where(SearchIndexModel.entity_type == entity_type)
            .where(SearchIndexModel.entity_id == entity_id)
        )
    ).scalar_one_or_none()
    return None if row is None else row.text


async def test_search_index_block_update_is_out_of_order_safe(db_session: AsyncSession):
    block_id = uuid4()
    book_id = uuid4()

    t0 = datetime.now(timezone.utc)
    t1 = t0 + timedelta(seconds=1)
    t2 = t0 + timedelta(seconds=2)

    await on_block_created(
        BlockCreated(
            block_id=block_id,
            book_id=book_id,
            block_type="text",
            content="v0",
            order=1.0,
            occurred_at=t0,
        ),
        db_session,
    )

    # Apply v2 first, then v1 (out-of-order)
    await on_block_updated(
        BlockUpdated(block_id=block_id, book_id=book_id, content="v2", occurred_at=t2),
        db_session,
    )
    await on_block_updated(
        BlockUpdated(block_id=block_id, book_id=book_id, content="v1", occurred_at=t1),
        db_session,
    )

    assert await _get_search_index_text(db_session, entity_type="block", entity_id=block_id) == "v2"


async def test_search_index_tag_rename_is_out_of_order_safe(db_session: AsyncSession):
    tag_id = uuid4()

    t0 = datetime.now(timezone.utc)
    t1 = t0 + timedelta(seconds=1)
    t2 = t0 + timedelta(seconds=2)

    await on_tag_created(
        TagCreated(
            tag_id=tag_id,
            name="v0",
            color="#000000",
            is_toplevel=True,
            occurred_at=t0,
        ),
        db_session,
    )

    # Apply v2 first, then v1 (out-of-order)
    await on_tag_renamed(
        TagRenamed(tag_id=tag_id, old_name="v0", new_name="v2", occurred_at=t2),
        db_session,
    )
    await on_tag_renamed(
        TagRenamed(tag_id=tag_id, old_name="v2", new_name="v1", occurred_at=t1),
        db_session,
    )

    assert await _get_search_index_text(db_session, entity_type="tag", entity_id=tag_id) == "v2"
