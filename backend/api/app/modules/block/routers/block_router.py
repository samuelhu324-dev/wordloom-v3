"""
Block Router - Hexagonal Architecture Pattern

块（Block）管理的 FastAPI 路由适配器。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from uuid import UUID
import logging

from dependencies import DIContainer, get_di_container_provider
from app.modules.block.application.ports.input import (
    CreateBlockRequest,
    ListBlocksRequest,
    GetBlockRequest,
    UpdateBlockRequest,
    ReorderBlocksRequest,
    DeleteBlockRequest,
    RestoreBlockRequest,
    ListDeletedBlocksRequest,
    BlockResponse,
    BlockListResponse,
)
from app.modules.block.domain.exceptions import (
    BlockNotFoundError,
    BlockInvalidTypeError,
    DomainException,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/blocks", tags=["blocks"])


async def get_di_container() -> DIContainer:
    """获取 DI 容器"""
    return get_di_container_provider()


# ============================================================================
# Create Block
# ============================================================================

@router.post(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new block",
)
async def create_block(
    request: CreateBlockRequest,
    di: DIContainer = Depends(get_di_container)
):
    """创建新块"""
    try:
        use_case = di.get_create_block_use_case()
        response: BlockResponse = await use_case.execute(request)
        return response.to_dict()
    except BlockInvalidTypeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# List Blocks
# ============================================================================

@router.get(
    "",
    response_model=dict,
    summary="List blocks",
)
async def list_blocks(
    book_id: UUID = Query(..., description="Book ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    di: DIContainer = Depends(get_di_container)
):
    """列出块"""
    try:
        request = ListBlocksRequest(
            book_id=book_id,
            skip=skip,
            limit=limit
        )
        use_case = di.get_list_blocks_use_case()
        response: BlockListResponse = await use_case.execute(request)
        return response.to_dict()
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Get Block
# ============================================================================

@router.get(
    "/{block_id}",
    response_model=dict,
    summary="Get block by ID",
)
async def get_block(
    block_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """获取块详情"""
    try:
        request = GetBlockRequest(block_id=block_id)
        use_case = di.get_get_block_use_case()
        response: BlockResponse = await use_case.execute(request)
        return response.to_dict()
    except BlockNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Update Block
# ============================================================================

@router.patch(
    "/{block_id}",
    response_model=dict,
    summary="Update a block",
)
async def update_block(
    block_id: UUID,
    request: UpdateBlockRequest,
    di: DIContainer = Depends(get_di_container)
):
    """更新块"""
    try:
        request.block_id = block_id
        use_case = di.get_update_block_use_case()
        response: BlockResponse = await use_case.execute(request)
        return response.to_dict()
    except BlockNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Reorder Blocks
# ============================================================================

@router.post(
    "/reorder",
    response_model=dict,
    summary="Reorder blocks",
)
async def reorder_blocks(
    request: ReorderBlocksRequest,
    di: DIContainer = Depends(get_di_container)
):
    """重新排序块"""
    try:
        use_case = di.get_reorder_blocks_use_case()
        response: BlockResponse = await use_case.execute(request)
        return response.to_dict()
    except BlockNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Delete Block
# ============================================================================

@router.delete(
    "/{block_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a block (soft delete)",
)
async def delete_block(
    block_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """删除块（逻辑删除）"""
    try:
        request = DeleteBlockRequest(block_id=block_id)
        use_case = di.get_delete_block_use_case()
        await use_case.execute(request)
    except BlockNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Restore Block
# ============================================================================

@router.post(
    "/{block_id}/restore",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Restore a deleted block",
)
async def restore_block(
    block_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """恢复已删除的块"""
    try:
        request = RestoreBlockRequest(block_id=block_id)
        use_case = di.get_restore_block_use_case()
        response: BlockResponse = await use_case.execute(request)
        return response.to_dict()
    except BlockNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# List Deleted Blocks
# ============================================================================

@router.get(
    "/deleted",
    response_model=dict,
    summary="List deleted blocks",
)
async def list_deleted_blocks(
    book_id: UUID = Query(..., description="Book ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    di: DIContainer = Depends(get_di_container)
):
    """列出已删除的块"""
    try:
        request = ListDeletedBlocksRequest(
            book_id=book_id,
            skip=skip,
            limit=limit
        )
        use_case = di.get_list_deleted_blocks_use_case()
        response: BlockListResponse = await use_case.execute(request)
        return response.to_dict()
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


__all__ = ["router"]
