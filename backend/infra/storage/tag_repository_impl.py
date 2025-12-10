"""
Tag Repository Implementation Adapter

Concrete SQLAlchemy implementation of TagRepository output port.

Location: infra/storage/tag_repository_impl.py
Port Interface: api/app/modules/tag/application/ports/output.py

Architecture:
  - Implements abstract TagRepository interface (output port)
  - Uses SQLAlchemy ORM models from infra/database/models
  - Converts ORM models ↔ Domain objects
  - Manages database transactions and error handling
  - Enforces business logic: soft delete, uniqueness, hierarchies
"""

import os
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.modules.tag.domain import Tag, TagAssociation, EntityType
from api.app.modules.tag.exceptions import (
    TagNotFoundError,
    TagAlreadyExistsError,
    TagRepositorySaveError,
    TagRepositoryQueryError,
)
from api.app.modules.tag.application.ports.output import TagRepository
from infra.database.models.tag_models import (
    TagModel,
    TagAssociationModel,
    EntityType as ORMEntityType,
)


def _resolve_default_user_id() -> UUID:
    """Resolve the development user id from environment or fallback."""
    override = os.getenv("DEV_USER_ID")
    if override:
        try:
            return UUID(override)
        except Exception:
            pass
    # 使用固定的系统用户 UUID（对应 Migration 003 中 UUID 类型）
    return UUID("550e8400-e29b-41d4-a716-446655440000")


DEFAULT_TAG_USER_ID = _resolve_default_user_id()


class SQLAlchemyTagRepository(TagRepository):
    """SQLAlchemy implementation of TagRepository using AsyncSession."""

    def __init__(self, db_session: AsyncSession):
        self.session = db_session

    async def save(self, tag: Tag) -> Tag:
        try:
            if await self.check_name_exists(tag.name, exclude_id=tag.id):
                raise TagAlreadyExistsError(tag.name)

            existing = await self.session.get(TagModel, tag.id)

            persisted_color = tag.color[:7]

            if existing:
                if existing.user_id != DEFAULT_TAG_USER_ID:
                    raise TagRepositorySaveError("Tag belongs to a different user context")
                existing.name = tag.name
                existing.color = persisted_color
                existing.icon = tag.icon
                existing.description = tag.description
                existing.parent_tag_id = tag.parent_tag_id
                existing.level = tag.level
                existing.usage_count = tag.usage_count
                existing.updated_at = tag.updated_at
                existing.deleted_at = tag.deleted_at
            else:
                model = TagModel(
                    id=tag.id,
                    user_id=DEFAULT_TAG_USER_ID,
                    name=tag.name,
                    color=persisted_color,
                    icon=tag.icon,
                    description=tag.description,
                    parent_tag_id=tag.parent_tag_id,
                    level=tag.level,
                    usage_count=tag.usage_count,
                    created_at=tag.created_at or datetime.now(timezone.utc),
                    updated_at=tag.updated_at or datetime.now(timezone.utc),
                    deleted_at=tag.deleted_at,
                )
                self.session.add(model)

            await self.session.commit()
            return tag

        except TagAlreadyExistsError:
            raise
        except Exception as exc:
            await self.session.rollback()
            raise TagRepositorySaveError(str(exc))

    async def get_by_id(self, tag_id: UUID) -> Optional[Tag]:
        try:
            model = await self.session.get(TagModel, tag_id)
            if model and model.user_id != DEFAULT_TAG_USER_ID:
                model = None
            if not model:
                return None
            return self._model_to_domain(model)
        except Exception as exc:
            raise TagRepositoryQueryError(str(exc))

    async def delete(self, tag_id: UUID) -> None:
        try:
            model = await self.session.get(TagModel, tag_id)
            if model and model.user_id != DEFAULT_TAG_USER_ID:
                model = None
            if not model:
                raise TagNotFoundError(tag_id)

            model.deleted_at = datetime.now(timezone.utc)
            await self.session.commit()

        except TagNotFoundError:
            raise
        except Exception as exc:
            await self.session.rollback()
            raise TagRepositorySaveError(str(exc))

    async def restore(self, tag_id: UUID) -> None:
        try:
            model = await self.session.get(TagModel, tag_id)
            if model and model.user_id != DEFAULT_TAG_USER_ID:
                model = None
            if not model:
                raise TagNotFoundError(tag_id)

            model.deleted_at = None
            await self.session.commit()

        except TagNotFoundError:
            raise
        except Exception as exc:
            await self.session.rollback()
            raise TagRepositorySaveError(str(exc))

    async def get_all_toplevel(self, limit: int = 100) -> List[Tag]:
        try:
            query = (
                select(TagModel)
                .where(
                    TagModel.user_id == DEFAULT_TAG_USER_ID,
                    TagModel.parent_tag_id.is_(None),
                    TagModel.deleted_at.is_(None),
                    TagModel.level == 0,
                )
                .order_by(TagModel.usage_count.desc())
                .limit(limit)
            )
            result = await self.session.execute(query)
            return [self._model_to_domain(model) for model in result.scalars().all()]
        except Exception as exc:
            raise TagRepositoryQueryError(str(exc))

    async def list_all(
        self,
        *,
        include_deleted: bool = False,
        only_top_level: bool = False,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "name_asc",
    ) -> Tuple[List[Tag], int]:
        try:
            filters = [
                TagModel.user_id == DEFAULT_TAG_USER_ID,
            ]
            if not include_deleted:
                filters.append(TagModel.deleted_at.is_(None))
            if only_top_level:
                filters.extend([
                    TagModel.parent_tag_id.is_(None),
                    TagModel.level == 0,
                ])

            order_map = {
                "name_asc": (
                    func.lower(TagModel.name).asc(),
                    TagModel.created_at.asc(),
                ),
                "name_desc": (
                    func.lower(TagModel.name).desc(),
                    TagModel.created_at.desc(),
                ),
                "usage_desc": (
                    TagModel.usage_count.desc(),
                    func.lower(TagModel.name).asc(),
                ),
                "created_desc": (
                    TagModel.created_at.desc(),
                ),
            }
            order_clauses = order_map.get(order_by, order_map["name_asc"])

            base_query = select(TagModel).where(*filters).order_by(*order_clauses)
            if offset:
                base_query = base_query.offset(offset)
            if limit:
                base_query = base_query.limit(limit)

            result = await self.session.execute(base_query)
            items = [self._model_to_domain(model) for model in result.scalars().all()]

            count_query = select(func.count()).select_from(TagModel).where(*filters)
            total_result = await self.session.execute(count_query)
            total = int(total_result.scalar_one())

            return items, total
        except Exception as exc:
            raise TagRepositoryQueryError(str(exc))

    async def get_by_parent(self, parent_tag_id: UUID) -> List[Tag]:
        try:
            query = (
                select(TagModel)
                .where(
                    TagModel.user_id == DEFAULT_TAG_USER_ID,
                    TagModel.parent_tag_id == parent_tag_id,
                    TagModel.deleted_at.is_(None),
                )
                .order_by(TagModel.usage_count.desc())
            )
            result = await self.session.execute(query)
            return [self._model_to_domain(model) for model in result.scalars().all()]
        except Exception as exc:
            raise TagRepositoryQueryError(str(exc))

    async def find_by_name(self, keyword: str, limit: int = 20, order_by: str = "name_asc") -> List[Tag]:
        try:
            search_pattern = f"%{keyword.lower()}%"
            query = (
                select(TagModel)
                .where(
                    TagModel.user_id == DEFAULT_TAG_USER_ID,
                    func.lower(TagModel.name).like(search_pattern),
                    TagModel.deleted_at.is_(None),
                )
            )

            order_map = {
                "name_asc": (
                    func.lower(TagModel.name).asc(),
                    TagModel.created_at.asc(),
                ),
                "name_desc": (
                    func.lower(TagModel.name).desc(),
                    TagModel.created_at.desc(),
                ),
                "usage_desc": (
                    TagModel.usage_count.desc(),
                    func.lower(TagModel.name).asc(),
                ),
                "created_desc": (
                    TagModel.created_at.desc(),
                ),
            }
            order_clauses = order_map.get(order_by, order_map["name_asc"])

            query = query.order_by(*order_clauses).limit(limit)
            result = await self.session.execute(query)
            return [self._model_to_domain(model) for model in result.scalars().all()]
        except Exception as exc:
            raise TagRepositoryQueryError(str(exc))

    async def find_most_used(self, limit: int = 30) -> List[Tag]:
        try:
            query = (
                select(TagModel)
                .where(
                    TagModel.user_id == DEFAULT_TAG_USER_ID,
                    TagModel.deleted_at.is_(None),
                    TagModel.level == 0,
                )
                .order_by(TagModel.usage_count.desc())
                .limit(limit)
            )
            result = await self.session.execute(query)
            return [self._model_to_domain(model) for model in result.scalars().all()]
        except Exception as exc:
            raise TagRepositoryQueryError(str(exc))

    async def find_by_entity(self, entity_type: EntityType, entity_id: UUID) -> List[Tag]:
        try:
            orm_entity_type = self._to_orm_entity_type(entity_type)
            stmt = (
                select(TagModel)
                .join(TagAssociationModel, TagAssociationModel.tag_id == TagModel.id)
                .where(
                    TagAssociationModel.entity_type == orm_entity_type,
                    TagAssociationModel.entity_id == entity_id,
                    TagModel.user_id == DEFAULT_TAG_USER_ID,
                    TagModel.deleted_at.is_(None),
                )
                .order_by(TagAssociationModel.created_at.asc())
            )
            result = await self.session.execute(stmt)
            return [self._model_to_domain(model) for model in result.scalars().all()]
        except Exception as exc:
            raise TagRepositoryQueryError(str(exc))

    async def find_entities_with_tag(self, tag_id: UUID, entity_type: EntityType) -> List[UUID]:
        try:
            tag_model = await self.session.get(TagModel, tag_id)
            if not tag_model or tag_model.user_id != DEFAULT_TAG_USER_ID:
                return []

            orm_entity_type = self._to_orm_entity_type(entity_type)
            query = select(TagAssociationModel.entity_id).where(
                TagAssociationModel.tag_id == tag_id,
                TagAssociationModel.entity_type == orm_entity_type,
            )
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as exc:
            raise TagRepositoryQueryError(str(exc))

    async def associate_tag_with_entity(
        self,
        tag_id: UUID,
        entity_type: EntityType,
        entity_id: UUID,
    ) -> TagAssociation:
        try:
            orm_entity_type = self._to_orm_entity_type(entity_type)
            existing_query = select(TagAssociationModel).where(
                TagAssociationModel.tag_id == tag_id,
                TagAssociationModel.entity_type == orm_entity_type,
                TagAssociationModel.entity_id == entity_id,
            )
            existing_result = await self.session.execute(existing_query)
            existing = existing_result.scalars().first()

            if existing:
                return self._assoc_model_to_domain(existing)

            tag_model = await self.session.get(TagModel, tag_id)
            if not tag_model or tag_model.user_id != DEFAULT_TAG_USER_ID:
                raise TagNotFoundError(tag_id)

            model = TagAssociationModel(
                tag_id=tag_id,
                entity_type=orm_entity_type,
                entity_id=entity_id,
                created_at=datetime.now(timezone.utc),
            )
            self.session.add(model)

            tag_model.usage_count += 1

            await self.session.commit()
            await self.session.refresh(model)
            return self._assoc_model_to_domain(model)

        except TagNotFoundError:
            await self.session.rollback()
            raise
        except Exception as exc:
            await self.session.rollback()
            raise TagRepositorySaveError(str(exc))

    async def disassociate_tag_from_entity(
        self,
        tag_id: UUID,
        entity_type: EntityType,
        entity_id: UUID,
    ) -> None:
        try:
            orm_entity_type = self._to_orm_entity_type(entity_type)
            query = select(TagAssociationModel).where(
                TagAssociationModel.tag_id == tag_id,
                TagAssociationModel.entity_type == orm_entity_type,
                TagAssociationModel.entity_id == entity_id,
            )
            result = await self.session.execute(query)
            assoc = result.scalars().first()

            if not assoc:
                return

            await self.session.delete(assoc)

            tag_model = await self.session.get(TagModel, tag_id)
            if tag_model and tag_model.user_id != DEFAULT_TAG_USER_ID:
                tag_model = None
            if tag_model:
                tag_model.usage_count = max(0, tag_model.usage_count - 1)

            await self.session.commit()

        except Exception as exc:
            await self.session.rollback()
            raise TagRepositorySaveError(str(exc))

    async def count_associations(self, tag_id: UUID) -> int:
        try:
            tag_model = await self.session.get(TagModel, tag_id)
            if not tag_model or tag_model.user_id != DEFAULT_TAG_USER_ID:
                return 0

            query = select(func.count()).select_from(TagAssociationModel).where(
                TagAssociationModel.tag_id == tag_id
            )
            result = await self.session.execute(query)
            return int(result.scalar_one())
        except Exception as exc:
            raise TagRepositoryQueryError(str(exc))

    async def check_name_exists(
        self,
        name: str,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        try:
            query = select(func.count()).select_from(TagModel).where(
                TagModel.user_id == DEFAULT_TAG_USER_ID,
                func.lower(TagModel.name) == name.lower(),
                TagModel.deleted_at.is_(None),
            )
            if exclude_id:
                query = query.where(TagModel.id != exclude_id)

            result = await self.session.execute(query)
            return int(result.scalar_one()) > 0
        except Exception as exc:
            raise TagRepositoryQueryError(str(exc))

    def _model_to_domain(self, model: TagModel) -> Tag:
        return Tag(
            id=model.id,
            name=model.name,
            color=model.color,
            icon=model.icon,
            description=model.description,
            parent_tag_id=model.parent_tag_id,
            level=model.level,
            usage_count=model.usage_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    def _assoc_model_to_domain(self, model: TagAssociationModel) -> TagAssociation:
        entity_type_value = getattr(model.entity_type, "value", model.entity_type)
        return TagAssociation(
            tag_id=model.tag_id,
            entity_type=EntityType(entity_type_value),
            entity_id=model.entity_id,
            created_at=model.created_at,
        )

    def _to_orm_entity_type(self, entity_type: EntityType) -> ORMEntityType:
        return ORMEntityType[entity_type.name]
