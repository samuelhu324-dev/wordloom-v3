"""SQLAlchemy repository for maturity snapshots."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.modules.maturity.application.ports import MaturitySnapshotRepository
from api.app.modules.maturity.domain import (
    MaturitySnapshot,
    MaturityStage,
    MaturityScore,
    ScoreComponent,
    StructureTaskState,
    StructureTaskStatus,
)
from infra.database.models import MaturitySnapshotModel


def _serialize_task(task: StructureTaskState) -> dict:
    return {
        "code": task.code,
        "title": task.title,
        "description": task.description,
        "weight": task.weight,
        "required_stage": task.required_stage.value,
        "status": task.status.value,
    }


def _deserialize_task(payload: dict) -> StructureTaskState:
    required_stage = payload.get("required_stage") or MaturityStage.SEED.value
    status = payload.get("status") or StructureTaskStatus.PENDING.value
    try:
        parsed_stage = MaturityStage(required_stage)
    except ValueError:
        parsed_stage = MaturityStage.SEED
    try:
        parsed_status = StructureTaskStatus(status)
    except ValueError:
        parsed_status = StructureTaskStatus.PENDING
    return StructureTaskState(
        code=payload.get("code", ""),
        title=payload.get("title", ""),
        description=payload.get("description", ""),
        weight=int(payload.get("weight", 1) or 1),
        required_stage=parsed_stage,
        status=parsed_status,
    )


def _serialize_signals(snapshot: MaturitySnapshot) -> dict:
    return {
        "blocks_count": snapshot.blocks_count,
        "block_type_count": snapshot.block_type_count,
        "todos_count": snapshot.todos_count,
        "tags_count": snapshot.tags_count,
        "visits_90d": snapshot.visits_90d,
        "summary_length": snapshot.summary_length,
        "has_title": snapshot.has_title,
        "has_summary": snapshot.has_summary,
        "has_cover_icon": snapshot.has_cover_icon,
        "operations_bonus": snapshot.operations_bonus,
        "last_visit_at": snapshot.last_visit_at.isoformat() if snapshot.last_visit_at else None,
        "last_event_at": snapshot.last_event_at.isoformat() if snapshot.last_event_at else None,
    }


def _parse_iso_datetime(value) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class SQLAlchemyMaturitySnapshotRepository(MaturitySnapshotRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_snapshot(self, snapshot: MaturitySnapshot) -> MaturitySnapshot:
        model = MaturitySnapshotModel(
            book_id=snapshot.book_id,
            stage=snapshot.stage.value,
            score=snapshot.score.value,
            components=[component.__dict__ for component in snapshot.score.components],
            tasks=[_serialize_task(task) for task in snapshot.tasks],
            signals=_serialize_signals(snapshot),
            manual_override=snapshot.manual_override,
            manual_reason=snapshot.manual_reason,
            created_at=snapshot.created_at,
        )
        self._session.add(model)
        await self._session.commit()
        return snapshot

    async def list_snapshots(self, book_id: UUID, limit: int = 10) -> List[MaturitySnapshot]:
        stmt = (
            select(MaturitySnapshotModel)
            .where(MaturitySnapshotModel.book_id == book_id)
            .order_by(desc(MaturitySnapshotModel.created_at))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def get_latest_stage(self, book_id: UUID) -> Optional[MaturityStage]:
        stmt = (
            select(MaturitySnapshotModel.stage)
            .where(MaturitySnapshotModel.book_id == book_id)
            .order_by(desc(MaturitySnapshotModel.created_at))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        stage_value = result.scalar_one_or_none()
        if not stage_value:
            return None
        try:
            return MaturityStage(stage_value)
        except ValueError:
            return None

    async def get_latest_snapshot(self, book_id: UUID) -> Optional[MaturitySnapshot]:
        stmt = (
            select(MaturitySnapshotModel)
            .where(MaturitySnapshotModel.book_id == book_id)
            .order_by(desc(MaturitySnapshotModel.created_at))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_domain(model)

    def _to_domain(self, model: MaturitySnapshotModel) -> MaturitySnapshot:
        components = [ScoreComponent(**item) for item in model.components or []]
        tasks_payload = model.tasks or []
        tasks = [_deserialize_task(item) for item in tasks_payload]
        score = MaturityScore(value=model.score, components=components)
        signals = model.signals or {}

        return MaturitySnapshot(
            book_id=model.book_id,
            stage=MaturityStage(model.stage),
            score=score,
            tasks=tasks,
            created_at=model.created_at,
            manual_override=model.manual_override,
            manual_reason=model.manual_reason,
            blocks_count=int(signals.get("blocks_count", 0) or 0),
            block_type_count=int(signals.get("block_type_count", 0) or 0),
            todos_count=int(signals.get("todos_count", 0) or 0),
            tags_count=int(signals.get("tags_count", 0) or 0),
            visits_90d=int(signals.get("visits_90d", 0) or 0),
            summary_length=int(signals.get("summary_length", 0) or 0),
            has_title=bool(signals.get("has_title", False)),
            has_summary=bool(signals.get("has_summary", False)),
            has_cover_icon=bool(signals.get("has_cover_icon", False)),
            operations_bonus=int(signals.get("operations_bonus", 0) or 0),
            last_visit_at=_parse_iso_datetime(signals.get("last_visit_at")),
            last_event_at=_parse_iso_datetime(signals.get("last_event_at")),
        )
