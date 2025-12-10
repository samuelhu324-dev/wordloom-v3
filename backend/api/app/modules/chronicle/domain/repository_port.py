from __future__ import annotations

from datetime import datetime
from typing import Protocol, Optional, Sequence, Tuple, List
from uuid import UUID

from .models import ChronicleEvent
from .event_types import ChronicleEventType


class ChronicleRepositoryPort(Protocol):
    """仓储端口 (Hexagonal Port)

    全部使用 async 接口以兼容 AsyncSession。
    """

    async def save(self, event: ChronicleEvent) -> ChronicleEvent: ...

    async def list_by_book(
        self,
        book_id: UUID,
        event_types: Optional[Sequence[ChronicleEventType]] = None,
        limit: int = 50,
        offset: int = 0,
        order_desc: bool = True,
    ) -> Tuple[List[ChronicleEvent], int]: ...

    async def list_by_time_range(
        self,
        start: datetime,
        end: datetime,
        event_types: Optional[Sequence[ChronicleEventType]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[ChronicleEvent], int]: ...
