"""Chronicle Schemas - Pydantic v2 DTO

只开放最小的写入入口：BOOK_OPENED。其它事件由内部或事件总线写入。
"""

from typing import Optional, Dict, Any, List, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime

from .domain.event_types import ChronicleEventType

if TYPE_CHECKING:  # pragma: no cover - typing assistance only
    from .domain.models import ChronicleEvent


class ChronicleBookOpenedRequest(BaseModel):
    book_id: UUID = Field(..., description="被打开的 Book ID")
    actor_id: Optional[UUID] = Field(None, description="触发者，匿名可为空")

    model_config = ConfigDict(
        json_schema_extra={"example": {"book_id": "11111111-1111-1111-1111-111111111111"}}
    )


class ChronicleEventRead(BaseModel):
    id: UUID
    event_type: ChronicleEventType
    book_id: UUID
    block_id: Optional[UUID] = None
    actor_id: Optional[UUID] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, event: "ChronicleEvent") -> "ChronicleEventRead":
        return cls(
            id=event.id,
            event_type=event.event_type,
            book_id=event.book_id,
            block_id=event.block_id,
            actor_id=event.actor_id,
            payload=event.payload or {},
            occurred_at=event.occurred_at,
            created_at=event.created_at,
        )


class ChronicleEventListResponse(BaseModel):
    items: List[ChronicleEventRead]
    total: int
    page: int
    size: int
    has_more: bool


class ChronicleRecentEventsResponse(BaseModel):
    items: List[ChronicleEventRead]
    total: int
    limit: int
