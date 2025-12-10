"""Application use cases for maturity module."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from api.app.modules.book.application.utils.maturity import derive_maturity_from_score
from api.app.modules.book.domain.services.plan111 import (
    PLAN111_STRUCTURE_TASKS,
    Plan111SnapshotInput,
    Plan111StructureTaskBlueprint,
    calculate_plan111_score,
    is_plan111_task_completed,
)

from ..domain import MaturitySnapshot, MaturityStage, MaturityScore, ScoreComponent, StructureTaskState, StructureTaskStatus
from .dtos import (
    CalculateBookMaturityCommand,
    GetSnapshotsQuery,
    MaturitySnapshotList,
    SnapshotPersistenceResult,
)
from .ports import MaturityDataProvider, MaturitySnapshotRepository


class CalculateBookMaturityUseCase:
    """Evaluates score, derives tasks, and (optionally) persists a snapshot."""

    def __init__(
        self,
        data_provider: MaturityDataProvider,
        snapshot_repository: Optional[MaturitySnapshotRepository] = None,
        **_: object,
    ) -> None:
        self._data_provider = data_provider
        self._snapshot_repository = snapshot_repository

    async def execute(self, command: CalculateBookMaturityCommand) -> SnapshotPersistenceResult:
        profile = await self._data_provider.load_book_profile(command.book_id)
        snapshot_input, metrics = self._build_snapshot_input(profile, command)
        score_value, components = calculate_plan111_score(snapshot_input)
        maturity_score = MaturityScore(
            value=score_value,
            components=[ScoreComponent(factor=item.factor, points=item.points, detail=item.detail) for item in components],
        )
        stage = _resolve_plan111_stage(score_value)
        tasks = _resolve_structure_tasks(stage, snapshot_input)

        snapshot = MaturitySnapshot(
            book_id=profile.book_id,
            stage=stage,
            score=maturity_score,
            tasks=tasks,
            manual_override=getattr(profile.book, "manual_maturity_override", False),
            manual_reason=getattr(profile.book, "manual_maturity_reason", None),
            blocks_count=metrics["blocks_count"],
            block_type_count=metrics["block_type_count"],
            todos_count=metrics["todos_count"],
            tags_count=metrics["tags_count"],
            visits_90d=snapshot_input.visits_90d,
            summary_length=snapshot_input.summary_length,
            has_title=snapshot_input.has_title,
            has_summary=snapshot_input.has_summary,
            has_cover_icon=snapshot_input.has_cover_icon,
            operations_bonus=profile.operations_bonus,
            last_visit_at=profile.last_visit_at,
            last_event_at=profile.last_event_at,
        )

        persisted = False
        if command.persist_snapshot and self._snapshot_repository is not None:
            await self._snapshot_repository.save_snapshot(snapshot)
            persisted = True

        return SnapshotPersistenceResult(snapshot=snapshot, persisted=persisted)

    def _build_snapshot_input(
        self,
        profile,
        command: CalculateBookMaturityCommand,
    ) -> tuple[Plan111SnapshotInput, dict[str, int]]:
        def pick(override: Optional[int], current: int) -> int:
            if override is None:
                return current
            return int(override)

        title = profile.title or (profile.book.title.value if profile.book else None)
        summary = profile.summary or (profile.book.summary.value if profile.book else None)
        cover_icon = command.cover_icon if command.cover_icon is not None else profile.cover_icon

        blocks_count = pick(command.block_count, profile.block_count)
        block_type_count = pick(command.block_type_count, profile.block_type_count)
        todos_count = pick(command.open_todo_count, profile.open_todo_snapshot)
        tags_count = pick(command.tag_count, profile.tag_count_snapshot)

        summary_text = (summary or "").strip()
        has_title = bool(title and str(title).strip())
        has_summary = bool(summary_text)
        has_cover_icon = bool(cover_icon)

        manual_adjustment = pick(command.operations_bonus, profile.operations_bonus)
        snapshot_input = Plan111SnapshotInput(
            blocks_count=blocks_count,
            block_type_count=block_type_count,
            todos_count=todos_count,
            tags_count=tags_count,
            summary_length=len(summary_text),
            has_title=has_title,
            has_summary=has_summary,
            has_cover_icon=has_cover_icon,
            visits_90d=profile.visit_count_90d,
            last_event_at=profile.last_event_at,
            manual_adjustment=manual_adjustment,
            calculated_at=datetime.now(timezone.utc),
        )

        metrics = {
            "blocks_count": blocks_count,
            "block_type_count": block_type_count,
            "todos_count": todos_count,
            "tags_count": tags_count,
        }

        return snapshot_input, metrics


class ListMaturitySnapshotsUseCase:
    """Returns maturity snapshots persisted for a book."""

    def __init__(self, repository: MaturitySnapshotRepository) -> None:
        self._repository = repository

    async def execute(self, query: GetSnapshotsQuery) -> MaturitySnapshotList:
        snapshots = await self._repository.list_snapshots(query.book_id, limit=query.limit)
        return MaturitySnapshotList(book_id=query.book_id, snapshots=snapshots)


_STAGE_ORDER = {
    MaturityStage.SEED: 0,
    MaturityStage.GROWING: 1,
    MaturityStage.STABLE: 2,
    MaturityStage.LEGACY: 3,
}


def _resolve_plan111_stage(score: int) -> MaturityStage:
    book_stage = derive_maturity_from_score(score)
    return MaturityStage(book_stage.value)


def _resolve_structure_tasks(stage: MaturityStage, snapshot: Plan111SnapshotInput) -> List[StructureTaskState]:
    states: List[StructureTaskState] = []
    current_order = _STAGE_ORDER.get(stage, 0)

    for blueprint in PLAN111_STRUCTURE_TASKS:
        required_stage = _blueprint_stage(blueprint)
        unlocked = current_order >= _STAGE_ORDER[required_stage]
        completed = is_plan111_task_completed(blueprint.code, snapshot)

        if not unlocked:
            status = StructureTaskStatus.LOCKED
        elif completed:
            status = StructureTaskStatus.COMPLETED
        elif current_order > _STAGE_ORDER[required_stage]:
            status = StructureTaskStatus.REGRESSED
        else:
            status = StructureTaskStatus.PENDING

        states.append(
            StructureTaskState(
                code=blueprint.code,
                title=blueprint.title,
                description=blueprint.description,
                weight=blueprint.points,
                required_stage=required_stage,
                status=status,
            )
        )

    return states


def _blueprint_stage(task: Plan111StructureTaskBlueprint) -> MaturityStage:
    try:
        return MaturityStage(task.required_stage)
    except ValueError:
        return MaturityStage.SEED
