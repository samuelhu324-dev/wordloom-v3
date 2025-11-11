"""
Bookshelf Exceptions - Domain-specific exceptions
"""


class BookshelfDomainException(Exception):
    """Base exception for Bookshelf Domain"""
    pass


class BookshelfNotFoundError(BookshelfDomainException):
    """Raised when a Bookshelf is not found"""
    pass


class InvalidBookshelfNameError(BookshelfDomainException):
    """Raised when attempting to set an invalid Bookshelf name"""
    pass


class BookshelfOperationError(BookshelfDomainException):
    """Raised when a Bookshelf operation fails"""
    pass
