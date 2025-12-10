"""ListTags UseCase - Provide paginated tag catalog views.

Responsibilities:
- Validate pagination and ordering parameters
- Fetch tag catalog from repository
- Map domain models to response DTOs
"""

from __future__ import annotations

from typing import Iterable

from ...application.ports.output import TagRepository
from ...exceptions import TagOperationError
from ...application.ports.input import (
    ListTagsRequest,
    ListTagsResult,
    TagResponse,
)


_ALLOWED_ORDERS = {"name_asc", "name_desc", "usage_desc", "created_desc"}


class ListTagsUseCase:
    """List tags with pagination and stable ordering."""

    def __init__(self, repository: TagRepository):
        self.repository = repository

    async def execute(self, request: ListTagsRequest) -> ListTagsResult:
        page = max(1, request.page or 1)
        size = max(1, min(request.size or 50, 200))
        order = request.order_by if request.order_by in _ALLOWED_ORDERS else "name_asc"
        offset = (page - 1) * size

        try:
            items, total = await self.repository.list_all(
                include_deleted=bool(request.include_deleted),
                only_top_level=bool(request.only_top_level),
                limit=size,
                offset=offset,
                order_by=order,
            )
        except Exception as exc:
            raise TagOperationError(f"Failed to list tags: {exc}") from exc

        responses = _map_domain_to_response(items)
        return ListTagsResult(
            items=responses,
            total=total,
            page=page,
            size=size,
        )


def _map_domain_to_response(items: Iterable) -> list[TagResponse]:
    """Convert domain Tag objects to response DTOs."""
    return [TagResponse.from_domain(tag) for tag in items]
