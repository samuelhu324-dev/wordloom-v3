"""
Storage Manager - Infrastructure layer for file storage

Purpose:
- Encapsulate storage path logic (moved from Domain)
- Support multiple storage strategies (local, S3, etc.)
- Provide consistent API for file operations

This is part of the Infrastructure layer, NOT Domain layer.
Domain models should only work with storage URLs, not paths.

Architecture Pattern: Strategy Pattern
- StorageManager defines interface
- Concrete implementations handle actual storage (LocalStorage, S3Storage, etc.)
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4
import os


# ============================================================================
# Storage Strategy Interface
# ============================================================================

class IStorageStrategy(ABC):
    """Abstract storage strategy interface"""

    @abstractmethod
    async def save_file(self, content: bytes, filename: str, directory: str) -> str:
        """
        Save file to storage

        Args:
            content: File content bytes
            filename: Name of file
            directory: Directory path

        Returns:
            URL or path to access file
        """
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> None:
        """Delete file from storage"""
        pass

    @abstractmethod
    async def get_file(self, file_path: str) -> Optional[bytes]:
        """Get file content from storage"""
        pass


# ============================================================================
# Local Storage Implementation
# ============================================================================

class LocalStorageStrategy(IStorageStrategy):
    """
    Local filesystem storage strategy

    Stores files on local disk. Good for:
    - Development
    - Single-server deployments
    - Testing
    """

    def __init__(self, base_path: str = "./storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save_file(self, content: bytes, filename: str, directory: str) -> str:
        """
        Save file locally

        Args:
            content: File content
            filename: Filename
            directory: Subdirectory (e.g., "bookshelf_covers")

        Returns:
            Relative path to file
        """
        dir_path = self.base_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)

        file_path = dir_path / filename
        file_path.write_bytes(content)

        return str(file_path.relative_to(self.base_path))

    async def delete_file(self, file_path: str) -> None:
        """Delete file"""
        full_path = self.base_path / file_path
        if full_path.exists():
            full_path.unlink()

    async def get_file(self, file_path: str) -> Optional[bytes]:
        """Get file content"""
        full_path = self.base_path / file_path
        if full_path.exists():
            return full_path.read_bytes()
        return None


# ============================================================================
# S3 Storage Implementation (Stub)
# ============================================================================

class S3StorageStrategy(IStorageStrategy):
    """
    AWS S3 storage strategy (stub - implement with boto3)

    Stores files on AWS S3. Good for:
    - Production deployments
    - Scalability
    - Availability
    """

    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.region = region
        # TODO: Initialize boto3 client

    async def save_file(self, content: bytes, filename: str, directory: str) -> str:
        """Save file to S3"""
        # TODO: Implement S3 upload
        key = f"{directory}/{filename}"
        return f"s3://{self.bucket_name}/{key}"

    async def delete_file(self, file_path: str) -> None:
        """Delete file from S3"""
        # TODO: Implement S3 delete
        pass

    async def get_file(self, file_path: str) -> Optional[bytes]:
        """Get file from S3"""
        # TODO: Implement S3 download
        return None


# ============================================================================
# Storage Manager (Facade)
# ============================================================================

class StorageManager:
    """
    Storage Manager - Facade for storage operations

    Provides unified interface for file storage operations.
    Uses Strategy pattern to support different storage backends.

    Usage:
        manager = StorageManager(LocalStorageStrategy())
        url = await manager.save_bookshelf_cover(image_bytes, bookshelf_id)
        await manager.delete_file(url)

    Directory Structure:
        storage/
        ├── library_covers/       (Library cover images)
        ├── bookshelf_covers/     (Bookshelf cover images)
        ├── book_covers/          (Book cover images)
        ├── block_images/         (Block embedded images)
        ├── chronicle_attachments/ (Time tracking attachments)
        └── temp/                 (Temporary uploads)
    """

    DIRECTORY_LIBRARY_COVERS = "library_covers"
    DIRECTORY_BOOKSHELF_COVERS = "bookshelf_covers"
    DIRECTORY_BOOK_COVERS = "book_covers"
    DIRECTORY_BLOCK_IMAGES = "block_images"
    DIRECTORY_CHRONICLE_ATTACHMENTS = "chronicle_attachments"
    DIRECTORY_TEMP = "temp"

    def __init__(self, strategy: IStorageStrategy):
        """
        Initialize storage manager

        Args:
            strategy: Storage strategy implementation
        """
        self.strategy = strategy

    async def save_bookshelf_cover(self, content: bytes, bookshelf_id: UUID) -> str:
        """Save Bookshelf cover image"""
        filename = f"{bookshelf_id}_{datetime.utcnow().isoformat()}.jpg"
        return await self.strategy.save_file(
            content,
            filename,
            self.DIRECTORY_BOOKSHELF_COVERS
        )

    async def save_library_cover(self, content: bytes, library_id: UUID, original_filename: str) -> str:
        """Save Library cover image and return storage key"""
        suffix = Path(original_filename or "").suffix.lower() or ".bin"
        unique_part = uuid4().hex
        filename = f"{library_id}_{unique_part}{suffix}"
        return await self.strategy.save_file(
            content,
            filename,
            self.DIRECTORY_LIBRARY_COVERS
        )

    async def save_book_cover(self, content: bytes, book_id: UUID, original_filename: str | None = None) -> str:
        """Save Book cover image (preserves extension when provided)."""
        suffix = Path(original_filename or "").suffix.lower() or ".jpg"
        safe_stem = Path(original_filename or f"book-{book_id}").stem or f"book-{book_id}"
        normalized = safe_stem.replace(" ", "_")
        filename = f"{book_id}_{uuid4().hex}_{normalized}{suffix}"
        return await self.strategy.save_file(
            content,
            filename,
            self.DIRECTORY_BOOK_COVERS
        )

    async def save_block_image(self, content: bytes, block_id: UUID) -> str:
        """Save Block embedded image"""
        filename = f"{block_id}_{datetime.utcnow().isoformat()}.jpg"
        return await self.strategy.save_file(
            content,
            filename,
            self.DIRECTORY_BLOCK_IMAGES
        )

    async def save_chronicle_attachment(self, content: bytes, session_id: UUID) -> str:
        """Save Chronicle attachment"""
        filename = f"{session_id}_{datetime.utcnow().isoformat()}"
        return await self.strategy.save_file(
            content,
            filename,
            self.DIRECTORY_CHRONICLE_ATTACHMENTS
        )

    async def save_temp_file(self, content: bytes, filename: str) -> str:
        """Save temporary file (during upload)"""
        return await self.strategy.save_file(
            content,
            filename,
            self.DIRECTORY_TEMP
        )

    async def delete_file(self, file_path: str) -> None:
        """Delete file"""
        await self.strategy.delete_file(file_path)

    async def get_file(self, file_path: str) -> Optional[bytes]:
        """Get file content"""
        return await self.strategy.get_file(file_path)

    def switch_strategy(self, strategy: IStorageStrategy) -> None:
        """Switch storage strategy at runtime"""
        self.strategy = strategy
