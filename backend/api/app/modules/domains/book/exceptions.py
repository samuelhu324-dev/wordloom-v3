"""Book Exceptions"""
class BookDomainException(Exception): pass
class BookNotFoundError(BookDomainException): pass
class InvalidBookTitleError(BookDomainException): pass
