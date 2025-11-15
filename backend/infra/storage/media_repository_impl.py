"""
Media Repository Implementation Adapter

Concrete SQLAlchemy implementation of MediaRepository output port.

Location: infra/storage/media_repository_impl.py
Port Interface: api/app/modules/media/application/ports/output.py

Architecture:
  - Implements abstract MediaRepository interface (output port)
  - Uses SQLAlchemy ORM models from infra/database/models
  - Converts ORM models ↔ Domain objects
  - Manages database transactions and error handling
  - Enforces business logic: trash lifecycle, 30-day retention (POLICY-010)
"""

from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.app.modules.media.domain import Media, MediaState, EntityTypeForMedia
from app.app.modules.media.domain import (
    MediaNotFoundError,
    MediaInTrashError,
    CannotPurgeError,
    CannotRestoreError,
    MediaRepositorySaveError,
    MediaRepositoryQueryError,
    MediaRepositoryDeleteError,
)
from app.app.modules.media.repository import MediaRepository
from app.infra.database.models.media_models import MediaModel, MediaAssociationModel, MediaState as ModelMediaState


class SQLAlchemyMediaRepository(MediaRepository):
    """SQLAlchemy implementation of MediaRepository (Infrastructure Adapter)

    This is an ADAPTER in Hexagonal architecture - it implements the
    output port interface defined in application/ports/output.py.

    Responsibilities:
    - Persist Media domain objects to database
    - Fetch Media from database and convert to domain objects
    - Enforce state machine: ACTIVE → TRASH → PURGED
    - Enforce 30-day trash retention (POLICY-010)
    - Manage Media-Entity associations through MediaAssociationModel
    - Handle transaction rollback on errors
    """

    def __init__(self, db_session: Session):
        """Initialize repository with database session

        Args:
            db_session: SQLAlchemy session for database access
        """
        self.session = db_session

    async def save(self, media: Media) -> Media:
        """Persist media (create or update)"""
        try:
            existing = self.session.query(MediaModel).filter(
                MediaModel.id == media.id
            ).first()

            if existing:
                # Update
                existing.filename = media.filename
                existing.mime_type = media.mime_type.value
                existing.file_size = media.file_size
                existing.width = media.width
                existing.height = media.height
                existing.duration_ms = media.duration_ms
                existing.state = media.state.value
                existing.trash_at = media.trash_at
                existing.deleted_at = media.deleted_at
                existing.updated_at = media.updated_at
            else:
                # Insert
                model = MediaModel(
                    id=media.id,
                    filename=media.filename,
                    storage_key=media.storage_key,
                    media_type=media.media_type.value,
                    mime_type=media.mime_type.value,
                    file_size=media.file_size,
                    width=media.width,
                    height=media.height,
                    duration_ms=media.duration_ms,
                    state=media.state.value,
                    trash_at=media.trash_at,
                    deleted_at=media.deleted_at,
                    created_at=media.created_at,
                    updated_at=media.updated_at,
                )
                self.session.add(model)

            self.session.commit()
            return media

        except Exception as e:
            self.session.rollback()
            raise MediaRepositorySaveError(str(e))

    async def get_by_id(self, media_id: UUID) -> Optional[Media]:
        """Fetch media by ID"""
        try:
            model = self.session.query(MediaModel).filter(
                MediaModel.id == media_id
            ).first()
            if not model:
                return None
            return self._model_to_domain(model)
        except Exception as e:
            raise MediaRepositoryQueryError(str(e))

    async def delete(self, media_id: UUID) -> None:
        """Soft delete media (move to trash)"""
        try:
            model = self.session.query(MediaModel).filter(
                MediaModel.id == media_id
            ).first()
            if not model:
                raise MediaNotFoundError(media_id)

            if model.state == ModelMediaState.TRASH.value:
                raise MediaInTrashError(media_id, "delete")

            model.state = ModelMediaState.TRASH.value
            model.trash_at = datetime.now(timezone.utc)
            model.updated_at = datetime.now(timezone.utc)
            self.session.commit()

        except (MediaNotFoundError, MediaInTrashError):
            raise
        except Exception as e:
            self.session.rollback()
            raise MediaRepositoryDeleteError(str(e))

    async def restore(self, media_id: UUID) -> None:
        """Restore media from trash"""
        try:
            model = self.session.query(MediaModel).filter(
                MediaModel.id == media_id
            ).first()
            if not model:
                raise MediaNotFoundError(media_id)

            if model.state != ModelMediaState.TRASH.value:
                raise CannotRestoreError(
                    media_id,
                    "Media is not in trash"
                )

            model.state = ModelMediaState.ACTIVE.value
            model.trash_at = None
            model.updated_at = datetime.now(timezone.utc)
            self.session.commit()

        except (MediaNotFoundError, CannotRestoreError):
            raise
        except Exception as e:
            self.session.rollback()
            raise MediaRepositoryDeleteError(str(e))

    async def purge(self, media_id: UUID) -> None:
        """Hard delete media (after 30-day retention)"""
        try:
            model = self.session.query(MediaModel).filter(
                MediaModel.id == media_id
            ).first()
            if not model:
                raise MediaNotFoundError(media_id)

            if model.state != ModelMediaState.TRASH.value:
                raise CannotPurgeError(
                    media_id,
                    "Media is not in trash"
                )

            # Check 30-day retention
            if model.trash_at:
                trash_duration = datetime.now(timezone.utc) - model.trash_at
                thirty_days = timedelta(days=30)
                if trash_duration < thirty_days:
                    days_remaining = (thirty_days - trash_duration).days
                    raise CannotPurgeError(
                        media_id,
                        "Cannot purge: media must stay in trash for 30 days",
                        days_remaining
                    )

            model.deleted_at = datetime.now(timezone.utc)
            self.session.commit()

        except (MediaNotFoundError, CannotPurgeError):
            raise
        except Exception as e:
            self.session.rollback()
            raise MediaRepositoryDeleteError(str(e))

    async def find_by_entity(
        self,
        entity_type: EntityTypeForMedia,
        entity_id: UUID
    ) -> List[Media]:
        """Get all active media associated with an entity"""
        try:
            associations = self.session.query(MediaAssociationModel).filter(
                and_(
                    MediaAssociationModel.entity_type == entity_type.value,
                    MediaAssociationModel.entity_id == entity_id
                )
            ).all()

            media_ids = [assoc.media_id for assoc in associations]
            if not media_ids:
                return []

            models = self.session.query(MediaModel).filter(
                and_(
                    MediaModel.id.in_(media_ids),
                    MediaModel.state == ModelMediaState.ACTIVE.value,
                    MediaModel.deleted_at.is_(None)
                )
            ).all()
            return [self._model_to_domain(m) for m in models]

        except Exception as e:
            raise MediaRepositoryQueryError(str(e))

    async def find_in_trash(
        self,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Media], int]:
        """Get paginated trash media with total count"""
        try:
            # Count total
            total = self.session.query(func.count(MediaModel.id)).filter(
                and_(
                    MediaModel.state == ModelMediaState.TRASH.value,
                    MediaModel.deleted_at.is_(None)
                )
            ).scalar()

            # Get paginated items
            models = self.session.query(MediaModel).filter(
                and_(
                    MediaModel.state == ModelMediaState.TRASH.value,
                    MediaModel.deleted_at.is_(None)
                )
            ).order_by(
                MediaModel.trash_at.desc()
            ).offset(skip).limit(limit).all()

            return [self._model_to_domain(m) for m in models], total

        except Exception as e:
            raise MediaRepositoryQueryError(str(e))

    async def find_active(
        self,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Media], int]:
        """Get paginated active media with total count"""
        try:
            # Count total
            total = self.session.query(func.count(MediaModel.id)).filter(
                and_(
                    MediaModel.state == ModelMediaState.ACTIVE.value,
                    MediaModel.deleted_at.is_(None)
                )
            ).scalar()

            # Get paginated items
            models = self.session.query(MediaModel).filter(
                and_(
                    MediaModel.state == ModelMediaState.ACTIVE.value,
                    MediaModel.deleted_at.is_(None)
                )
            ).order_by(
                MediaModel.created_at.desc()
            ).offset(skip).limit(limit).all()

            return [self._model_to_domain(m) for m in models], total

        except Exception as e:
            raise MediaRepositoryQueryError(str(e))

    async def count_in_trash(self) -> int:
        """Count total media items in trash"""
        try:
            return self.session.query(func.count(MediaModel.id)).filter(
                and_(
                    MediaModel.state == ModelMediaState.TRASH.value,
                    MediaModel.deleted_at.is_(None)
                )
            ).scalar()
        except Exception as e:
            raise MediaRepositoryQueryError(str(e))

    async def find_eligible_for_purge(self) -> List[Media]:
        """Find media that has been in trash for 30+ days"""
        try:
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

            models = self.session.query(MediaModel).filter(
                and_(
                    MediaModel.state == ModelMediaState.TRASH.value,
                    MediaModel.trash_at.isnot(None),
                    MediaModel.trash_at <= thirty_days_ago,
                    MediaModel.deleted_at.is_(None)
                )
            ).all()

            return [self._model_to_domain(m) for m in models]

        except Exception as e:
            raise MediaRepositoryQueryError(str(e))

    async def find_by_storage_key(self, storage_key: str) -> Optional[Media]:
        """Find media by storage key (for duplicate prevention)"""
        try:
            model = self.session.query(MediaModel).filter(
                and_(
                    MediaModel.storage_key == storage_key,
                    MediaModel.deleted_at.is_(None)
                )
            ).first()
            if not model:
                return None
            return self._model_to_domain(model)
        except Exception as e:
            raise MediaRepositoryQueryError(str(e))

    async def associate_media_with_entity(
        self,
        media_id: UUID,
        entity_type: EntityTypeForMedia,
        entity_id: UUID
    ) -> None:
        """Create media-entity association"""
        try:
            # Check if association already exists
            existing = self.session.query(MediaAssociationModel).filter(
                and_(
                    MediaAssociationModel.media_id == media_id,
                    MediaAssociationModel.entity_type == entity_type.value,
                    MediaAssociationModel.entity_id == entity_id
                )
            ).first()

            if existing:
                return  # Idempotent

            # Create new association
            model = MediaAssociationModel(
                media_id=media_id,
                entity_type=entity_type.value,
                entity_id=entity_id,
                created_at=datetime.now(timezone.utc)
            )
            self.session.add(model)
            self.session.commit()

        except Exception as e:
            self.session.rollback()
            raise MediaRepositorySaveError(str(e))

    async def disassociate_media_from_entity(
        self,
        media_id: UUID,
        entity_type: EntityTypeForMedia,
        entity_id: UUID
    ) -> None:
        """Remove media-entity association"""
        try:
            assoc = self.session.query(MediaAssociationModel).filter(
                and_(
                    MediaAssociationModel.media_id == media_id,
                    MediaAssociationModel.entity_type == entity_type.value,
                    MediaAssociationModel.entity_id == entity_id
                )
            ).first()

            if not assoc:
                return  # Idempotent

            self.session.delete(assoc)
            self.session.commit()

        except Exception as e:
            self.session.rollback()
            raise MediaRepositoryDeleteError(str(e))

    async def count_associations(self, media_id: UUID) -> int:
        """Count total associations for media"""
        try:
            return self.session.query(func.count(MediaAssociationModel.id)).filter(
                MediaAssociationModel.media_id == media_id
            ).scalar()
        except Exception as e:
            raise MediaRepositoryQueryError(str(e))

    async def check_key_exists(self, storage_key: str) -> bool:
        """Check if a storage key already exists"""
        try:
            return self.session.query(MediaModel).filter(
                and_(
                    MediaModel.storage_key == storage_key,
                    MediaModel.deleted_at.is_(None)
                )
            ).first() is not None
        except Exception as e:
            raise MediaRepositoryQueryError(str(e))

    # ========================================================================
    # Private Helpers
    # ========================================================================

    def _model_to_domain(self, model: MediaModel) -> Media:
        """Convert ORM model to domain object"""
        from api.app.modules.media.domain import MediaMimeType
        return Media(
            id=model.id,
            filename=model.filename,
            media_type=model.media_type,
            mime_type=MediaMimeType(model.mime_type),
            file_size=model.file_size,
            storage_key=model.storage_key,
            width=model.width,
            height=model.height,
            duration_ms=model.duration_ms,
            state=model.state,
            trash_at=model.trash_at,
            deleted_at=model.deleted_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
