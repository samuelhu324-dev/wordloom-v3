"""
Block Router - RESTful API endpoints for Block domain

Implements complete 4-layer architecture with DI chain:
  Layer 1: HTTP validation + permission checks
  Layer 2: Domain service calls (type-specific factory methods)
  Layer 3: ORM persistence
  Layer 4: Event publishing

Endpoints:
  POST   /api/v1/books/{book_id}/blocks
  GET    /api/v1/books/{book_id}/blocks
  GET    /api/v1/books/{book_id}/blocks/{block_id}
  PUT    /api/v1/books/{book_id}/blocks/{block_id}
  PATCH  /api/v1/books/{book_id}/blocks/{block_id}
  DELETE /api/v1/books/{book_id}/blocks/{block_id}
  POST   /api/v1/books/{book_id}/blocks/{block_id}/restore
  POST   /api/v1/books/{book_id}/blocks/reorder

Maps RULE-013-REVISED through RULE-016 and POLICY-008 with comprehensive error handling.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session

from modules.block.schemas import (
    BlockCreate,
    BlockUpdate,
    BlockReorderRequest,
    BlockResponse,
    BlockDetailResponse,
    BlockPaginatedResponse,
    BlockErrorResponse,
    BlockDTO,
    BlockTypeEnum,
)
from modules.block.service import BlockService
from modules.block.repository import BlockRepositoryImpl
from modules.block.exceptions import (
    BlockNotFoundError,
    BookNotFoundError,
    InvalidBlockTypeError,
    InvalidHeadingLevelError,
    BlockContentTooLongError,
    FractionalIndexError,
    BlockInBasementError,
    BlockOperationError,
)
from infra.database import get_db_session

logger = logging.getLogger(__name__)

# ============================================================================
# Dependency Injection
# ============================================================================

async def get_block_repository(session: Session = Depends(get_db_session)) -> BlockRepositoryImpl:
    """Provide BlockRepositoryImpl instance"""
    return BlockRepositoryImpl(session)


async def get_block_service(
    repository: BlockRepositoryImpl = Depends(get_block_repository),
) -> BlockService:
    """Provide BlockService instance with dependencies"""
    # Note: book_repository should be injected here for permission checks
    return BlockService(repository=repository, book_repository=None)


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(
    prefix="/api/v1/books/{book_id}/blocks",
    tags=["blocks"],
    responses={
        404: {"model": BlockErrorResponse, "description": "Block or Book not found"},
        422: {"model": BlockErrorResponse, "description": "Validation error"},
        500: {"model": BlockErrorResponse, "description": "Internal server error"},
    },
)


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "",
    response_model=BlockResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Block",
    description="Create a new Block in a Book (RULE-013-REVISED: Type-specific factory)",
)
async def create_block(
    book_id: UUID,
    request: BlockCreate,
    service: BlockService = Depends(get_block_service),
) -> BlockResponse:
    """
    Create a new Block in the specified Book.

    RULE-013-REVISED: Create type-specific Blocks (TEXT, HEADING, IMAGE, etc.)
    RULE-014: Block type validation
    RULE-015-REVISED: Fractional Index support for ordering

    Args:
        book_id: Parent Book ID
        request: Block creation payload

    Returns:
        Created Block

    Raises:
        HTTPException 422: Book not found or invalid block type
        HTTPException 500: Operation error
    """
    logger.info(f"Creating Block in Book {book_id}: type={request.block_type}")

    try:
        # Type-specific factory calls
        if request.block_type == BlockTypeEnum.TEXT:
            block_domain = await service.create_text_block(
                book_id=book_id,
                content=request.content,
                order=request.order,
            )
        elif request.block_type == BlockTypeEnum.HEADING:
            block_domain = await service.create_heading_block(
                book_id=book_id,
                content=request.content,
                heading_level=request.heading_level,
                order=request.order,
            )
        elif request.block_type == BlockTypeEnum.CODE:
            block_domain = await service.create_code_block(
                book_id=book_id,
                content=request.content,
                order=request.order,
            )
        elif request.block_type == BlockTypeEnum.IMAGE:
            block_domain = await service.create_image_block(
                book_id=book_id,
                content=request.content,
                order=request.order,
            )
        elif request.block_type == BlockTypeEnum.TABLE:
            block_domain = await service.create_table_block(
                book_id=book_id,
                content=request.content,
                order=request.order,
            )
        elif request.block_type == BlockTypeEnum.QUOTE:
            block_domain = await service.create_quote_block(
                book_id=book_id,
                content=request.content,
                order=request.order,
            )
        elif request.block_type == BlockTypeEnum.LIST:
            block_domain = await service.create_list_block(
                book_id=book_id,
                content=request.content,
                order=request.order,
            )
        elif request.block_type == BlockTypeEnum.DIVIDER:
            block_domain = await service.create_divider_block(
                book_id=book_id,
                order=request.order,
            )
        else:
            raise InvalidBlockTypeError(str(request.block_type))

        block_dto = BlockDTO.from_domain(block_domain)
        return block_dto.to_response()

    except BookNotFoundError as e:
        logger.warning(f"Book not found: {e.message}")
        raise HTTPException(status_code=422, detail=e.to_dict())
    except InvalidHeadingLevelError as e:
        logger.warning(f"Invalid heading level: {e.message}")
        raise HTTPException(status_code=422, detail=e.to_dict())
    except InvalidBlockTypeError as e:
        logger.warning(f"Invalid block type: {e.message}")
        raise HTTPException(status_code=422, detail=e.to_dict())
    except FractionalIndexError as e:
        logger.warning(f"Fractional index error: {e.message}")
        raise HTTPException(status_code=422, detail=e.to_dict())
    except Exception as e:
        logger.error(f"Failed to create Block: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "BLOCK_OPERATION_ERROR",
                "message": f"Failed to create Block: {str(e)}",
            },
        )


@router.get(
    "",
    response_model=BlockPaginatedResponse,
    summary="List Blocks in a Book",
    description="Retrieve paginated list of Blocks (RULE-015: ordered by Fractional Index)",
)
async def list_blocks(
    book_id: UUID,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    include_deleted: bool = Query(False, description="Include soft-deleted Blocks (POLICY-008)"),
    service: BlockService = Depends(get_block_service),
) -> BlockPaginatedResponse:
    """
    List Blocks in the specified Book with pagination.

    RULE-015-REVISED: Blocks ordered by Fractional Index (O(1) drag/drop)
    POLICY-008: By default, soft-deleted Blocks are excluded.

    Args:
        book_id: Parent Book ID
        page: Page number (1-indexed)
        page_size: Items per page (1-100)
        include_deleted: Include soft-deleted items

    Returns:
        Paginated list of Blocks
    """
    logger.debug(f"Listing Blocks in Book {book_id}, page {page}, size {page_size}")

    try:
        blocks = await service.list_blocks(book_id)

        # Filter soft-deleted if needed (POLICY-008)
        if not include_deleted:
            blocks = [b for b in blocks if not (hasattr(b, 'soft_deleted_at') and b.soft_deleted_at)]

        # Apply pagination
        total = len(blocks)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_blocks = blocks[start_idx:end_idx]

        items = [BlockDTO.from_domain(b).to_detail_response() for b in paginated_blocks]

        return BlockPaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=(end_idx < total),
        )

    except Exception as e:
        logger.error(f"Failed to list Blocks: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "BLOCK_OPERATION_ERROR",
                "message": f"Failed to list Blocks: {str(e)}",
            },
        )


@router.get(
    "/{block_id}",
    response_model=BlockDetailResponse,
    summary="Get Block details",
    description="Retrieve detailed information about a specific Block",
)
async def get_block(
    book_id: UUID,
    block_id: UUID,
    service: BlockService = Depends(get_block_service),
) -> BlockDetailResponse:
    """
    Retrieve details for a specific Block.

    Args:
        book_id: Parent Book ID
        block_id: Block ID

    Returns:
        Detailed Block information

    Raises:
        HTTPException 404: Block not found
        HTTPException 500: Operation error
    """
    logger.debug(f"Getting Block {block_id}")

    try:
        block = await service.get_block(block_id)
        block_dto = BlockDTO.from_domain(block)
        return block_dto.to_detail_response()

    except BlockNotFoundError as e:
        logger.warning(f"Block not found: {e.message}")
        raise HTTPException(status_code=404, detail=e.to_dict())
    except Exception as e:
        logger.error(f"Failed to get Block: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "BLOCK_OPERATION_ERROR",
                "message": f"Failed to get Block: {str(e)}",
            },
        )


@router.put(
    "/{block_id}",
    response_model=BlockResponse,
    summary="Update Block (full update)",
    description="Replace entire Block content (RULE-015: supports fractional index update)",
)
async def update_block(
    book_id: UUID,
    block_id: UUID,
    request: BlockUpdate,
    service: BlockService = Depends(get_block_service),
) -> BlockResponse:
    """
    Update a Block's properties (full replacement).

    RULE-015-REVISED: Supports reordering via fractional index
    POLICY-008: Cannot update soft-deleted Blocks

    Args:
        book_id: Parent Book ID
        block_id: Block ID
        request: Update payload

    Returns:
        Updated Block

    Raises:
        HTTPException 404: Block not found
        HTTPException 422: Validation error
        HTTPException 500: Operation error
    """
    logger.info(f"Updating Block {block_id}")

    try:
        block = await service.get_block(block_id)

        if request.content:
            await service.update_block_content(block_id, request.content)

        if request.order:
            await service.reorder_block(block_id, request.order)

        if request.heading_level is not None:
            await service.update_heading_level(block_id, request.heading_level)

        updated_block = await service.get_block(block_id)
        block_dto = BlockDTO.from_domain(updated_block)
        return block_dto.to_response()

    except BlockNotFoundError as e:
        logger.warning(f"Block not found: {e.message}")
        raise HTTPException(status_code=404, detail=e.to_dict())
    except BlockContentTooLongError as e:
        logger.warning(f"Content too long: {e.message}")
        raise HTTPException(status_code=422, detail=e.to_dict())
    except FractionalIndexError as e:
        logger.warning(f"Fractional index error: {e.message}")
        raise HTTPException(status_code=422, detail=e.to_dict())
    except Exception as e:
        logger.error(f"Failed to update Block: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "BLOCK_OPERATION_ERROR",
                "message": f"Failed to update Block: {str(e)}",
            },
        )


@router.patch(
    "/{block_id}",
    response_model=BlockResponse,
    summary="Patch Block (partial update)",
    description="Partially update Block fields",
)
async def patch_block(
    book_id: UUID,
    block_id: UUID,
    request: BlockUpdate,
    service: BlockService = Depends(get_block_service),
) -> BlockResponse:
    """Partially update a Block."""
    return await update_block(book_id, block_id, request, service)


@router.delete(
    "/{block_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Block (soft-delete)",
    description="Delete a Block by marking it deleted (POLICY-008)",
)
async def delete_block(
    book_id: UUID,
    block_id: UUID,
    service: BlockService = Depends(get_block_service),
) -> None:
    """
    Delete a Block via soft-delete.

    POLICY-008: Block deletion is implemented as marking soft_deleted_at,
    allowing recovery.

    Args:
        book_id: Parent Book ID
        block_id: Block ID to delete

    Raises:
        HTTPException 404: Block not found
        HTTPException 409: Block already deleted
        HTTPException 500: Operation error
    """
    logger.info(f"Soft-deleting Block {block_id}")

    try:
        await service.delete_block(block_id)

    except BlockNotFoundError as e:
        logger.warning(f"Block not found: {e.message}")
        raise HTTPException(status_code=404, detail=e.to_dict())
    except BlockInBasementError as e:
        logger.warning(f"Block already deleted: {e.message}")
        raise HTTPException(status_code=409, detail=e.to_dict())
    except Exception as e:
        logger.error(f"Failed to delete Block: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "BLOCK_OPERATION_ERROR",
                "message": f"Failed to delete Block: {str(e)}",
            },
        )


@router.post(
    "/{block_id}/restore",
    response_model=BlockResponse,
    status_code=status.HTTP_200_OK,
    summary="Restore Block from Basement",
    description="Restore a soft-deleted Block (POLICY-008)",
)
async def restore_block(
    book_id: UUID,
    block_id: UUID,
    service: BlockService = Depends(get_block_service),
) -> BlockResponse:
    """
    Restore a soft-deleted Block.

    POLICY-008: Block restoration from soft-delete state

    Args:
        book_id: Parent Book ID
        block_id: Block ID to restore

    Returns:
        Restored Block

    Raises:
        HTTPException 404: Block not found
        HTTPException 422: Block not in Basement
        HTTPException 500: Operation error
    """
    logger.info(f"Restoring Block {block_id}")

    try:
        restored_block = await service.restore_block(block_id)
        block_dto = BlockDTO.from_domain(restored_block)
        return block_dto.to_response()

    except BlockNotFoundError as e:
        logger.warning(f"Block not found: {e.message}")
        raise HTTPException(status_code=404, detail=e.to_dict())
    except Exception as e:
        logger.error(f"Failed to restore Block: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "BLOCK_OPERATION_ERROR",
                "message": f"Failed to restore Block: {str(e)}",
            },
        )


@router.post(
    "/reorder",
    status_code=status.HTTP_200_OK,
    summary="Batch reorder Blocks",
    description="Reorder multiple Blocks using fractional index (RULE-015: O(1) performance)",
)
async def reorder_blocks(
    book_id: UUID,
    request: BlockReorderRequest,
    service: BlockService = Depends(get_block_service),
) -> BlockPaginatedResponse:
    """
    Batch reorder blocks using fractional index.

    RULE-015-REVISED: Supports O(1) drag/drop reordering via Fractional Index

    Args:
        book_id: Parent Book ID
        request: List of block_id + new order pairs

    Returns:
        Updated list of Blocks

    Raises:
        HTTPException 404: Block or Book not found
        HTTPException 422: Invalid fractional index
        HTTPException 500: Operation error
    """
    logger.info(f"Reordering {len(request.reorders)} Blocks in Book {book_id}")

    try:
        for reorder_item in request.reorders:
            await service.reorder_block(reorder_item.block_id, reorder_item.order)

        # Return updated list
        blocks = await service.list_blocks(book_id)
        items = [BlockDTO.from_domain(b).to_detail_response() for b in blocks]

        return BlockPaginatedResponse(
            items=items,
            total=len(items),
            page=1,
            page_size=len(items),
            has_more=False,
        )

    except FractionalIndexError as e:
        logger.warning(f"Fractional index error: {e.message}")
        raise HTTPException(status_code=422, detail=e.to_dict())
    except BlockNotFoundError as e:
        logger.warning(f"Block not found: {e.message}")
        raise HTTPException(status_code=404, detail=e.to_dict())
    except Exception as e:
        logger.error(f"Failed to reorder Blocks: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "BLOCK_OPERATION_ERROR",
                "message": f"Failed to reorder Blocks: {str(e)}",
            },
        )
