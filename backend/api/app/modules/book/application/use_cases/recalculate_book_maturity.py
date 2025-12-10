"""RecalculateBookMaturityUseCase - 自动成熟度重算入口.

职责:
- 根据最新快照计算 maturity_score 与 components
- 在未被手动锁定且未处于 Legacy 时，根据 score 派生 maturity
- 如果 maturity 发生变化，输出 PartitionMigrationResult 并写入 Chronicle
- 持久化 Book 聚合并广播领域事件
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from api.app.shared.events import EventBus
from api.app.modules.chronicle.application.services import ChronicleRecorderService

from ...domain import Book, BookMaturity
from ...domain.services import ScoreComponent as BookScoreComponent
from ..models.maturity import BookMaturityMutationResult, PartitionMigrationResult
from ..ports.input import RecalculateBookMaturityRequest
from ..ports.output import BookRepository
from ...exceptions import (
    BookNotFoundError,
    BookOperationError,
    DomainException,
)
from ..utils.maturity import (
    normalize_maturity,
    transition_book_maturity,
)
from api.app.modules.maturity.application.dtos import CalculateBookMaturityCommand
from api.app.modules.maturity.application.ports import MaturitySnapshotRepository
from api.app.modules.maturity.application.use_cases import CalculateBookMaturityUseCase
from api.app.modules.maturity.domain import (
    MaturityStage,
    MaturitySnapshot,
    StructureTaskStatus,
)
from api.app.modules.maturity.exceptions import BookMaturitySourceNotFound


class RecalculateBookMaturityUseCase:
    """自动触发的成熟度重算用例"""

    def __init__(
        self,
        repository: BookRepository,
        maturity_calculator: CalculateBookMaturityUseCase,
        event_bus: Optional[EventBus] = None,
        chronicle_service: Optional[ChronicleRecorderService] = None,
        snapshot_repository: Optional[MaturitySnapshotRepository] = None,
    ) -> None:
        self.repository = repository
        self.maturity_calculator = maturity_calculator
        self.event_bus = event_bus
        self.chronicle_service = chronicle_service
        self.snapshot_repository = snapshot_repository

    async def execute(self, request: RecalculateBookMaturityRequest) -> BookMaturityMutationResult:
        book = await self.repository.get_by_id(request.book_id)
        if not book:
            raise BookNotFoundError(str(request.book_id))

        previous_snapshot = await self._load_previous_snapshot(request.book_id)
        previous_score_value = int(getattr(book, "maturity_score", 0) or 0)
        trigger = request.trigger or "recalculate"

        try:
            snapshot = await self._evaluate_snapshot(request)
            setattr(book, "maturity_score", snapshot.score.value)
            partition_result = self._maybe_transition_maturity(book, snapshot.stage, snapshot.score.value, request)

            saved_book = await self.repository.save(book)
            await self._publish_events(saved_book)
            await self._record_partition_change(partition_result, request.actor_id)
            await self._record_maturity_recomputed(
                previous_snapshot=previous_snapshot,
                previous_score=previous_score_value,
                new_snapshot=snapshot,
                trigger=trigger,
                actor_id=request.actor_id,
            )
            await self._record_structure_task_events(
                previous_snapshot=previous_snapshot,
                new_snapshot=snapshot,
                trigger=trigger,
                actor_id=request.actor_id,
            )

            return BookMaturityMutationResult(
                book_id=request.book_id,
                maturity=self._maturity_value(saved_book),
                maturity_score=snapshot.score.value,
                manual_override=bool(getattr(saved_book, "manual_maturity_override", False)),
                partition_migration=partition_result,
                score_components=self._to_book_components(snapshot.score.components),
            )
        except BookMaturitySourceNotFound as error:
            raise BookNotFoundError(str(error.book_id)) from error
        except DomainException:
            raise
        except Exception as exc:  # pragma: no cover - 防御性日志
            raise BookOperationError(f"Failed to recalculate maturity: {exc}")

    async def _evaluate_snapshot(self, request: RecalculateBookMaturityRequest):
        command = CalculateBookMaturityCommand(
            book_id=request.book_id,
            persist_snapshot=True,
            tag_count=request.tag_count,
            block_type_count=request.block_type_count,
            block_count=request.block_count,
            open_todo_count=request.open_todo_count,
            operations_bonus=request.operations_bonus,
            cover_icon=request.cover_icon,
        )
        result = await self.maturity_calculator.execute(command)
        return result.snapshot

    def _maybe_transition_maturity(
        self,
        book: Book,
        stage: MaturityStage,
        score_value: int,
        request: RecalculateBookMaturityRequest,
    ) -> Optional[PartitionMigrationResult]:
        legacy_flag = bool(getattr(book, "legacy_flag", False))
        manual_override = bool(getattr(book, "manual_maturity_override", False))
        current = normalize_maturity(getattr(book, "maturity", BookMaturity.SEED))

        if legacy_flag:
            if current == BookMaturity.LEGACY:
                return None
            previous, _ = transition_book_maturity(book, BookMaturity.LEGACY)
            return self._build_partition_result(
                book=book,
                from_maturity=previous,
                to_maturity=BookMaturity.LEGACY,
                score=score_value,
                trigger=request.trigger or "recalculate",
                manual_override=False,
            )

        if manual_override:
            return None

        target = BookMaturity(stage.value)
        if target == current:
            return None

        previous, _ = transition_book_maturity(book, target)
        setattr(book, "manual_maturity_override", False)
        setattr(book, "manual_maturity_reason", None)
        return self._build_partition_result(
            book=book,
            from_maturity=previous,
            to_maturity=target,
            score=score_value,
            trigger=request.trigger or "recalculate",
            manual_override=False,
        )

    async def _record_partition_change(
        self,
        partition_result: Optional[PartitionMigrationResult],
        actor_id: Optional[UUID],
    ) -> None:
        if not partition_result or not self.chronicle_service:
            return

        await self.chronicle_service.record_book_stage_changed(
            book_id=partition_result.book_id,
            from_stage=partition_result.from_maturity,
            to_stage=partition_result.to_maturity,
            score=partition_result.score,
            trigger=partition_result.trigger,
            manual_override=partition_result.is_manual_override,
            actor_id=actor_id,
            occurred_at=partition_result.occurred_at,
        )

    async def _publish_events(self, book: Book) -> None:
        if not self.event_bus:
            return

        events = getattr(book, "get_events", lambda: [])()
        for event in events:
            await self.event_bus.publish(event)

        clear = getattr(book, "clear_events", None)
        if callable(clear):
            clear()

    async def _record_maturity_recomputed(
        self,
        previous_snapshot: Optional[MaturitySnapshot],
        previous_score: int,
        new_snapshot: MaturitySnapshot,
        trigger: str,
        actor_id: Optional[UUID],
    ) -> None:
        if not self.chronicle_service:
            return

        baseline = previous_snapshot.score.value if previous_snapshot else previous_score
        initial_run = previous_snapshot is None and self.snapshot_repository is not None
        await self.chronicle_service.record_book_maturity_recomputed(
            book_id=new_snapshot.book_id,
            previous_score=baseline,
            new_score=new_snapshot.score.value,
            stage=new_snapshot.stage.value,
            trigger=trigger,
            actor_id=actor_id,
            occurred_at=new_snapshot.created_at,
            initial=initial_run,
        )

    async def _record_structure_task_events(
        self,
        previous_snapshot: Optional[MaturitySnapshot],
        new_snapshot: MaturitySnapshot,
        trigger: str,
        actor_id: Optional[UUID],
    ) -> None:
        if not self.chronicle_service or not previous_snapshot:
            return

        previous_states = {task.code: task for task in previous_snapshot.tasks}

        for task in new_snapshot.tasks:
            previous_state = previous_states.get(task.code)
            previous_status = getattr(previous_state, "status", None)

            if task.status == StructureTaskStatus.COMPLETED and previous_status != StructureTaskStatus.COMPLETED:
                await self.chronicle_service.record_structure_task_completed(
                    book_id=new_snapshot.book_id,
                    task_code=task.code,
                    title=task.title,
                    points=task.weight,
                    stage=new_snapshot.stage.value,
                    trigger=trigger,
                    actor_id=actor_id,
                    occurred_at=new_snapshot.created_at,
                )
            elif (
                task.status == StructureTaskStatus.REGRESSED
                and previous_status == StructureTaskStatus.COMPLETED
            ):
                await self.chronicle_service.record_structure_task_regressed(
                    book_id=new_snapshot.book_id,
                    task_code=task.code,
                    title=task.title,
                    points=task.weight,
                    stage=new_snapshot.stage.value,
                    trigger=trigger,
                    actor_id=actor_id,
                    occurred_at=new_snapshot.created_at,
                )

    async def _load_previous_snapshot(self, book_id: UUID) -> Optional[MaturitySnapshot]:
        if not self.snapshot_repository:
            return None
        return await self.snapshot_repository.get_latest_snapshot(book_id)

    def _build_partition_result(
        self,
        book: Book,
        from_maturity: BookMaturity,
        to_maturity: BookMaturity,
        score: int,
        trigger: str,
        manual_override: bool,
    ) -> PartitionMigrationResult:
        occurred_at = getattr(book, "updated_at", None) or datetime.now(timezone.utc)
        return PartitionMigrationResult(
            book_id=book.id,
            from_maturity=from_maturity.value,
            to_maturity=to_maturity.value,
            score=score,
            trigger=trigger,
            is_manual_override=manual_override,
            occurred_at=occurred_at,
        )

    def _maturity_value(self, book: Book) -> str:
        maturity = getattr(book, "maturity", BookMaturity.SEED)
        if isinstance(maturity, BookMaturity):
            return maturity.value
        return str(maturity)

    def _to_book_components(self, components: list) -> List[BookScoreComponent]:
        converted: List[BookScoreComponent] = []
        for component in components or []:
            if isinstance(component, BookScoreComponent):
                converted.append(component)
            else:
                converted.append(
                    BookScoreComponent(
                        factor=getattr(component, "factor", "unknown"),
                        points=int(getattr(component, "points", 0) or 0),
                        detail=getattr(component, "detail", ""),
                    )
                )
        return converted
