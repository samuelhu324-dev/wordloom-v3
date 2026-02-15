"""Input adapters mapping HTTP layer DTOs to domain use cases.

These classes implement the input port interfaces defined in
`api.app.modules.tag.application.ports.input` by delegating to the
existing domain-level use cases in `api.app.modules.tag.application.use_cases`.

The legacy implementation expected routers to call the domain use cases
with primitive parameters. In the new hexagonal/ports setup, routers
work with request DTOs, so these adapters bridge the two layers and
ensure consistent TagResponse serialization.
"""

import logging
import os
from typing import List, Optional
from uuid import UUID

from .ports.input import (
    CreateTagRequest,
    CreateSubtagRequest,
    UpdateTagRequest,
    DeleteTagRequest,
    RestoreTagRequest,
    AssociateTagRequest,
    DisassociateTagRequest,
    SearchTagsRequest,
    GetMostUsedTagsRequest,
    ListTagsRequest,
    ListTagsResult,
    TagResponse,
    CreateTagUseCase as CreateTagInputPort,
    CreateSubtagUseCase as CreateSubtagInputPort,
    UpdateTagUseCase as UpdateTagInputPort,
    DeleteTagUseCase as DeleteTagInputPort,
    RestoreTagUseCase as RestoreTagInputPort,
    AssociateTagUseCase as AssociateTagInputPort,
    DisassociateTagUseCase as DisassociateTagInputPort,
    SearchTagsUseCase as SearchTagsInputPort,
    GetMostUsedTagsUseCase as GetMostUsedTagsInputPort,
    ListTagsUseCase as ListTagsInputPort,
)
from .use_cases import (
    CreateTagUseCase as CreateTagDomainUseCase,
    CreateSubtagUseCase as CreateSubtagDomainUseCase,
    UpdateTagUseCase as UpdateTagDomainUseCase,
    DeleteTagUseCase as DeleteTagDomainUseCase,
    RestoreTagUseCase as RestoreTagDomainUseCase,
    AssociateTagUseCase as AssociateTagDomainUseCase,
    DisassociateTagUseCase as DisassociateTagDomainUseCase,
    SearchTagsUseCase as SearchTagsDomainUseCase,
    GetMostUsedTagsUseCase as GetMostUsedTagsDomainUseCase,
    ListTagsUseCase as ListTagsDomainUseCase,
)
from .ports.output import TagRepository
from api.app.modules.tag.exceptions import TagForbiddenError
from api.app.modules.library.application.ports.output import ILibraryRepository
from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository
from api.app.modules.book.application.ports.output import BookRepository
from api.app.modules.block.application.ports.output import BlockRepository
from api.app.modules.tag.domain import EntityType
from api.app.modules.chronicle.application.services import ChronicleRecorderService


logger = logging.getLogger(__name__)


def _resolve_dev_user_id() -> UUID:
    """Resolve dev user id from environment (must match security.get_current_user_id)."""

    override = os.getenv("DEV_USER_ID")
    if override:
        try:
            return UUID(override)
        except Exception:
            pass
    return UUID("550e8400-e29b-41d4-a716-446655440000")


DEV_USER_ID = _resolve_dev_user_id()


def _enforce_tag_user_context(*, actor_user_id: Optional[UUID], enforce_owner_check: bool) -> None:
    """Authorization skeleton for Tag module.

    Tag storage is currently scoped to a single dev user context (see infra/storage/tag_repository_impl.py).
    Until TagRepository is fully user-scoped per request, we enforce that the request actor matches the
    active dev user when owner checks are enabled.
    """

    if not enforce_owner_check:
        return
    if actor_user_id is None:
        return
    if actor_user_id != DEV_USER_ID:
        raise TagForbiddenError(
            "Actor is not allowed to access Tag resources in current user context",
            actor_user_id=str(actor_user_id),
        )


class CreateTagAdapter(CreateTagInputPort):
    """Adapter implementing CreateTag input port."""

    def __init__(self, repository: TagRepository):
        self._use_case = CreateTagDomainUseCase(repository)

    async def execute(self, request: CreateTagRequest) -> TagResponse:
        _enforce_tag_user_context(
            actor_user_id=getattr(request, "actor_user_id", None),
            enforce_owner_check=getattr(request, "enforce_owner_check", True),
        )
        tag = await self._use_case.execute(
            name=request.name,
            color=request.color,
            icon=request.icon,
            description=request.description,
        )
        return TagResponse.from_domain(tag)


class CreateSubtagAdapter(CreateSubtagInputPort):
    """Adapter implementing CreateSubtag input port."""

    def __init__(self, repository: TagRepository):
        self._use_case = CreateSubtagDomainUseCase(repository)

    async def execute(self, request: CreateSubtagRequest) -> TagResponse:
        _enforce_tag_user_context(
            actor_user_id=getattr(request, "actor_user_id", None),
            enforce_owner_check=getattr(request, "enforce_owner_check", True),
        )
        tag = await self._use_case.execute(
            parent_tag_id=request.parent_tag_id,
            name=request.name,
            color=request.color,
            icon=request.icon,
            description=request.description,
        )
        return TagResponse.from_domain(tag)


class UpdateTagAdapter(UpdateTagInputPort):
    """Adapter implementing UpdateTag input port."""

    def __init__(self, repository: TagRepository):
        self._use_case = UpdateTagDomainUseCase(repository)

    async def execute(self, request: UpdateTagRequest) -> TagResponse:
        _enforce_tag_user_context(
            actor_user_id=getattr(request, "actor_user_id", None),
            enforce_owner_check=getattr(request, "enforce_owner_check", True),
        )
        tag = await self._use_case.execute(
            tag_id=request.tag_id,
            name=request.name,
            color=request.color,
            icon=request.icon,
            description=request.description,
            parent_tag_id=request.parent_tag_id,
            parent_tag_provided=request.parent_tag_provided,
        )
        return TagResponse.from_domain(tag)


class DeleteTagAdapter(DeleteTagInputPort):
    """Adapter implementing DeleteTag input port."""

    def __init__(self, repository: TagRepository):
        self._use_case = DeleteTagDomainUseCase(repository)

    async def execute(self, request: DeleteTagRequest) -> None:
        _enforce_tag_user_context(
            actor_user_id=getattr(request, "actor_user_id", None),
            enforce_owner_check=getattr(request, "enforce_owner_check", True),
        )
        await self._use_case.execute(request.tag_id)


class RestoreTagAdapter(RestoreTagInputPort):
    """Adapter implementing RestoreTag input port."""

    def __init__(self, repository: TagRepository):
        self._use_case = RestoreTagDomainUseCase(repository)

    async def execute(self, request: RestoreTagRequest) -> TagResponse:
        _enforce_tag_user_context(
            actor_user_id=getattr(request, "actor_user_id", None),
            enforce_owner_check=getattr(request, "enforce_owner_check", True),
        )
        tag = await self._use_case.execute(request.tag_id)
        return TagResponse.from_domain(tag)


class AssociateTagAdapter(AssociateTagInputPort):
    """Adapter implementing AssociateTag input port."""

    def __init__(
        self,
        repository: TagRepository,
        *,
        library_repository: ILibraryRepository,
        bookshelf_repository: IBookshelfRepository,
        book_repository: BookRepository,
        block_repository: BlockRepository,
        chronicle_service: Optional[ChronicleRecorderService] = None,
    ):
        self._use_case = AssociateTagDomainUseCase(
            repository,
            library_repository=library_repository,
            bookshelf_repository=bookshelf_repository,
            book_repository=book_repository,
            block_repository=block_repository,
        )
        self._chronicle_service = chronicle_service

    async def execute(self, request: AssociateTagRequest) -> None:
        _enforce_tag_user_context(
            actor_user_id=getattr(request, "actor_user_id", None),
            enforce_owner_check=getattr(request, "enforce_owner_check", True),
        )
        await self._use_case.execute(
            tag_id=request.tag_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            actor_user_id=getattr(request, "actor_user_id", None),
            enforce_owner_check=getattr(request, "enforce_owner_check", True),
        )

        if (
            self._chronicle_service
            and getattr(request, "entity_type", None) == EntityType.BOOK
            and getattr(request, "entity_id", None) is not None
        ):
            try:
                await self._chronicle_service.record_tag_added_to_book(
                    book_id=request.entity_id,
                    tag_id=request.tag_id,
                    actor_id=getattr(request, "actor_user_id", None),
                )
            except Exception:
                logger.warning("Chronicle record_tag_added_to_book failed", exc_info=True)


class DisassociateTagAdapter(DisassociateTagInputPort):
    """Adapter implementing DisassociateTag input port."""

    def __init__(
        self,
        repository: TagRepository,
        *,
        library_repository: ILibraryRepository,
        bookshelf_repository: IBookshelfRepository,
        book_repository: BookRepository,
        block_repository: BlockRepository,
        chronicle_service: Optional[ChronicleRecorderService] = None,
    ):
        self._use_case = DisassociateTagDomainUseCase(
            repository,
            library_repository=library_repository,
            bookshelf_repository=bookshelf_repository,
            book_repository=book_repository,
            block_repository=block_repository,
        )
        self._chronicle_service = chronicle_service

    async def execute(self, request: DisassociateTagRequest) -> None:
        _enforce_tag_user_context(
            actor_user_id=getattr(request, "actor_user_id", None),
            enforce_owner_check=getattr(request, "enforce_owner_check", True),
        )
        await self._use_case.execute(
            tag_id=request.tag_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            actor_user_id=getattr(request, "actor_user_id", None),
            enforce_owner_check=getattr(request, "enforce_owner_check", True),
        )

        if (
            self._chronicle_service
            and getattr(request, "entity_type", None) == EntityType.BOOK
            and getattr(request, "entity_id", None) is not None
        ):
            try:
                await self._chronicle_service.record_tag_removed_from_book(
                    book_id=request.entity_id,
                    tag_id=request.tag_id,
                    actor_id=getattr(request, "actor_user_id", None),
                )
            except Exception:
                logger.warning("Chronicle record_tag_removed_from_book failed", exc_info=True)


class SearchTagsAdapter(SearchTagsInputPort):
    """Adapter implementing SearchTags input port."""

    def __init__(self, repository: TagRepository):
        self._use_case = SearchTagsDomainUseCase(repository)

    async def execute(self, request: SearchTagsRequest) -> List[TagResponse]:
        _enforce_tag_user_context(
            actor_user_id=getattr(request, "actor_user_id", None),
            enforce_owner_check=getattr(request, "enforce_owner_check", True),
        )
        tags = await self._use_case.execute(
            keyword=request.keyword,
            limit=request.limit,
            order=request.order,
        )
        return [TagResponse.from_domain(tag) for tag in tags]


class GetMostUsedTagsAdapter(GetMostUsedTagsInputPort):
    """Adapter implementing GetMostUsedTags input port."""

    def __init__(self, repository: TagRepository):
        self._use_case = GetMostUsedTagsDomainUseCase(repository)

    async def execute(self, request: GetMostUsedTagsRequest) -> List[TagResponse]:
        _enforce_tag_user_context(
            actor_user_id=getattr(request, "actor_user_id", None),
            enforce_owner_check=getattr(request, "enforce_owner_check", True),
        )
        tags = await self._use_case.execute(limit=request.limit)
        return [TagResponse.from_domain(tag) for tag in tags]


class ListTagsAdapter(ListTagsInputPort):
    """Adapter implementing ListTags input port."""

    def __init__(self, repository: TagRepository):
        self._use_case = ListTagsDomainUseCase(repository)

    async def execute(self, request: ListTagsRequest) -> ListTagsResult:
        _enforce_tag_user_context(
            actor_user_id=getattr(request, "actor_user_id", None),
            enforce_owner_check=getattr(request, "enforce_owner_check", True),
        )
        return await self._use_case.execute(request)
