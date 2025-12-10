from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from .event_types import ChronicleEventType


@dataclass(frozen=True)
class ChronicleEvent:
    """领域事件对象 (不可变)

    设计原则：
      - occurred_at: 业务发生时间
      - created_at: 记录插入时间（默认 now，由仓储填充）
      - payload: 补充维度 (例如 bookshel_id/library_id 快照) —— 可为空
      - actor_id: 触发者 (匿名或系统操作可为空)
      - block_id: 仅在 Block 相关事件出现
    """

    id: UUID
    event_type: ChronicleEventType
    book_id: UUID
    block_id: Optional[UUID]
    actor_id: Optional[UUID]
    payload: Dict[str, Any]
    occurred_at: datetime
    created_at: Optional[datetime] = None

    @staticmethod
    def create(
        event_type: ChronicleEventType,
        book_id: UUID,
        occurred_at: Optional[datetime] = None,
        block_id: Optional[UUID] = None,
        actor_id: Optional[UUID] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> "ChronicleEvent":
        if not book_id:
            raise ValueError("ChronicleEvent requires book_id")
        return ChronicleEvent(
            id=uuid4(),
            event_type=event_type,
            book_id=book_id,
            block_id=block_id,
            actor_id=actor_id,
            payload=payload or {},
            occurred_at=occurred_at or datetime.utcnow(),
        )
