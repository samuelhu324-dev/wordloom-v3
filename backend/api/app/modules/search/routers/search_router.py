"""
Search Router - HTTP Input Adapter

FastAPI router adapter that:
1. Parses HTTP requests and converts to UseCase Request DTOs
2. Gets SearchService (ExecuteSearchUseCase) from DI container
3. Executes UseCase
4. Converts Response DTOs to HTTP responses
5. Maps exceptions to HTTP errors

Endpoints:
- GET /search                 Global search (all entity types)
- GET /search/blocks          Search only blocks
- GET /search/books           Search only books
- GET /search/bookshelves     Search only bookshelves
- GET /search/tags            Search only tags
- GET /search/libraries       Search only libraries
- GET /search/entries         Search only entries (Loom terms)

Query Parameters:
- q: str (required, min_length=1)
- type: Optional[str] (None=global, or "blocks"/"books"/...)
- book_id: Optional[UUID] (limit search to specific book)
- limit: int = 20
- offset: int = 0
"""

from dataclasses import asdict
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.dependencies import DIContainer, get_di_container
from api.app.modules.search.application.ports.input import (
    ExecuteSearchRequest,
    ExecuteSearchResponse,
    ExecuteSearchUseCase,
)
from api.app.modules.search.schemas import BlockSearchHitSchema, BlockTwoStageSearchResponse
from infra.database.session import get_db_session
from infra.storage.search_repository_impl import PostgresSearchAdapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["search"])


# ============================================================================
# Dependency: Get DI Container and Search Service
# ============================================================================



# ============================================================================


async def get_search_service(di: DIContainer = Depends(get_di_container)) -> ExecuteSearchUseCase:
    """Get Search Service (ExecuteSearchUseCase) from DI container"""
    return di.get_search_service()


# ============================================================================
# Endpoint: Global Search (All Entity Types)
# ============================================================================

@router.get(
    "",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Global search across all entity types",
    description="""
    Global search across all entities.
    Searches blocks (content), books (title/metadata), bookshelves, tags, libraries, and entries.
    Results ordered by relevance.
    """
)
async def search_global(
    q: str = Query(..., min_length=1, max_length=500, description="Search keyword"),
    book_id: Optional[UUID] = Query(None, description="Optional: scope search to specific book"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    search_service: ExecuteSearchUseCase = Depends(get_search_service)
):
    """Execute global search across all entity types"""
    try:
        request = ExecuteSearchRequest(
            text=q,
            entity_type=None,
            book_id=book_id,
            limit=limit,
            offset=offset
        )
        response: ExecuteSearchResponse = await search_service.execute(request)
        return asdict(response)
    except ValueError as e:
        logger.warning(f"Invalid search query: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid search query: {e}"
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


# ============================================================================
# Endpoint: Search Blocks
# ============================================================================

@router.get(
    "/blocks",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Search blocks",
    description="Full text search on block content"
)
async def search_blocks(
    q: str = Query(..., min_length=1, max_length=500, description="Search keyword"),
    book_id: Optional[UUID] = Query(None, description="Optional: limit to specific book"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    search_service: ExecuteSearchUseCase = Depends(get_search_service)
):
    """Search blocks by content"""
    try:
        request = ExecuteSearchRequest(
            text=q,
            entity_type="blocks",
            book_id=book_id,
            limit=limit,
            offset=offset
        )
        response: ExecuteSearchResponse = await search_service.execute(request)
        return asdict(response)
    except ValueError as e:
        logger.warning(f"Invalid search query: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid search query: {e}"
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


# =========================================================================
# Endpoint: Search Blocks (Two-Stage, with tags)
# =========================================================================


@router.get(
    "/blocks/two-stage",
    response_model=BlockTwoStageSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Two-stage search blocks (with tags)",
    description="""
    Two-stage block search:
    1) search_index recall (cheap)
    2) blocks + tag_associations + tags join (strict business filter)

    This endpoint is intentionally implemented without touching SearchPort,
    as a search-specific workflow/DTO.
    """,
)
async def search_blocks_two_stage(
    q: str = Query(..., min_length=1, max_length=500, description="Search keyword"),
    book_id: Optional[UUID] = Query(None, description="Optional: limit to specific book"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    candidate_limit: int = Query(200, ge=1, le=5000, description="Stage1 candidate limit"),
    session: AsyncSession = Depends(get_db_session),
):
    """Search blocks via two-stage SQL, returning tags."""
    try:
        logger.info(
            {
                "event": "search.blocks.two_stage.requested",
                "q_preview": (q[:80] + "…") if len(q) > 80 else q,
                "book_id": str(book_id) if book_id else None,
                "limit": limit,
                "candidate_limit": candidate_limit,
            }
        )
        repo = PostgresSearchAdapter(session)
        hits = await repo.search_block_hits_two_stage(
            q=q,
            book_id=book_id,
            limit=limit,
            candidate_limit=candidate_limit,
        )
        logger.info(
            {
                "event": "search.blocks.two_stage.returned",
                "count": len(hits),
            }
        )
        return BlockTwoStageSearchResponse(
            total=len(hits),
            hits=[
                BlockSearchHitSchema(
                    id=str(h.id),
                    snippet=h.snippet,
                    score=h.score,
                    tags=h.tags,
                )
                for h in hits
            ],
        )
    except ValueError as e:
        logger.warning(f"Invalid search query: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid search query: {e}",
        )
    except Exception as e:
        logger.error(f"Two-stage search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Two-stage search failed",
        )


# ============================================================================
# Endpoint: Search Books
# ============================================================================

@router.get(
    "/books",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Search books",
    description="Search books by title and metadata"
)
async def search_books(
    q: str = Query(..., min_length=1, max_length=500, description="Search keyword"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    search_service: ExecuteSearchUseCase = Depends(get_search_service)
):
    """Search books by title and metadata"""
    try:
        request = ExecuteSearchRequest(
            text=q,
            entity_type="books",
            limit=limit,
            offset=offset
        )
        response: ExecuteSearchResponse = await search_service.execute(request)
        return asdict(response)
    except ValueError as e:
        logger.warning(f"Invalid search query: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid search query: {e}"
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


# ============================================================================
# Endpoint: Search Bookshelves
# ============================================================================

@router.get(
    "/bookshelves",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Search bookshelves",
    description="Search bookshelves by name"
)
async def search_bookshelves(
    q: str = Query(..., min_length=1, max_length=500, description="Search keyword"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    search_service: ExecuteSearchUseCase = Depends(get_search_service)
):
    """Search bookshelves by name"""
    try:
        request = ExecuteSearchRequest(
            text=q,
            entity_type="bookshelves",
            limit=limit,
            offset=offset
        )
        response: ExecuteSearchResponse = await search_service.execute(request)
        return asdict(response)
    except ValueError as e:
        logger.warning(f"Invalid search query: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid search query: {e}"
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


# ============================================================================
# Endpoint: Search Tags
# ============================================================================

@router.get(
    "/tags",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Search tags",
    description="Search tags by name"
)
async def search_tags(
    q: str = Query(..., min_length=1, max_length=500, description="Search keyword"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    search_service: ExecuteSearchUseCase = Depends(get_search_service)
):
    """Search tags by name"""
    try:
        request = ExecuteSearchRequest(
            text=q,
            entity_type="tags",
            limit=limit,
            offset=offset
        )
        response: ExecuteSearchResponse = await search_service.execute(request)
        return asdict(response)
    except ValueError as e:
        logger.warning(f"Invalid search query: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid search query: {e}"
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


# ============================================================================
# Endpoint: Search Libraries
# ============================================================================

@router.get(
    "/libraries",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Search libraries",
    description="Search libraries by name"
)
async def search_libraries(
    q: str = Query(..., min_length=1, max_length=500, description="Search keyword"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    search_service: ExecuteSearchUseCase = Depends(get_search_service)
):
    """Search libraries by name"""
    try:
        request = ExecuteSearchRequest(
            text=q,
            entity_type="libraries",
            limit=limit,
            offset=offset
        )
        response: ExecuteSearchResponse = await search_service.execute(request)
        return asdict(response)
    except ValueError as e:
        logger.warning(f"Invalid search query: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid search query: {e}"
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


# ============================================================================
# Endpoint: Search Entries (Loom Terms)
# ============================================================================

@router.get(
    "/entries",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Search entries (Loom terms)",
    description="Search entries by term and content"
)
async def search_entries(
    q: str = Query(..., min_length=1, max_length=500, description="Search keyword"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    search_service: ExecuteSearchUseCase = Depends(get_search_service)
):
    """Search entries by term and content"""
    try:
        request = ExecuteSearchRequest(
            text=q,
            entity_type="entries",
            limit=limit,
            offset=offset
        )
        response: ExecuteSearchResponse = await search_service.execute(request)
        return asdict(response)
    except ValueError as e:
        logger.warning(f"Invalid search query: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid search query: {e}"
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


