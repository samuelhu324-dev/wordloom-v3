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
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.config.setting import Settings, get_settings
from api.app.modules.search.domain import SearchQuery, SearchResult
from api.app.modules.search.schemas import BlockSearchHitSchema, BlockTwoStageSearchResponse
from infra.database.session import get_db_session
from infra.storage.search_repository_impl import PostgresSearchAdapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["search"])


def _empty_search_response(*, limit: int, offset: int) -> dict:
    return {
        "total": 0,
        "hits": [],
        "limit": limit,
        "offset": offset,
    }


def _result_to_dict(result: SearchResult) -> dict:
    return {
        "total": result.total,
        "hits": [
            {
                "entity_type": h.entity_type.value,
                "entity_id": str(h.entity_id),
                "title": h.title,
                "snippet": h.snippet,
                "score": h.score,
                "path": h.path,
                "rank_algorithm": h.rank_algorithm,
            }
            for h in result.hits
        ],
        "limit": result.query.limit if result.query else len(result.hits),
        "offset": result.query.offset if result.query else 0,
    }


async def get_search_db_session(
    settings: Settings = Depends(get_settings),
):
    """Only open a DB session when projection reads are enabled.

    This keeps the feature-flag "off" mode cheap and testable.
    """

    if not settings.enable_search_projection:
        yield None
        return

    async for session in get_db_session():
        yield session


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
    library_id: Optional[UUID] = Query(None, description="Scope key: library_id"),
    book_id: Optional[UUID] = Query(None, description="Optional: scope search to specific book"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    session: Optional[AsyncSession] = Depends(get_search_db_session),
    settings: Settings = Depends(get_settings),
):
    """Execute global search across all entity types"""
    try:
        if not settings.enable_search_projection:
            return _empty_search_response(limit=limit, offset=offset)

        if session is None:
            return _empty_search_response(limit=limit, offset=offset)

        repo = PostgresSearchAdapter(session)
        query = SearchQuery(
            text=q,
            library_id=library_id,
            book_id=book_id,
            limit=limit,
            offset=offset,
        )

        # MVP global search: block + book (projection-backed).
        block_result = await repo.search_blocks(query)
        book_result = await repo.search_books(query)

        all_hits = block_result.hits + book_result.hits
        all_hits.sort(key=lambda h: h.score, reverse=True)
        paginated_hits = all_hits[offset : offset + limit]
        combined = SearchResult(total=len(all_hits), hits=paginated_hits, query=query)
        return _result_to_dict(combined)
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
    library_id: Optional[UUID] = Query(None, description="Scope key: library_id"),
    book_id: Optional[UUID] = Query(None, description="Optional: limit to specific book"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    session: Optional[AsyncSession] = Depends(get_search_db_session),
    settings: Settings = Depends(get_settings),
):
    """Search blocks by content"""
    try:
        if not settings.enable_search_projection:
            return _empty_search_response(limit=limit, offset=offset)

        if session is None:
            return _empty_search_response(limit=limit, offset=offset)

        repo = PostgresSearchAdapter(session)
        query = SearchQuery(
            text=q,
            library_id=library_id,
            book_id=book_id,
            limit=limit,
            offset=offset,
        )
        result = await repo.search_blocks(query)
        return _result_to_dict(result)
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
    library_id: Optional[UUID] = Query(None, description="Scope key: library_id"),
    book_id: Optional[UUID] = Query(None, description="Optional: limit to specific book"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    candidate_limit: int = Query(200, ge=1, le=5000, description="Stage1 candidate limit"),
    session: Optional[AsyncSession] = Depends(get_search_db_session),
    settings: Settings = Depends(get_settings),
):
    """Search blocks via two-stage SQL, returning tags."""
    try:
        if not settings.enable_search_projection:
            return BlockTwoStageSearchResponse(total=0, hits=[])

        logger.info(
            {
                "event": "search.blocks.two_stage.requested",
                "q_preview": (q[:80] + "…") if len(q) > 80 else q,
                "library_id": str(library_id) if library_id else None,
                "book_id": str(book_id) if book_id else None,
                "limit": limit,
                "candidate_limit": candidate_limit,
            }
        )
        if session is None:
            return BlockTwoStageSearchResponse(total=0, hits=[])

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
    library_id: Optional[UUID] = Query(None, description="Scope key: library_id"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    session: Optional[AsyncSession] = Depends(get_search_db_session),
    settings: Settings = Depends(get_settings),
):
    """Search books by title and metadata"""
    try:
        if not settings.enable_search_projection:
            return _empty_search_response(limit=limit, offset=offset)

        if session is None:
            return _empty_search_response(limit=limit, offset=offset)

        repo = PostgresSearchAdapter(session)
        query = SearchQuery(
            text=q,
            library_id=library_id,
            limit=limit,
            offset=offset,
        )
        result = await repo.search_books(query)
        return _result_to_dict(result)
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
    library_id: Optional[UUID] = Query(None, description="Scope key: library_id"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    session: Optional[AsyncSession] = Depends(get_search_db_session),
    settings: Settings = Depends(get_settings),
):
    """Search bookshelves by name"""
    try:
        if not settings.enable_search_projection:
            return _empty_search_response(limit=limit, offset=offset)

        if session is None:
            return _empty_search_response(limit=limit, offset=offset)

        repo = PostgresSearchAdapter(session)
        query = SearchQuery(
            text=q,
            library_id=library_id,
            limit=limit,
            offset=offset,
        )
        result = await repo.search_bookshelves(query)
        return _result_to_dict(result)
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
    library_id: Optional[UUID] = Query(None, description="Scope key: library_id (optional for tags)"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    session: Optional[AsyncSession] = Depends(get_search_db_session),
    settings: Settings = Depends(get_settings),
):
    """Search tags by name"""
    try:
        if not settings.enable_search_projection:
            return _empty_search_response(limit=limit, offset=offset)

        if session is None:
            return _empty_search_response(limit=limit, offset=offset)

        repo = PostgresSearchAdapter(session)
        query = SearchQuery(
            text=q,
            library_id=library_id,
            limit=limit,
            offset=offset,
        )
        result = await repo.search_tags(query)
        return _result_to_dict(result)
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
    library_id: Optional[UUID] = Query(None, description="Scope key: library_id"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    session: Optional[AsyncSession] = Depends(get_search_db_session),
    settings: Settings = Depends(get_settings),
):
    """Search libraries by name"""
    try:
        if not settings.enable_search_projection:
            return _empty_search_response(limit=limit, offset=offset)

        if session is None:
            return _empty_search_response(limit=limit, offset=offset)

        repo = PostgresSearchAdapter(session)
        query = SearchQuery(
            text=q,
            library_id=library_id,
            limit=limit,
            offset=offset,
        )
        result = await repo.search_libraries(query)
        return _result_to_dict(result)
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
    library_id: Optional[UUID] = Query(None, description="Scope key: library_id"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    session: Optional[AsyncSession] = Depends(get_search_db_session),
    settings: Settings = Depends(get_settings),
):
    """Search entries by term and content"""
    try:
        if not settings.enable_search_projection:
            return _empty_search_response(limit=limit, offset=offset)

        if session is None:
            return _empty_search_response(limit=limit, offset=offset)

        repo = PostgresSearchAdapter(session)
        query = SearchQuery(
            text=q,
            library_id=library_id,
            limit=limit,
            offset=offset,
        )
        result = await repo.search_entries(query)
        return _result_to_dict(result)
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


