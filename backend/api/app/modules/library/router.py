"""
Library Router - FastAPI routes for Library endpoints

体系结构：
  ├─ Dependency Injection (获取 Service)
  ├─ Request Validation (Pydantic schemas)
  ├─ Business Logic Execution (Service 层)
  ├─ Exception Handling (Domain exceptions → HTTP)
  ├─ Response Serialization (Schemas)
  └─ Logging & Monitoring

对应 DDD_RULES：
  - RULE-001: POST /libraries - 创建唯一 Library
  - RULE-002: GET /libraries/user/{user_id} - 获取用户唯一库
  - RULE-003: PUT /libraries/{library_id} - 更新名称

Exposes Library operations via HTTP API:
- POST /api/v1/libraries - Create Library
- GET /api/v1/libraries/{library_id} - Get Library by ID
- GET /api/v1/libraries/user/{user_id} - Get Library for user
- PUT /api/v1/libraries/{library_id} - Update Library
- DELETE /api/v1/libraries/{library_id} - Delete Library
"""

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
import logging

from modules.library.schemas import (
    LibraryCreate,
    LibraryUpdate,
    LibraryResponse,
    LibraryDetailResponse,
    LibraryPaginatedResponse,
    ErrorDetail,
)
from modules.library.service import LibraryService
from modules.library.repository import LibraryRepositoryImpl
from modules.library.exceptions import (
    LibraryNotFoundError,
    LibraryAlreadyExistsError,
    InvalidLibraryNameError,
    LibraryUserAssociationError,
    LibraryException,
    DomainException,
)
from infra.database import get_db_session
from core.security import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/libraries",
    tags=["libraries"],
    responses={
        404: {"description": "Library not found", "model": ErrorDetail},
        409: {"description": "Conflict (e.g., user already has a library)", "model": ErrorDetail},
        422: {"description": "Validation error", "model": ErrorDetail},
    },
)


# ============================================
# Dependency Injection
# ============================================

async def get_library_service(
    session: AsyncSession = Depends(get_db_session),
) -> LibraryService:
    """
    依赖注入：获取 LibraryService

    生产级设计：
      1. 获取数据库 Session
      2. 创建 Repository 实现
      3. 创建 Service 实例
      4. 自动清理资源

    对应 DDD_RULES 分层：
      - Repository Layer: LibraryRepositoryImpl(session)
      - Service Layer: LibraryService(repository)
    """
    repository = LibraryRepositoryImpl(session)
    service = LibraryService(repository)
    logger.debug(f"LibraryService initialized with session {id(session)}")
    return service


# ============================================
# Exception Handlers (映射到 HTTP)
# ============================================

def _handle_domain_exception(exc: DomainException) -> HTTPException:
    """
    将 Domain Exception 映射到 HTTP Exception

    对应 exceptions.py 的异常体系：
      - LibraryAlreadyExistsError → 409 Conflict
      - LibraryNotFoundError → 404 Not Found
      - InvalidLibraryNameError → 422 Unprocessable Entity
      - LibraryUserAssociationError → 422 Unprocessable Entity
    """
    error_detail = exc.to_dict() if hasattr(exc, "to_dict") else {"message": str(exc)}

    log_level = "warning" if exc.http_status < 500 else "error"
    getattr(logger, log_level)(f"Domain exception: {exc.code} - {exc.message}")

    return HTTPException(
        status_code=exc.http_status if hasattr(exc, "http_status") else 500,
        detail=error_detail,
    )


# ============================================
# Routes
# ============================================

@router.post(
    "",
    response_model=LibraryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Library for current user",
    description="创建当前用户的 Library（每个用户只能有一个 Library）",
    responses={
        409: {
            "description": "User already has a Library",
            "content": {
                "application/json": {
                    "example": {
                        "code": "LIBRARY_ALREADY_EXISTS",
                        "message": "User 650e8400-e29b-41d4-a716-446655440000 already has a Library",
                        "details": {"user_id": "650e8400-e29b-41d4-a716-446655440000"}
                    }
                }
            }
        },
        422: {
            "description": "Validation failed",
            "content": {
                "application/json": {
                    "example": {
                        "code": "INVALID_LIBRARY_NAME",
                        "message": "Invalid Library name: name is required",
                        "details": {"constraints": {"min_length": 1, "max_length": 255}}
                    }
                }
            }
        }
    },
)
async def create_library(
    request: LibraryCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: LibraryService = Depends(get_library_service),
) -> LibraryResponse:
    """
    Create a new Library for the authenticated user

    **对应 RULE-001:** 每个用户只拥有一个 Library
    **对应 RULE-003:** Library 名称必须满足 1-255 字符

    Args:
        request: LibraryCreate schema with name
        user_id: Extracted from JWT token (dependency)
        service: LibraryService instance (dependency)

    Returns:
        201: Created Library response
        409: User already has a Library
        422: Validation failed

    Example:
        ```
        POST /api/v1/libraries
        Content-Type: application/json
        Authorization: Bearer <token>

        {
            "name": "My Personal Library"
        }

        Response (201):
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "650e8400-e29b-41d4-a716-446655440000",
            "name": "My Personal Library",
            "created_at": "2025-01-15T10:30:00Z",
            "updated_at": "2025-01-15T10:30:00Z"
        }
        ```
    """
    try:
        logger.info(f"Creating Library for user {user_id} with name '{request.name}'")

        # Service 层：业务逻辑 + 异常转译
        library = await service.create_library(
            user_id=user_id,
            name=request.name,
        )

        logger.info(f"Library created successfully: {library.id}")
        return LibraryResponse.model_validate(library)

    except LibraryAlreadyExistsError as exc:
        logger.warning(f"Conflict: {exc.message}")
        raise _handle_domain_exception(exc)

    except InvalidLibraryNameError as exc:
        logger.warning(f"Validation failed: {exc.message}")
        raise _handle_domain_exception(exc)

    except LibraryException as exc:
        logger.error(f"Unexpected library exception: {exc.message}", exc_info=True)
        raise _handle_domain_exception(exc)


@router.get(
    "/{library_id}",
    response_model=LibraryDetailResponse,
    summary="Get Library by ID",
    description="获取指定 Library 的详细信息",
)
async def get_library(
    library_id: UUID = Path(..., description="Library 的唯一 ID"),
    service: LibraryService = Depends(get_library_service),
) -> LibraryDetailResponse:
    """
    Get a Library by its ID

    Args:
        library_id: UUID of the Library
        service: LibraryService instance (dependency)

    Returns:
        200: Library details
        404: Library not found

    Example:
        ```
        GET /api/v1/libraries/550e8400-e29b-41d4-a716-446655440000

        Response (200):
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "650e8400-e29b-41d4-a716-446655440000",
            "name": "My Personal Library",
            "created_at": "2025-01-15T10:30:00Z",
            "updated_at": "2025-01-15T10:30:00Z",
            "bookshelf_count": 5,
            "basement_bookshelf_id": "750e8400-e29b-41d4-a716-446655440000",
            "status": "active"
        }
        ```
    """
    try:
        logger.debug(f"Fetching Library {library_id}")
        library = await service.get_library(library_id)

        # 构建详细响应（包含统计）
        return LibraryDetailResponse.model_validate(library)

    except LibraryNotFoundError as exc:
        logger.warning(f"Not found: {exc.message}")
        raise _handle_domain_exception(exc)

    except LibraryException as exc:
        logger.error(f"Unexpected error: {exc.message}", exc_info=True)
        raise _handle_domain_exception(exc)


@router.get(
    "/user/{user_id}",
    response_model=LibraryDetailResponse,
    summary="Get Library for user",
    description="获取指定用户的 Library（每个用户唯一）",
)
async def get_user_library(
    user_id: UUID = Path(..., description="User 的唯一 ID"),
    service: LibraryService = Depends(get_library_service),
) -> LibraryDetailResponse:
    """
    Get the Library for a user

    **对应 RULE-001:** 每个用户只有一个 Library

    Args:
        user_id: UUID of the user
        service: LibraryService instance (dependency)

    Returns:
        200: User's Library
        404: User has no Library

    Example:
        ```
        GET /api/v1/libraries/user/650e8400-e29b-41d4-a716-446655440000

        Response (200):
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "650e8400-e29b-41d4-a716-446655440000",
            ...
        }
        ```
    """
    try:
        logger.debug(f"Fetching Library for user {user_id}")
        library = await service.get_user_library(user_id)
        return LibraryDetailResponse.model_validate(library)

    except LibraryNotFoundError as exc:
        logger.warning(f"User {user_id} has no Library")
        raise _handle_domain_exception(exc)

    except LibraryException as exc:
        logger.error(f"Error fetching user library: {exc.message}", exc_info=True)
        raise _handle_domain_exception(exc)


@router.put(
    "/{library_id}",
    response_model=LibraryResponse,
    summary="Update Library",
    description="更新 Library 信息",
)
async def update_library(
    library_id: UUID = Path(..., description="Library 的唯一 ID"),
    request: LibraryUpdate = None,
    user_id: UUID = Depends(get_current_user_id),
    service: LibraryService = Depends(get_library_service),
) -> LibraryResponse:
    """
    Update a Library

    **对应 RULE-003:** Library 名称验证

    Args:
        library_id: UUID of the Library
        request: Update data (name is optional)
        user_id: Current user (for permission check)
        service: LibraryService instance (dependency)

    Returns:
        200: Updated Library
        403: Permission denied
        404: Library not found
        422: Validation failed

    Example:
        ```
        PUT /api/v1/libraries/550e8400-e29b-41d4-a716-446655440000
        Content-Type: application/json
        Authorization: Bearer <token>

        {
            "name": "Updated Library Name"
        }

        Response (200):
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Updated Library Name",
            "updated_at": "2025-01-15T11:00:00Z",
            ...
        }
        ```
    """
    try:
        logger.info(f"Updating Library {library_id} for user {user_id}")

        # Permission check: 用户只能修改自己的 Library
        library = await service.get_library(library_id)
        if library.user_id != user_id:
            logger.warning(f"Permission denied: user {user_id} attempting to modify library owned by {library.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "PERMISSION_DENIED",
                    "message": "You can only update your own Library",
                    "details": {"library_id": str(library_id), "owner_id": str(library.user_id)}
                },
            )

        # 仅更新提供的字段
        if request.name:
            library = await service.rename_library(library_id, request.name)
        else:
            library = await service.get_library(library_id)

        logger.info(f"Library {library_id} updated successfully")
        return LibraryResponse.model_validate(library)

    except LibraryNotFoundError as exc:
        raise _handle_domain_exception(exc)

    except InvalidLibraryNameError as exc:
        raise _handle_domain_exception(exc)

    except LibraryException as exc:
        logger.error(f"Update failed: {exc.message}", exc_info=True)
        raise _handle_domain_exception(exc)


@router.delete(
    "/{library_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Library",
    description="删除 Library 及其所有内容",
)
async def delete_library(
    library_id: UUID = Path(..., description="Library 的唯一 ID"),
    user_id: UUID = Depends(get_current_user_id),
    service: LibraryService = Depends(get_library_service),
) -> None:
    """
    Delete a Library

    ⚠️ 级联删除：
      - 所有 Bookshelves（包括 Basement）
      - 所有 Books
      - 所有 Blocks
      - 关联的 Media 资源

    Args:
        library_id: UUID of the Library
        user_id: Current user (for permission check)
        service: LibraryService instance (dependency)

    Returns:
        204: No Content (successful deletion)
        403: Permission denied
        404: Library not found

    Example:
        ```
        DELETE /api/v1/libraries/550e8400-e29b-41d4-a716-446655440000
        Authorization: Bearer <token>

        Response (204): No Content
        ```
    """
    try:
        logger.info(f"Deleting Library {library_id} for user {user_id}")

        # Permission check
        library = await service.get_library(library_id)
        if library.user_id != user_id:
            logger.warning(f"Permission denied: user {user_id} attempting to delete library owned by {library.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "PERMISSION_DENIED",
                    "message": "You can only delete your own Library",
                    "details": {"library_id": str(library_id), "owner_id": str(library.user_id)}
                },
            )

        # 软删除（标记 deleted_at）
        await service.delete_library(library_id)

        logger.info(f"Library {library_id} deleted successfully")

    except LibraryNotFoundError as exc:
        raise _handle_domain_exception(exc)

    except LibraryException as exc:
        logger.error(f"Deletion failed: {exc.message}", exc_info=True)
        raise _handle_domain_exception(exc)


# ============================================
# Health Check (Optional)
# ============================================

@router.get(
    "/health",
    tags=["health"],
    summary="Library service health check",
)
async def health_check() -> dict:
    """检查 Library 服务健康状态"""
    logger.debug("Health check requested")
    return {"status": "ok", "service": "library"}
