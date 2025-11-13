"""
Tag Router - Hexagonal Architecture Pattern

FastAPI 路由适配器，将 HTTP 请求转换为 UseCase 调用。

职责:
1. 解析 HTTP 请求 → 转换为 Input DTO
2. 从 DI 容器获取 UseCase
3. 执行 UseCase
4. 将 Output DTO → 转换为 HTTP 响应
5. 异常映射到 HTTP 错误码
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from uuid import UUID
import logging

from dependencies import DIContainer, get_di_container_provider
from app.modules.tag.application.ports.input import (
    CreateTagRequest,
    CreateSubtagRequest,
    UpdateTagRequest,
    DeleteTagRequest,
    RestoreTagRequest,
    AssociateTagRequest,
    DisassociateTagRequest,
    SearchTagsRequest,
    GetMostUsedTagsRequest,
    TagResponse,
)
from app.modules.tag.domain.exceptions import (
    TagNotFoundError,
    TagAlreadyExistsError,
    DomainException,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tags", tags=["tags"])


# ============================================================================
# Dependency: Get DI Container
# ============================================================================

async def get_di_container() -> DIContainer:
    """
    获取 DI 容器（FastAPI 依赖）

    在实际应用中，这会从全局初始化的容器获取。
    """
    return get_di_container_provider()


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tag",
)
async def create_tag(
    request: CreateTagRequest,
    di: DIContainer = Depends(get_di_container)
):
    """
    创建新的顶层 Tag

    请求体:
    ```json
    {
        "name": "Python",
        "color": "#3776AB",
        "icon": "python",
        "description": "Python programming language"
    }
    ```

    返回: TagResponse
    """
    try:
        use_case = di.get_create_tag_use_case()
        response: TagResponse = await use_case.execute(request)
        return response.to_dict()
    except TagAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{tag_id}/subtags",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a subtag under a parent tag",
)
async def create_subtag(
    tag_id: UUID,
    request: CreateSubtagRequest,
    di: DIContainer = Depends(get_di_container)
):
    """创建 Subtag"""
    try:
        request.parent_tag_id = tag_id
        use_case = di.get_create_subtag_use_case()
        response: TagResponse = await use_case.execute(request)
        return response.to_dict()
    except TagNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{tag_id}",
    response_model=dict,
    summary="Get tag by ID",
)
async def get_tag(
    tag_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """获取单个 Tag 详情"""
    try:
        request = SearchTagsRequest(tag_id=tag_id, limit=1)
        use_case = di.get_search_tags_use_case()
        responses: List[TagResponse] = await use_case.execute(request)

        if not responses:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag {tag_id} not found"
            )

        return responses[0].to_dict()
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch(
    "/{tag_id}",
    response_model=dict,
    summary="Update a tag",
)
async def update_tag(
    tag_id: UUID,
    request: UpdateTagRequest,
    di: DIContainer = Depends(get_di_container)
):
    """更新 Tag"""
    try:
        request.tag_id = tag_id
        use_case = di.get_update_tag_use_case()
        response: TagResponse = await use_case.execute(request)
        return response.to_dict()
    except TagNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tag (soft delete)",
)
async def delete_tag(
    tag_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """删除 Tag（逻辑删除）"""
    try:
        request = DeleteTagRequest(tag_id=tag_id)
        use_case = di.get_delete_tag_use_case()
        await use_case.execute(request)
    except TagNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{tag_id}/restore",
    response_model=dict,
    summary="Restore a deleted tag",
)
async def restore_tag(
    tag_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """恢复已删除的 Tag"""
    try:
        request = RestoreTagRequest(tag_id=tag_id)
        use_case = di.get_restore_tag_use_case()
        response: TagResponse = await use_case.execute(request)
        return response.to_dict()
    except TagNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "",
    response_model=dict,
    summary="Search tags",
)
async def search_tags(
    keyword: Optional[str] = Query(None, description="Search keyword"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    di: DIContainer = Depends(get_di_container)
):
    """搜索 Tags"""
    try:
        request = SearchTagsRequest(
            keyword=keyword,
            limit=limit,
            skip=skip
        )
        use_case = di.get_search_tags_use_case()
        responses: List[TagResponse] = await use_case.execute(request)
        return {
            "total": len(responses),
            "items": [r.to_dict() for r in responses]
        }
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/most-used",
    response_model=dict,
    summary="Get most used tags",
)
async def get_most_used_tags(
    limit: int = Query(10, ge=1, le=50),
    di: DIContainer = Depends(get_di_container)
):
    """获取最常用的 Tags"""
    try:
        request = GetMostUsedTagsRequest(limit=limit)
        use_case = di.get_get_most_used_tags_use_case()
        responses: List[TagResponse] = await use_case.execute(request)
        return {
            "total": len(responses),
            "items": [r.to_dict() for r in responses]
        }
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{tag_id}/associate",
    status_code=status.HTTP_200_OK,
    summary="Associate tag with entity",
)
async def associate_tag(
    tag_id: UUID,
    entity_type: str = Query(..., description="Entity type: BOOK, BOOKSHELF, BLOCK"),
    entity_id: UUID = Query(..., description="Entity ID"),
    di: DIContainer = Depends(get_di_container)
):
    """关联 Tag 到实体（Book/Bookshelf/Block）"""
    try:
        request = AssociateTagRequest(
            tag_id=tag_id,
            entity_type=entity_type,
            entity_id=entity_id
        )
        use_case = di.get_associate_tag_use_case()
        await use_case.execute(request)
        return {"message": "Tag associated successfully"}
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{tag_id}/disassociate",
    status_code=status.HTTP_200_OK,
    summary="Disassociate tag from entity",
)
async def disassociate_tag(
    tag_id: UUID,
    entity_type: str = Query(...),
    entity_id: UUID = Query(...),
    di: DIContainer = Depends(get_di_container)
):
    """取消关联 Tag 和实体"""
    try:
        request = DisassociateTagRequest(
            tag_id=tag_id,
            entity_type=entity_type,
            entity_id=entity_id
        )
        use_case = di.get_disassociate_tag_use_case()
        await use_case.execute(request)
        return {"message": "Tag disassociated successfully"}
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


__all__ = ["router"]
