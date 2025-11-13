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

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from api.app.modules.tag.domain import Tag, TagAssociation, EntityType
from api.app.modules.tag.exceptions import (
    TagNotFoundError,
    TagAlreadyExistsError,
    TagRepositorySaveError,
    TagRepositoryQueryError,
)
from api.app.modules.tag.application.ports.output import TagRepository
from infra.database.models import TagModel, TagAssociationModel


class SQLAlchemyTagRepository(TagRepository):
    """SQLAlchemy implementation of TagRepository (Infrastructure Adapter)

    This is an ADAPTER in Hexagonal architecture - it implements the
    output port interface defined in application/ports/output.py.

    Responsibilities:
    - Persist Tag domain objects to database
    - Fetch Tags from database and convert to domain objects
    - Enforce database constraints (unique names, soft delete)
    - Manage Tag-Entity associations through TagAssociationModel
    - Handle transaction rollback on errors
    """

    def __init__(self, db_session: Session):
        """Initialize repository with database session

        Args:
            db_session: SQLAlchemy session for database access
        """
        self.session = db_session

    async def save(self, tag: Tag) -> Tag:
        """Persist a tag (create or update)"""
        try:
            # Check name uniqueness (for active tags)
            if await self.check_name_exists(tag.name, exclude_id=tag.id):
                raise TagAlreadyExistsError(tag.name)

            # Determine if insert or update
            existing = self.session.query(TagModel).filter(TagModel.id == tag.id).first()

            if existing:
                # Update
                existing.name = tag.name
                existing.color = tag.color
                existing.icon = tag.icon
                existing.description = tag.description
                existing.parent_tag_id = tag.parent_tag_id
                existing.level = tag.level
                existing.usage_count = tag.usage_count
                existing.updated_at = tag.updated_at
                existing.deleted_at = tag.deleted_at
            else:
                # Insert
                model = TagModel(
                    id=tag.id,
                    name=tag.name,
                    color=tag.color,
                    icon=tag.icon,
                    description=tag.description,
                    parent_tag_id=tag.parent_tag_id,
                    level=tag.level,
                    usage_count=tag.usage_count,
                    created_at=tag.created_at,
                    updated_at=tag.updated_at,
                    deleted_at=tag.deleted_at,
                )
                self.session.add(model)

            self.session.commit()
            return tag

        except TagAlreadyExistsError:
            raise
        except Exception as e:
            self.session.rollback()
            raise TagRepositorySaveError(str(e))

    async def get_by_id(self, tag_id: UUID) -> Optional[Tag]:
        """Fetch a tag by ID (including soft-deleted)"""
        try:
            model = self.session.query(TagModel).filter(TagModel.id == tag_id).first()
            if not model:
                return None
            return self._model_to_domain(model)
        except Exception as e:
            raise TagRepositoryQueryError(str(e))

    async def delete(self, tag_id: UUID) -> None:
        """Soft delete a tag"""
        try:
            model = self.session.query(TagModel).filter(TagModel.id == tag_id).first()
            if not model:
                raise TagNotFoundError(tag_id)

            model.deleted_at = datetime.now(timezone.utc)
            self.session.commit()

        except TagNotFoundError:
            raise
        except Exception as e:
            self.session.rollback()
            raise TagRepositorySaveError(str(e))

    async def restore(self, tag_id: UUID) -> None:
        """Restore a soft-deleted tag"""
        try:
            model = self.session.query(TagModel).filter(TagModel.id == tag_id).first()
            if not model:
                raise TagNotFoundError(tag_id)

            model.deleted_at = None
            self.session.commit()

        except TagNotFoundError:
            raise
        except Exception as e:
            self.session.rollback()
            raise TagRepositorySaveError(str(e))

    async def get_all_toplevel(self, limit: int = 100) -> List[Tag]:
        """Get all top-level tags (parent_tag_id IS NULL, deleted_at IS NULL)"""
        try:
            models = self.session.query(TagModel).filter(
                and_(
                    TagModel.parent_tag_id.is_(None),
                    TagModel.deleted_at.is_(None),
                    TagModel.level == 0
                )
            ).order_by(TagModel.usage_count.desc()).limit(limit).all()
            return [self._model_to_domain(m) for m in models]
        except Exception as e:
            raise TagRepositoryQueryError(str(e))

    async def get_by_parent(self, parent_tag_id: UUID) -> List[Tag]:
        """Get all sub-tags of a parent tag"""
        try:
            models = self.session.query(TagModel).filter(
                and_(
                    TagModel.parent_tag_id == parent_tag_id,
                    TagModel.deleted_at.is_(None)
                )
            ).order_by(TagModel.usage_count.desc()).all()
            return [self._model_to_domain(m) for m in models]
        except Exception as e:
            raise TagRepositoryQueryError(str(e))

    async def find_by_name(self, keyword: str, limit: int = 20) -> List[Tag]:
        """Search tags by partial name match (case-insensitive)"""
        try:
            search_pattern = f"%{keyword.lower()}%"
            models = self.session.query(TagModel).filter(
                and_(
                    func.lower(TagModel.name).like(search_pattern),
                    TagModel.deleted_at.is_(None)
                )
            ).order_by(TagModel.usage_count.desc()).limit(limit).all()
            return [self._model_to_domain(m) for m in models]
        except Exception as e:
            raise TagRepositoryQueryError(str(e))

    async def find_most_used(self, limit: int = 30) -> List[Tag]:
        """Get most frequently used tags (for menu bar)"""
        try:
            models = self.session.query(TagModel).filter(
                and_(
                    TagModel.deleted_at.is_(None),
                    TagModel.level == 0  # Only top-level for menu
                )
            ).order_by(TagModel.usage_count.desc()).limit(limit).all()
            return [self._model_to_domain(m) for m in models]
        except Exception as e:
            raise TagRepositoryQueryError(str(e))

    async def find_by_entity(self, entity_type: EntityType, entity_id: UUID) -> List[Tag]:
        """Get all tags associated with a specific entity"""
        try:
            associations = self.session.query(TagAssociationModel).filter(
                and_(
                    TagAssociationModel.entity_type == entity_type,
                    TagAssociationModel.entity_id == entity_id
                )
            ).all()

            tag_ids = [assoc.tag_id for assoc in associations]
            if not tag_ids:
                return []

            models = self.session.query(TagModel).filter(
                and_(
                    TagModel.id.in_(tag_ids),
                    TagModel.deleted_at.is_(None)
                )
            ).all()
            return [self._model_to_domain(m) for m in models]
        except Exception as e:
            raise TagRepositoryQueryError(str(e))

    async def find_entities_with_tag(self, tag_id: UUID, entity_type: EntityType) -> List[UUID]:
        """Reverse lookup: get all entity IDs with a specific tag"""
        try:
            associations = self.session.query(TagAssociationModel).filter(
                and_(
                    TagAssociationModel.tag_id == tag_id,
                    TagAssociationModel.entity_type == entity_type
                )
            ).all()
            return [assoc.entity_id for assoc in associations]
        except Exception as e:
            raise TagRepositoryQueryError(str(e))

    async def associate_tag_with_entity(
        self,
        tag_id: UUID,
        entity_type: EntityType,
        entity_id: UUID
    ) -> TagAssociation:
        """Create a tag-entity association"""
        try:
            # Check if association already exists
            existing = self.session.query(TagAssociationModel).filter(
                and_(
                    TagAssociationModel.tag_id == tag_id,
                    TagAssociationModel.entity_type == entity_type,
                    TagAssociationModel.entity_id == entity_id
                )
            ).first()

            if existing:
                return self._assoc_model_to_domain(existing)

            # Create new association
            model = TagAssociationModel(
                tag_id=tag_id,
                entity_type=entity_type,
                entity_id=entity_id,
                created_at=datetime.now(timezone.utc)
            )
            self.session.add(model)

            # Update tag usage count
            tag_model = self.session.query(TagModel).filter(TagModel.id == tag_id).first()
            if tag_model:
                tag_model.usage_count += 1

            self.session.commit()
            return self._assoc_model_to_domain(model)

        except Exception as e:
            self.session.rollback()
            raise TagRepositorySaveError(str(e))

    async def disassociate_tag_from_entity(
        self,
        tag_id: UUID,
        entity_type: EntityType,
        entity_id: UUID
    ) -> None:
        """Remove a tag-entity association"""
        try:
            assoc = self.session.query(TagAssociationModel).filter(
                and_(
                    TagAssociationModel.tag_id == tag_id,
                    TagAssociationModel.entity_type == entity_type,
                    TagAssociationModel.entity_id == entity_id
                )
            ).first()

            if not assoc:
                return  # Idempotent

            self.session.delete(assoc)

            # Update tag usage count
            tag_model = self.session.query(TagModel).filter(TagModel.id == tag_id).first()
            if tag_model:
                tag_model.usage_count = max(0, tag_model.usage_count - 1)

            self.session.commit()

        except Exception as e:
            self.session.rollback()
            raise TagRepositorySaveError(str(e))

    async def count_associations(self, tag_id: UUID) -> int:
        """Count total associations for a tag"""
        try:
            return self.session.query(TagAssociationModel).filter(
                TagAssociationModel.tag_id == tag_id
            ).count()
        except Exception as e:
            raise TagRepositoryQueryError(str(e))

    async def check_name_exists(self, name: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a tag name already exists (active tags only)"""
        try:
            query = self.session.query(TagModel).filter(
                and_(
                    func.lower(TagModel.name) == name.lower(),
                    TagModel.deleted_at.is_(None)
                )
            )
            if exclude_id:
                query = query.filter(TagModel.id != exclude_id)
            return query.first() is not None
        except Exception as e:
            raise TagRepositoryQueryError(str(e))

    # ========================================================================
    # Private Helpers
    # ========================================================================

    def _model_to_domain(self, model: TagModel) -> Tag:
        """Convert ORM model to domain object"""
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
        """Convert association ORM model to domain object"""
        return TagAssociation(
            tag_id=model.tag_id,
            entity_type=EntityType(model.entity_type.value),
            entity_id=model.entity_id,
            created_at=model.created_at,
        )
