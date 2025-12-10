"""
Bookshelf Schemas - Pydantic v2 models for API validation and serialization

对应 DDD_RULES：
  - RULE-004: Bookshelf 可无限创建
  - RULE-005: Bookshelf 必须属于 Library
  - RULE-006: Bookshelf 名称在同 Library 下唯一
  - RULE-010: Basement Bookshelf 特殊支持
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Dict, Any
from enum import Enum


# ============================================
# Enums
# ============================================

class BookshelfStatus(str, Enum):
    """Bookshelf 状态枚举"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class BookshelfType(str, Enum):
    """Bookshelf 类型枚举"""
    NORMAL = "normal"
    BASEMENT = "basement"  # RULE-010: 特殊的系统 Bookshelf


# ============================================
# Request Schemas (API 输入)
# ============================================

class BookshelfCreate(BaseModel):
    """创建 Bookshelf 时的请求体"""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Bookshelf 名称（同 Library 下唯一）",
        examples=["技术文档", "工作笔记", "阅读清单"],
    )

    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Bookshelf 描述（可选）",
    )

    @field_validator("name", mode="before")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """验证名称不为空且不仅是空格"""
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Bookshelf name cannot be empty or whitespace only")
        return v

    @field_validator("description", mode="before")
    @classmethod
    def validate_description_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """验证描述如果提供则不仅是空格"""
        if v is not None and isinstance(v, str):
            v = v.strip() or None
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "技术文档",
                "description": "存放各种编程语言和框架的学习笔记"
            }
        }
    )


class BookshelfUpdate(BaseModel):
    """更新 Bookshelf 时的请求体"""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="新的 Bookshelf 名称（可选）",
    )

    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="新的 Bookshelf 描述（可选）",
    )

    is_pinned: Optional[bool] = Field(
        None,
        description="是否固定到菜单栏（可选）",
    )

    is_favorite: Optional[bool] = Field(
        None,
        description="是否收藏（可选）",
    )

    @field_validator("name", mode="before")
    @classmethod
    def validate_name_if_provided(cls, v: Optional[str]) -> Optional[str]:
        """如果提供了名称，则验证"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Bookshelf name cannot be empty or whitespace only")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "更新的书架名称",
                "is_pinned": True
            }
        }
    )


# ============================================
# Response Schemas (API 输出)
# ============================================

class BookshelfResponse(BaseModel):
    """基础 Bookshelf 响应（用于列表、简略显示）"""

    id: UUID = Field(..., description="Bookshelf 全局唯一 ID")
    library_id: UUID = Field(..., description="所属 Library ID")
    name: str = Field(..., description="Bookshelf 名称")
    description: Optional[str] = Field(None, description="Bookshelf 描述")
    is_pinned: bool = Field(False, description="是否固定到菜单栏")
    is_favorite: bool = Field(False, description="是否收藏")
    is_basement: bool = Field(False, description="是否为 Basement（RULE-010）")
    status: BookshelfStatus = Field(BookshelfStatus.ACTIVE, description="Bookshelf 状态")
    created_at: datetime = Field(..., description="创建时间（ISO 8601）")
    updated_at: datetime = Field(..., description="最后修改时间（ISO 8601）")

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
        },
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "library_id": "650e8400-e29b-41d4-a716-446655440000",
                "name": "技术文档",
                "description": "存放编程笔记",
                "is_pinned": True,
                "is_favorite": False,
                "is_basement": False,
                "status": "active",
                "created_at": "2025-01-15T10:30:00+00:00",
                "updated_at": "2025-01-15T10:30:00+00:00",
            }
        }
    )


class BookshelfDetailResponse(BookshelfResponse):
    """详细 Bookshelf 响应（包含统计和扩展信息）"""

    book_count: int = Field(
        0,
        description="该 Bookshelf 内的 Book 总数",
        ge=0,
    )

    pinned_at: Optional[datetime] = Field(
        None,
        description="固定时间（如果已固定）",
    )

    bookshelf_type: BookshelfType = Field(
        BookshelfType.NORMAL,
        description="Bookshelf 类型（normal 或 basement）",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "library_id": "650e8400-e29b-41d4-a716-446655440000",
                "name": "技术文档",
                "description": "存放编程笔记",
                "is_pinned": True,
                "is_favorite": False,
                "is_basement": False,
                "status": "active",
                "book_count": 12,
                "pinned_at": "2025-01-15T10:35:00+00:00",
                "bookshelf_type": "normal",
                "created_at": "2025-01-15T10:30:00+00:00",
                "updated_at": "2025-01-15T10:30:00+00:00",
            }
        }
    )


class BookshelfPaginatedResponse(BaseModel):
    """分页 Bookshelf 响应"""

    items: List[BookshelfDetailResponse] = Field(
        ...,
        description="Bookshelf 列表",
    )

    total: int = Field(
        ...,
        ge=0,
        description="总记录数",
    )

    page: int = Field(
        ...,
        ge=1,
        description="当前页码",
    )

    page_size: int = Field(
        ...,
        ge=1,
        le=100,
        description="每页记录数",
    )

    has_more: bool = Field(
        ...,
        description="是否有下一页",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "has_more": False,
            }
        }
    )


class BookshelfDashboardBookCounts(BaseModel):
    """书架面板的书籍数量统计"""

    total: int = Field(0, ge=0)
    seed: int = Field(0, ge=0)
    growing: int = Field(0, ge=0)
    stable: int = Field(0, ge=0)
    legacy: int = Field(0, ge=0)


class BookshelfDashboardHealthCounts(BaseModel):
    """书架健康度指标统计"""

    active: int = Field(0, ge=0)
    slowing: int = Field(0, ge=0)
    cooling: int = Field(0, ge=0)
    archived: int = Field(0, ge=0)


class BookshelfDashboardSnapshot(BaseModel):
    """书架面板摘要统计"""

    total: int = Field(0, ge=0)
    pinned: int = Field(0, ge=0)
    health: BookshelfDashboardHealthCounts = Field(
        default_factory=BookshelfDashboardHealthCounts,
        description="按健康度划分的书架数量",
    )


class BookshelfTagSummary(BaseModel):
    """书架标签简要信息"""

    id: UUID
    name: str
    color: str = Field('#6366F1', description="标签配色（#RRGGBB）")
    description: Optional[str] = Field(None, description="标签说明（Tooltip 使用）")


class BookshelfDashboardItem(BaseModel):
    """书架面板单项"""

    id: UUID
    library_id: UUID
    name: str
    description: Optional[str] = None
    status: BookshelfStatus = BookshelfStatus.ACTIVE
    is_pinned: bool = False
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime
    last_activity_at: Optional[datetime] = None
    health: str = Field(..., description="健康度标签")
    theme_color: Optional[str] = Field(None, description="预设主题色（可选）")
    cover_media_id: Optional[UUID] = Field(None, description="封面媒体 ID")
    book_counts: BookshelfDashboardBookCounts
    edits_last_7d: int = Field(0, ge=0)
    views_last_7d: int = Field(0, ge=0)
    tag_ids: List[UUID] = Field(default_factory=list, description="关联标签 ID（顺序与 tags 一致）")
    tags_summary: List[str] = Field(default_factory=list, description="标签名称列表（最多 3 个可在前端展示）")
    tags: List[BookshelfTagSummary] = Field(default_factory=list, description="标签详细信息（颜色/说明）")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
        }
    )


class BookshelfDashboardResponse(BaseModel):
    """书架面板响应"""

    items: List[BookshelfDashboardItem]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    snapshot: BookshelfDashboardSnapshot = Field(
        default_factory=BookshelfDashboardSnapshot,
        description="当前 Library 的聚合统计",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 2,
                "page": 1,
                "page_size": 20,
                "snapshot": {
                    "total": 8,
                    "pinned": 2,
                    "health": {
                        "active": 3,
                        "slowing": 2,
                        "cooling": 2,
                        "archived": 1,
                    },
                },
                "items": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "library_id": "650e8400-e29b-41d4-a716-446655440000",
                        "name": "AAA 学习",
                        "description": "长期知识积累",
                        "status": "active",
                        "is_pinned": True,
                        "is_archived": False,
                        "created_at": "2025-01-10T08:00:00+00:00",
                        "updated_at": "2025-11-23T23:10:00+00:00",
                        "last_activity_at": "2025-11-23T22:58:00+00:00",
                        "health": "active",
                        "theme_color": "#D9C7B2",
                        "cover_media_id": None,
                        "book_counts": {
                            "total": 12,
                            "seed": 3,
                            "growing": 5,
                            "stable": 3,
                            "legacy": 1,
                        },
                        "edits_last_7d": 9,
                        "views_last_7d": 21,
                        "tag_ids": ["7c5976a5-6daa-4de3-8f8a-41066f275040"],
                        "tags_summary": ["OBSERVATION"],
                        "tags": [
                            {
                                "id": "7c5976a5-6daa-4de3-8f8a-41066f275040",
                                "name": "OBSERVATION",
                                "color": "#6366F1",
                                "description": "用于标记需要观察的书架",
                            }
                        ],
                    }
                ],
            }
        }
    )


# ============================================
# DTO (Data Transfer Object) - 内部使用
# ============================================

class BookshelfDTO(BaseModel):
    """内部使用的 DTO（Service ↔ Repository）"""

    id: UUID
    library_id: UUID
    name: str
    description: Optional[str] = None
    is_pinned: bool = False
    is_favorite: bool = False
    is_basement: bool = False
    status: BookshelfStatus = BookshelfStatus.ACTIVE
    book_count: int = 0
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, bookshelf):
        """从 Domain 对象转换（ORM 模型 → DTO）"""
        return cls(
            id=bookshelf.id,
            library_id=bookshelf.library_id,
            name=bookshelf.name,
            description=bookshelf.description,
            is_pinned=getattr(bookshelf, "is_pinned", False),
            is_favorite=getattr(bookshelf, "is_favorite", False),
            is_basement=getattr(bookshelf, "is_basement", False),
            status=BookshelfStatus(bookshelf.status) if hasattr(bookshelf, "status") else BookshelfStatus.ACTIVE,
            book_count=getattr(bookshelf, "book_count", 0),
            created_at=bookshelf.created_at,
            updated_at=bookshelf.updated_at,
        )

    def to_response(self) -> BookshelfResponse:
        """转换为 API 响应（DTO → Response）"""
        return BookshelfResponse(**self.model_dump())

    def to_detail_response(self) -> BookshelfDetailResponse:
        """转换为详细 API 响应"""
        return BookshelfDetailResponse(**self.model_dump())


# ============================================
# Error Responses
# ============================================

class ErrorDetail(BaseModel):
    """错误响应详情"""
    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误信息")
    details: Optional[Dict[str, Any]] = Field(None, description="详细错误信息")
