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
import os

import sqlalchemy as sa
from sqlalchemy import select, func, desc, asc, and_, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from api.app.modules.chronicle.domain import (
    ChronicleRepositoryPort,
    ChronicleEvent,
    ChronicleEventType,
)
from api.app.modules.chronicle.exceptions import ChronicleRepositoryError
from infra.database.models import ChronicleEventModel, ChronicleOutboxEventModel, ChronicleEventDedupeStateModel


def _get_block_updated_dedupe_window_seconds() -> int:
    raw = os.getenv("CHRONICLE_BLOCK_UPDATED_DEDUPE_SECONDS", "10")
    try:
        window = int(raw)
    except Exception:
        window = 10
    return max(1, window)


async def _should_emit_block_updated(
    session: AsyncSession,
    *,
    event_type: str,
    book_id: UUID,
    block_id: UUID,
    actor_id: UUID,
    window_seconds: int,
) -> bool:
    """DB-consistent dedupe: allow at most one event per key per time bucket.

    Returns True if caller should write chronicle_events/outbox, False if suppressed.
    """

    # Use DB time to avoid multi-instance clock skew.
    bucket_expr = cast(
        cast(func.extract("epoch", func.now()), sa.BigInteger) / int(window_seconds),
        sa.BigInteger,
    )

    stmt = (
        pg_insert(ChronicleEventDedupeStateModel)
        .values(
            event_type=event_type,
            book_id=book_id,
            block_id=block_id,
            actor_id=actor_id,
            window_seconds=int(window_seconds),
            last_bucket=bucket_expr,
            updated_at=func.now(),
        )
        .on_conflict_do_update(
            index_elements=[
                ChronicleEventDedupeStateModel.event_type,
                ChronicleEventDedupeStateModel.book_id,
                ChronicleEventDedupeStateModel.block_id,
                ChronicleEventDedupeStateModel.actor_id,
                ChronicleEventDedupeStateModel.window_seconds,
            ],
            set_={
                "last_bucket": bucket_expr,
                "updated_at": func.now(),
            },
            where=(ChronicleEventDedupeStateModel.last_bucket < bucket_expr),
        )
    )

    result = await session.execute(stmt)
    return int(getattr(result, "rowcount", 0) or 0) > 0


class SQLAlchemyChronicleRepository(ChronicleRepositoryPort):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, event: ChronicleEvent) -> ChronicleEvent:
        try:
            # Multi-instance consistent dedupe for high-frequency facts.
            if event.event_type == ChronicleEventType.BLOCK_UPDATED:
                if event.actor_id is not None and event.block_id is not None and event.book_id is not None:
                    window_seconds = _get_block_updated_dedupe_window_seconds()
                    should_emit = await _should_emit_block_updated(
                        self._session,
                        event_type=event.event_type.value,
                        book_id=event.book_id,
                        block_id=event.block_id,
                        actor_id=event.actor_id,
                        window_seconds=window_seconds,
                    )
                    if not should_emit:
                        # Suppressed: do not write chronicle_events nor outbox.
                        # End the transaction opened by the UPSERT.
                        # Note: this repository owns transaction boundaries (it commits on success).
                        await self._session.commit()
                        return event

            payload = event.payload or {}
            model = ChronicleEventModel(
                id=event.id,
                event_type=event.event_type.value,
                book_id=event.book_id,
                block_id=event.block_id,
                actor_id=event.actor_id,
                payload=payload,
                occurred_at=event.occurred_at,
                created_at=event.created_at,
            )

            # Phase C: promote durable envelope fields to columns.
            # Keep payload as source of truth for backwards compatibility.
            try:
                model.schema_version = payload.get("schema_version")
            except Exception:
                model.schema_version = None
            model.provenance = payload.get("provenance")
            model.source = payload.get("source")
            model.actor_kind = payload.get("actor_kind")
            model.correlation_id = payload.get("correlation_id")
            self._session.add(model)

            # In the same transaction: enqueue outbox event for async projection.
            # Idempotency: entity_id is chronicle_event_id; worker upserts chronicle_entries.
            traceparent = None
            tracestate = None
            try:
                from infra.observability.tracing import inject_trace_context

                traceparent, tracestate = inject_trace_context()
            except Exception:
                traceparent, tracestate = None, None
            outbox_row = ChronicleOutboxEventModel(
                entity_type="chronicle_event",
                entity_id=event.id,
                op="upsert",
                event_version=0,
                status="pending",
                attempts=0,
                replay_count=0,
                traceparent=traceparent,
                tracestate=tracestate,
            )
            self._session.add(outbox_row)

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

            # Stable pagination: tie-break by id when occurred_at is equal.
            order_by = (
                (desc(ChronicleEventModel.occurred_at), desc(ChronicleEventModel.id))
                if order_desc
                else (asc(ChronicleEventModel.occurred_at), asc(ChronicleEventModel.id))
            )

            count_stmt = select(func.count(ChronicleEventModel.id)).where(and_(*filters))
            total_result = await self._session.execute(count_stmt)
            total = int(total_result.scalar() or 0)

            stmt = (
                select(ChronicleEventModel)
                .where(and_(*filters))
                .order_by(*order_by)
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
