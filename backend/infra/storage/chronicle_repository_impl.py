"""Chronicle Repository Implementation

SQLAlchemy Adapter 实现 ChronicleRepositoryPort。

职责：
  - 写入事件至 chronicle_events 表
  - 基于 book_id 或时间窗口分页查询
  - 转换 ORM ↔ 领域对象

注意：所有操作采用 AsyncSession，调用方需在 FastAPI 依赖中提供。
"""

from dataclasses import replace
from typing import Optional, Sequence, Tuple, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func, desc, asc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.modules.chronicle.domain import (
    ChronicleRepositoryPort,
    ChronicleEvent,
    ChronicleEventType,
)
from api.app.modules.chronicle.exceptions import ChronicleRepositoryError
from infra.database.models import ChronicleEventModel


class SQLAlchemyChronicleRepository(ChronicleRepositoryPort):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, event: ChronicleEvent) -> ChronicleEvent:
        try:
            model = ChronicleEventModel(
                id=event.id,
                event_type=event.event_type.value,
                book_id=event.book_id,
                block_id=event.block_id,
                actor_id=event.actor_id,
                payload=event.payload or {},
                occurred_at=event.occurred_at,
                created_at=event.created_at,
            )
            self._session.add(model)
            await self._session.commit()
            await self._session.refresh(model)
            return replace(
                event,
                occurred_at=model.occurred_at,
                created_at=model.created_at,
            )
        except Exception as exc:
            await self._session.rollback()
            raise ChronicleRepositoryError(str(exc)) from exc

    async def list_by_book(
        self,
        book_id: UUID,
        event_types: Optional[Sequence[ChronicleEventType]] = None,
        limit: int = 50,
        offset: int = 0,
        order_desc: bool = True,
    ) -> Tuple[List[ChronicleEvent], int]:
        try:
            filters = [ChronicleEventModel.book_id == book_id]
            if event_types:
                filters.append(
                    ChronicleEventModel.event_type.in_([et.value for et in event_types])
                )

            order_by = (
                desc(ChronicleEventModel.occurred_at)
                if order_desc
                else asc(ChronicleEventModel.occurred_at)
            )

            count_stmt = select(func.count(ChronicleEventModel.id)).where(and_(*filters))
            total_result = await self._session.execute(count_stmt)
            total = int(total_result.scalar() or 0)

            stmt = (
                select(ChronicleEventModel)
                .where(and_(*filters))
                .order_by(order_by)
                .offset(offset)
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()
            return [self._to_domain(model) for model in models], total
        except Exception as exc:
            raise ChronicleRepositoryError(str(exc)) from exc

    async def list_by_time_range(
        self,
        start: datetime,
        end: datetime,
        event_types: Optional[Sequence[ChronicleEventType]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[ChronicleEvent], int]:
        try:
            filters = [ChronicleEventModel.occurred_at.between(start, end)]
            if event_types:
                filters.append(
                    ChronicleEventModel.event_type.in_([et.value for et in event_types])
                )

            count_stmt = select(func.count(ChronicleEventModel.id)).where(and_(*filters))
            total_result = await self._session.execute(count_stmt)
            total = int(total_result.scalar() or 0)

            stmt = (
                select(ChronicleEventModel)
                .where(and_(*filters))
                .order_by(desc(ChronicleEventModel.occurred_at))
                .offset(offset)
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()
            return [self._to_domain(model) for model in models], total
        except Exception as exc:
            raise ChronicleRepositoryError(str(exc)) from exc

    def _to_domain(self, model: ChronicleEventModel) -> ChronicleEvent:
        return ChronicleEvent(
            id=model.id,
            event_type=ChronicleEventType(model.event_type),
            book_id=model.book_id,
            block_id=model.block_id,
            actor_id=model.actor_id,
            payload=model.payload or {},
            occurred_at=model.occurred_at,
            created_at=model.created_at,
        )
