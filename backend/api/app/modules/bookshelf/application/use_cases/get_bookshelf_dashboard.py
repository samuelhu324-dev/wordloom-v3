"""GetBookshelfDashboard UseCase

聚合 Library 下书架的运营面板数据：
- 书籍成熟度统计
- Chronicle 活跃度（近 7 天编辑/浏览数、最近活动时间）
- 衍生健康度标签

该 UseCase 直接使用 AsyncSession 执行聚合查询，返回应用层可用的
BookshelfDashboardItem 列表，供路由层序列化为 API 输出。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import locale

try:
    locale.setlocale(locale.LC_COLLATE, "zh_CN.UTF-8")
except locale.Error:
    # Fallback to default locale if zh_CN is unavailable
    locale.setlocale(locale.LC_COLLATE, "")

from sqlalchemy import and_, case, func, select
from sqlalchemy.sql import Select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.modules.bookshelf.application.ports.input import (
    BookshelfDashboardFilter,
    BookshelfDashboardRequest,
    BookshelfDashboardSort,
)
from api.app.modules.bookshelf.exceptions import (
    BookshelfForbiddenError,
    BookshelfLibraryAssociationError,
    BookshelfOperationError,
)
from api.app.modules.bookshelf.domain import BookshelfStatus
from api.app.modules.library.application.ports.output import ILibraryRepository
from infra.database.models.book_models import BookModel
from infra.database.models.bookshelf_models import BookshelfModel
from infra.database.models.library_models import LibraryModel
from infra.database.models.chronicle_models import ChronicleEventModel
from infra.database.models.tag_models import (
    TagAssociationModel,
    TagModel,
    EntityType as TagEntityType,
)


@dataclass
class BookshelfBookCounts:
    total: int = 0
    seed: int = 0
    growing: int = 0
    stable: int = 0
    legacy: int = 0


@dataclass
class BookshelfHealthCounts:
    active: int = 0
    slowing: int = 0
    cooling: int = 0
    archived: int = 0


@dataclass
class BookshelfDashboardSnapshot:
    total: int = 0
    pinned: int = 0
    health_counts: BookshelfHealthCounts = field(default_factory=BookshelfHealthCounts)


@dataclass
class BookshelfTagSnapshot:
    id: UUID
    name: str
    color: str
    description: Optional[str]


@dataclass
class BookshelfDashboardItem:
    id: UUID
    library_id: UUID
    name: str
    description: Optional[str]
    status: str
    is_pinned: bool
    is_archived: bool
    is_basement: bool
    created_at: datetime
    updated_at: datetime
    book_counts: BookshelfBookCounts
    edits_last_7d: int
    views_last_7d: int
    last_activity_at: Optional[datetime]
    health: str
    theme_color: Optional[str] = None
    cover_media_id: Optional[UUID] = None
    tag_ids: List[UUID] = field(default_factory=list)
    tag_names: List[str] = field(default_factory=list)
    tags: List[BookshelfTagSnapshot] = field(default_factory=list)


@dataclass
class BookshelfDashboardResult:
    items: List[BookshelfDashboardItem]
    total: int
    snapshot: BookshelfDashboardSnapshot


class GetBookshelfDashboardUseCase:
    """返回 Bookshelf 运营面板数据"""

    HEALTH_ACTIVE_THRESHOLD_DAYS = 7
    HEALTH_SLOWING_THRESHOLD_DAYS = 21
    HEALTH_COOLING_THRESHOLD_DAYS = 60

    def __init__(
        self,
        session: AsyncSession,
        *,
        library_repository: ILibraryRepository | None = None,
    ):
        self.session = session
        self.library_repository = library_repository

    async def execute(self, request: BookshelfDashboardRequest) -> BookshelfDashboardResult:
        await self._enforce_library_owner(request)

        # 1. 拉取基础书架列表（排除 Basement / Deleted）
        shelves = await self._fetch_bookshelves(request.library_id)
        if not shelves:
            return BookshelfDashboardResult(
                items=[],
                total=0,
                snapshot=BookshelfDashboardSnapshot(),
            )

        shelf_ids = [model.id for model, _ in shelves]

        # 2. 统计书籍成熟度
        counts_by_shelf = await self._fetch_book_counts(shelf_ids)

        # 3. 统计 Chronicle 活跃度
        chronicle_stats = await self._fetch_chronicle_stats(
            request.library_id,
            shelf_ids,
        )

        # 4. 拉取标签快照
        tag_snapshots_by_shelf = await self._fetch_tag_snapshots(shelf_ids)

        now = datetime.now(timezone.utc)
        items: List[BookshelfDashboardItem] = []
        pinned_total = 0
        health_totals = {
            "active": 0,
            "slowing": 0,
            "cooling": 0,
            "archived": 0,
        }
        for model, library_cover_media_id in shelves:
            counts = counts_by_shelf.get(model.id, BookshelfBookCounts())
            stats = chronicle_stats.get(model.id, {})
            last_activity_at = self._ensure_timezone_aware(stats.get("last_activity_at"))
            edits_last_7d = int(stats.get("edits_last_7d", 0) or 0)
            views_last_7d = int(stats.get("views_last_7d", 0) or 0)
            created_at = self._ensure_timezone_aware(model.created_at)
            updated_at = self._ensure_timezone_aware(model.updated_at)
            health = self._compute_health(model.status, last_activity_at, now)
            effective_cover_media_id = library_cover_media_id
            tag_snapshots = tag_snapshots_by_shelf.get(model.id, [])
            tag_ids = [snapshot.id for snapshot in tag_snapshots]
            tag_names = [snapshot.name for snapshot in tag_snapshots]

            if model.is_pinned:
                pinned_total += 1
            if health not in health_totals:
                health_totals[health] = 0
            health_totals[health] += 1

            items.append(
                BookshelfDashboardItem(
                    id=model.id,
                    library_id=model.library_id,
                    name=model.name,
                    description=model.description,
                    status=model.status,
                    is_pinned=model.is_pinned,
                    is_archived=model.status == BookshelfStatus.ARCHIVED.value,
                    is_basement=model.is_basement,
                    created_at=created_at,
                    updated_at=updated_at,
                    book_counts=counts,
                    edits_last_7d=edits_last_7d,
                    views_last_7d=views_last_7d,
                    last_activity_at=last_activity_at,
                    health=health,
                    theme_color=None,
                    cover_media_id=effective_cover_media_id,
                    tag_ids=tag_ids,
                    tag_names=tag_names,
                    tags=tag_snapshots,
                )
            )

        # 4. 过滤 + 排序 + 分页（内存层处理，书架数量通常较小）
        filtered = [item for item in items if self._matches_filter(item, request.status_filter)]
        total = len(filtered)

        pinned_items = [item for item in filtered if item.is_pinned]
        regular_items = [item for item in filtered if not item.is_pinned]

        pinned_sorted = self._sort_items(pinned_items, BookshelfDashboardSort.RECENT_ACTIVITY)
        regular_sorted = self._sort_items(regular_items, request.sort)

        sorted_items = pinned_sorted + regular_sorted
        start = (request.page - 1) * request.size
        end = start + request.size
        paginated = sorted_items[start:end]

        snapshot = BookshelfDashboardSnapshot(
            total=len(items),
            pinned=pinned_total,
            health_counts=BookshelfHealthCounts(**health_totals),
        )

        return BookshelfDashboardResult(items=paginated, total=total, snapshot=snapshot)

    async def _enforce_library_owner(self, request: BookshelfDashboardRequest) -> None:
        if not request.enforce_owner_check or request.actor_user_id is None:
            return
        if self.library_repository is None:
            raise BookshelfOperationError(
                bookshelf_id="<unknown>",
                operation="authorize",
                reason="library_repository is required when enforcing owner checks",
            )

        library = await self.library_repository.get_by_id(request.library_id)
        if not library:
            raise BookshelfLibraryAssociationError(
                bookshelf_id="<unknown>",
                library_id=str(request.library_id),
                reason="Library not found",
            )
        if getattr(library, "user_id", None) != request.actor_user_id:
            raise BookshelfForbiddenError(
                library_id=str(request.library_id),
                actor_user_id=str(request.actor_user_id),
                reason="Actor does not own this library",
            )

    async def _fetch_tag_snapshots(self, shelf_ids: List[UUID]) -> Dict[UUID, List[BookshelfTagSnapshot]]:
        if not shelf_ids:
            return {}

        stmt = (
            select(
                TagAssociationModel.entity_id.label("bookshelf_id"),
                TagModel.id.label("tag_id"),
                TagModel.name,
                TagModel.color,
                TagModel.description,
                TagAssociationModel.created_at,
            )
            .join(TagModel, TagModel.id == TagAssociationModel.tag_id)
            .where(
                TagAssociationModel.entity_type == TagEntityType.BOOKSHELF,
                TagAssociationModel.entity_id.in_(shelf_ids),
                TagModel.deleted_at.is_(None),
            )
            .order_by(TagAssociationModel.entity_id.asc(), TagAssociationModel.created_at.asc())
        )

        result = await self.session.execute(stmt)
        snapshots: Dict[UUID, List[BookshelfTagSnapshot]] = {}
        for row in result:
            bookshelf_id: UUID = row.bookshelf_id
            snapshot = BookshelfTagSnapshot(
                id=row.tag_id,
                name=row.name,
                color=row.color or "#6366F1",
                description=row.description,
            )
            snapshots.setdefault(bookshelf_id, []).append(snapshot)
        return snapshots

    async def _fetch_bookshelves(self, library_id: UUID) -> List[Tuple[BookshelfModel, Optional[UUID]]]:
        stmt: Select = (
            select(
                BookshelfModel,
                LibraryModel.cover_media_id.label("library_cover_media_id"),
            )
            .join(LibraryModel, LibraryModel.id == BookshelfModel.library_id)
            .where(
                and_(
                    BookshelfModel.library_id == library_id,
                    BookshelfModel.status != BookshelfStatus.DELETED.value,
                    BookshelfModel.is_basement.is_(False),
                )
            )
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [(row[0], row.library_cover_media_id) for row in rows]

    async def _fetch_book_counts(self, shelf_ids: List[UUID]) -> Dict[UUID, BookshelfBookCounts]:
        if not shelf_ids:
            return {}

        stmt: Select = (
            select(
                BookModel.bookshelf_id,
                func.count().label("total"),
                func.sum(case((BookModel.maturity == "seed", 1), else_=0)).label("seed"),
                func.sum(case((BookModel.maturity == "growing", 1), else_=0)).label("growing"),
                func.sum(case((BookModel.maturity == "stable", 1), else_=0)).label("stable"),
                func.sum(case((BookModel.maturity == "legacy", 1), else_=0)).label("legacy"),
            )
            .where(
                and_(
                    BookModel.bookshelf_id.in_(shelf_ids),
                    BookModel.soft_deleted_at.is_(None),
                )
            )
            .group_by(BookModel.bookshelf_id)
        )

        result = await self.session.execute(stmt)
        counts: Dict[UUID, BookshelfBookCounts] = {}
        for row in result:
            counts[row.bookshelf_id] = BookshelfBookCounts(
                total=int(row.total or 0),
                seed=int(row.seed or 0),
                growing=int(row.growing or 0),
                stable=int(row.stable or 0),
                legacy=int(row.legacy or 0),
            )
        return counts

    async def _fetch_chronicle_stats(
        self,
        library_id: UUID,
        shelf_ids: List[UUID],
    ) -> Dict[UUID, Dict[str, Optional[int]]]:
        if not shelf_ids:
            return {}

        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        stmt: Select = (
            select(
                BookModel.bookshelf_id,
                func.max(ChronicleEventModel.occurred_at).label("last_activity_at"),
                func.sum(
                    case(
                        (
                            and_(
                                ChronicleEventModel.occurred_at >= seven_days_ago,
                                ChronicleEventModel.event_type != "book_opened",
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("edits_last_7d"),
                func.sum(
                    case(
                        (
                            and_(
                                ChronicleEventModel.occurred_at >= seven_days_ago,
                                ChronicleEventModel.event_type == "book_opened",
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("views_last_7d"),
            )
            .join(BookModel, ChronicleEventModel.book_id == BookModel.id)
            .where(
                and_(
                    BookModel.bookshelf_id.in_(shelf_ids),
                    BookModel.library_id == library_id,
                )
            )
            .group_by(BookModel.bookshelf_id)
        )

        result = await self.session.execute(stmt)
        stats: Dict[UUID, Dict[str, Optional[int]]] = {}
        for row in result:
            last_activity_at = row.last_activity_at
            if last_activity_at is not None and last_activity_at.tzinfo is None:
                # 旧数据可能缺少时区信息，这里补齐为 UTC，确保后续排序不会抛出 offset-naive 错误
                last_activity_at = last_activity_at.replace(tzinfo=timezone.utc)
            stats[row.bookshelf_id] = {
                "last_activity_at": last_activity_at,
                "edits_last_7d": int(row.edits_last_7d or 0),
                "views_last_7d": int(row.views_last_7d or 0),
            }
        return stats

    @staticmethod
    def _ensure_timezone_aware(value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _compute_health(self, status: str, last_activity_at: Optional[datetime], now: datetime) -> str:
        if status == BookshelfStatus.ARCHIVED.value:
            return "archived"

        if last_activity_at is None:
            return "cooling"

        delta = now - last_activity_at
        days = delta.total_seconds() / 86400
        if days <= self.HEALTH_ACTIVE_THRESHOLD_DAYS:
            return "active"
        if days <= self.HEALTH_SLOWING_THRESHOLD_DAYS:
            return "slowing"
        return "cooling"

    def _matches_filter(
        self,
        item: BookshelfDashboardItem,
        status_filter: BookshelfDashboardFilter,
    ) -> bool:
        if status_filter == BookshelfDashboardFilter.ALL:
            return True
        if status_filter == BookshelfDashboardFilter.ACTIVE:
            return item.status == BookshelfStatus.ACTIVE.value
        if status_filter == BookshelfDashboardFilter.ARCHIVED:
            return item.status == BookshelfStatus.ARCHIVED.value
        if status_filter == BookshelfDashboardFilter.PINNED:
            return item.is_pinned
        if status_filter == BookshelfDashboardFilter.STALE:
            return item.health in {"cooling", "archived"}
        return True

    def _sort_items(
        self,
        items: List[BookshelfDashboardItem],
        sort: BookshelfDashboardSort,
    ) -> List[BookshelfDashboardItem]:
        if not items:
            return items

        if sort == BookshelfDashboardSort.NAME_ASC:
            return sorted(
                items,
                key=lambda i: locale.strxfrm((i.name or "").casefold()),
            )
        if sort == BookshelfDashboardSort.CREATED_DESC:
            return sorted(
                items,
                key=lambda i: i.created_at or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True,
            )
        if sort == BookshelfDashboardSort.BOOK_COUNT_DESC:
            return sorted(
                items,
                key=lambda i: (
                    i.book_counts.total,
                    i.last_activity_at or i.updated_at or datetime.min.replace(tzinfo=timezone.utc),
                ),
                reverse=True,
            )
        # Default: recent activity (DESC, None last)
        return sorted(
            items,
            key=lambda i: i.last_activity_at or i.updated_at or i.created_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )