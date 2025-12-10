"""Tag Router - FastAPI endpoints for tag management

Architecture (ADR-025: Tag Router & API):
========================================
- Dependency injection: FastAPI Depends → service → repository → domain
- Exception handling with HTTP status code mapping
- Request/response validation with Pydantic schemas
- Structured logging for debugging
- FastAPI native patterns (no DIContainer)

Endpoints (11 endpoints):
- POST /tags - Create new tag
- POST /tags/{id}/subtags - Create subtag
- GET /tags/{id} - Get tag details
- PATCH /tags/{id} - Update tag
- DELETE /tags/{id} - Soft delete tag
- POST /tags/{id}/restore - Restore deleted tag
- GET /tags - List tags (search/pagination)
- GET /tags/hierarchy - Get hierarchical tree
- POST /tags/{id}/associate - Link tag to entity
- DELETE /tags/{id}/associate - Unlink tag
- GET /tags/{entity_type}/{entity_id}/tags - Get entity tags
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID
import logging

from app.shared.deps import get_db
from .domain import EntityType
from .schemas import (
    CreateTagRequest, CreateSubtagRequest, UpdateTagRequest,
    AssociateTagRequest, TagResponse, TagListResponse,
    EntityTagsResponse, TagHierarchyResponse, ErrorResponse
)
from .service import TagService
from .exceptions import (
    TagNotFoundError, TagAlreadyExistsError,
    TagInvalidNameError, TagInvalidColorError,
    TagInvalidHierarchyError, TagAlreadyDeletedError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tags", tags=["tags"])


# ============================================================================
# Dependency Injection
# ============================================================================

async def get_tag_service(db = Depends(get_db)) -> TagService:
    """Get TagService instance with database session"""
    from .repository import SQLAlchemyTagRepository
    repository = SQLAlchemyTagRepository(db)
    return TagService(repository)


# ============================================================================
# POST: Create / Create Subtag
# ============================================================================

@router.post(
    "",
    response_model=TagResponse,
    status_code=201,
    summary="Create a new top-level tag",
    responses={
        201: {"description": "Tag created successfully"},
        409: {"model": ErrorResponse, "description": "Tag name already exists"},
        422: {"model": ErrorResponse, "description": "Invalid tag data"},
    }
)
async def create_tag(
    request: CreateTagRequest,
    service: TagService = Depends(get_tag_service)
):
    """
    Create a new top-level tag.

    **Rules (RULE-018):** name unique, 1-50 chars; color hex format; optional icon/description

    **Example:** `{"name": "Python", "color": "#3776AB", "icon": "code"}`
    """
    try:
        tag = await service.create_tag(
            name=request.name,
            color=request.color,
            icon=request.icon,
            description=request.description
        )
        logger.info(f"Created tag {tag.id} ({tag.name})")
        return TagResponse.from_orm(tag)
    except TagAlreadyExistsError as e:
        logger.warning(f"Tag conflict: {e}")
        raise HTTPException(status_code=409, detail=e.to_dict())
    except (TagInvalidNameError, TagInvalidColorError) as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=422, detail=e.to_dict())


@router.post(
    "/{tag_id}/subtags",
    response_model=TagResponse,
    status_code=201,
    summary="Create hierarchical sub-tag",
    responses={
        201: {"description": "Sub-tag created"},
        404: {"model": ErrorResponse, "description": "Parent tag not found"},
        422: {"model": ErrorResponse, "description": "Invalid hierarchy"},
    }
)
async def create_subtag(
    tag_id: UUID,
    request: CreateSubtagRequest,
    service: TagService = Depends(get_tag_service)
):
    """
    Create hierarchical sub-tag under a parent.

    **Rules (RULE-020):** parent must exist, no cycles, max 3 levels deep
    """
    try:
        tag = await service.create_subtag(
            parent_tag_id=request.parent_tag_id,
            name=request.name,
            color=request.color,
            icon=request.icon
        )
        logger.info(f"Created subtag {tag.id} under {request.parent_tag_id}")
        return TagResponse.from_orm(tag)
    except TagNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())
    except TagInvalidHierarchyError as e:
        raise HTTPException(status_code=422, detail=e.to_dict())


# ============================================================================
# GET: Retrieve / List / Hierarchy
# ============================================================================

@router.get(
    "/{tag_id}",
    response_model=TagResponse,
    summary="Get tag details",
)
async def get_tag(
    tag_id: UUID,
    service: TagService = Depends(get_tag_service)
):
    """Get detailed information about a specific tag."""
    try:
        tag = await service.get_tag_by_id(tag_id)
        if not tag:
            raise TagNotFoundError(tag_id)
        logger.info(f"Retrieved tag {tag_id}")
        return TagResponse.from_orm(tag)
    except TagNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())


@router.get(
    "",
    response_model=TagListResponse,
    summary="List tags with search and pagination",
)
async def list_tags(
    keyword: Optional[str] = Query(None, min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("usage_count", regex="^(usage_count|name|created_at)$"),
    service: TagService = Depends(get_tag_service)
):
    """
    List tags with optional search and pagination.

    **Query Parameters:**
    - `keyword`: Search by partial name match (case-insensitive)
    - `page`: Page number (1-indexed)
    - `size`: Items per page (1-100)
    - `sort_by`: Sort field (usage_count|name|created_at)
    """
    try:
        if keyword:
            tags = await service.search_tags(keyword, limit=size * 10)
        else:
            tags = await service.get_most_used_tags(limit=size * 10)

        total = len(tags)
        start = (page - 1) * size
        end = start + size
        items = tags[start:end]

        logger.info(f"Listed tags: keyword={keyword}, page={page}, size={size}")
        return TagListResponse(
            items=[TagResponse.from_orm(tag) for tag in items],
            total=total,
            page=page,
            size=size,
            has_more=end < total
        )
    except Exception as e:
        logger.error(f"List tags error: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})


@router.get(
    "/hierarchy",
    response_model=List[TagHierarchyResponse],
    summary="Get hierarchical tag tree",
)
async def get_tag_hierarchy(
    service: TagService = Depends(get_tag_service)
):
    """Get all tags in hierarchical structure (tree format)."""
    try:
        tags = await service.get_tag_hierarchy()
        logger.info(f"Retrieved tag hierarchy ({len(tags)} top-level tags)")
        return [
            TagHierarchyResponse(
                id=tag.id,
                name=tag.name,
                color=tag.color,
                icon=tag.icon,
                level=tag.level,
                usage_count=tag.usage_count,
                children=[]
            )
            for tag in tags
        ]
    except Exception as e:
        logger.error(f"Hierarchy error: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})


# ============================================================================
# PATCH: Update
# ============================================================================

@router.patch(
    "/{tag_id}",
    response_model=TagResponse,
    summary="Update tag properties",
    responses={
        200: {"description": "Tag updated"},
        404: {"model": ErrorResponse, "description": "Tag not found"},
        409: {"model": ErrorResponse, "description": "Tag already deleted"},
        422: {"model": ErrorResponse, "description": "Invalid update data"},
    }
)
async def update_tag(
    tag_id: UUID,
    request: UpdateTagRequest,
    service: TagService = Depends(get_tag_service)
):
    """Update tag properties (name, color, icon, description). At least one field required."""
    try:
        tag = await service.update_tag(
            tag_id=tag_id,
            name=request.name,
            color=request.color,
            icon=request.icon,
            description=request.description
        )
        logger.info(f"Updated tag {tag_id}")
        return TagResponse.from_orm(tag)
    except TagNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())
    except TagAlreadyDeletedError as e:
        raise HTTPException(status_code=409, detail=e.to_dict())
    except (TagAlreadyExistsError, TagInvalidNameError, TagInvalidColorError) as e:
        raise HTTPException(status_code=422, detail=e.to_dict())


# ============================================================================
# DELETE: Delete / Restore
# ============================================================================

@router.delete(
    "/{tag_id}",
    status_code=204,
    summary="Soft delete a tag",
    responses={
        204: {"description": "Tag deleted"},
        404: {"model": ErrorResponse, "description": "Tag not found"},
        409: {"model": ErrorResponse, "description": "Tag already deleted"},
    }
)
async def delete_tag(
    tag_id: UUID,
    service: TagService = Depends(get_tag_service)
):
    """
    Soft delete a tag (preserves associations).

    Can be restored later via POST /tags/{id}/restore
    """
    try:
        await service.delete_tag(tag_id)
        logger.info(f"Soft deleted tag {tag_id}")
    except TagNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())
    except TagAlreadyDeletedError as e:
        raise HTTPException(status_code=409, detail=e.to_dict())


@router.post(
    "/{tag_id}/restore",
    response_model=TagResponse,
    summary="Restore a deleted tag",
)
async def restore_tag(
    tag_id: UUID,
    service: TagService = Depends(get_tag_service)
):
    """Restore a soft-deleted tag."""
    try:
        tag = await service.restore_tag(tag_id)
        logger.info(f"Restored tag {tag_id}")
        return TagResponse.from_orm(tag)
    except TagNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())


# ============================================================================
# POST/DELETE: Associate / Disassociate
# ============================================================================

@router.post(
    "/{tag_id}/associate",
    status_code=204,
    summary="Associate tag with an entity",
    responses={
        204: {"description": "Tag associated"},
        404: {"model": ErrorResponse, "description": "Tag not found"},
        422: {"model": ErrorResponse, "description": "Invalid request"},
    }
)
async def associate_tag(
    tag_id: UUID,
    request: AssociateTagRequest,
    service: TagService = Depends(get_tag_service)
):
    """
    Associate a tag with an entity (Book/Bookshelf/Block).

    **Rules (RULE-019):** Idempotent; tag must exist and not be deleted; valid entity_type
    """
    try:
        await service.associate_tag_with_entity(
            tag_id=tag_id,
            entity_type=EntityType(request.entity_type.value),
            entity_id=request.entity_id
        )
        logger.info(f"Associated tag {tag_id} with {request.entity_type} {request.entity_id}")
    except TagNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())


@router.delete(
    "/{tag_id}/associate",
    status_code=204,
    summary="Disassociate tag from an entity",
)
async def disassociate_tag(
    tag_id: UUID,
    entity_type: EntityType = Query(...),
    entity_id: UUID = Query(...),
    service: TagService = Depends(get_tag_service)
):
    """Remove association between a tag and an entity."""
    try:
        await service.disassociate_tag_from_entity(
            tag_id=tag_id,
            entity_type=entity_type,
            entity_id=entity_id
        )
        logger.info(f"Disassociated tag {tag_id} from {entity_type} {entity_id}")
    except TagNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())


# ============================================================================
# GET: Get Entity Tags
# ============================================================================

@router.get(
    "/{entity_type}/{entity_id}/tags",
    response_model=EntityTagsResponse,
    summary="Get all tags for an entity",
)
async def get_entity_tags(
    entity_type: str,
    entity_id: UUID,
    service: TagService = Depends(get_tag_service)
):
    """
    Get all tags associated with a specific entity (Book/Bookshelf/Block).

    **Path Parameters:**
    - `entity_type`: BOOKSHELF | BOOK | BLOCK
    - `entity_id`: UUID of the entity
    """
    try:
        entity_type_enum = EntityType(entity_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail={"message": "Invalid entity_type (must be BOOKSHELF, BOOK, or BLOCK)"}
        )

    try:
        tags = await service.get_tags_for_entity(entity_type_enum, entity_id)
        logger.info(f"Retrieved {len(tags)} tags for {entity_type} {entity_id}")
        return EntityTagsResponse(
            entity_type=entity_type_enum,
            entity_id=entity_id,
            tags=[TagResponse.from_orm(tag) for tag in tags],
            count=len(tags)
        )
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID
import logging

from schemas import (
    CreateTagRequest, CreateSubtagRequest, UpdateTagRequest,
    AssociateTagRequest, TagResponse, TagListResponse,
    EntityTagsResponse, TagHierarchyResponse, ErrorResponse
)
from service import TagService
from repository import TagRepository, SQLAlchemyTagRepository
from exceptions import (
    DomainException, TagException,
    TagNotFoundError, TagAlreadyExistsError,
    TagInvalidNameError, TagInvalidColorError,
    TagInvalidHierarchyError, TagAlreadyDeletedError,
    TagOperationError,
)
from domain import EntityType


logger = logging.getLogger(__name__)


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/tags", tags=["tags"])


# ============================================================================
# Dependency Injection
# ============================================================================

async def get_tag_service(
    db_session = Depends(...)  # Database session from FastAPI Depends
) -> TagService:
    """Dependency: Get TagService with repository"""
    repository = SQLAlchemyTagRepository(db_session)
    return TagService(repository)


# ============================================================================
# Request Handlers
# ============================================================================

@router.post(
    "",
    response_model=TagResponse,
    status_code=201,
    summary="Create a new tag",
    responses={
        201: {"description": "Tag created successfully"},
        409: {"model": ErrorResponse, "description": "Tag name already exists"},
        422: {"model": ErrorResponse, "description": "Invalid tag data"},
    }
)
async def create_tag(
    request: CreateTagRequest,
    service: TagService = Depends(get_tag_service)
):
    """
    Create a new top-level tag.

    **Rules (RULE-018):**
    - name: unique, 1-50 characters, non-empty
    - color: valid hex format (#RRGGBB or #RRGGBBAA)
    - icon: optional lucide icon name
    - description: optional text

    **Example Request:**
    ```json
    {
        "name": "Python",
        "color": "#3776AB",
        "icon": "code",
        "description": "Python programming language"
    }
    ```
    """
    try:
        tag = await service.create_tag(
            name=request.name,
            color=request.color,
            icon=request.icon,
            description=request.description
        )
        logger.info(f"Created tag: {tag.id} ({tag.name})")
        return TagResponse.from_orm(tag)

    except TagAlreadyExistsError as e:
        logger.warning(f"Tag creation conflict: {e.message}")
        raise HTTPException(status_code=409, detail=e.to_dict())

    except (TagInvalidNameError, TagInvalidColorError) as e:
        logger.warning(f"Tag validation error: {e.message}")
        raise HTTPException(status_code=422, detail=e.to_dict())

    except Exception as e:
        logger.error(f"Unexpected error creating tag: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})


@router.post(
    "/{tag_id}/subtags",
    response_model=TagResponse,
    status_code=201,
    summary="Create a hierarchical sub-tag",
    responses={
        201: {"description": "Sub-tag created successfully"},
        404: {"model": ErrorResponse, "description": "Parent tag not found"},
        422: {"model": ErrorResponse, "description": "Invalid hierarchy"},
    }
)
async def create_subtag(
    tag_id: UUID,
    request: CreateSubtagRequest,
    service: TagService = Depends(get_tag_service)
):
    """
    Create a hierarchical sub-tag under a parent tag.

    **Rules (RULE-020):**
    - parent_tag_id must reference an existing tag
    - Cannot create cycles
    - Maximum 3 levels deep (0=top, 1=sub, 2=sub-sub)

    **Example Request:**
    ```json
    {
        "parent_tag_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Django",
        "color": "#092E20",
        "icon": "framework"
    }
    ```
    """
    try:
        tag = await service.create_subtag(
            parent_tag_id=request.parent_tag_id,
            name=request.name,
            color=request.color,
            icon=request.icon
        )
        logger.info(f"Created subtag: {tag.id} ({tag.name}) under {request.parent_tag_id}")
        return TagResponse.from_orm(tag)

    except TagNotFoundError as e:
        logger.warning(f"Parent tag not found: {e.message}")
        raise HTTPException(status_code=404, detail=e.to_dict())

    except TagInvalidHierarchyError as e:
        logger.warning(f"Invalid hierarchy: {e.message}")
        raise HTTPException(status_code=422, detail=e.to_dict())

    except Exception as e:
        logger.error(f"Error creating subtag: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})


@router.get(
    "/{tag_id}",
    response_model=TagResponse,
    summary="Get tag details",
    responses={
        200: {"description": "Tag found"},
        404: {"model": ErrorResponse, "description": "Tag not found"},
    }
)
async def get_tag(
    tag_id: UUID,
    service: TagService = Depends(get_tag_service)
):
    """Get detailed information about a specific tag."""
    try:
        tag = await service.get_tag_by_id(tag_id)
        if not tag:
            raise TagNotFoundError(tag_id)

        logger.info(f"Retrieved tag: {tag_id}")
        return TagResponse.from_orm(tag)

    except TagNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())

    except Exception as e:
        logger.error(f"Error retrieving tag: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})


@router.patch(
    "/{tag_id}",
    response_model=TagResponse,
    summary="Update tag properties",
    responses={
        200: {"description": "Tag updated"},
        404: {"model": ErrorResponse, "description": "Tag not found"},
        409: {"model": ErrorResponse, "description": "Tag already deleted"},
        422: {"model": ErrorResponse, "description": "Invalid update data"},
    }
)
async def update_tag(
    tag_id: UUID,
    request: UpdateTagRequest,
    service: TagService = Depends(get_tag_service)
):
    """
    Update tag properties (name, color, icon, description).

    At least one field must be provided.
    """
    try:
        tag = await service.update_tag(
            tag_id=tag_id,
            name=request.name,
            color=request.color,
            icon=request.icon,
            description=request.description
        )
        logger.info(f"Updated tag: {tag_id}")
        return TagResponse.from_orm(tag)

    except TagNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())

    except TagAlreadyDeletedError as e:
        raise HTTPException(status_code=409, detail=e.to_dict())

    except (TagAlreadyExistsError, TagInvalidNameError, TagInvalidColorError) as e:
        raise HTTPException(status_code=422, detail=e.to_dict())

    except Exception as e:
        logger.error(f"Error updating tag: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})


@router.delete(
    "/{tag_id}",
    status_code=204,
    summary="Soft delete a tag",
    responses={
        204: {"description": "Tag deleted"},
        404: {"model": ErrorResponse, "description": "Tag not found"},
        409: {"model": ErrorResponse, "description": "Tag already deleted"},
    }
)
async def delete_tag(
    tag_id: UUID,
    service: TagService = Depends(get_tag_service)
):
    """
    Soft delete a tag.

    - Tag is marked as deleted but associations are preserved
    - Can be restored later
    - Use DELETE /tags/{id}/restore to undo
    """
    try:
        await service.delete_tag(tag_id)
        logger.info(f"Soft deleted tag: {tag_id}")

    except TagNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())

    except TagAlreadyDeletedError as e:
        raise HTTPException(status_code=409, detail=e.to_dict())

    except Exception as e:
        logger.error(f"Error deleting tag: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})


@router.post(
    "/{tag_id}/restore",
    response_model=TagResponse,
    summary="Restore a deleted tag",
    responses={
        200: {"description": "Tag restored"},
        404: {"model": ErrorResponse, "description": "Tag not found"},
    }
)
async def restore_tag(
    tag_id: UUID,
    service: TagService = Depends(get_tag_service)
):
    """Restore a soft-deleted tag."""
    try:
        tag = await service.restore_tag(tag_id)
        logger.info(f"Restored tag: {tag_id}")
        return TagResponse.from_orm(tag)

    except TagNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())

    except Exception as e:
        logger.error(f"Error restoring tag: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})


@router.get(
    "",
    response_model=TagListResponse,
    summary="List tags with search and pagination",
    responses={
        200: {"description": "Tags retrieved"},
    }
)
async def list_tags(
    keyword: Optional[str] = Query(None, min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("usage_count", regex="^(usage_count|name|created_at)$"),
    service: TagService = Depends(get_tag_service)
):
    """
    List tags with optional search and pagination.

    **Query Parameters:**
    - keyword: Search by partial name match (case-insensitive)
    - page: Page number (1-indexed)
    - size: Items per page (1-100)
    - sort_by: Sort field (usage_count|name|created_at)

    **Behavior:**
    - If keyword is provided: returns search results
    - Otherwise: returns top-level tags sorted by sort_by field
    """
    try:
        if keyword:
            tags = await service.search_tags(keyword, limit=size * 10)  # Fetch more for sorting
        else:
            tags = await service.get_most_used_tags(limit=size * 10)

        # Apply pagination
        total = len(tags)
        start = (page - 1) * size
        end = start + size
        items = tags[start:end]

        logger.info(f"Listed tags: keyword={keyword}, page={page}, size={size}, total={total}")

        return TagListResponse(
            items=[TagResponse.from_orm(tag) for tag in items],
            total=total,
            page=page,
            size=size,
            has_more=end < total
        )

    except Exception as e:
        logger.error(f"Error listing tags: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})


@router.get(
    "/hierarchy",
    response_model=List[TagHierarchyResponse],
    summary="Get hierarchical tag tree",
    responses={
        200: {"description": "Tag hierarchy retrieved"},
    }
)
async def get_tag_hierarchy(
    service: TagService = Depends(get_tag_service)
):
    """
    Get all tags in hierarchical structure.

    Returns a tree with top-level tags and their children.
    Useful for building menu bars and tag pickers.
    """
    try:
        tags = await service.get_tag_hierarchy()
        logger.info(f"Retrieved tag hierarchy with {len(tags)} top-level tags")

        # Build nested response
        responses = []
        for tag in tags:
            response = TagHierarchyResponse(
                id=tag.id,
                name=tag.name,
                color=tag.color,
                icon=tag.icon,
                level=tag.level,
                usage_count=tag.usage_count,
                children=[]
            )
            responses.append(response)

        return responses

    except Exception as e:
        logger.error(f"Error retrieving tag hierarchy: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})


@router.post(
    "/{tag_id}/associate",
    status_code=204,
    summary="Associate tag with an entity",
    responses={
        204: {"description": "Tag associated"},
        404: {"model": ErrorResponse, "description": "Tag not found"},
        422: {"model": ErrorResponse, "description": "Invalid request"},
    }
)
async def associate_tag(
    tag_id: UUID,
    request: AssociateTagRequest,
    service: TagService = Depends(get_tag_service)
):
    """
    Associate a tag with an entity (Book/Bookshelf/Block).

    **Rules (RULE-019):**
    - Idempotent: associating twice is safe
    - Tag must exist and not be deleted
    - entity_type must be one of: BOOKSHELF, BOOK, BLOCK
    """
    try:
        await service.associate_tag_with_entity(
            tag_id=tag_id,
            entity_type=EntityType(request.entity_type.value),
            entity_id=request.entity_id
        )
        logger.info(f"Associated tag {tag_id} with {request.entity_type} {request.entity_id}")

    except TagNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())

    except Exception as e:
        logger.error(f"Error associating tag: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})


@router.delete(
    "/{tag_id}/associate",
    status_code=204,
    summary="Disassociate tag from an entity",
    responses={
        204: {"description": "Association removed"},
        404: {"model": ErrorResponse, "description": "Tag not found"},
    }
)
async def disassociate_tag(
    tag_id: UUID,
    entity_type: EntityType = Query(...),
    entity_id: UUID = Query(...),
    service: TagService = Depends(get_tag_service)
):
    """Remove association between a tag and an entity."""
    try:
        await service.disassociate_tag_from_entity(
            tag_id=tag_id,
            entity_type=entity_type,
            entity_id=entity_id
        )
        logger.info(f"Disassociated tag {tag_id} from {entity_type} {entity_id}")

    except TagNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())

    except Exception as e:
        logger.error(f"Error disassociating tag: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})


@router.get(
    "/{entity_type}/{entity_id}/tags",
    response_model=EntityTagsResponse,
    summary="Get all tags for an entity",
    responses={
        200: {"description": "Tags retrieved"},
    }
)
async def get_entity_tags(
    entity_type: str,
    entity_id: UUID,
    service: TagService = Depends(get_tag_service)
):
    """
    Get all tags associated with a specific entity (Book/Bookshelf/Block).

    **Path Parameters:**
    - entity_type: BOOKSHELF | BOOK | BLOCK
    - entity_id: UUID of the entity
    """
    try:
        # Validate entity_type
        try:
            entity_type_enum = EntityType(entity_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail={"message": "Invalid entity_type (must be BOOKSHELF, BOOK, or BLOCK)"}
            )

        tags = await service.get_tags_for_entity(entity_type_enum, entity_id)
        logger.info(f"Retrieved tags for {entity_type} {entity_id}: {len(tags)} tags")

        return EntityTagsResponse(
            entity_type=entity_type_enum,
            entity_id=entity_id,
            tags=[TagResponse.from_orm(tag) for tag in tags],
            count=len(tags)
        )

    except Exception as e:
        logger.error(f"Error retrieving entity tags: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})
