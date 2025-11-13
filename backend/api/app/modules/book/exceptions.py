"""
Book Exceptions - Domain-specific exceptions with HTTP mapping

Implements comprehensive exception hierarchy aligned with DDD_RULES:
  - RULE-009: Book unlimited creation (no constraints)
  - RULE-010: Book must belong to Bookshelf (FK constraint)
  - RULE-011: Book can move across Bookshelves (with permission check)
  - RULE-012: Book soft delete (move to Basement)
  - RULE-013: Book restoration from Basement

Exception Hierarchy:
  DomainException (base)
    ├─ BookException
    │   ├─ NotFoundError (404)
    │   ├─ AlreadyExistsError (409)
    │   ├─ InvalidTitleError (422)
    │   ├─ BookshelfNotFoundError (422)
    │   ├─ InvalidBookMoveError (422)
    │   ├─ NotInBasementError (422)
    │   ├─ AlreadyDeletedError (409)
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
# Book Domain Exceptions
# ============================================

class BookException(DomainException):
    """Base for all Book Domain exceptions"""
    pass


class BookNotFoundError(BookException):
    """
    RULE-009: 当请求的 Book 不存在时触发

    对应场景：
    - GET /books/{id} 不存在
    - 删除已删除的 Book
    - 更新不存在的 Book
    """
    code = "BOOK_NOT_FOUND"
    http_status = 404

    def __init__(
        self,
        book_id: str,
        bookshelf_id: Optional[str] = None,
    ):
        message = f"Book not found: {book_id}"
        if bookshelf_id:
            message += f" in Bookshelf {bookshelf_id}"

        super().__init__(
            message=message,
            details={
                "book_id": book_id,
                "bookshelf_id": bookshelf_id,
            }
        )


class BookAlreadyExistsError(BookException):
    """
    RULE-009: 当创建重复的 Book 时触发（极少情况）

    Invariant: Book 由 UUID 唯一标识
    Database: PRIMARY KEY(id) 约束
    """
    code = "BOOK_ALREADY_EXISTS"
    http_status = 409  # Conflict

    def __init__(
        self,
        book_id: str,
        bookshelf_id: Optional[str] = None,
    ):
        message = f"Book already exists: {book_id}"
        if bookshelf_id:
            message += f" in Bookshelf {bookshelf_id}"

        super().__init__(
            message=message,
            details={
                "book_id": book_id,
                "bookshelf_id": bookshelf_id,
            }
        )


class InvalidBookTitleError(BookException):
    """
    RULE-009: 当 Book 标题不满足要求时触发

    Invariant: title 必须满足 1 <= len(title) <= 255
    """
    code = "INVALID_BOOK_TITLE"
    http_status = 422  # Unprocessable Entity

    def __init__(self, title: Optional[str], reason: str):
        message = f"Invalid Book title: {reason}"
        if title:
            message += f" (got: '{title}')"

        super().__init__(
            message=message,
            details={
                "provided_title": title,
                "reason": reason,
                "constraints": {
                    "min_length": 1,
                    "max_length": 255,
                }
            }
        )


class BookshelfNotFoundError(BookException):
    """
    RULE-010: 当 Book 的 Bookshelf 不存在时触发

    Invariant: bookshelf_id 是必填字段，且必须指向有效的 Bookshelf
    """
    code = "BOOKSHELF_NOT_FOUND"
    http_status = 422

    def __init__(
        self,
        bookshelf_id: str,
        book_id: Optional[str] = None,
    ):
        super().__init__(
            message=f"Bookshelf not found: {bookshelf_id}",
            details={
                "book_id": book_id,
                "bookshelf_id": bookshelf_id,
            }
        )


class InvalidBookMoveError(BookException):
    """
    RULE-011: 当尝试将 Book 移到非法目标 Bookshelf 时触发

    Invariant: Book 只能在同一 Library 内的 Bookshelf 间转移
    - 不能转移到其他 Library 的 Bookshelf
    - 不能手动转移到 Basement（必须通过 delete_book）
    """
    code = "INVALID_BOOK_MOVE"
    http_status = 422

    def __init__(
        self,
        book_id: str,
        source_bookshelf_id: str,
        target_bookshelf_id: str,
        reason: str,
    ):
        super().__init__(
            message=f"Cannot move Book {book_id} to Bookshelf {target_bookshelf_id}: {reason}",
            details={
                "book_id": book_id,
                "source_bookshelf_id": source_bookshelf_id,
                "target_bookshelf_id": target_bookshelf_id,
                "reason": reason,
            }
        )


class BookNotInBasementError(BookException):
    """
    RULE-013: 当尝试恢复一个不在 Basement 中的 Book 时触发

    Invariant: 只有 soft_deleted_at IS NOT NULL 的 Book 才能从 Basement 恢复
    """
    code = "BOOK_NOT_IN_BASEMENT"
    http_status = 422

    def __init__(self, book_id: str):
        super().__init__(
            message=f"Book is not in Basement: {book_id}",
            details={
                "book_id": book_id,
                "reason": "Book must be soft-deleted (in Basement) to restore",
            }
        )


class BookAlreadyDeletedError(BookException):
    """
    RULE-012: 当尝试删除一个已在 Basement 中的 Book 时触发

    Invariant: 一个 Book 不能被多次转移到 Basement
    """
    code = "BOOK_ALREADY_DELETED"
    http_status = 409  # Conflict

    def __init__(self, book_id: str):
        super().__init__(
            message=f"Book is already deleted (in Basement): {book_id}",
            details={
                "book_id": book_id,
                "reason": "Cannot delete a book that is already in Basement",
            }
        )


class BookOperationError(BookException):
    """Generic Book operation failure"""
    code = "BOOK_OPERATION_ERROR"
    http_status = 500

    def __init__(
        self,
        book_id: str,
        operation: str,
        reason: str,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=f"Failed to {operation} Book {book_id}: {reason}",
            details={
                "book_id": book_id,
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


class BookPersistenceError(RepositoryException):
    """When persistence fails (DB constraint, integrity, etc.)"""
    code = "BOOK_PERSISTENCE_ERROR"

    def __init__(
        self,
        operation: str,
        reason: str,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=f"Failed to persist Book during {operation}: {reason}",
            details={
                "operation": operation,
                "reason": reason,
                "original_error": str(original_error) if original_error else None,
            }
        )
