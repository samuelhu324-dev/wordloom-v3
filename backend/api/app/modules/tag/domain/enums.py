"""Tag module enums - Entity type classification

RULE-018: Tag Creation & Management
RULE-019: Tag-Entity Association
"""

from enum import Enum


class EntityType(str, Enum):
    """Entity types that can be tagged.

    Supported entities:
    - BOOKSHELF: Global bookshelves
    - BOOK: Books within bookshelves
    - BLOCK: Content blocks within books

    Used in TagAssociation to link tags to different aggregate types.
    """
    BOOKSHELF = "bookshelf"
    BOOK = "book"
    BLOCK = "block"
