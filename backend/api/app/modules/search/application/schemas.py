"""Search Application Schemas - Pydantic v2 DTOs

Data Transfer Objects for request/response serialization.
Follows Media module pattern with comprehensive Pydantic validation.

DTO 设计原则:
1. Request DTOs (input): FastAPI Query/Body parameters
2. Response DTOs (output): HTTP response models
3. Internal DTOs: Domain �?DTO conversions
4. Validation: Pydantic Field constraints, custom validators
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID

from modules.search.domain import SearchEntityType


# ============================================================================
# Request DTOs (Input Models)
# ============================================================================

class ExecuteSearchRequest(BaseModel):
    """
    Search execution request - maps to HTTP query parameters

    字段:
    - text: 搜索关键�?(必填, 1-500 chars)
    - type: 实体类型过滤 (可�? block|book|bookshelf|tag|library)
    - book_id: 书籍范围限制 (可�? 仅搜索特定书内容)
    - limit: 分页大小 (1-1000, default 20)
    - offset: 分页偏移 (>=0, default 0)
    """
    text: str = Field(..., min_length=1, max_length=500, description="Search keyword")
    type: Optional[str] = Field(
        None,
        pattern="^(block|book|bookshelf|tag|library)?$",
        description="Entity type filter (None = global search)"
    )
    book_id: Optional[UUID] = Field(None, description="Scope search to specific book")
    limit: int = Field(20, ge=1, le=1000, description="Results per page")
    offset: int = Field(0, ge=0, description="Pagination offset")

    model_config = {"from_attributes": True}


# ============================================================================
# Response DTOs (Output Models)
# ============================================================================

class SearchHitSchema(BaseModel):
    """Single search result item"""
    entity_type: str = Field(..., description="Entity type (block|book|bookshelf|tag|library)")
    entity_id: str = Field(..., description="Entity UUID")
    title: str = Field(..., description="Result title")
    snippet: str = Field(..., description="Preview text (first 200 chars)")
    score: float = Field(..., ge=0, le=1, description="Relevance score (0-1)")
    path: str = Field(..., description="Breadcrumb path")
    rank_algorithm: str = Field("ts_rank_cd", description="Ranking algorithm used")

    model_config = {"from_attributes": True}


class ExecuteSearchResponse(BaseModel):
    """Search execution response"""
    total: int = Field(..., ge=0, description="Total results count")
    hits: List[SearchHitSchema] = Field(default_factory=list, description="Search results")
    query: Optional[dict] = Field(None, description="Query metadata")

    model_config = {"from_attributes": True}


__all__ = [
    "ExecuteSearchRequest",
    "SearchHitSchema",
    "ExecuteSearchResponse",
]
