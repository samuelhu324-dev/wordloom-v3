"""Tag Router - Hexagonal Architecture Pattern"""

from dataclasses import asdict
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from api.app.dependencies import DIContainer, get_di_container
from api.app.modules.tag.domain import EntityType
from api.app.modules.tag.exceptions import (
    DomainException,
    TagAlreadyExistsError,
    TagNotFoundError,
)
from api.app.modules.tag.schemas import (
    CreateTagRequest as CreateTagSchema,
    CreateSubtagRequest as CreateSubtagSchema,
    UpdateTagRequest as UpdateTagSchema,
    AssociateTagRequest as AssociateTagSchema,
)
from api.app.modules.tag.application.ports.input import (
    AssociateTagRequest as AssociateTagInput,
    CreateSubtagRequest as CreateSubtagInput,
    CreateTagRequest as CreateTagInput,
    DeleteTagRequest,
    DisassociateTagRequest,
    GetMostUsedTagsRequest,
    ListTagsRequest,
    RestoreTagRequest,
    SearchTagsRequest,
    TagResponse,
    UpdateTagRequest as UpdateTagInput,
)


router = APIRouter(prefix="", tags=["Tags"])


def _normalize_entity_type(raw: EntityType | str) -> EntityType:
    """Allow case-insensitive entity_type parsing for backward compatibility."""

    if isinstance(raw, EntityType):
        return raw

    value = (raw or "").strip().lower()
    try:
        return EntityType(value)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_ENTITY_TYPE",
                "message": f"Unsupported entity_type '{raw}'. Use library/bookshelf/book/block.",
            },
        ) from exc


def _resolve_association_payload(
    query_entity_type: str | EntityType | None,
    query_entity_id: UUID | None,
    body: AssociateTagSchema | None,
) -> tuple[EntityType, UUID]:
    """Resolve entity_type/entity_id from either query params or JSON body."""

    if body is not None:
        return _normalize_entity_type(body.entity_type), body.entity_id

    if query_entity_type is None or query_entity_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "MISSING_ASSOCIATION_PARAMS",
                "message": "Provide entity_type/entity_id via query parameters or JSON body.",
            },
        )

    return _normalize_entity_type(query_entity_type), query_entity_id


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tag",
)
async def create_tag(
    request: CreateTagSchema,
    di: DIContainer = Depends(get_di_container),
):
    """创建新的顶层 Tag。"""

    try:
        use_case = di.get_create_tag_use_case()
        dto = CreateTagInput(
            name=request.name,
            color=request.color,
            icon=request.icon,
            description=request.description,
        )
        response: TagResponse = await use_case.execute(dto)
        return asdict(response)
    except TagAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except DomainException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/{tag_id}/subtags",
    status_code=status.HTTP_201_CREATED,
    summary="Create a subtag under a parent tag",
)
async def create_subtag(
    tag_id: UUID,
    request: CreateSubtagSchema,
    di: DIContainer = Depends(get_di_container),
):
    """创建子标签。"""

    try:
        use_case = di.get_create_subtag_use_case()
        dto = CreateSubtagInput(
            parent_tag_id=tag_id,
            name=request.name,
            color=request.color,
            icon=request.icon,
        )
        response: TagResponse = await use_case.execute(dto)
        return asdict(response)
    except TagNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except DomainException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{tag_id}",
    summary="Update a tag",
)
async def update_tag(
    tag_id: UUID,
    request: UpdateTagSchema,
    di: DIContainer = Depends(get_di_container),
):
    """更新 Tag。"""

    try:
        use_case = di.get_update_tag_use_case()
        dto = UpdateTagInput(
            tag_id=tag_id,
            name=request.name,
            color=request.color,
            icon=request.icon,
            description=request.description,
        )
        response: TagResponse = await use_case.execute(dto)
        return asdict(response)
    except TagNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except DomainException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tag (soft delete)",
)
async def delete_tag(
    tag_id: UUID,
    di: DIContainer = Depends(get_di_container),
):
    """软删除 Tag。"""

    try:
        use_case = di.get_delete_tag_use_case()
        dto = DeleteTagRequest(tag_id=tag_id)
        await use_case.execute(dto)
    except TagNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except DomainException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/{tag_id}/restore",
    summary="Restore a deleted tag",
)
async def restore_tag(
    tag_id: UUID,
    di: DIContainer = Depends(get_di_container),
):
    """恢复已软删除的 Tag。"""

    try:
        use_case = di.get_restore_tag_use_case()
        dto = RestoreTagRequest(tag_id=tag_id)
        response: TagResponse = await use_case.execute(dto)
        return asdict(response)
    except TagNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except DomainException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    summary="Search tags",
)
async def search_tags(
    keyword: Optional[str] = Query(None, description="Search keyword"),
    limit: int = Query(50, ge=1, le=100),
    order: str = Query(
        "name_asc",
        description="Sort order: name_asc | name_desc | usage_desc | created_desc",
    ),
    di: DIContainer = Depends(get_di_container),
):
    """搜索 Tags。"""

    try:
        use_case = di.get_search_tags_use_case()
        dto = SearchTagsRequest(
            keyword=(keyword or ""),
            limit=limit,
            order=order,
        )
        responses: List[TagResponse] = await use_case.execute(dto)
        return {
            "total": len(responses),
            "items": [asdict(item) for item in responses],
        }
    except DomainException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/most-used",
    summary="Get most used tags",
)
async def get_most_used_tags(
    limit: int = Query(10, ge=1, le=50),
    di: DIContainer = Depends(get_di_container),
):
    """获取最常用标签。"""

    try:
        use_case = di.get_get_most_used_tags_use_case()
        dto = GetMostUsedTagsRequest(limit=limit)
        responses: List[TagResponse] = await use_case.execute(dto)
        return {
            "total": len(responses),
            "items": [asdict(item) for item in responses],
        }
    except DomainException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/catalog",
    summary="List tags catalog",
)
async def list_tags(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    include_deleted: bool = Query(False),
    only_top_level: bool = Query(True),
    order: str = Query(
        "name_asc",
        description="Sort order: name_asc | name_desc | usage_desc | created_desc",
    ),
    di: DIContainer = Depends(get_di_container),
):
    """分页列出标签目录。"""

    try:
        use_case = di.get_list_tags_use_case()
        request = ListTagsRequest(
            page=page,
            size=size,
            include_deleted=include_deleted,
            only_top_level=only_top_level,
            order_by=order,
        )
        result = await use_case.execute(request)
        return {
            "total": result.total,
            "items": [asdict(item) for item in result.items],
            "page": result.page,
            "size": result.size,
            "has_more": result.has_more,
        }
    except DomainException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/{tag_id}",
    summary="Get tag by ID",
)
async def get_tag(
    tag_id: UUID,
    di: DIContainer = Depends(get_di_container),
):
    """根据 ID 获取单个 Tag。"""

    try:
        use_case = di.get_search_tags_use_case()
        dto = SearchTagsRequest(keyword=str(tag_id), limit=1)
        responses: List[TagResponse] = await use_case.execute(dto)
        if not responses:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag {tag_id} not found",
            )
        return asdict(responses[0])
    except DomainException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/{tag_id}/associate",
    summary="Associate tag with entity",
)
async def associate_tag(
    tag_id: UUID,
    entity_type: str | EntityType | None = Query(
        None,
        description="Entity type (library/bookshelf/book/block). Prefer lowercase.",
    ),
    entity_id: Optional[UUID] = Query(None, description="Entity ID"),
    body: Optional[AssociateTagSchema] = Body(
        None,
        description="Optional JSON payload for association (preferred).",
    ),
    di: DIContainer = Depends(get_di_container),
):
    """关联 Tag 到实体。"""

    try:
        normalized_type, normalized_id = _resolve_association_payload(entity_type, entity_id, body)
        use_case = di.get_associate_tag_use_case()
        dto = AssociateTagInput(
            tag_id=tag_id,
            entity_type=normalized_type,
            entity_id=normalized_id,
        )
        await use_case.execute(dto)
        return {"message": "Tag associated successfully"}
    except DomainException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{tag_id}/disassociate",
    summary="Disassociate tag from entity",
)
async def disassociate_tag(
    tag_id: UUID,
    entity_type: str | EntityType | None = Query(
        None,
        description="Entity type (library/bookshelf/book/block).",
    ),
    entity_id: Optional[UUID] = Query(None),
    body: Optional[AssociateTagSchema] = Body(
        None,
        description="Optional JSON payload mirroring associate request.",
    ),
    di: DIContainer = Depends(get_di_container),
):
    """取消 Tag 与实体的关联。"""

    try:
        normalized_type, normalized_id = _resolve_association_payload(entity_type, entity_id, body)
        use_case = di.get_disassociate_tag_use_case()
        dto = DisassociateTagRequest(
            tag_id=tag_id,
            entity_type=normalized_type,
            entity_id=normalized_id,
        )
        await use_case.execute(dto)
        return {"message": "Tag disassociated successfully"}
    except DomainException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


__all__ = ["router"]


