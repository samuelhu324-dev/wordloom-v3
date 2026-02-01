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
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
import time

from api.app.modules.media.domain import Media, MediaState, EntityTypeForMedia
from api.app.modules.media.domain import (
    MediaNotFoundError,
    MediaInTrashError,
    CannotPurgeError,
    CannotRestoreError,
    MediaRepositorySaveError,
    MediaRepositoryQueryError,
    MediaRepositoryDeleteError,
)
from api.app.modules.media.application.ports.output import MediaRepository
from api.app.shared.request_context import RequestContext
from infra.database.models.media_models import MediaModel, MediaAssociationModel, MediaState as ModelMediaState


logger = logging.getLogger(__name__)


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

    def __init__(self, db_session: AsyncSession):
        """Initialize repository with database session

        Args:
            db_session: SQLAlchemy session for database access
        """
        self.session = db_session

    async def save(self, media: Media) -> Media:
        """Persist media (create or update)"""
        try:
            logger.info(
                f"[SAVE] Attempting to save media: id={media.id}, user_id={media.user_id}, storage_key={media.storage_key}, filename={media.filename}"
            )

            stmt = select(MediaModel).where(MediaModel.id == media.id)
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                logger.info(f"[SAVE] Updating existing media: {media.id}")
                existing.filename = media.filename
                existing.user_id = media.user_id
                existing.storage_key = media.storage_key
                existing.media_type = media.media_type.value
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
                logger.info(f"[SAVE] Creating new media: {media.id}")
                model = MediaModel(
                    id=media.id,
                    user_id=media.user_id,
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
                logger.info("[SAVE] Model added to session")

            # Flush so downstream code in the same transaction can read it,
            # but leave commit/rollback to the outer Unit of Work / request boundary.
            await self.session.flush()
            logger.info(f"[SAVE] Successfully flushed media: {media.id}")
            # Verify the saved data by loading from database
            logger.info(f"[SAVE] Verifying save by loading from database...")
            stmt_verify = select(MediaModel).where(MediaModel.id == media.id)
            result_verify = await self.session.execute(stmt_verify)
            verified_model = result_verify.scalar_one_or_none()
            if verified_model:
                logger.info(f"[SAVE] Verified: media_type={verified_model.media_type}, state={verified_model.state}")
            return media

        except Exception as e:
            logger.exception(f"[MediaRepositoryImpl.save] Exception during save: {type(e).__name__}: {e}")
            # Include original exception type and message for diagnostic clarity
            raise MediaRepositorySaveError(f"{type(e).__name__}: {e}")

    async def get_by_id(self, media_id: UUID, *, ctx: Optional[RequestContext] = None) -> Optional[Media]:
        """Fetch media by ID"""
        start = time.perf_counter()
        correlation_id = getattr(ctx, "correlation_id", None)
        try:
            stmt = select(MediaModel).where(MediaModel.id == media_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            db_duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                {
                    "event": "media.repo.get_by_id",
                    "operation": "media.get",
                    "layer": "repo",
                    "correlation_id": correlation_id,
                    "media_id": str(media_id),
                    "db_duration_ms": db_duration_ms,
                    "row_count": 1 if model else 0,
                }
            )

            if not model:
                return None
            return self._model_to_domain(model)
        except Exception as e:
            db_duration_ms = (time.perf_counter() - start) * 1000

            db_error_code = None
            if isinstance(e, SQLAlchemyError):
                orig = getattr(e, "orig", None)
                db_error_code = getattr(orig, "pgcode", None) or getattr(orig, "sqlstate", None)

            logger.exception(
                {
                    "event": "media.repo.get_by_id.failed",
                    "operation": "media.get",
                    "layer": "repo",
                    "correlation_id": correlation_id,
                    "media_id": str(media_id),
                    "db_duration_ms": db_duration_ms,
                    "error_type": type(e).__name__,
                    "db_error_code": db_error_code,
                }
            )
            raise MediaRepositoryQueryError(str(e)) from e

    async def list_active(self, skip: int = 0, limit: int = 100) -> List[Media]:
        """List active media items (without totals)"""
        media, _ = await self.find_active(skip=skip, limit=limit)
        return media

    async def list_in_trash(self, skip: int = 0, limit: int = 100) -> List[Media]:
        """List trash media items (without totals)"""
        media, _ = await self.find_in_trash(skip=skip, limit=limit)
        return media

    async def delete(self, media_id: UUID) -> None:
        """Hard delete media (delegates to purge semantics)"""
        await self.purge(media_id)

    async def purge_expired(self, older_than_days: int = 30) -> int:
        """Purge all media older than the given retention threshold"""
        eligible = await self.find_eligible_for_purge(older_than_days)
        purged = 0
        for media in eligible:
            await self.purge(media.id)
            purged += 1
        return purged

    async def count_by_state(self, state: MediaState) -> int:
        """Count media items in the specified state"""
        try:
            stmt = select(func.count(MediaModel.id)).where(
                and_(
                    MediaModel.state == state.value,
                    MediaModel.deleted_at.is_(None)
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar_one()
        except Exception as e:
            raise MediaRepositoryQueryError(str(e))

    async def move_to_trash(self, media_id: UUID) -> None:
        """Soft delete media (move to trash)"""
        try:
            stmt = select(MediaModel).where(MediaModel.id == media_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            if not model:
                raise MediaNotFoundError(media_id)

            if model.state == ModelMediaState.TRASH.value:
                raise MediaInTrashError(media_id, "delete")

            now = datetime.now(timezone.utc)
            model.state = ModelMediaState.TRASH.value
            model.trash_at = now
            model.updated_at = now
            await self.session.commit()

        except (MediaNotFoundError, MediaInTrashError):
            raise
        except Exception as e:
            await self.session.rollback()
            raise MediaRepositoryDeleteError(str(e))

    async def restore_from_trash(self, media_id: UUID) -> None:
        """Restore media from trash"""
        try:
            stmt = select(MediaModel).where(MediaModel.id == media_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
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
            await self.session.commit()

        except (MediaNotFoundError, CannotRestoreError):
            raise
        except Exception as e:
            await self.session.rollback()
            raise MediaRepositoryDeleteError(str(e))

    async def purge(self, media_id: UUID) -> None:
        """Hard delete media (after 30-day retention)"""
        try:
            stmt = select(MediaModel).where(MediaModel.id == media_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            if not model:
                raise MediaNotFoundError(media_id)

            if model.state != ModelMediaState.TRASH.value:
                raise CannotPurgeError(
                    media_id,
                    "Media is not in trash"
                )

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
            await self.session.commit()

        except (MediaNotFoundError, CannotPurgeError):
            raise
        except Exception as e:
            await self.session.rollback()
            raise MediaRepositoryDeleteError(str(e))

    async def find_by_entity(
        self,
        entity_type: EntityTypeForMedia,
        entity_id: UUID
    ) -> List[Media]:
        """Get all active media associated with an entity"""
        try:
            assoc_stmt = select(MediaAssociationModel).where(
                and_(
                    MediaAssociationModel.entity_type == entity_type.value,
                    MediaAssociationModel.entity_id == entity_id
                )
            )
            assoc_result = await self.session.execute(assoc_stmt)
            associations = assoc_result.scalars().all()

            media_ids = [assoc.media_id for assoc in associations]
            if not media_ids:
                return []

            media_stmt = select(MediaModel).where(
                and_(
                    MediaModel.id.in_(media_ids),
                    MediaModel.state == ModelMediaState.ACTIVE.value,
                    MediaModel.deleted_at.is_(None)
                )
            )
            media_result = await self.session.execute(media_stmt)
            models = media_result.scalars().all()
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
            count_stmt = select(func.count(MediaModel.id)).where(
                and_(
                    MediaModel.state == ModelMediaState.TRASH.value,
                    MediaModel.deleted_at.is_(None)
                )
            )
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar_one()

            list_stmt = select(MediaModel).where(
                and_(
                    MediaModel.state == ModelMediaState.TRASH.value,
                    MediaModel.deleted_at.is_(None)
                )
            ).order_by(
                MediaModel.trash_at.desc()
            ).offset(skip).limit(limit)
            list_result = await self.session.execute(list_stmt)
            models = list_result.scalars().all()

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
            count_stmt = select(func.count(MediaModel.id)).where(
                and_(
                    MediaModel.state == ModelMediaState.ACTIVE.value,
                    MediaModel.deleted_at.is_(None)
                )
            )
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar_one()

            list_stmt = select(MediaModel).where(
                and_(
                    MediaModel.state == ModelMediaState.ACTIVE.value,
                    MediaModel.deleted_at.is_(None)
                )
            ).order_by(
                MediaModel.created_at.desc()
            ).offset(skip).limit(limit)
            list_result = await self.session.execute(list_stmt)
            models = list_result.scalars().all()

            return [self._model_to_domain(m) for m in models], total

        except Exception as e:
            raise MediaRepositoryQueryError(str(e))

    async def count_in_trash(self) -> int:
        """Count total media items in trash"""
        try:
            stmt = select(func.count(MediaModel.id)).where(
                and_(
                    MediaModel.state == ModelMediaState.TRASH.value,
                    MediaModel.deleted_at.is_(None)
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar_one()
        except Exception as e:
            raise MediaRepositoryQueryError(str(e))

    async def find_eligible_for_purge(self, older_than_days: int = 30) -> List[Media]:
        """Find media that has been in trash past the retention threshold"""
        try:
            threshold = datetime.now(timezone.utc) - timedelta(days=older_than_days)

            stmt = select(MediaModel).where(
                and_(
                    MediaModel.state == ModelMediaState.TRASH.value,
                    MediaModel.trash_at.isnot(None),
                    MediaModel.trash_at <= threshold,
                    MediaModel.deleted_at.is_(None)
                )
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()

            return [self._model_to_domain(m) for m in models]

        except Exception as e:
            raise MediaRepositoryQueryError(str(e))

    async def find_by_storage_key(self, storage_key: str) -> Optional[Media]:
        """Find media by storage key (for duplicate prevention)"""
        try:
            stmt = select(MediaModel).where(
                and_(
                    MediaModel.storage_key == storage_key,
                    MediaModel.deleted_at.is_(None)
                )
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
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
            stmt = select(MediaAssociationModel).where(
                and_(
                    MediaAssociationModel.media_id == media_id,
                    MediaAssociationModel.entity_type == entity_type.value,
                    MediaAssociationModel.entity_id == entity_id
                )
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                return

            model = MediaAssociationModel(
                media_id=media_id,
                entity_type=entity_type.value,
                entity_id=entity_id,
                created_at=datetime.now(timezone.utc)
            )
            self.session.add(model)
            await self.session.commit()

        except Exception as e:
            await self.session.rollback()
            raise MediaRepositorySaveError(str(e))

    async def disassociate_media_from_entity(
        self,
        media_id: UUID,
        entity_type: EntityTypeForMedia,
        entity_id: UUID
    ) -> None:
        """Remove media-entity association"""
        try:
            stmt = select(MediaAssociationModel).where(
                and_(
                    MediaAssociationModel.media_id == media_id,
                    MediaAssociationModel.entity_type == entity_type.value,
                    MediaAssociationModel.entity_id == entity_id
                )
            )
            result = await self.session.execute(stmt)
            assoc = result.scalar_one_or_none()

            if not assoc:
                return

            await self.session.delete(assoc)
            await self.session.commit()

        except Exception as e:
            await self.session.rollback()
            raise MediaRepositoryDeleteError(str(e))

    async def count_associations(self, media_id: UUID) -> int:
        """Count total associations for media"""
        try:
            stmt = select(func.count(MediaAssociationModel.id)).where(
                MediaAssociationModel.media_id == media_id
            )
            result = await self.session.execute(stmt)
            return result.scalar_one()
        except Exception as e:
            raise MediaRepositoryQueryError(str(e))

    async def check_key_exists(self, storage_key: str) -> bool:
        """Check if a storage key already exists"""
        try:
            stmt = select(MediaModel).where(
                and_(
                    MediaModel.storage_key == storage_key,
                    MediaModel.deleted_at.is_(None)
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            raise MediaRepositoryQueryError(str(e))

    # ========================================================================
    # Private Helpers
    # ========================================================================

    def _model_to_domain(self, model: MediaModel) -> Media:
        """Convert ORM model to domain object"""
        from api.app.modules.media.domain import MediaType, MediaMimeType, MediaState

        # Handle string values from database
        media_type = MediaType(model.media_type) if model.media_type else MediaType.IMAGE
        mime_type = MediaMimeType(model.mime_type) if model.mime_type else MediaMimeType.JPEG
        state_value = (model.state or MediaState.ACTIVE.value)
        state = MediaState(state_value.upper()) if isinstance(state_value, str) else MediaState.ACTIVE

        return Media(
            id=model.id,
            user_id=model.user_id,
            filename=model.filename,
            media_type=media_type,
            mime_type=mime_type,
            file_size=model.file_size,
            storage_key=model.storage_key,
            width=model.width,
            height=model.height,
            duration_ms=model.duration_ms,
            state=state,
            trash_at=model.trash_at,
            deleted_at=model.deleted_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
