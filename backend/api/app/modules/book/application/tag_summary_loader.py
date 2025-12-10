"""Utilities for loading tag summaries for Book aggregates."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from infra.database.models.tag_models import (
    TagAssociationModel,
    TagModel,
    EntityType as TagEntityType,
)


async def load_book_tags_summary(
    session: AsyncSession,
    book_ids: Iterable[UUID],
    *,
    per_book_limit: int = 3,
) -> Dict[UUID, List[str]]:
    """Fetch ordered tag name summaries for the given book IDs.

    Args:
        session: Async SQLAlchemy session (same scope as repositories).
        book_ids: Iterable of book UUIDs to resolve.
        per_book_limit: Maximum number of names to keep per book. Use <=0 to disable.

    Returns:
        Mapping of book_id -> ordered tag name list suitable for badges.
    """
    ids = [book_id for book_id in book_ids if book_id is not None]
    if not ids:
        return {}

    stmt: Select = (
        select(
            TagAssociationModel.entity_id.label("book_id"),
            TagModel.name.label("tag_name"),
            TagAssociationModel.created_at,
        )
        .join(TagModel, TagModel.id == TagAssociationModel.tag_id)
        .where(
            TagAssociationModel.entity_type == TagEntityType.BOOK,
            TagAssociationModel.entity_id.in_(ids),
            TagModel.deleted_at.is_(None),
        )
        .order_by(
            TagAssociationModel.entity_id.asc(),
            TagAssociationModel.created_at.asc(),
        )
    )

    result = await session.execute(stmt)
    summary: Dict[UUID, List[str]] = defaultdict(list)
    for row in result:
        book_id = row.book_id
        tag_name = row.tag_name
        if not tag_name:
            continue
        if per_book_limit > 0 and len(summary[book_id]) >= per_book_limit:
            continue
        summary[book_id].append(tag_name)

    return dict(summary)
