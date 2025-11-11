"""Tag Exceptions"""
class TagDomainException(Exception): pass
class TagNotFoundError(TagDomainException): pass
class DuplicateTagNameError(TagDomainException): pass
