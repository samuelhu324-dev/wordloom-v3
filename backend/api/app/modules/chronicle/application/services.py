from __future__ import annotations
from typing import Sequence, Optional, Tuple, List, Dict, Any
from uuid import UUID
from datetime import datetime

from ..domain import ChronicleEventType, ChronicleEvent, ChronicleRepositoryPort
from api.app.shared.request_context import get_request_context


RECENT_EVENT_TYPES: Tuple[ChronicleEventType, ...] = (
    ChronicleEventType.BOOK_CREATED,
    ChronicleEventType.BOOK_SOFT_DELETED,
    ChronicleEventType.BOOK_RESTORED,
    ChronicleEventType.BOOK_STAGE_CHANGED,
    ChronicleEventType.BOOK_MATURITY_RECOMPUTED,
    ChronicleEventType.STRUCTURE_TASK_COMPLETED,
    ChronicleEventType.STRUCTURE_TASK_REGRESSED,
    ChronicleEventType.COVER_CHANGED,
    ChronicleEventType.COVER_COLOR_CHANGED,
    ChronicleEventType.CONTENT_SNAPSHOT_TAKEN,
    ChronicleEventType.WORDCOUNT_MILESTONE_REACHED,
    ChronicleEventType.TODO_PROMOTED_FROM_BLOCK,
    ChronicleEventType.TODO_COMPLETED,
)


class ChronicleRecorderService:
    """记录事件的应用服务

    仅封装创建与保存逻辑；不做去重与速率限制（后续迭代）。
    """

    def __init__(self, repo: ChronicleRepositoryPort):
        self._repo = repo

    async def record_event(
        self,
        *,
        book_id: UUID,
        event_type: ChronicleEventType,
        payload: Optional[Dict[str, Any]] = None,
        actor_id: Optional[UUID] = None,
        block_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
    ) -> ChronicleEvent:
        """Low-level helper to persist a Chronicle event."""

        ctx = get_request_context()
        if actor_id is None and ctx and ctx.actor_id:
            actor_id = ctx.actor_id

        # Build payload with durable envelope fields.
        # Keep these stable even if Timeline/scoring rules evolve.
        final_payload: Dict[str, Any] = dict(payload or {})
        final_payload.setdefault("schema_version", 1)
        final_payload.setdefault("provenance", "live")

        if ctx and ctx.correlation_id:
            final_payload.setdefault("correlation_id", ctx.correlation_id)
            final_payload.setdefault("source", "api")
            if ctx.route or ctx.method:
                http_ctx = dict(final_payload.get("http") or {})
                if ctx.route:
                    http_ctx.setdefault("route", ctx.route)
                if ctx.method:
                    http_ctx.setdefault("method", ctx.method)
                if http_ctx:
                    final_payload["http"] = http_ctx
        else:
            final_payload.setdefault("source", "unknown")

        if actor_id is not None:
            final_payload.setdefault("actor_kind", "user")
        else:
            final_payload.setdefault("actor_kind", "unknown")

        event = ChronicleEvent.create(
            event_type=event_type,
            book_id=book_id,
            actor_id=actor_id,
            block_id=block_id,
            payload=final_payload,
            occurred_at=occurred_at,
        )
        await self._repo.save(event)
        return event

    async def record_book_opened(self, book_id: UUID, actor_id: Optional[UUID] = None) -> ChronicleEvent:
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.BOOK_OPENED,
            actor_id=actor_id,
        )

    async def record_book_viewed(
        self,
        *,
        book_id: UUID,
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
        source: Optional[str] = None,
    ) -> ChronicleEvent:
        # Avoid colliding with durable envelope field `source`.
        payload = {"view_source": source} if source else None
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.BOOK_VIEWED,
            actor_id=actor_id,
            occurred_at=occurred_at,
            payload=payload,
        )

    async def record_book_created(
        self,
        book_id: UUID,
        bookshelf_id: UUID,
        occurred_at: Optional[datetime] = None,
        actor_id: Optional[UUID] = None,
    ) -> ChronicleEvent:
        payload = {"bookshelf_id": str(bookshelf_id)}
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.BOOK_CREATED,
            actor_id=actor_id,
            occurred_at=occurred_at,
            payload=payload,
        )

    async def record_book_renamed(
        self,
        *,
        book_id: UUID,
        from_title: str,
        to_title: str,
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
    ) -> ChronicleEvent:
        payload = {"from": from_title, "to": to_title}
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.BOOK_RENAMED,
            actor_id=actor_id,
            occurred_at=occurred_at,
            payload=payload,
        )

    async def record_book_updated(
        self,
        *,
        book_id: UUID,
        fields: Dict[str, Any],
        trigger: Optional[str] = None,
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
    ) -> ChronicleEvent:
        payload: Dict[str, Any] = {"fields": dict(fields)}
        if trigger:
            payload["trigger"] = trigger
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.BOOK_UPDATED,
            actor_id=actor_id,
            occurred_at=occurred_at,
            payload=payload,
        )

    async def record_block_created(
        self,
        *,
        book_id: UUID,
        block_id: UUID,
        block_type: Optional[str] = None,
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
    ) -> ChronicleEvent:
        payload: Dict[str, Any] = {}
        if block_type:
            payload["block_type"] = str(block_type)
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.BLOCK_CREATED,
            actor_id=actor_id,
            block_id=block_id,
            occurred_at=occurred_at,
            payload=payload,
        )

    async def record_block_updated(
        self,
        *,
        book_id: UUID,
        block_id: UUID,
        fields: Dict[str, Any],
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
    ) -> ChronicleEvent:
        payload: Dict[str, Any] = {"fields": dict(fields)}
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.BLOCK_UPDATED,
            actor_id=actor_id,
            block_id=block_id,
            occurred_at=occurred_at,
            payload=payload,
        )

    async def record_block_soft_deleted(
        self,
        *,
        book_id: UUID,
        block_id: UUID,
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
    ) -> ChronicleEvent:
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.BLOCK_SOFT_DELETED,
            actor_id=actor_id,
            block_id=block_id,
            occurred_at=occurred_at,
            payload={},
        )

    async def record_block_restored(
        self,
        *,
        book_id: UUID,
        block_id: UUID,
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
    ) -> ChronicleEvent:
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.BLOCK_RESTORED,
            actor_id=actor_id,
            block_id=block_id,
            occurred_at=occurred_at,
            payload={},
        )

    async def record_block_type_changed(
        self,
        *,
        book_id: UUID,
        block_id: UUID,
        from_type: Optional[str] = None,
        to_type: Optional[str] = None,
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
    ) -> ChronicleEvent:
        payload: Dict[str, Any] = {
            "from": str(from_type) if from_type is not None else None,
            "to": str(to_type) if to_type is not None else None,
        }
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.BLOCK_TYPE_CHANGED,
            actor_id=actor_id,
            block_id=block_id,
            occurred_at=occurred_at,
            payload=payload,
        )

    async def record_tag_added_to_book(
        self,
        *,
        book_id: UUID,
        tag_id: UUID,
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
    ) -> ChronicleEvent:
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.TAG_ADDED_TO_BOOK,
            actor_id=actor_id,
            occurred_at=occurred_at,
            payload={"tag_id": str(tag_id)},
        )

    async def record_tag_removed_from_book(
        self,
        *,
        book_id: UUID,
        tag_id: UUID,
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
    ) -> ChronicleEvent:
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.TAG_REMOVED_FROM_BOOK,
            actor_id=actor_id,
            occurred_at=occurred_at,
            payload={"tag_id": str(tag_id)},
        )

    async def record_book_moved(
        self,
        book_id: UUID,
        from_bookshelf_id: UUID,
        to_bookshelf_id: UUID,
        moved_at: Optional[datetime] = None,
        actor_id: Optional[UUID] = None,
    ) -> ChronicleEvent:
        payload = {
            "from_bookshelf_id": str(from_bookshelf_id),
            "to_bookshelf_id": str(to_bookshelf_id),
        }
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.BOOK_MOVED,
            actor_id=actor_id,
            occurred_at=moved_at,
            payload=payload,
        )

    async def record_book_soft_deleted(
        self,
        *,
        book_id: UUID,
        from_bookshelf_id: UUID,
        basement_bookshelf_id: UUID,
        deleted_at: Optional[datetime] = None,
        actor_id: Optional[UUID] = None,
        trigger: Optional[str] = None,
    ) -> ChronicleEvent:
        payload = {
            "from_bookshelf_id": str(from_bookshelf_id),
            "basement_bookshelf_id": str(basement_bookshelf_id),
            "trigger": trigger,
        }
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.BOOK_SOFT_DELETED,
            actor_id=actor_id,
            occurred_at=deleted_at,
            payload=payload,
        )

    async def record_book_moved_to_basement(
        self,
        book_id: UUID,
        from_bookshelf_id: UUID,
        basement_bookshelf_id: UUID,
        deleted_at: Optional[datetime] = None,
        actor_id: Optional[UUID] = None,
    ) -> ChronicleEvent:
        """Legacy alias for handlers still using old method name."""

        return await self.record_book_soft_deleted(
            book_id=book_id,
            from_bookshelf_id=from_bookshelf_id,
            basement_bookshelf_id=basement_bookshelf_id,
            deleted_at=deleted_at,
            actor_id=actor_id,
        )

    async def record_book_restored(
        self,
        book_id: UUID,
        from_basement_id: UUID,
        restored_to_bookshelf_id: UUID,
        restored_at: Optional[datetime] = None,
        actor_id: Optional[UUID] = None,
    ) -> ChronicleEvent:
        payload = {
            "basement_bookshelf_id": str(from_basement_id),
            "restored_to_bookshelf_id": str(restored_to_bookshelf_id),
        }
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.BOOK_RESTORED,
            actor_id=actor_id,
            occurred_at=restored_at,
            payload=payload,
        )

    async def record_book_deleted(
        self,
        book_id: UUID,
        bookshelf_id: UUID,
        occurred_at: Optional[datetime] = None,
        actor_id: Optional[UUID] = None,
    ) -> ChronicleEvent:
        payload = {"bookshelf_id": str(bookshelf_id)}
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.BOOK_DELETED,
            actor_id=actor_id,
            occurred_at=occurred_at,
            payload=payload,
        )

    async def record_book_stage_changed(
        self,
        book_id: UUID,
        from_stage: str,
        to_stage: str,
        score: int,
        trigger: str,
        manual_override: bool,
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
    ) -> ChronicleEvent:
        payload = {
            "from": from_stage,
            "to": to_stage,
            "score": score,
            "trigger": trigger,
            "manual_override": manual_override,
        }
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.BOOK_STAGE_CHANGED,
            actor_id=actor_id,
            occurred_at=occurred_at,
            payload=payload,
        )

    async def record_book_maturity_recomputed(
        self,
        book_id: UUID,
        previous_score: Optional[int],
        new_score: int,
        stage: str,
        trigger: str,
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
        initial: bool = False,
    ) -> ChronicleEvent:
        baseline = previous_score if previous_score is not None else 0
        payload = {
            "previous_score": previous_score,
            "new_score": new_score,
            "delta": (new_score or 0) - baseline,
            "stage": stage,
            "trigger": trigger,
            "initial": initial,
        }
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.BOOK_MATURITY_RECOMPUTED,
            actor_id=actor_id,
            occurred_at=occurred_at,
            payload=payload,
        )

    async def record_structure_task_completed(
        self,
        book_id: UUID,
        task_code: str,
        title: str,
        points: int,
        stage: str,
        trigger: str,
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
    ) -> ChronicleEvent:
        payload = {
            "task_id": task_code,
            "title": title,
            "points": points,
            "stage": stage,
            "trigger": trigger,
        }
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.STRUCTURE_TASK_COMPLETED,
            actor_id=actor_id,
            occurred_at=occurred_at,
            payload=payload,
        )

    async def record_structure_task_regressed(
        self,
        book_id: UUID,
        task_code: str,
        title: str,
        points: int,
        stage: str,
        trigger: str,
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
    ) -> ChronicleEvent:
        payload = {
            "task_id": task_code,
            "title": title,
            "points": -abs(points),
            "stage": stage,
            "trigger": trigger,
        }
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.STRUCTURE_TASK_REGRESSED,
            actor_id=actor_id,
            occurred_at=occurred_at,
            payload=payload,
        )

    async def record_block_status_changed(
        self,
        book_id: UUID,
        block_id: UUID,
        old_status: str,
        new_status: str,
        actor_id: Optional[UUID] = None,
    ) -> ChronicleEvent:
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.BLOCK_STATUS_CHANGED,
            actor_id=actor_id,
            block_id=block_id,
            payload={"old_status": old_status, "new_status": new_status},
        )

    async def record_cover_changed(
        self,
        *,
        book_id: UUID,
        from_icon: Optional[str] = None,
        to_icon: Optional[str] = None,
        media_id: Optional[UUID] = None,
        trigger: Optional[str] = None,
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
    ) -> ChronicleEvent:
        payload = {
            "from_icon": from_icon,
            "to_icon": to_icon,
            "media_id": str(media_id) if media_id else None,
            "trigger": trigger,
        }
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.COVER_CHANGED,
            actor_id=actor_id,
            occurred_at=occurred_at,
            payload=payload,
        )

    async def record_cover_color_changed(
        self,
        *,
        book_id: UUID,
        from_color: Optional[str] = None,
        to_color: Optional[str] = None,
        palette: Optional[Sequence[str]] = None,
        trigger: Optional[str] = None,
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
    ) -> ChronicleEvent:
        payload = {
            "from_color": from_color,
            "to_color": to_color,
            "palette": list(palette) if palette else None,
            "trigger": trigger,
        }
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.COVER_COLOR_CHANGED,
            actor_id=actor_id,
            occurred_at=occurred_at,
            payload=payload,
        )

    async def record_content_snapshot_taken(
        self,
        *,
        book_id: UUID,
        block_count: int,
        block_type_counts: Optional[Dict[str, int]] = None,
        total_word_count: Optional[int] = None,
        trigger: Optional[str] = None,
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
    ) -> ChronicleEvent:
        type_counts = {
            str(block_type): int(count)
            for block_type, count in (block_type_counts or {}).items()
        }
        payload: Dict[str, Any] = {
            "block_count": int(block_count),
            "block_type_counts": type_counts,
            "total_word_count": total_word_count,
            "trigger": trigger,
        }
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.CONTENT_SNAPSHOT_TAKEN,
            actor_id=actor_id,
            occurred_at=occurred_at,
            payload=payload,
        )

    async def record_wordcount_milestone_reached(
        self,
        *,
        book_id: UUID,
        milestone: int,
        total_word_count: int,
        previous_word_count: Optional[int] = None,
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
    ) -> ChronicleEvent:
        payload = {
            "milestone": int(milestone),
            "total_word_count": int(total_word_count),
            "previous_word_count": previous_word_count,
        }
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.WORDCOUNT_MILESTONE_REACHED,
            actor_id=actor_id,
            occurred_at=occurred_at,
            payload=payload,
        )

    async def record_todo_promoted_from_block(
        self,
        *,
        book_id: UUID,
        block_id: Optional[UUID],
        todo_id: Optional[str],
        text: Optional[str],
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
        is_urgent: Optional[bool] = None,
    ) -> ChronicleEvent:
        payload = {
            "block_id": str(block_id) if block_id else None,
            "todo_id": todo_id,
            "text": text,
            "is_urgent": is_urgent,
        }
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.TODO_PROMOTED_FROM_BLOCK,
            actor_id=actor_id,
            block_id=block_id,
            occurred_at=occurred_at,
            payload=payload,
        )

    async def record_todo_completed(
        self,
        *,
        book_id: UUID,
        block_id: Optional[UUID],
        todo_id: Optional[str],
        text: Optional[str],
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
        promoted: Optional[bool] = None,
    ) -> ChronicleEvent:
        payload = {
            "block_id": str(block_id) if block_id else None,
            "todo_id": todo_id,
            "text": text,
            "promoted": promoted,
        }
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.TODO_COMPLETED,
            actor_id=actor_id,
            block_id=block_id,
            occurred_at=occurred_at,
            payload=payload,
        )

    async def record_work_session_summary(
        self,
        *,
        book_id: UUID,
        duration_seconds: int,
        blocks_touched: Optional[int] = None,
        word_delta: Optional[int] = None,
        actor_id: Optional[UUID] = None,
        occurred_at: Optional[datetime] = None,
    ) -> ChronicleEvent:
        payload = {
            "duration_seconds": int(duration_seconds),
            "blocks_touched": blocks_touched,
            "word_delta": word_delta,
        }
        return await self.record_event(
            book_id=book_id,
            event_type=ChronicleEventType.WORK_SESSION_SUMMARY,
            actor_id=actor_id,
            occurred_at=occurred_at,
            payload=payload,
        )


class ChronicleQueryService:
    """查询事件的应用服务 (读侧简单分页)"""

    def __init__(self, repo: ChronicleRepositoryPort):
        self._repo = repo

    async def list_book_events(
        self,
        book_id: UUID,
        event_types: Optional[Sequence[ChronicleEventType]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ChronicleEvent], int]:
        return await self._repo.list_by_book(
            book_id=book_id,
            event_types=event_types,
            limit=limit,
            offset=offset,
        )

    async def list_recent_book_events(
        self,
        book_id: UUID,
        limit: int = 5,
    ) -> Tuple[List[ChronicleEvent], int]:
        return await self._repo.list_by_book(
            book_id=book_id,
            event_types=RECENT_EVENT_TYPES,
            limit=limit,
            offset=0,
        )
