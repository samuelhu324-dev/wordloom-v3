"""
Block Router - Hexagonal Architecture Pattern

块（Block）管理的 FastAPI 路由适配器�?
Routes (8 total):
  POST   /blocks                           CreateBlockUseCase           (RULE-013-REVISED: type-specific factory)
  GET    /books/{book_id}/blocks           ListBlocksUseCase            (RULE-015-REVISED: ordered by sort_key)
  GET    /books/{book_id}/blocks/{id}      GetBlockUseCase              (RULE-013-REVISED)
  PATCH  /blocks/{block_id}                UpdateBlockUseCase           (RULE-014: content update)
  DELETE /blocks/{block_id}                DeleteBlockUseCase           (RULE-012: soft-delete, Paperballs context)
  POST   /blocks/reorder                   ReorderBlocksUseCase         (RULE-015-REVISED: Fractional Index O(1))
  POST   /blocks/{block_id}/restore        RestoreBlockUseCase          (RULE-013-REVISED: Paperballs recovery 3-level fallback)
  GET    /blocks/deleted                   ListDeletedBlocksUseCase     (RULE-012: Paperballs view, deleted metadata)

Design Decisions:
- Route prefix is /blocks (not nested under /books) for consistency
- Type validation enforced in CreateBlock (8 types: TEXT, HEADING, CODE, IMAGE, TABLE, QUOTE, LIST, DIVIDER)
- Soft delete records deleted_prev_id, deleted_next_id, deleted_section_path for Paperballs recovery
- Reorder endpoint uses Fractional Index (Decimal) for O(1) drag/drop without batch reindex
- Full DIContainer dependency injection chain
- Structured error handling with HTTP status mappings (400/404/409/422/500)
- Comprehensive logging for observability (info/warning/error)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from uuid import UUID
import logging

from dependencies import DIContainer, get_di_container_provider
from modules.block.application.ports.input import (
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
from modules.block.domain.exceptions import (
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
    description="Create a new block with type-specific factory (RULE-013-REVISED: TEXT|HEADING|CODE|IMAGE|TABLE|QUOTE|LIST|DIVIDER)"
)
async def create_block(
    request: CreateBlockRequest,
    di: DIContainer = Depends(get_di_container)
):
    """创建新块

    Args:
        request: CreateBlockRequest with:
            - book_id: UUID (required, block parent)
            - block_type: BlockType (required, one of 8 types)
            - content: str (required, 1-10000 chars)
            - order: Decimal (optional, fractional index)
            - heading_level: Optional[int] (required if type=HEADING, must be 1-3)

    Returns:
        Created Block response with full metadata

    Raises:
        HTTPException 400: Invalid block type
        HTTPException 422: Validation error (content length, heading_level invalid)
        HTTPException 500: Operation error
    """
    try:
        logger.info(f"Creating block: type={request.block_type}, book_id={request.book_id}")
        use_case = di.get_create_block_use_case()
        response: BlockResponse = await use_case.execute(request)
        logger.info(f"Block created successfully: block_id={response.id}, type={response.block_type}")
        return response.to_dict()
    except BlockInvalidTypeError as e:
        logger.warning(f"Block creation failed - invalid type: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_BLOCK_TYPE", "message": str(e)}
        )
    except DomainException as e:
        logger.warning(f"Block creation failed - validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error creating block: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to create block"}
        )


# ============================================================================
# List Blocks (RULE-015-REVISED: Ordered by sort_key, POLICY-008: soft-delete filter)
# ============================================================================

@router.get(
    "",
    response_model=dict,
    summary="List blocks",
    description="List blocks ordered by sort_key with soft-delete filtering (RULE-015-REVISED, POLICY-008)"
)
async def list_blocks(
    book_id: UUID = Query(..., description="Book ID (required)"),
    include_deleted: bool = Query(False, description="Include soft-deleted blocks (RULE-012/POLICY-008)"),
    skip: int = Query(0, ge=0, description="Pagination skip"),
    limit: int = Query(50, ge=1, le=100, description="Pagination limit"),
    di: DIContainer = Depends(get_di_container)
):
    """列出�?(RULE-015-REVISED: �?sort_key 排序, POLICY-008: 默认排除软删除的�?

    Args:
        book_id: Book ID to filter blocks (required)
        include_deleted: Include soft-deleted blocks (default False, RULE-012)
        skip: Pagination offset
        limit: Pagination page size (1-100)

    Returns:
        Paginated list of blocks ordered by sort_key

    Raises:
        HTTPException 422: Validation error
        HTTPException 500: Operation error
    """
    try:
        logger.debug(f"Listing blocks: book_id={book_id}, include_deleted={include_deleted}")
        request = ListBlocksRequest(
            book_id=book_id,
            skip=skip,
            limit=limit,
            include_deleted=include_deleted
        )
        use_case = di.get_list_blocks_use_case()
        response: BlockListResponse = await use_case.execute(request)
        logger.debug(f"Listed {len(response.items)} blocks from book {book_id}")
        return response.to_dict()
    except DomainException as e:
        logger.warning(f"List blocks failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error listing blocks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to list blocks"}
        )


# ============================================================================
# Get Block (RULE-013-REVISED: Query any block)
# ============================================================================

@router.get(
    "/{block_id}",
    response_model=dict,
    summary="Get block by ID",
    description="Retrieve detailed information about a specific block"
)
async def get_block(
    block_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """获取块详�?
    Args:
        block_id: Block ID to retrieve

    Returns:
        Detailed block information with all metadata

    Raises:
        HTTPException 404: Block not found
        HTTPException 500: Operation error
    """
    try:
        logger.debug(f"Getting block: block_id={block_id}")
        request = GetBlockRequest(block_id=block_id)
        use_case = di.get_get_block_use_case()
        response: BlockResponse = await use_case.execute(request)
        logger.debug(f"Retrieved block: {response.id}")
        return response.to_dict()
    except BlockNotFoundError as e:
        logger.warning(f"Block not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BLOCK_NOT_FOUND", "message": str(e)}
        )
    except DomainException as e:
        logger.warning(f"Get block failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error getting block: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to get block"}
        )


# ============================================================================
# Update Block (RULE-014: Content update)
# ============================================================================

@router.patch(
    "/{block_id}",
    response_model=dict,
    summary="Update a block",
    description="Update block properties (content, heading_level) - RULE-014"
)
async def update_block(
    block_id: UUID,
    request: UpdateBlockRequest,
    di: DIContainer = Depends(get_di_container)
):
    """更新�?
    Args:
        block_id: Block ID to update
        request: UpdateBlockRequest with fields to update:
            - content: Optional[str] (1-10000 chars)
            - heading_level: Optional[int] (1-3 if type=HEADING)

    Returns:
        Updated block response

    Raises:
        HTTPException 404: Block not found
        HTTPException 422: Validation error
        HTTPException 500: Operation error
    """
    try:
        logger.debug(f"Updating block: block_id={block_id}")
        request.block_id = block_id
        use_case = di.get_update_block_use_case()
        response: BlockResponse = await use_case.execute(request)
        logger.info(f"Block updated successfully: block_id={block_id}")
        return response.to_dict()
    except BlockNotFoundError as e:
        logger.warning(f"Block not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BLOCK_NOT_FOUND", "message": str(e)}
        )
    except DomainException as e:
        logger.warning(f"Block update failed - validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error updating block: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to update block"}
        )


# ============================================================================
# Reorder Blocks (RULE-015-REVISED: Fractional Index O(1) drag/drop)
# ============================================================================

@router.post(
    "/reorder",
    response_model=dict,
    summary="Reorder blocks (batch fractional index)",
    description="Batch reorder blocks with fractional index for O(1) drag/drop (RULE-015-REVISED)"
)
async def reorder_blocks(
    request: ReorderBlocksRequest,
    di: DIContainer = Depends(get_di_container)
):
    """重新排序�?
    Args:
        request: ReorderBlocksRequest with:
            - block_id: UUID (block to reorder)
            - new_order: Decimal (new fractional index position)

    Returns:
        Updated block with new order

    Raises:
        HTTPException 404: Block not found
        HTTPException 422: Validation error (invalid Decimal order)
        HTTPException 500: Operation error
    """
    try:
        logger.debug(f"Reordering block: block_id={request.block_id}, new_order={request.new_order}")
        use_case = di.get_reorder_blocks_use_case()
        response: BlockResponse = await use_case.execute(request)
        logger.info(f"Block reordered successfully: block_id={request.block_id}")
        return response.to_dict()
    except BlockNotFoundError as e:
        logger.warning(f"Block not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BLOCK_NOT_FOUND", "message": str(e)}
        )
    except DomainException as e:
        logger.warning(f"Reorder failed - validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error reordering block: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to reorder block"}
        )


# ============================================================================
# Delete Block (RULE-012: Soft-delete, records Paperballs recovery context)
# ============================================================================

@router.delete(
    "/{block_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a block (soft delete)",
    description="Soft-delete a block and record Paperballs recovery metadata (RULE-012)"
)
async def delete_block(
    block_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """删除块（逻辑删除�?
    Args:
        block_id: Block ID to soft-delete

    Returns:
        204 No Content on success

    Raises:
        HTTPException 404: Block not found
        HTTPException 422: Validation error
        HTTPException 500: Operation error
    """
    try:
        logger.info(f"Soft-deleting block: block_id={block_id}")
        request = DeleteBlockRequest(block_id=block_id)
        use_case = di.get_delete_block_use_case()
        await use_case.execute(request)
        logger.info(f"Block soft-deleted successfully: block_id={block_id}")
    except BlockNotFoundError as e:
        logger.warning(f"Block not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BLOCK_NOT_FOUND", "message": str(e)}
        )
    except DomainException as e:
        logger.warning(f"Delete failed - validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting block: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to delete block"}
        )


# ============================================================================
# Restore Block (RULE-013-REVISED: Paperballs recovery with 3-level fallback)
# ============================================================================

@router.post(
    "/{block_id}/restore",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Restore a deleted block from Paperballs",
    description="Restore block from soft-delete with 3-level positioning fallback (RULE-013-REVISED)"
)
async def restore_block(
    block_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """恢复已删除的�?
    Args:
        block_id: Block ID to restore from Paperballs

    Returns:
        Restored block response with new position (may vary due to 3-level fallback)

    Raises:
        HTTPException 404: Block not found or not in Paperballs
        HTTPException 409: Block not in soft-deleted state
        HTTPException 422: Validation error
        HTTPException 500: Operation error
    """
    try:
        logger.info(f"Restoring block from Paperballs: block_id={block_id}")
        request = RestoreBlockRequest(block_id=block_id)
        use_case = di.get_restore_block_use_case()
        response: BlockResponse = await use_case.execute(request)
        logger.info(f"Block restored successfully: block_id={block_id}")
        return response.to_dict()
    except BlockNotFoundError as e:
        logger.warning(f"Block not found or not in Paperballs: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BLOCK_NOT_FOUND", "message": str(e)}
        )
    except DomainException as e:
        logger.warning(f"Restore failed - validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error restoring block: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to restore block"}
        )


# ============================================================================
# List Deleted Blocks (RULE-012: Paperballs view with recovery metadata)
# ============================================================================

@router.get(
    "/deleted",
    response_model=dict,
    summary="List deleted blocks (Paperballs view)",
    description="List soft-deleted blocks with recovery metadata (RULE-012, Paperballs)"
)
async def list_deleted_blocks(
    book_id: UUID = Query(..., description="Book ID (required)"),
    skip: int = Query(0, ge=0, description="Pagination skip"),
    limit: int = Query(50, ge=1, le=100, description="Pagination limit"),
    di: DIContainer = Depends(get_di_container)
):
    """列出已删除的块（Paperballs 视图�?
    Args:
        book_id: Book ID to filter deleted blocks (required)
        skip: Pagination offset
        limit: Pagination page size (1-100)

    Returns:
        Paginated list of soft-deleted blocks with recovery metadata:
        - deleted_prev_id, deleted_next_id (3-level fallback recovery)
        - deleted_section_path (context)
        - soft_deleted_at (deletion timestamp)

    Raises:
        HTTPException 422: Validation error
        HTTPException 500: Operation error
    """
    try:
        logger.debug(f"Listing deleted blocks: book_id={book_id}")
        request = ListDeletedBlocksRequest(
            book_id=book_id,
            skip=skip,
            limit=limit
        )
        use_case = di.get_list_deleted_blocks_use_case()
        response: BlockListResponse = await use_case.execute(request)
        logger.debug(f"Listed {len(response.items)} deleted blocks from book {book_id}")
        return response.to_dict()
    except DomainException as e:
        logger.warning(f"List deleted blocks failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error listing deleted blocks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to list deleted blocks"}
        )


__all__ = ["router"]

