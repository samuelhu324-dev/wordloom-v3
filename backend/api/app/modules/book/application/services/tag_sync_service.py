"""Book Tag Synchronization Service.

Coordinates Tag module ports so Book update flows can accept tag_ids payloads
without embedding tag logic inside the Book aggregate.
"""

from __future__ import annotations

from typing import List, Sequence
from uuid import UUID

from api.app.modules.tag.application.ports.input import (
    AssociateTagRequest as AssociateTagInput,
    AssociateTagUseCase,
    DisassociateTagRequest as DisassociateTagInput,
    DisassociateTagUseCase,
)
from api.app.modules.tag.application.ports.output import TagRepository
from api.app.modules.tag.domain import EntityType


class BookTagSyncService:
    """Synchronize tag associations for a Book aggregate."""

    def __init__(
        self,
        tag_repository: TagRepository,
        associate_use_case: AssociateTagUseCase,
        disassociate_use_case: DisassociateTagUseCase,
        *,
        max_tags: int = 3,
    ) -> None:
        self._tag_repository = tag_repository
        self._associate_use_case = associate_use_case
        self._disassociate_use_case = disassociate_use_case
        self._max_tags = max(1, max_tags)

    async def sync_tags(self, book_id: UUID, desired_tag_ids: Sequence[UUID] | None) -> List[str]:
        """Ensure the given book is associated with exactly desired_tag_ids.

        Returns the ordered tag name summary (respecting desired order).
        """

        normalized_ids = self._normalize_tag_ids(desired_tag_ids)
        current_tags = await self._tag_repository.find_by_entity(EntityType.BOOK, book_id)
        current_ids = {tag.id for tag in current_tags}
        desired_set = set(normalized_ids)

        # Remove associations that are no longer desired
        remove_ids = [tag_id for tag_id in current_ids if tag_id not in desired_set]
        for tag_id in remove_ids:
            await self._disassociate_use_case.execute(
                DisassociateTagInput(
                    tag_id=tag_id,
                    entity_type=EntityType.BOOK,
                    entity_id=book_id,
                )
            )

        # Add newly requested tags in order, skipping ones already linked
        for tag_id in normalized_ids:
            if tag_id in current_ids:
                continue
            await self._associate_use_case.execute(
                AssociateTagInput(
                    tag_id=tag_id,
                    entity_type=EntityType.BOOK,
                    entity_id=book_id,
                )
            )

        # Build ordered summary list for UI consumption
        return await self._build_summary(book_id, normalized_ids)

    def _normalize_tag_ids(self, tag_ids: Sequence[UUID] | None) -> List[UUID]:
        if not tag_ids:
            return []

        ordered: List[UUID] = []
        seen = set()
        for tag_id in tag_ids:
            if not tag_id or tag_id in seen:
                continue
            seen.add(tag_id)
            ordered.append(tag_id)
            if len(ordered) >= self._max_tags:
                break
        return ordered

    async def _build_summary(self, book_id: UUID, desired_order: Sequence[UUID]) -> List[str]:
        tag_objects = await self._tag_repository.find_by_entity(EntityType.BOOK, book_id)
        tags_by_id = {tag.id: tag for tag in tag_objects}

        ordered_summary: List[str] = []
        for tag_id in desired_order:
            tag = tags_by_id.get(tag_id)
            if tag and tag.name:
                ordered_summary.append(tag.name)

        if ordered_summary:
            return ordered_summary[: self._max_tags]

        # Fallback to whatever order repository returns (created_at ASC)
        fallback = [tag.name for tag in tag_objects if tag.name]
        return fallback[: self._max_tags]