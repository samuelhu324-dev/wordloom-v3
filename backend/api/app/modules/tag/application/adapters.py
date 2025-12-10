"""Input adapters mapping HTTP layer DTOs to domain use cases.

These classes implement the input port interfaces defined in
`api.app.modules.tag.application.ports.input` by delegating to the
existing domain-level use cases in `api.app.modules.tag.application.use_cases`.

The legacy implementation expected routers to call the domain use cases
with primitive parameters. In the new hexagonal/ports setup, routers
work with request DTOs, so these adapters bridge the two layers and
ensure consistent TagResponse serialization.
"""

from typing import List

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


class CreateTagAdapter(CreateTagInputPort):
    """Adapter implementing CreateTag input port."""

    def __init__(self, repository: TagRepository):
        self._use_case = CreateTagDomainUseCase(repository)

    async def execute(self, request: CreateTagRequest) -> TagResponse:
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
        tag = await self._use_case.execute(
            parent_tag_id=request.parent_tag_id,
            name=request.name,
            color=request.color,
            icon=request.icon,
        )
        return TagResponse.from_domain(tag)


class UpdateTagAdapter(UpdateTagInputPort):
    """Adapter implementing UpdateTag input port."""

    def __init__(self, repository: TagRepository):
        self._use_case = UpdateTagDomainUseCase(repository)

    async def execute(self, request: UpdateTagRequest) -> TagResponse:
        tag = await self._use_case.execute(
            tag_id=request.tag_id,
            name=request.name,
            color=request.color,
            icon=request.icon,
            description=request.description,
        )
        return TagResponse.from_domain(tag)


class DeleteTagAdapter(DeleteTagInputPort):
    """Adapter implementing DeleteTag input port."""

    def __init__(self, repository: TagRepository):
        self._use_case = DeleteTagDomainUseCase(repository)

    async def execute(self, request: DeleteTagRequest) -> None:
        await self._use_case.execute(request.tag_id)


class RestoreTagAdapter(RestoreTagInputPort):
    """Adapter implementing RestoreTag input port."""

    def __init__(self, repository: TagRepository):
        self._use_case = RestoreTagDomainUseCase(repository)

    async def execute(self, request: RestoreTagRequest) -> TagResponse:
        tag = await self._use_case.execute(request.tag_id)
        return TagResponse.from_domain(tag)


class AssociateTagAdapter(AssociateTagInputPort):
    """Adapter implementing AssociateTag input port."""

    def __init__(self, repository: TagRepository):
        self._use_case = AssociateTagDomainUseCase(repository)

    async def execute(self, request: AssociateTagRequest) -> None:
        await self._use_case.execute(
            tag_id=request.tag_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
        )


class DisassociateTagAdapter(DisassociateTagInputPort):
    """Adapter implementing DisassociateTag input port."""

    def __init__(self, repository: TagRepository):
        self._use_case = DisassociateTagDomainUseCase(repository)

    async def execute(self, request: DisassociateTagRequest) -> None:
        await self._use_case.execute(
            tag_id=request.tag_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
        )


class SearchTagsAdapter(SearchTagsInputPort):
    """Adapter implementing SearchTags input port."""

    def __init__(self, repository: TagRepository):
        self._use_case = SearchTagsDomainUseCase(repository)

    async def execute(self, request: SearchTagsRequest) -> List[TagResponse]:
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
        tags = await self._use_case.execute(limit=request.limit)
        return [TagResponse.from_domain(tag) for tag in tags]


class ListTagsAdapter(ListTagsInputPort):
    """Adapter implementing ListTags input port."""

    def __init__(self, repository: TagRepository):
        self._use_case = ListTagsDomainUseCase(repository)

    async def execute(self, request: ListTagsRequest) -> ListTagsResult:
        return await self._use_case.execute(request)
