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
from dataclasses import asdict

from api.app.dependencies import DIContainer, get_di_container
from api.app.shared.actor import Actor
from api.app.config.security import get_current_actor
from api.app.config.setting import get_settings
from api.app.modules.block.application.ports.input import (
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
from api.app.modules.block.exceptions import (
    DomainException,
)
from api.app.modules.chronicle.application.todo_facts import diff_todo_list_facts


_settings = get_settings()


logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["blocks"])


# ============================================================================
# Create Block
# ============================================================================

@router.post(
    "",
    response_model=None,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new block",
    description="Create a new block with type-specific factory (RULE-013-REVISED: TEXT|HEADING|CODE|IMAGE|TABLE|QUOTE|LIST|DIVIDER)"
)
async def create_block(
    request: CreateBlockRequest,
    actor: Actor = Depends(get_current_actor),
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
        logger.info("Creating block: type=%s, book_id=%s", request.block_type, request.book_id)

        create_request = CreateBlockRequest(
            book_id=request.book_id,
            block_type=request.block_type,
            content=request.content,
            metadata=request.metadata,
            position_after_id=request.position_after_id,
            actor_user_id=actor.user_id,
            enforce_owner_check=(not _settings.allow_dev_library_owner_override),
        )

        use_case = di.get_create_block_use_case()
        created_block = await use_case.execute(create_request)

        # Chronicle: record stable fact for timeline/audit.
        try:
            chronicle = di.get_chronicle_recorder_service()
            await chronicle.record_block_created(
                book_id=request.book_id,
                block_id=getattr(created_block, "id", None) or getattr(created_block, "block_id", None),
                block_type=str(request.block_type) if getattr(request, "block_type", None) else None,
                actor_id=actor.user_id,
            )
        except Exception:
            # Non-blocking: keep write path resilient.
            logger.warning("Chronicle record_block_created failed", exc_info=True)

        response: BlockResponse = BlockResponse.from_domain(created_block)
        logger.info("Block created successfully: block_id=%s", response.id)
        return asdict(response)
    except DomainException as error:
        logger.warning("Block creation failed: %s", error)
        raise HTTPException(
            status_code=error.http_status,
            detail=error.to_dict(),
        )
    except Exception as error:
        logger.error("Unexpected error creating block: %s", error, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to create block"},
        )


# ============================================================================
# List Blocks (RULE-015-REVISED: Ordered by sort_key, POLICY-008: soft-delete filter)
# ============================================================================

@router.get(
    "",
    response_model=None,
    summary="List blocks",
    description="List blocks ordered by sort_key with soft-delete filtering (RULE-015-REVISED, POLICY-008)"
)
async def list_blocks(
    book_id: UUID = Query(..., description="Book ID (required)"),
    include_deleted: bool = Query(False, description="Include soft-deleted blocks (RULE-012/POLICY-008)"),
    skip: int = Query(0, ge=0, description="Pagination skip"),
    limit: int = Query(50, ge=1, le=100, description="Pagination limit"),
    actor: Actor = Depends(get_current_actor),
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
            include_deleted=include_deleted,
            actor_user_id=actor.user_id,
            enforce_owner_check=(not _settings.allow_dev_library_owner_override),
        )
        use_case = di.get_list_blocks_use_case()
        response: BlockListResponse = await use_case.execute(request)

        # Chronicle: treat first page list as opening the book content.
        if skip == 0 and not include_deleted:
            try:
                chronicle = di.get_chronicle_recorder_service()
                await chronicle.record_book_opened(book_id=book_id, actor_id=actor.user_id)
            except Exception:
                logger.warning("Chronicle record_book_opened failed", exc_info=True)

        logger.debug(f"Listed {len(response.items)} blocks from book {book_id}")
        return asdict(response)
    except DomainException as error:
        logger.warning("List blocks failed: %s", error)
        raise HTTPException(status_code=error.http_status, detail=error.to_dict())
    except Exception as error:
        logger.error("Unexpected error listing blocks: %s", error, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to list blocks"}
        )


# ============================================================================
# Get Block (RULE-013-REVISED: Query any block)
# ============================================================================

@router.get(
    "/{block_id}",
    response_model=None,
    summary="Get block by ID",
    description="Retrieve detailed information about a specific block"
)
async def get_block(
    block_id: UUID,
    actor: Actor = Depends(get_current_actor),
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
        request = GetBlockRequest(
            block_id=block_id,
            actor_user_id=actor.user_id,
            enforce_owner_check=(not _settings.allow_dev_library_owner_override),
        )
        use_case = di.get_get_block_use_case()
        block = await use_case.execute(request)
        response: BlockResponse = BlockResponse.from_domain(block)
        logger.debug(f"Retrieved block: {response.id}")
        return asdict(response)
    except DomainException as error:
        logger.warning("Get block failed: %s", error)
        raise HTTPException(status_code=error.http_status, detail=error.to_dict())
    except Exception as error:
        logger.error("Unexpected error getting block: %s", error, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to get block"}
        )


# ============================================================================
# Update Block (RULE-014: Content update)
# ============================================================================

@router.patch(
    "/{block_id}",
    response_model=None,
    summary="Update a block",
    description="Update block properties (content, heading_level) - RULE-014"
)
async def update_block(
    block_id: UUID,
    request: UpdateBlockRequest,
    actor: Actor = Depends(get_current_actor),
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

        existing_block = None
        existing_block_type: Optional[str] = None
        existing_content: Optional[str] = None
        if request.content is not None:
            try:
                get_uc = di.get_get_block_use_case()
                existing_block = await get_uc.execute(
                    GetBlockRequest(
                        block_id=block_id,
                        actor_user_id=actor.user_id,
                        enforce_owner_check=(not _settings.allow_dev_library_owner_override),
                    )
                )
                existing_type = getattr(existing_block, "type", None)
                existing_block_type = getattr(existing_type, "value", None) or (str(existing_type) if existing_type is not None else None)
                existing_content = str(getattr(existing_block, "content", ""))
            except Exception:
                existing_block = None

        use_case = di.get_update_block_use_case()
        update_request = UpdateBlockRequest(
            block_id=block_id,
            content=request.content,
            metadata=request.metadata,
            actor_user_id=actor.user_id,
            enforce_owner_check=(not _settings.allow_dev_library_owner_override),
        )
        updated_block = await use_case.execute(update_request)

        # Chronicle: record stable fact for timeline/audit.
        try:
            changed: List[str] = []
            if request.content is not None:
                changed.append("content")
            if request.metadata is not None:
                changed.append("metadata")
            fields = {"changed": changed}
            chronicle = di.get_chronicle_recorder_service()
            await chronicle.record_block_updated(
                book_id=getattr(updated_block, "book_id", None),
                block_id=block_id,
                fields=fields,
                actor_id=actor.user_id,
            )

            # TODO facts: derive promoted/completed from todo_list content changes.
            if (
                request.content is not None
                and existing_block_type == "todo_list"
                and getattr(updated_block, "book_id", None) is not None
            ):
                promoted_events, completed_events = diff_todo_list_facts(
                    old_content=existing_content,
                    new_content=request.content,
                )
                for item in promoted_events:
                    await chronicle.record_todo_promoted_from_block(
                        book_id=getattr(updated_block, "book_id", None),
                        block_id=block_id,
                        todo_id=item.get("todo_id"),
                        text=item.get("text"),
                        is_urgent=item.get("is_urgent"),
                        actor_id=actor.user_id,
                    )
                for item in completed_events:
                    await chronicle.record_todo_completed(
                        book_id=getattr(updated_block, "book_id", None),
                        block_id=block_id,
                        todo_id=item.get("todo_id"),
                        text=item.get("text"),
                        promoted=item.get("promoted"),
                        actor_id=actor.user_id,
                    )
        except Exception:
            logger.warning("Chronicle record_block_updated failed", exc_info=True)

        response: BlockResponse = BlockResponse.from_domain(updated_block)
        logger.info(f"Block updated successfully: block_id={block_id}")
        return asdict(response)
    except DomainException as error:
        logger.warning("Block update failed: %s", error)
        raise HTTPException(status_code=error.http_status, detail=error.to_dict())
    except Exception as error:
        logger.error("Unexpected error updating block: %s", error, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to update block"}
        )


# ============================================================================
# Reorder Blocks (RULE-015-REVISED: Fractional Index O(1) drag/drop)
# ============================================================================

@router.post(
    "/reorder",
    response_model=None,
    summary="Reorder blocks (batch fractional index)",
    description="Batch reorder blocks with fractional index for O(1) drag/drop (RULE-015-REVISED)"
)
async def reorder_blocks(
    request: ReorderBlocksRequest,
    actor: Actor = Depends(get_current_actor),
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

        reorder_request = ReorderBlocksRequest(
            block_id=request.block_id,
            position_after_id=request.position_after_id,
            position_before_id=request.position_before_id,
            new_order=request.new_order,
            actor_user_id=actor.user_id,
            enforce_owner_check=(not _settings.allow_dev_library_owner_override),
        )
        use_case = di.get_reorder_blocks_use_case()
        response: BlockResponse = await use_case.execute(reorder_request)
        logger.info(f"Block reordered successfully: block_id={request.block_id}")
        return asdict(response)
    except DomainException as error:
        logger.warning("Reorder failed: %s", error)
        raise HTTPException(status_code=error.http_status, detail=error.to_dict())
    except Exception as error:
        logger.error("Unexpected error reordering block: %s", error, exc_info=True)
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
    actor: Actor = Depends(get_current_actor),
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

        # Fetch book_id before delete for Chronicle fact.
        book_id: Optional[UUID] = None
        try:
            get_uc = di.get_get_block_use_case()
            existing = await get_uc.execute(
                GetBlockRequest(
                    block_id=block_id,
                    actor_user_id=actor.user_id,
                    enforce_owner_check=(not _settings.allow_dev_library_owner_override),
                )
            )
            book_id = getattr(existing, "book_id", None)
        except Exception:
            book_id = None

        request = DeleteBlockRequest(
            block_id=block_id,
            actor_user_id=actor.user_id,
            enforce_owner_check=(not _settings.allow_dev_library_owner_override),
        )
        use_case = di.get_delete_block_use_case()
        await use_case.execute(request)

        if book_id is not None:
            try:
                chronicle = di.get_chronicle_recorder_service()
                await chronicle.record_block_soft_deleted(
                    book_id=book_id,
                    block_id=block_id,
                    actor_id=actor.user_id,
                )
            except Exception:
                logger.warning("Chronicle record_block_soft_deleted failed", exc_info=True)

        logger.info(f"Block soft-deleted successfully: block_id={block_id}")
    except DomainException as error:
        logger.warning("Delete failed: %s", error)
        raise HTTPException(status_code=error.http_status, detail=error.to_dict())
    except Exception as error:
        logger.error("Unexpected error deleting block: %s", error, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to delete block"}
        )


# ============================================================================
# Restore Block (RULE-013-REVISED: Paperballs recovery with 3-level fallback)
# ============================================================================

@router.post(
    "/{block_id}/restore",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Restore a deleted block from Paperballs",
    description="Restore block from soft-delete with 3-level positioning fallback (RULE-013-REVISED)"
)
async def restore_block(
    block_id: UUID,
    actor: Actor = Depends(get_current_actor),
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
        request = RestoreBlockRequest(
            block_id=block_id,
            actor_user_id=actor.user_id,
            enforce_owner_check=(not _settings.allow_dev_library_owner_override),
        )
        use_case = di.get_restore_block_use_case()
        restored_block = await use_case.execute(request)

        # Chronicle: record stable fact for timeline/audit.
        try:
            chronicle = di.get_chronicle_recorder_service()
            await chronicle.record_block_restored(
                book_id=getattr(restored_block, "book_id", None),
                block_id=block_id,
                actor_id=actor.user_id,
            )
        except Exception:
            logger.warning("Chronicle record_block_restored failed", exc_info=True)

        response: BlockResponse = BlockResponse.from_domain(restored_block)
        logger.info(f"Block restored successfully: block_id={block_id}")
        return asdict(response)
    except DomainException as error:
        logger.warning("Restore failed: %s", error)
        raise HTTPException(status_code=error.http_status, detail=error.to_dict())
    except Exception as error:
        logger.error("Unexpected error restoring block: %s", error, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to restore block"}
        )


# ============================================================================
# List Deleted Blocks (RULE-012: Paperballs view with recovery metadata)
# ============================================================================

@router.get(
    "/deleted",
    response_model=None,
    summary="List deleted blocks (Paperballs view)",
    description="List soft-deleted blocks with recovery metadata (RULE-012, Paperballs)"
)
async def list_deleted_blocks(
    book_id: UUID = Query(..., description="Book ID (required)"),
    skip: int = Query(0, ge=0, description="Pagination skip"),
    limit: int = Query(50, ge=1, le=100, description="Pagination limit"),
    actor: Actor = Depends(get_current_actor),
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
            limit=limit,
            actor_user_id=actor.user_id,
            enforce_owner_check=(not _settings.allow_dev_library_owner_override),
        )
        use_case = di.get_list_deleted_blocks_use_case()
        response: BlockListResponse = await use_case.execute(request)
        logger.debug(f"Listed {len(response.items)} deleted blocks from book {book_id}")
        return asdict(response)
    except DomainException as error:
        logger.warning("List deleted blocks failed: %s", error)
        raise HTTPException(status_code=error.http_status, detail=error.to_dict())
    except Exception as error:
        logger.error("Unexpected error listing deleted blocks: %s", error, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to list deleted blocks"}
        )


__all__ = ["router"]



