"""
Book domain-specific exceptions - Business error hierarchy

All exceptions inherit from BusinessError base class.
Mapped to HTTP status codes in router layer.
"""

from typing import Optional
from uuid import UUID

from api.app.shared.errors import BusinessError


# Domain exception alias for router exception handling
DomainException = BusinessError


# Book-specific exceptions

class BookNotFoundError(BusinessError):
    """Book with given ID does not exist"""
    status_code = 404
    error_code = "BOOK_NOT_FOUND"
    message = "Book not found"

    def __init__(self, book_id: UUID, detail: Optional[str] = None):
        self.book_id = book_id
        self.detail = detail or f"Book {book_id} does not exist"
        super().__init__(self.message, self.detail)


class BookAlreadyExistsError(BusinessError):
    """Book with same title already exists in this library"""
    status_code = 409
    error_code = "BOOK_ALREADY_EXISTS"
    message = "Book already exists"

    def __init__(self, title: str, detail: Optional[str] = None):
        self.title = title
        self.detail = detail or f"Book '{title}' already exists"
        super().__init__(self.message, self.detail)


class InvalidBookDataError(BusinessError):
    """Book data is invalid"""
    status_code = 422
    error_code = "INVALID_BOOK_DATA"
    message = "Invalid book data"

    def __init__(self, detail: str):
        super().__init__(self.message, detail)


class InvalidBookMoveError(BusinessError):
    """Cannot move book to specified bookshelf"""
    status_code = 422
    error_code = "INVALID_BOOK_MOVE"
    message = "Cannot move book"

    def __init__(self, book_id: UUID, reason: str):
        self.book_id = book_id
        detail = f"Cannot move book {book_id}: {reason}"
        super().__init__(self.message, detail)


class BookNotInBasementError(BusinessError):
    """Book is not in basement"""
    status_code = 422
    error_code = "BOOK_NOT_IN_BASEMENT"
    message = "Book is not in basement"

    def __init__(self, book_id: UUID, detail: Optional[str] = None):
        self.book_id = book_id
        msg = detail or f"Book {book_id} is not in basement"
        super().__init__(self.message, msg)


class BookOperationError(BusinessError):
    """Generic book operation error"""
    status_code = 500
    error_code = "BOOK_OPERATION_ERROR"
    message = "Book operation failed"

    def __init__(self, operation: str, reason: str):
        self.operation = operation
        detail = f"Operation '{operation}' failed: {reason}"
        super().__init__(self.message, detail)
