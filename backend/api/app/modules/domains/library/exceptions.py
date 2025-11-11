"""
Library Exceptions - Domain-specific exceptions

Custom exceptions for Library Domain error handling.
"""


class LibraryDomainException(Exception):
    """Base exception for Library Domain"""
    pass


class LibraryNotFoundError(LibraryDomainException):
    """Raised when a Library is not found"""
    pass


class LibraryAlreadyExistsError(LibraryDomainException):
    """Raised when attempting to create a Library but user already has one"""
    pass


class InvalidLibraryNameError(LibraryDomainException):
    """Raised when attempting to set an invalid Library name"""
    pass


class LibraryOperationError(LibraryDomainException):
    """Raised when a Library operation fails"""
    pass
