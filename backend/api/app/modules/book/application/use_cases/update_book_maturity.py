"""UpdateBookMaturityUseCase - 手动成熟度覆盖 & Legacy 切换."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from api.app.shared.events import EventBus
from api.app.modules.chronicle.application.services import ChronicleRecorderService

from ...domain import Book, BookMaturity
from ...domain.services import BookMaturityScoreResult, BookMaturityScoreService
from ...exceptions import (
    BookNotFoundError,
    BookOperationError,
    DomainException,
    InvalidBookDataError,
)
from ..models.maturity import BookMaturityMutationResult, PartitionMigrationResult
from ..ports.input import UpdateBookMaturityRequest
from ..ports.output import BookRepository
from ..utils.maturity import build_score_input, normalize_maturity, transition_book_maturity


LEGACY_INACTIVITY_DAYS = 180
LEGACY_VISIT_WINDOW_DAYS = 90
STABLE_SCORE_THRESHOLD = 70


@dataclass
class GuardContext:
    score: Optional[int]
    open_todo_count: Optional[int]
    visit_count_90d: Optional[int]
    last_content_edit_at: Optional[datetime]
    last_visited_at: Optional[datetime]
    is_pinned: bool


class UpdateBookMaturityUseCase:
    """处理手动成熟度覆盖、强制 Legacy 的 UseCase"""

    def __init__(
        self,
        repository: BookRepository,
        score_service: BookMaturityScoreService,
        event_bus: Optional[EventBus] = None,
        chronicle_service: Optional[ChronicleRecorderService] = None,
    ) -> None:
        self.repository = repository
        self.score_service = score_service
        self.event_bus = event_bus
        self.chronicle_service = chronicle_service

    async def execute(self, request: UpdateBookMaturityRequest) -> BookMaturityMutationResult:
        book = await self.repository.get_by_id(request.book_id)
        if not book:
            raise BookNotFoundError(str(request.book_id))

        try:
            guard_ctx = self._build_guard_context(book, request)
            if not request.force:
                self._validate_transition(request, guard_ctx)

            score_result = self._maybe_recalculate_score(book, request)
            score_value = self._resolve_score_value(book, request, guard_ctx, score_result)
            partition_result = self._apply_manual_transition(book, request, score_value)

            saved_book = await self.repository.save(book)
            await self._publish_events(saved_book)
            await self._record_partition_change(partition_result, request.actor_id)

            return BookMaturityMutationResult(
                book_id=request.book_id,
                maturity=self._maturity_value(saved_book),
                maturity_score=score_value,
                manual_override=bool(getattr(saved_book, "manual_maturity_override", False)),
                partition_migration=partition_result,
                score_components=score_result.components if score_result else None,
            )
        except DomainException:
            raise
        except Exception as exc:  # pragma: no cover - 防御性日志
            raise BookOperationError(f"Failed to update maturity: {exc}")

    def _build_guard_context(
        self,
        book: Book,
        request: UpdateBookMaturityRequest,
    ) -> GuardContext:
        score = self._to_int(request.maturity_score, getattr(book, "maturity_score", None))
        open_todos = self._to_int(request.open_todo_count, getattr(book, "open_todo_snapshot", None))
        visit_count = self._to_int(request.visit_count_90d, getattr(book, "visit_count_90d", None))
        last_edit = self._ensure_datetime(
            request.last_content_edit_at or getattr(book, "last_content_edit_at", getattr(book, "updated_at", None))
        )
        last_visit = self._ensure_datetime(request.last_visited_at or getattr(book, "last_visited_at", None))
        is_pinned = request.is_pinned if request.is_pinned is not None else bool(getattr(book, "is_pinned", False))

        return GuardContext(
            score=score,
            open_todo_count=open_todos,
            visit_count_90d=visit_count,
            last_content_edit_at=last_edit,
            last_visited_at=last_visit,
            is_pinned=is_pinned,
        )

    def _validate_transition(
        self,
        request: UpdateBookMaturityRequest,
        context: GuardContext,
    ) -> None:
        target = normalize_maturity(request.target_maturity)

        if target == BookMaturity.STABLE:
            self._assert_stable_guards(context)
        if target == BookMaturity.LEGACY:
            self._assert_legacy_guards(context)

    def _assert_stable_guards(self, context: GuardContext) -> None:
        if context.score is None:
            raise InvalidBookDataError("Stable maturity requires latest maturity_score snapshot")
        if context.score < STABLE_SCORE_THRESHOLD:
            raise InvalidBookDataError(
                f"Stable maturity requires maturity_score ≥ {STABLE_SCORE_THRESHOLD} (current={context.score})"
            )
        if context.open_todo_count is None:
            raise InvalidBookDataError("Stable maturity requires TODO snapshot")
        if context.open_todo_count > 0:
            raise InvalidBookDataError("Clear all open TODO items before promoting to Stable")

    def _assert_legacy_guards(self, context: GuardContext) -> None:
        if context.visit_count_90d is None:
            raise InvalidBookDataError("Legacy promotion requires visit_count_90d snapshot")
        if context.visit_count_90d > 0:
            raise InvalidBookDataError("Legacy promotion requires 90 consecutive days with zero visits")
        if context.is_pinned:
            raise InvalidBookDataError("Unpin the book before moving it to Legacy")

        now = datetime.now(timezone.utc)
        if not context.last_content_edit_at:
            raise InvalidBookDataError("Legacy promotion requires last edit timestamp")
        if now - context.last_content_edit_at < timedelta(days=LEGACY_INACTIVITY_DAYS):
            raise InvalidBookDataError(
                f"Legacy promotion requires {LEGACY_INACTIVITY_DAYS} days without edits"
            )
        if context.last_visited_at and now - context.last_visited_at < timedelta(days=LEGACY_VISIT_WINDOW_DAYS):
            raise InvalidBookDataError(
                f"Legacy promotion requires {LEGACY_VISIT_WINDOW_DAYS} days without visits"
            )

    def _maybe_recalculate_score(
        self,
        book: Book,
        request: UpdateBookMaturityRequest,
    ) -> Optional[BookMaturityScoreResult]:
        if not self._has_score_payload(request):
            return None

        score_input = build_score_input(
            book,
            tag_count=request.tag_count,
            block_type_count=request.block_type_count,
            block_count=request.block_count,
            open_todo_count=request.open_todo_count,
            operations_bonus=request.operations_bonus,
            cover_icon=request.cover_icon,
            visit_count_90d=request.visit_count_90d,
            last_content_edit_at=request.last_content_edit_at,
        )
        return self.score_service.calculate(score_input)

    def _resolve_score_value(
        self,
        book: Book,
        request: UpdateBookMaturityRequest,
        context: GuardContext,
        score_result: Optional[BookMaturityScoreResult],
    ) -> int:
        if score_result:
            value = score_result.score
        elif request.maturity_score is not None:
            value = int(request.maturity_score)
        elif context.score is not None:
            value = context.score
        else:
            value = int(getattr(book, "maturity_score", 0) or 0)

        setattr(book, "maturity_score", value)
        return value

    def _apply_manual_transition(
        self,
        book: Book,
        request: UpdateBookMaturityRequest,
        score_value: int,
    ) -> Optional[PartitionMigrationResult]:
        target = normalize_maturity(request.target_maturity)
        current = normalize_maturity(getattr(book, "maturity", BookMaturity.SEED))

        manual_override = target != BookMaturity.LEGACY
        setattr(book, "legacy_flag", target == BookMaturity.LEGACY)
        setattr(book, "manual_maturity_override", manual_override)
        setattr(book, "manual_maturity_reason", request.override_reason)

        if target == current:
            return None

        previous, _ = transition_book_maturity(book, target)
        trigger = request.override_reason or request.trigger or "manual_override"
        return self._build_partition_result(
            book=book,
            from_maturity=previous,
            to_maturity=target,
            score=score_value,
            trigger=trigger,
            manual_override=manual_override,
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

    def _to_int(self, *candidates: Optional[int]) -> Optional[int]:
        for value in candidates:
            if value is None:
                continue
            return int(value)
        return None

    def _ensure_datetime(self, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value)
            except ValueError:
                return None
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        return None

    def _has_score_payload(self, request: UpdateBookMaturityRequest) -> bool:
        return any(
            value is not None
            for value in (
                request.tag_count,
                request.block_type_count,
                request.block_count,
                request.open_todo_count,
                request.operations_bonus,
                request.cover_icon,
            )
        )
