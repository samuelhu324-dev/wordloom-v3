#!/usr/bin/env python
"""Rewrite corrupt media files"""

from pathlib import Path

# Media input.py
input_file = Path('d:\\Project\\Wordloom\\backend\\api\\app\\modules\\media\\application\\ports\\input.py')
input_content = '''"""
Media Input Ports - UseCase Interfaces

Defines the input port interfaces (abstract base classes) that the application layer
(use cases) expose to the outside world (routers).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID
from dataclasses import dataclass

from api.app.modules.media.domain import Media, MediaMimeType, EntityTypeForMedia


@dataclass
class UploadMediaRequest:
    """Upload media file request"""
    filename: str
    mime_type: str
    file_size: int
    storage_key: str


@dataclass
class DeleteMediaRequest:
    """Delete media request"""
    media_id: UUID


@dataclass
class RestoreMediaRequest:
    """Restore media from trash request"""
    media_id: UUID


class IUploadMediaUseCase(ABC):
    """Upload media use case interface"""

    @abstractmethod
    async def execute(self, request: UploadMediaRequest):
        pass
'''

input_file.write_text(input_content, encoding='utf-8')
print(f"✅ Fixed {input_file.name}")

# Media output.py
output_file = Path('d:\\Project\\Wordloom\\backend\\api\\app\\modules\\media\\application\\ports\\output.py')
output_content = '''"""
Media Repository Output Port

This file defines the abstract interface (output port) that the application layer
expects from the infrastructure layer for persistent storage of Media.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime

from api.app.modules.media.domain import Media, MediaState, EntityTypeForMedia


class MediaRepository(ABC):
    """Abstract repository for Media persistence (Output Port)

    Defines the contract that application layer (use cases) expects from
    infrastructure layer (storage adapters).
    """

    @abstractmethod
    async def save(self, media: Media) -> None:
        """Save a media object to persistent storage"""
        pass

    @abstractmethod
    async def get_by_id(self, media_id: UUID) -> Optional[Media]:
        """Retrieve a media object by ID"""
        pass

    @abstractmethod
    async def delete_by_id(self, media_id: UUID) -> None:
        """Soft delete a media object"""
        pass
'''

output_file.write_text(output_content, encoding='utf-8')
print(f"✅ Fixed {output_file.name}")
