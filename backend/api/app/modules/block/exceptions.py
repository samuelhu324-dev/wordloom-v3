"""
Block Exceptions - Domain-specific exceptions with HTTP mapping

Implements comprehensive exception hierarchy aligned with DDD_RULES:
  - RULE-013-REVISED: Block type system with HEADING support
  - RULE-014: Block type must be valid
  - RULE-015-REVISED: Block ordering via Fractional Index
  - RULE-016: Block must belong to Book (FK constraint)
  - POLICY-008: Block soft delete (move to Basement)

Exception Hierarchy:
  DomainException (base)
    ├─ BlockException
    │   ├─ NotFoundError (404)
    │   ├─ BookNotFoundError (422)
    │   ├─ InvalidBlockTypeError (422)
    │   ├─ InvalidHeadingLevelError (422)
    │   ├─ BlockContentTooLongError (422)
    │   ├─ FractionalIndexError (422)
    │   ├─ BlockInBasementError (409)
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
# Block Domain Exceptions
# ============================================

class BlockException(DomainException):
    """Base for all Block Domain exceptions"""
    pass


class BlockNotFoundError(BlockException):
    """
    RULE-016: 当请求的 Block 不存在时触发

    对应场景：
    - GET /books/{id}/blocks/{block_id} 不存在
    - 删除已删除的 Block
    - 更新不存在的 Block
    """
    code = "BLOCK_NOT_FOUND"
    http_status = 404

    def __init__(
        self,
        block_id: str,
        book_id: Optional[str] = None,
    ):
        message = f"Block not found: {block_id}"
        if book_id:
            message += f" in Book {book_id}"

        super().__init__(
            message=message,
            details={
                "block_id": block_id,
                "book_id": book_id,
            }
        )


class BookNotFoundError(BlockException):
    """
    RULE-016: 当 Block 的 Book 不存在或用户无权限时触发

    Invariant: book_id 是必填字段，且必须指向有效的 Book
    Permission: User 必须拥有该 Book 的 Library
    """
    code = "BOOK_NOT_FOUND"
    http_status = 422

    def __init__(
        self,
        book_id: str,
        block_id: Optional[str] = None,
    ):
        super().__init__(
            message=f"Book not found or permission denied: {book_id}",
            details={
                "book_id": book_id,
                "block_id": block_id,
            }
        )


class InvalidBlockTypeError(BlockException):
    """
    RULE-014: 当 Block 类型不支持时触发

    Invariant: block_type 必须是支持的类型之一：
    - TEXT, HEADING, IMAGE, CODE, TABLE, QUOTE, LIST, DIVIDER
    """
    code = "INVALID_BLOCK_TYPE"
    http_status = 422

    def __init__(self, block_type: str, reason: Optional[str] = None):
        message = f"Invalid Block type: {block_type}"
        if reason:
            message += f" ({reason})"

        super().__init__(
            message=message,
            details={
                "provided_type": block_type,
                "supported_types": [
                    "text", "heading", "image", "code", "table", "quote", "list", "divider"
                ],
                "reason": reason,
            }
        )


class InvalidBlockContentError(BlockException):
    """
    RULE-014: 当 Block 内容无效时触发

    Invariant: content 必须非空且不超过 10000 字符
    """
    code = "INVALID_BLOCK_CONTENT"
    http_status = 422

    def __init__(self, reason: str):
        super().__init__(
            message=f"Invalid Block content: {reason}",
            details={
                "reason": reason,
            }
        )


class InvalidHeadingLevelError(BlockException):
    """
    RULE-013-REVISED: 当 HEADING Block 的 level 不在 1-3 范围时触发

    Invariant: heading_level 必须是 1, 2, 或 3（对应 h1, h2, h3）
    """
    code = "INVALID_HEADING_LEVEL"
    http_status = 422

    def __init__(self, provided_level: Optional[int], reason: str = ""):
        message = f"Invalid heading level: {provided_level}"
        if reason:
            message += f" ({reason})"

        super().__init__(
            message=message,
            details={
                "provided_level": provided_level,
                "valid_levels": [1, 2, 3],
                "reason": reason or "Heading level must be 1, 2, or 3",
            }
        )


class BlockContentTooLongError(BlockException):
    """
    RULE-014: 当 Block 内容超过 10000 字符限制时触发

    Invariant: content 最大长度为 10000 字符
    """
    code = "BLOCK_CONTENT_TOO_LONG"
    http_status = 422

    def __init__(self, content_length: int, max_length: int = 10000):
        super().__init__(
            message=f"Block content exceeds maximum length: {content_length} > {max_length}",
            details={
                "content_length": content_length,
                "max_length": max_length,
                "excess": content_length - max_length,
            }
        )


class FractionalIndexError(BlockException):
    """
    RULE-015-REVISED: 当分数索引计算失败时触发

    Invariant: Block 顺序由分数索引 (Decimal) 维护
    - 支持 O(1) 拖拽插入
    - 位置：0 <= order < 1024
    """
    code = "FRACTIONAL_INDEX_ERROR"
    http_status = 422

    def __init__(
        self,
        block_id: str,
        reason: str,
        current_order: Optional[str] = None,
    ):
        super().__init__(
            message=f"Fractional index calculation failed for Block {block_id}: {reason}",
            details={
                "block_id": block_id,
                "reason": reason,
                "current_order": current_order,
            }
        )


class BlockInBasementError(BlockException):
    """
    POLICY-008: 当尝试操作一个已在 Basement 中的 Block 时触发

    Invariant: 软删除的 Block 不能再被删除或修改
    """
    code = "BLOCK_IN_BASEMENT"
    http_status = 409  # Conflict

    def __init__(self, block_id: str):
        super().__init__(
            message=f"Block is soft-deleted (in Basement): {block_id}",
            details={
                "block_id": block_id,
                "reason": "Cannot operate on soft-deleted Block",
            }
        )


class BlockOperationError(BlockException):
    """Generic Block operation failure"""
    code = "BLOCK_OPERATION_ERROR"
    http_status = 500

    def __init__(
        self,
        block_id: str,
        operation: str,
        reason: str,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=f"Failed to {operation} Block {block_id}: {reason}",
            details={
                "block_id": block_id,
                "operation": operation,
                "reason": reason,
                "original_error": str(original_error) if original_error else None,
            }
        )


# ============================================
# Repository Exceptions
# ============================================

class RepositoryException(DomainException):
    """Base for Repository/Infrastructure exceptions"""
    code = "REPOSITORY_ERROR"
    http_status = 500


class BlockPersistenceError(RepositoryException):
    """When persistence fails (DB constraint, integrity, etc.)"""
    code = "BLOCK_PERSISTENCE_ERROR"

    def __init__(
        self,
        operation: str,
        reason: str,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=f"Failed to persist Block during {operation}: {reason}",
            details={
                "operation": operation,
                "reason": reason,
                "original_error": str(original_error) if original_error else None,
            }
        )
