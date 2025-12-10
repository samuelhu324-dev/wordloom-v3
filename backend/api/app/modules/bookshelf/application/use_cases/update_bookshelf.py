"""UpdateBookshelf UseCase - 更新书橱数据与标签"""

from __future__ import annotations

from typing import List, Optional, Tuple
from uuid import UUID

from api.app.modules.bookshelf.application.ports.input import (
    IUpdateBookshelfUseCase,
    UpdateBookshelfRequest,
    UpdateBookshelfResponse,
)
from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository
from api.app.modules.bookshelf.domain import Bookshelf, BookshelfStatus
from api.app.modules.bookshelf.exceptions import (
    BookshelfAlreadyExistsError,
    BookshelfNotFoundError,
    BookshelfOperationError,
    BookshelfTagSyncError,
)
from api.app.modules.tag.application.ports.output import TagRepository
from api.app.modules.tag.domain import EntityType
from api.app.modules.tag.exceptions import TagNotFoundError, TagOperationError


class UpdateBookshelfUseCase(IUpdateBookshelfUseCase):
    """整合书橱基础信息与标签的更新逻辑"""

    def __init__(self, bookshelf_repository: IBookshelfRepository, tag_repository: TagRepository):
        self.bookshelf_repository = bookshelf_repository
        self.tag_repository = tag_repository

    async def execute(self, request: UpdateBookshelfRequest) -> UpdateBookshelfResponse:
        bookshelf_id = request.bookshelf_id
        if bookshelf_id is None:
            raise BookshelfOperationError(
                bookshelf_id="<unknown>",
                operation="update",
                reason="bookshelf_id is required",
            )

        bookshelf = await self.bookshelf_repository.get_by_id(bookshelf_id)
        if not bookshelf:
            raise BookshelfNotFoundError(str(bookshelf_id))

        await self._apply_core_updates(bookshelf, request)
        tag_ids, tag_names = await self._sync_tags(bookshelf, request.tag_ids)

        return UpdateBookshelfResponse.from_domain(
            bookshelf,
            tag_ids=tag_ids,
            tags_summary=tag_names,
        )

    async def _apply_core_updates(
        self,
        bookshelf: Bookshelf,
        request: UpdateBookshelfRequest,
    ) -> None:
        changes_applied = False

        if request.name is not None and request.name != str(bookshelf.name):
            name_exists = await self.bookshelf_repository.exists_by_name(
                bookshelf.library_id,
                request.name,
            )
            if name_exists:
                raise BookshelfAlreadyExistsError(
                    library_id=str(bookshelf.library_id),
                    name=request.name,
                    existing_bookshelf_id=str(bookshelf.id),
                )

            try:
                bookshelf.rename(request.name)
            except ValueError as exc:
                raise BookshelfOperationError(
                    bookshelf_id=str(bookshelf.id),
                    operation="rename",
                    reason=str(exc),
                    original_error=exc,
                ) from exc
            changes_applied = True

        if request.description is not None:
            try:
                bookshelf.update_description(request.description)
            except ValueError as exc:
                raise BookshelfOperationError(
                    bookshelf_id=str(bookshelf.id),
                    operation="update_description",
                    reason=str(exc),
                    original_error=exc,
                ) from exc
            changes_applied = True

        if request.status is not None:
            if request.status == BookshelfStatus.DELETED:
                raise BookshelfOperationError(
                    bookshelf_id=str(bookshelf.id),
                    operation="change_status",
                    reason="Status transition to deleted is not supported via update",
                )

            if request.status != bookshelf.status:
                try:
                    bookshelf.change_status(request.status)
                except ValueError as exc:
                    raise BookshelfOperationError(
                        bookshelf_id=str(bookshelf.id),
                        operation="change_status",
                        reason=str(exc),
                        original_error=exc,
                    ) from exc
                changes_applied = True

        if request.is_pinned is not None and request.is_pinned != bookshelf.is_pinned:
            bookshelf.mark_as_pinned(request.is_pinned)
            changes_applied = True

        if changes_applied:
            await self.bookshelf_repository.save(bookshelf)

    async def _sync_tags(
        self,
        bookshelf: Bookshelf,
        incoming_tag_ids: Optional[List[UUID]],
    ) -> Tuple[List[UUID], List[str]]:
        entity_id = bookshelf.id

        if incoming_tag_ids is not None:
            # Use order-preserving unique list already enforced by validator but re-apply for safety
            ordered_unique: List[UUID] = []
            seen: set[UUID] = set()
            for tag_id in incoming_tag_ids:
                if tag_id in seen:
                    continue
                ordered_unique.append(tag_id)
                seen.add(tag_id)

            current_tags = await self.tag_repository.find_by_entity(EntityType.BOOKSHELF, entity_id)
            current_ids = {tag.id for tag in current_tags}
            target_set = set(ordered_unique)

            to_add = [tag_id for tag_id in ordered_unique if tag_id not in current_ids]
            to_remove = [tag_id for tag_id in current_ids if tag_id not in target_set]

            try:
                for tag_id in to_add:
                    await self.tag_repository.associate_tag_with_entity(
                        tag_id,
                        EntityType.BOOKSHELF,
                        entity_id,
                    )

                for tag_id in to_remove:
                    await self.tag_repository.disassociate_tag_from_entity(
                        tag_id,
                        EntityType.BOOKSHELF,
                        entity_id,
                    )
            except (TagNotFoundError, TagOperationError) as exc:
                raise BookshelfTagSyncError(
                    bookshelf_id=str(bookshelf.id),
                    reason=str(exc),
                ) from exc

        final_tags = await self.tag_repository.find_by_entity(EntityType.BOOKSHELF, entity_id)
        final_ids = [tag.id for tag in final_tags]
        final_names = [tag.name for tag in final_tags]
        return final_ids, final_names
