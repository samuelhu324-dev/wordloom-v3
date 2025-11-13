"""
Library Router - Hexagonal Architecture Pattern

库管理的 FastAPI 路由适配器。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID
import logging

from dependencies import DIContainer, get_di_container_provider
from app.modules.library.application.ports.input import (
    GetUserLibraryRequest,
    DeleteLibraryRequest,
    LibraryResponse,
)
from app.modules.library.domain.exceptions import (
    LibraryNotFoundError,
    DomainException,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/libraries", tags=["libraries"])


async def get_di_container() -> DIContainer:
    """获取 DI 容器"""
    return get_di_container_provider()


# ============================================================================
# Get User Library
# ============================================================================

@router.get(
    "/{user_id}",
    response_model=dict,
    summary="Get user library",
)
async def get_user_library(
    user_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """获取用户库（不存在则创建）"""
    try:
        request = GetUserLibraryRequest(user_id=user_id)
        use_case = di.get_get_user_library_use_case()
        response: LibraryResponse = await use_case.execute(request)
        return response.to_dict()
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Delete Library
# ============================================================================

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user library",
)
async def delete_library(
    user_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """删除用户库及其所有数据"""
    try:
        request = DeleteLibraryRequest(user_id=user_id)
        use_case = di.get_delete_library_use_case()
        await use_case.execute(request)
    except LibraryNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


__all__ = ["router"]
