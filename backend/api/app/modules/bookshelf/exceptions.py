"""
Bookshelf Exceptions - Domain-specific exceptions with HTTP mapping

Implements comprehensive exception hierarchy aligned with DDD_RULES:
  - RULE-004: Bookshelf unlimited creation (no constraints)
  - RULE-005: Bookshelf must belong to Library (FK constraint)
  - RULE-006: Bookshelf names unique per Library (UNIQUE constraint)
  - RULE-010: Basement Bookshelf special handling

Exception Hierarchy:
  DomainException (base)
    ├─ BookshelfException
    │   ├─ NotFoundError (404)
    │   ├─ AlreadyExistsError (409)
    │   ├─ InvalidNameError (422)
    │   ├─ LibraryAssociationError (422)
    │   ├─ BasementOperationError (422)
    │   └─ OperationError (500)
    └─ RepositoryException (500)
"""

from typing import Optional, Dict, Any


class DomainException(Exception):
    """Base for all Domain exceptions"""
    code: str = "DOMAIN_ERROR"
    http_status: int = 500
    details: Dict[str, Any] = {}

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        http_status: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if http_status:
            self.http_status = http_status
        if details:
            self.details = details

    @property
    def http_status_code(self) -> int:
        """Alias for http_status"""
        return self.http_status

    def to_dict(self) -> Dict[str, Any]:
        """序列化为 API 响应"""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


# ============================================
# Bookshelf Domain Exceptions
# ============================================

class BookshelfException(DomainException):
    """Base for all Bookshelf Domain exceptions"""
    pass


class BookshelfNotFoundError(BookshelfException):
    """
    RULE-005: 当请求的 Bookshelf 不存在时触发

    对应场景：
    - GET /libraries/{id}/bookshelves/{bookshelf_id} 不存在
    - 删除已删除的 Bookshelf
    - 更新不存在的 Bookshelf
    """
    code = "BOOKSHELF_NOT_FOUND"
    http_status = 404

    def __init__(
        self,
        bookshelf_id: str,
        library_id: Optional[str] = None,
    ):
        message = f"Bookshelf not found: {bookshelf_id}"
        if library_id:
            message += f" in Library {library_id}"

        super().__init__(
            message=message,
            details={
                "bookshelf_id": bookshelf_id,
                "library_id": library_id,
            }
        )


class BookshelfForbiddenError(BookshelfException):
    """Authorization failure when actor does not own the target library/bookshelf."""

    code = "BOOKSHELF_FORBIDDEN"
    http_status = 403

    def __init__(
        self,
        *,
        bookshelf_id: Optional[str] = None,
        library_id: Optional[str] = None,
        actor_user_id: Optional[str] = None,
        reason: str = "Actor is not allowed to access this bookshelf",
    ):
        message = reason
        super().__init__(
            message=message,
            details={
                "bookshelf_id": bookshelf_id,
                "library_id": library_id,
                "actor_user_id": actor_user_id,
                "reason": reason,
            },
        )


class BookshelfAlreadyExistsError(BookshelfException):
    """
    RULE-006: 当同一 Library 下创建重名 Bookshelf 时触发

    Invariant: 同一 Library 下，Bookshelf 名称必须唯一
    Database: UNIQUE(library_id, name) 约束
    """
    code = "BOOKSHELF_ALREADY_EXISTS"
    http_status = 409  # Conflict

    def __init__(
        self,
        library_id: Optional[str] = None,
        name: Optional[str] = None,
        existing_bookshelf_id: Optional[str] = None,
    ):
        core = "Bookshelf with this name already exists"
        if library_id and name:
            message = f"Bookshelf with name '{name}' already exists in Library {library_id}"
        elif name:
            message = f"Bookshelf named '{name}' already exists"
        else:
            message = core

        if existing_bookshelf_id:
            message += f" (ID: {existing_bookshelf_id})"

        super().__init__(
            message=message,
            details={
                "library_id": library_id,
                "name": name,
                "existing_bookshelf_id": existing_bookshelf_id,
            }
        )


class InvalidBookshelfNameError(BookshelfException):
    """
    RULE-006: 当 Bookshelf 名称不满足要求时触发

    Invariant: name 必须满足 1 <= len(name) <= 255
    """
    code = "INVALID_BOOKSHELF_NAME"
    http_status = 422  # Unprocessable Entity

    def __init__(self, name: Optional[str], reason: str):
        message = f"Invalid Bookshelf name: {reason}"
        if name:
            message += f" (got: '{name}')"

        super().__init__(
            message=message,
            details={
                "provided_name": name,
                "reason": reason,
                "constraints": {
                    "min_length": 1,
                    "max_length": 255,
                }
            }
        )


class BookshelfLibraryAssociationError(BookshelfException):
    """
    RULE-005: 当 Bookshelf 的 library_id 不合法或丢失时触发

    Invariant: library_id 是必填字段，且必须指向有效的 Library
    """
    code = "BOOKSHELF_LIBRARY_ASSOCIATION_ERROR"
    http_status = 422

    def __init__(
        self,
        bookshelf_id: str,
        reason: str,
        library_id: Optional[str] = None,
    ):
        super().__init__(
            message=f"Bookshelf library association error: {reason}",
            details={
                "bookshelf_id": bookshelf_id,
                "library_id": library_id,
                "reason": reason,
            }
        )


class BasementOperationError(BookshelfException):
    """
    RULE-010: 当尝试对 Basement Bookshelf 进行非法操作时触发

    Invariant: Basement Bookshelf 是特殊的系统 Bookshelf，不能：
    - 被删除
    - 被重命名
    - 被取消固定（如果已固定）
    """
    code = "BASEMENT_OPERATION_ERROR"
    http_status = 422

    def __init__(self, bookshelf_id: str, operation: str, reason: str):
        super().__init__(
            message=f"Cannot {operation} Basement Bookshelf: {reason}",
            details={
                "bookshelf_id": bookshelf_id,
                "operation": operation,
                "reason": reason,
                "basement_info": "Basement is a system-managed bookshelf for soft-deleted items",
            }
        )


class BookshelfOperationError(BookshelfException):
    """Generic Bookshelf operation failure"""
    code = "BOOKSHELF_OPERATION_ERROR"
    http_status = 500

    def __init__(
        self,
        bookshelf_id: str,
        operation: str,
        reason: str,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=f"Failed to {operation} Bookshelf {bookshelf_id}: {reason}",
            details={
                "bookshelf_id": bookshelf_id,
                "operation": operation,
                "reason": reason,
                "original_error": str(original_error) if original_error else None,
            }
        )


class BookshelfTagSyncError(BookshelfException):
    """Tag 同步失败时抛出的异常"""

    code = "BOOKSHELF_TAG_SYNC_ERROR"
    http_status = 400

    def __init__(self, bookshelf_id: str, reason: str):
        super().__init__(
            message=f"Failed to synchronize tags for Bookshelf {bookshelf_id}: {reason}",
            details={
                "bookshelf_id": bookshelf_id,
                "reason": reason,
            },
        )


# ============================================
# Repository Exceptions
# ============================================

class RepositoryException(DomainException):
    """Base for Repository/Infrastructure exceptions"""
    code = "REPOSITORY_ERROR"
    http_status = 500


class BookshelfPersistenceError(RepositoryException):
    """When persistence fails (DB constraint, integrity, etc.)"""
    code = "BOOKSHELF_PERSISTENCE_ERROR"

    def __init__(
        self,
        operation: str,
        reason: str,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=f"Failed to persist Bookshelf during {operation}: {reason}",
            details={
                "operation": operation,
                "reason": reason,
                "original_error": str(original_error) if original_error else None,
            }
        )
