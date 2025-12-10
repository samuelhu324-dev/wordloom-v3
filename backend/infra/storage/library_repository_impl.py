"""
Library Repository Implementation Adapter

Concrete SQLAlchemy implementation of LibraryRepository output port.

Location: infra/storage/library_repository_impl.py
Port Interface: api/app/modules/library/application/ports/output.py

Architecture:
  - Implements abstract LibraryRepository interface (output port)
  - Uses SQLAlchemy ORM models from infra/database/models
  - Converts ORM models ↔ Domain objects
  - Manages database transactions and error handling
  - Enforces business logic: 1 Library per user (RULE-001)
"""

import logging
from typing import Optional, List
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, desc, asc, case
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.modules.library.domain import Library, LibraryName
from api.app.modules.library.exceptions import LibraryAlreadyExistsError
from api.app.modules.library.application.ports.output import ILibraryRepository, LibrarySort
from infra.database.models import LibraryModel

logger = logging.getLogger(__name__)


class SQLAlchemyLibraryRepository(ILibraryRepository):
    """SQLAlchemy implementation of LibraryRepository (Infrastructure Adapter)

    This is an ADAPTER in Hexagonal architecture - it implements the
    output port interface defined in application/ports/output.py.

    Responsibilities:
    - Persist Library domain objects to database
    - Fetch Libraries from database and convert to domain objects
    - Enforce 1 Library per user (RULE-001)
    - Handle transaction rollback on errors
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with async database session

        Args:
            session: AsyncSession for async database access
        """
        self.session = session

    async def save(self, library: Library) -> None:
        """Persist Library (insert or update).

        Multi-Library Mode: UNIQUE(user_id) removed (Migration 002).
        We attempt upsert logic by checking existence first.
        """
        try:
            stmt = select(LibraryModel).where(LibraryModel.id == library.id)
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing record
                existing.name = library.name.value
                existing.description = library.description
                existing.basement_bookshelf_id = library.basement_bookshelf_id
                existing.cover_media_id = library.cover_media_id
                existing.theme_color = getattr(library, 'theme_color', None)
                existing.pinned = library.pinned
                existing.pinned_order = library.pinned_order
                existing.archived_at = library.archived_at
                existing.last_activity_at = library.last_activity_at
                existing.views_count = library.views_count
                existing.last_viewed_at = library.last_viewed_at
                existing.updated_at = library.updated_at
                existing.soft_deleted_at = library.soft_deleted_at
            else:
                model = LibraryModel(
                    id=library.id,
                    user_id=library.user_id,
                    basement_bookshelf_id=library.basement_bookshelf_id,
                    name=library.name.value,
                    description=library.description,
                    cover_media_id=library.cover_media_id,
                    theme_color=getattr(library, 'theme_color', None),
                    pinned=library.pinned,
                    pinned_order=library.pinned_order,
                    archived_at=library.archived_at,
                    last_activity_at=library.last_activity_at,
                    views_count=library.views_count,
                    last_viewed_at=library.last_viewed_at,
                    created_at=library.created_at,
                    updated_at=library.updated_at,
                    soft_deleted_at=library.soft_deleted_at,
                )
                self.session.add(model)
            await self.session.commit()
        except IntegrityError as e:
            await self.session.rollback()
            error_str = str(e).lower()
            # Multi-library: user_id uniqueness removed; treat remaining integrity errors generically
            logger.error(f"Integrity error persisting Library: {e}")
            raise

    async def get_by_id(self, library_id: UUID) -> Optional[Library]:
        """Retrieve Library by ID"""
        try:
            stmt = select(LibraryModel).where(LibraryModel.id == library_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            if not model:
                logger.debug(f"Library not found: {library_id}")
                return None
            return self._to_domain(model)
        except Exception as e:
            logger.error(f"Error fetching Library {library_id}: {e}")
            raise

    async def list_by_user_id(self, user_id: UUID) -> List[Library]:
        """List Libraries by user ID (multi-library supported)"""
        try:
            stmt = select(LibraryModel).where(LibraryModel.user_id == user_id)
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [self._to_domain(m) for m in models]
        except Exception as e:
            logger.error(f"Error listing Libraries for user {user_id}: {e}")
            raise

    async def list_all(self) -> List[Library]:
        """List all Libraries (diagnostic / single-user mode)."""
        return await self.list_overview(include_archived=True)

    async def search(self, query: str) -> List[Library]:
        return await self.list_overview(query=query, include_archived=True)

    async def list_overview(
        self,
        *,
        query: Optional[str] = None,
        include_archived: bool = False,
        sort: Optional[LibrarySort] = None,
        pinned_first: bool = True,
    ) -> List[Library]:
        try:
            stmt = select(LibraryModel)

            if query:
                pattern = f"%{query.strip()}%"
                stmt = stmt.where(
                    (LibraryModel.name.ilike(pattern)) | (LibraryModel.description.ilike(pattern))
                )

            if not include_archived:
                stmt = stmt.where(LibraryModel.archived_at.is_(None))

            order_clauses = []

            if include_archived:
                archived_priority = case((LibraryModel.archived_at.is_(None), 0), else_=1)
                order_clauses.append(asc(archived_priority))

            if pinned_first:
                order_clauses.append(desc(LibraryModel.pinned))
                order_clauses.append(asc(LibraryModel.pinned_order))

            sort = sort or LibrarySort.LAST_ACTIVITY_DESC
            if sort == LibrarySort.NAME_ASC:
                order_clauses.append(asc(LibraryModel.name))
            elif sort == LibrarySort.CREATED_DESC:
                order_clauses.append(desc(LibraryModel.created_at))
            elif sort == LibrarySort.VIEWS_DESC:
                order_clauses.append(desc(LibraryModel.views_count))
            else:
                order_clauses.append(desc(LibraryModel.last_activity_at))

            order_clauses.extend((desc(LibraryModel.updated_at), desc(LibraryModel.created_at)))

            stmt = stmt.order_by(*order_clauses)

            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [self._to_domain(m) for m in models]
        except Exception as e:
            logger.error(f"Error listing Libraries overview: {e}")
            raise

    async def delete(self, library_id: UUID) -> None:
        """Delete Library by ID"""
        try:
            stmt = select(LibraryModel).where(LibraryModel.id == library_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            if model:
                await self.session.delete(model)
                await self.session.commit()
                logger.info(f"Library deleted: {library_id}")
            else:
                logger.debug(f"Library not found for deletion: {library_id}")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting Library {library_id}: {e}")
            raise

    async def exists(self, library_id: UUID) -> bool:
        """Check if Library exists"""
        try:
            stmt = select(LibraryModel).where(LibraryModel.id == library_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            return model is not None
        except Exception as e:
            logger.error(f"Error checking Library existence {library_id}: {e}")
            raise

    def _to_domain(self, model: LibraryModel) -> Library:
        """Convert ORM model to Domain model"""
        return Library(
            library_id=model.id,
            user_id=model.user_id,
            name=LibraryName(value=model.name),
            basement_bookshelf_id=getattr(model, 'basement_bookshelf_id', None),
            description=getattr(model, 'description', None),
            cover_media_id=getattr(model, 'cover_media_id', None),
            theme_color=getattr(model, 'theme_color', None),
            pinned=getattr(model, 'pinned', False),
            pinned_order=getattr(model, 'pinned_order', None),
            archived_at=getattr(model, 'archived_at', None),
            last_activity_at=getattr(model, 'last_activity_at', None),
            views_count=getattr(model, 'views_count', 0),
            last_viewed_at=getattr(model, 'last_viewed_at', None),
            created_at=model.created_at,
            updated_at=model.updated_at,
            soft_deleted_at=getattr(model, 'soft_deleted_at', None),
        )
