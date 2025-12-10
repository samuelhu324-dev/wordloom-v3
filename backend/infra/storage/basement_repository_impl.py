"""SQLAlchemy implementation of BasementRepository."""
from __future__ import annotations

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.modules.basement.application.ports.output import BasementRepository
from api.app.modules.basement.domain.basement_entry import BasementEntry
from infra.database.models.basement_models import BasementEntryModel
from infra.database.models.book_models import BookModel


class SQLAlchemyBasementRepository(BasementRepository):
    """Basement repository backed by PostgreSQL via SQLAlchemy ORM."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, entry: BasementEntry) -> BasementEntry:
        model = self._to_model(entry)
        self._session.add(model)
        await self._session.flush()
        return entry

    async def get_by_id(self, entry_id: UUID) -> Optional[BasementEntry]:
        stmt = select(BasementEntryModel).where(BasementEntryModel.id == entry_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_book_id(self, book_id: UUID) -> Optional[BasementEntry]:
        stmt = select(BasementEntryModel).where(BasementEntryModel.book_id == book_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_library(
        self, library_id: UUID, skip: int = 0, limit: int = 20
    ) -> Tuple[List[BasementEntry], int]:
        """Return Basement entries, falling back to books table when snapshots are missing."""

        basement_condition = or_(
            BookModel.soft_deleted_at.isnot(None),
            BookModel.moved_to_basement_at.isnot(None),
        )

        count_stmt = (
            select(func.count())
            .select_from(BookModel)
            .where(BookModel.library_id == library_id)
            .where(basement_condition)
        )
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar() or 0

        order_expr = func.coalesce(
            BasementEntryModel.moved_at,
            BookModel.moved_to_basement_at,
            BookModel.soft_deleted_at,
            BookModel.updated_at,
            BookModel.created_at,
        ).desc()

        stmt = (
            select(BookModel, BasementEntryModel)
            .outerjoin(BasementEntryModel, BasementEntryModel.book_id == BookModel.id)
            .where(BookModel.library_id == library_id)
            .where(basement_condition)
            .order_by(order_expr)
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        rows = result.all()

        entries: List[BasementEntry] = []
        for book_model, entry_model in rows:
            if entry_model is not None:
                entries.append(self._to_domain(entry_model))
            else:
                entries.append(self._from_book_model(book_model))

        return entries, total

    async def delete(self, entry_id: UUID) -> None:
        stmt = delete(BasementEntryModel).where(BasementEntryModel.id == entry_id)
        await self._session.execute(stmt)
        await self._session.flush()

    async def delete_by_book_id(self, book_id: UUID) -> None:
        stmt = delete(BasementEntryModel).where(BasementEntryModel.book_id == book_id)
        await self._session.execute(stmt)
        await self._session.flush()

    @staticmethod
    def _to_domain(model: BasementEntryModel) -> BasementEntry:
        return BasementEntry(
            id=model.id,
            book_id=model.book_id,
            library_id=model.library_id,
            bookshelf_id=model.bookshelf_id,
            previous_bookshelf_id=model.previous_bookshelf_id,
            title_snapshot=model.title_snapshot,
            summary_snapshot=model.summary_snapshot,
            status_snapshot=model.status_snapshot,
            block_count_snapshot=model.block_count_snapshot,
            moved_at=model.moved_at,
            created_at=model.created_at,
        )

    @staticmethod
    def _to_model(entry: BasementEntry) -> BasementEntryModel:
        return BasementEntryModel(
            id=entry.id,
            book_id=entry.book_id,
            library_id=entry.library_id,
            bookshelf_id=entry.bookshelf_id,
            previous_bookshelf_id=entry.previous_bookshelf_id,
            title_snapshot=entry.title_snapshot,
            summary_snapshot=entry.summary_snapshot,
            status_snapshot=entry.status_snapshot,
            block_count_snapshot=entry.block_count_snapshot,
            moved_at=entry.moved_at,
            created_at=entry.created_at,
        )

    @staticmethod
    def _from_book_model(model: BookModel) -> BasementEntry:
        moved_at = (
            getattr(model, "moved_to_basement_at", None)
            or getattr(model, "soft_deleted_at", None)
            or getattr(model, "updated_at", None)
            or getattr(model, "created_at", None)
        )
        created_at = moved_at or getattr(model, "created_at", None)
        return BasementEntry(
            id=model.id,
            book_id=model.id,
            library_id=model.library_id,
            bookshelf_id=model.bookshelf_id,
            previous_bookshelf_id=model.previous_bookshelf_id,
            title_snapshot=model.title,
            summary_snapshot=model.summary,
            status_snapshot=model.status,
            block_count_snapshot=getattr(model, "block_count", 0) or 0,
            moved_at=moved_at,
            created_at=created_at,
        )
