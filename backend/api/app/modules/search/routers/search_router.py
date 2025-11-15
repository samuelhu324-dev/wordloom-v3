"""
Search Router - HTTP Input Adapter

FastAPI 路由适配器，提供搜索 REST API�?
职责:
1. 解析 HTTP 请求 �?转换�?UseCase Request DTO
2. �?DI 容器获取 SearchService (ExecuteSearchUseCase)
3. 执行 UseCase
4. �?Response DTO �?转换�?HTTP 响应
5. 异常映射�?HTTP 错误�?
Endpoints (9 �?:
  - GET /search              全局搜索（所有类型）
  - GET /search/blocks       仅搜�?Blocks
  - GET /search/books        仅搜�?Books
  - GET /search/bookshelves  仅搜�?Bookshelves
  - GET /search/tags         仅搜�?Tags
  + 其他扩展端点

参数:
  - q: str (required, min_length=1)
  - type: Optional[str] (None = 全局, �?"blocks"/"books"/...)
  - book_id: Optional[UUID] (限定 Book 内搜�?
  - limit: int = 20
  - offset: int = 0
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from uuid import UUID
import logging

from dependencies import DIContainer, get_di_container_provider
from modules.search.application.ports.input import (
    ExecuteSearchRequest,
    ExecuteSearchResponse,
    ExecuteSearchUseCase,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


# ============================================================================
# Dependency: Get DI Container & Search Service
# ============================================================================

async def get_di_container() -> DIContainer:
    """获取 DI 容器（FastAPI 依赖�?""
    return get_di_container_provider()


async def get_search_service(di: DIContainer = Depends(get_di_container)) -> ExecuteSearchUseCase:
    """获取 Search Service（UseCase�?""
    return di.get_search_service()


# ============================================================================
# Endpoint 1: Global Search (All Types)
# ============================================================================

@router.get(
    "",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Global search across all entity types",
    description="""
    全局搜索：一个关键字查询所有实体类�?
    支持:
    - Block 内容全文搜索
    - Book 标题和元数据搜索
    - Bookshelf 名称搜索
    - Tag 名称搜索

    结果按相关性排序（ts_rank_cd�?    """
)
async def search_global(
    q: str = Query(..., min_length=1, max_length=500, description="Search keyword"),
    book_id: Optional[UUID] = Query(None, description="Optional: scope search to specific book"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: ExecuteSearchUseCase = Depends(get_search_service),
):
    """
    全局搜索所有实体类�?
    返回按相关性排序的混合结果�?    """
    try:
        request = ExecuteSearchRequest(
            text=q,
            type=None,  # Global search
            book_id=book_id,
            limit=limit,
            offset=offset,
        )
        result: ExecuteSearchResponse = await service.execute(request)
        logger.info(f"Global search: '{q}' returned {result.total} results")
        return {
            "total": result.total,
            "hits": [hit.dict() for hit in result.hits],
            "query": {"text": q, "type": None, "book_id": str(book_id) if book_id else None},
        }
    except ValueError as e:
        logger.warning(f"Invalid search parameters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Global search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search operation failed"
        )


# ============================================================================
# Endpoint 2: Search Blocks Only
# ============================================================================

@router.get(
    "/blocks",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Search blocks only",
    description="""
    仅搜�?Block 内容

    搜索范围:
    - Block content (full text)

    结果按文本相关性排�?    """
)
async def search_blocks_only(
    q: str = Query(..., min_length=1, max_length=500, description="Search keyword"),
    book_id: Optional[UUID] = Query(None, description="Optional: scope to specific book"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: ExecuteSearchUseCase = Depends(get_search_service),
):
    """仅搜�?Blocks"""
    try:
        request = ExecuteSearchRequest(
            text=q,
            type="block",
            book_id=book_id,
            limit=limit,
            offset=offset,
        )
        result: ExecuteSearchResponse = await service.execute(request)
        logger.info(f"Block search: '{q}' returned {result.total} results")
        return {
            "total": result.total,
            "hits": [hit.dict() for hit in result.hits],
            "query": {"text": q, "type": "block"},
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"Block search failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Search failed")


# ============================================================================
# Endpoint 3: Search Books Only
# ============================================================================

@router.get(
    "/books",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Search books only",
    description="""
    仅搜�?Book 元数�?
    搜索范围:
    - Book title
    - Book description
    """
)
async def search_books_only(
    q: str = Query(..., min_length=1, max_length=500, description="Search keyword"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: ExecuteSearchUseCase = Depends(get_search_service),
):
    """仅搜�?Books"""
    try:
        request = ExecuteSearchRequest(
            text=q,
            type="book",
            limit=limit,
            offset=offset,
        )
        result: ExecuteSearchResponse = await service.execute(request)
        logger.info(f"Book search: '{q}' returned {result.total} results")
        return {
            "total": result.total,
            "hits": [hit.dict() for hit in result.hits],
            "query": {"text": q, "type": "book"},
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"Book search failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Search failed")


# ============================================================================
# Endpoint 4: Search Bookshelves Only
# ============================================================================

@router.get(
    "/bookshelves",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Search bookshelves only",
    description="""
    仅搜�?Bookshelf 名称

    快速定位书�?    """
)
async def search_bookshelves_only(
    q: str = Query(..., min_length=1, max_length=500, description="Search keyword"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: ExecuteSearchUseCase = Depends(get_search_service),
):
    """仅搜�?Bookshelves"""
    try:
        request = ExecuteSearchRequest(
            text=q,
            type="bookshelf",
            limit=limit,
            offset=offset,
        )
        result: ExecuteSearchResponse = await service.execute(request)
        logger.info(f"Bookshelf search: '{q}' returned {result.total} results")
        return {
            "total": result.total,
            "hits": [hit.dict() for hit in result.hits],
            "query": {"text": q, "type": "bookshelf"},
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"Bookshelf search failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Search failed")


# ============================================================================
# Endpoint 5: Search Tags Only
# ============================================================================

@router.get(
    "/tags",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Search tags only",
    description="""
    仅搜�?Tag 名称

    快速查找特定标�?    """
)
async def search_tags_only(
    q: str = Query(..., min_length=1, max_length=500, description="Search keyword"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: ExecuteSearchUseCase = Depends(get_search_service),
):
    """仅搜�?Tags"""
    try:
        request = ExecuteSearchRequest(
            text=q,
            type="tag",
            limit=limit,
            offset=offset,
        )
        result: ExecuteSearchResponse = await service.execute(request)
        logger.info(f"Tag search: '{q}' returned {result.total} results")
        return {
            "total": result.total,
            "hits": [hit.dict() for hit in result.hits],
            "query": {"text": q, "type": "tag"},
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"Tag search failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Search failed")


# ============================================================================
# Endpoint 6: Generic Type Search
# ============================================================================

@router.get(
    "/{entity_type}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Search specific entity type",
    description="""
    搜索指定类型的实�?
    entity_type: block | book | bookshelf | tag
    """
)
async def search_by_type(
    entity_type: str = Query(..., regex="^(block|book|bookshelf|tag)$", description="Entity type"),
    q: str = Query(..., min_length=1, max_length=500, description="Search keyword"),
    book_id: Optional[UUID] = Query(None, description="Optional: scope to specific book"),
    limit: int = Query(20, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: ExecuteSearchUseCase = Depends(get_search_service),
):
    """按类型搜索实�?""
    try:
        request = ExecuteSearchRequest(
            text=q,
            type=entity_type,
            book_id=book_id,
            limit=limit,
            offset=offset,
        )
        result: ExecuteSearchResponse = await service.execute(request)
        logger.info(f"{entity_type} search: '{q}' returned {result.total} results")
        return {
            "total": result.total,
            "hits": [hit.dict() for hit in result.hits],
            "query": {"text": q, "type": entity_type},
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"Type search failed for {entity_type}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Search failed")


__all__ = ["router"]
