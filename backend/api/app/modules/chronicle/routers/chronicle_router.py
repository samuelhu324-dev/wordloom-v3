from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from uuid import UUID

from api.app.dependencies import get_di_container, DIContainer
from ..domain.event_types import ChronicleEventType
from ..schemas import (
    ChronicleBookOpenedRequest,
    ChronicleEventRead,
    ChronicleEventListResponse,
    ChronicleRecentEventsResponse,
)


router = APIRouter(prefix="", tags=["Chronicle"])


@router.post("/book-opened", response_model=ChronicleEventRead)
async def record_book_opened(
    req: ChronicleBookOpenedRequest,
    di: DIContainer = Depends(get_di_container),
):
    # TODO: 速率限制 & 防抖 (后续) / actor_id 来源统一化
    service = di.get_chronicle_recorder_service()
    event = await service.record_book_opened(book_id=req.book_id, actor_id=req.actor_id)
    return ChronicleEventRead.from_domain(event)


@router.get("/books/{book_id}/events", response_model=ChronicleEventListResponse)
async def list_book_events(
    book_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    event_types: Optional[List[ChronicleEventType]] = Query(None),
    di: DIContainer = Depends(get_di_container),
):
    service = di.get_chronicle_query_service()
    offset = (page - 1) * size
    items, total = await service.list_book_events(
        book_id=book_id, event_types=event_types, limit=size, offset=offset
    )
    has_more = offset + len(items) < total
    return ChronicleEventListResponse(
        items=[ChronicleEventRead.from_domain(item) for item in items],
        total=total,
        page=page,
        size=size,
        has_more=has_more,
    )


@router.get("/books/{book_id}/recent-events", response_model=ChronicleRecentEventsResponse)
async def list_recent_book_events(
    book_id: UUID,
    limit: int = Query(5, ge=1, le=25),
    di: DIContainer = Depends(get_di_container),
):
    service = di.get_chronicle_query_service()
    items, total = await service.list_recent_book_events(book_id=book_id, limit=limit)
    return ChronicleRecentEventsResponse(
        items=[ChronicleEventRead.from_domain(item) for item in items],
        total=total,
        limit=limit,
    )
