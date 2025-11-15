"""Search Domain Enums - Constant definitions

Pure enum definitions for Search domain.
No dependencies on infrastructure or other layers.
"""

from enum import Enum


class SearchEntityType(str, Enum):
    """Entity types that can be searched"""
    BLOCK = "block"
    BOOK = "book"
    BOOKSHELF = "bookshelf"
    TAG = "tag"
    LIBRARY = "library"


class SearchMediaType(str, Enum):
    """Media types associated with search results (optional metadata)"""
    IMAGE = "image"
    VIDEO = "video"


__all__ = [
    "SearchEntityType",
    "SearchMediaType",
]
