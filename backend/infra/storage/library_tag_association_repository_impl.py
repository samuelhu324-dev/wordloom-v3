"""Library ↔ Tag Association Repository Implementation.

Implements ILibraryTagAssociationRepository using SQLAlchemy ORM models.
"""

from __future__ import annotations

import logging
from typing import List, Dict
from uuid import UUID

from sqlalchemy import select, func, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.modules.library.application.ports.output import (
    ILibraryTagAssociationRepository,
    LibraryTagAssociationDTO,
)
from infra.database.models.tag_models import (
    TagAssociationModel,
    TagModel,
    EntityType as TagEntityType,
)

logger = logging.getLogger(__name__)


class SQLAlchemyLibraryTagAssociationRepository(ILibraryTagAssociationRepository):
    """SQLAlchemy adapter for Library tag associations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def fetch_option_a_tags(
        self,
        library_ids: List[UUID],
        *,
        limit_per_library: int = 3,
    ) -> List[LibraryTagAssociationDTO]:
        if not library_ids:
            return []

        stmt = (
            select(
                TagAssociationModel.entity_id,
                TagAssociationModel.tag_id,
                TagModel.name,
                TagModel.color,
                TagModel.description,
                TagAssociationModel.created_at,
            )
            .join(TagModel, TagAssociationModel.tag_id == TagModel.id)
            .where(
                TagAssociationModel.entity_type == TagEntityType.LIBRARY,
                TagAssociationModel.entity_id.in_(library_ids),
                TagModel.deleted_at.is_(None),
            )
            .order_by(TagAssociationModel.entity_id, TagAssociationModel.created_at.asc())
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        chips_per_library: Dict[UUID, int] = {lib_id: 0 for lib_id in library_ids}
        dtos: List[LibraryTagAssociationDTO] = []

        for entity_id, tag_id, tag_name, tag_color, tag_description, created_at in rows:
            if chips_per_library.get(entity_id, 0) >= limit_per_library:
                continue
            chips_per_library[entity_id] = chips_per_library.get(entity_id, 0) + 1
            dtos.append(
                LibraryTagAssociationDTO(
                    library_id=entity_id,
                    tag_id=tag_id,
                    tag_name=tag_name,
                    tag_color=tag_color or "#F3F4F6",
                    tag_description=tag_description,
                    created_at=created_at,
                )
            )

        return dtos

    async def count_tags_by_library(self, library_ids: List[UUID]) -> Dict[UUID, int]:
        if not library_ids:
            return {}

        stmt = (
            select(
                TagAssociationModel.entity_id,
                func.count(TagAssociationModel.tag_id),
            )
            .where(
                TagAssociationModel.entity_type == TagEntityType.LIBRARY,
                TagAssociationModel.entity_id.in_(library_ids),
            )
            .group_by(TagAssociationModel.entity_id)
        )

        result = await self.session.execute(stmt)
        return {entity_id: count for entity_id, count in result.all()}

    async def replace_library_tags(
        self,
        library_id: UUID,
        tag_ids: List[UUID],
        *,
        actor_id: UUID | None = None,
    ) -> None:
        del actor_id  # Reserved for future auditing
        try:
            await self.session.execute(
                delete(TagAssociationModel).where(
                    TagAssociationModel.entity_type == TagEntityType.LIBRARY,
                    TagAssociationModel.entity_id == library_id,
                )
            )

            unique_ids = []
            seen = set()
            for tag_id in tag_ids:
                if tag_id in seen:
                    continue
                seen.add(tag_id)
                unique_ids.append(tag_id)

            if unique_ids:
                values = [
                    {
                        "tag_id": tag_id,
                        "entity_type": TagEntityType.LIBRARY,
                        "entity_id": library_id,
                    }
                    for tag_id in unique_ids
                ]

                insert_stmt = pg_insert(TagAssociationModel).values(values)
                insert_stmt = insert_stmt.on_conflict_do_nothing(
                    index_elements=[
                        TagAssociationModel.tag_id,
                        TagAssociationModel.entity_type,
                        TagAssociationModel.entity_id,
                    ]
                )
                await self.session.execute(insert_stmt)

            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def list_tag_ids(self, library_id: UUID) -> List[UUID]:
        stmt = (
            select(TagAssociationModel.tag_id)
            .where(
                TagAssociationModel.entity_type == TagEntityType.LIBRARY,
                TagAssociationModel.entity_id == library_id,
            )
            .order_by(TagAssociationModel.created_at.asc())
        )

        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]
