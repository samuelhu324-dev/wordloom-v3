"""Media enums - Constant definitions for media domain

POLICY-010: Media Management & Trash Lifecycle
"""

from enum import Enum


class MediaType(str, Enum):
    """Type of media file"""
    IMAGE = "image"
    VIDEO = "video"


class MediaMimeType(str, Enum):
    """Supported MIME types for media files"""
    # Images
    JPEG = "image/jpeg"
    PNG = "image/png"
    WEBP = "image/webp"
    GIF = "image/gif"

    # Videos
    MP4 = "video/mp4"
    WEBM = "video/webm"
    OGG = "video/ogg"


class MediaState(str, Enum):
    """Current state of media (soft delete tracking)"""
    ACTIVE = "ACTIVE"
    TRASH = "TRASH"


class EntityTypeForMedia(str, Enum):
    """Entity types that can reference media

    POLICY-010: Media associations are independent (no cascading)
    """
    BOOKSHELF = "bookshelf"
    BOOK = "book"
    BLOCK = "block"
