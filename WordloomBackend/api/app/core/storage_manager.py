"""
业界标准存储管理器 - 固定存储路径，不随业务关系变化
核心思想：storage_path 一旦创建就永不改变
"""
from pathlib import Path
from typing import Optional
import shutil
from datetime import datetime

class StorageManager:
    """
    管理 Orbit 存储结构 - 业界标准方案

    存储结构（固定、不变）：
    storage/orbit_uploads/
    ├── notes/
    │   ├── {note_id_1}/
    │   │   ├── content.md
    │   │   └── images/
    │   │       ├── img1.jpg
    │   │       └── img2.png
    │   └── {note_id_2}/
    │       ├── content.md
    │       └── images/
    └── bookshelves/
        ├── {bookshelf_id_1}/
        │   └── cover.{ext}
        └── {bookshelf_id_2}/
            └── cover.{ext}

    业务关系（灵活、可变）：
    数据库 orbit_notes 表：
    - id
    - bookshelf_id (可以改变，不影响存储路径)
    - storage_path (固定: notes/{note_id})
    """

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.notes_dir = self.base_dir / "notes"
        self.bookshelves_dir = self.base_dir / "bookshelves"
        self._ensure_dirs()

    def _ensure_dirs(self):
        """确保根目录存在"""
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.bookshelves_dir.mkdir(parents=True, exist_ok=True)

    # ========== 核心方法：创建和删除 ==========

    def create_note_storage(self, note_id: str) -> str:
        """
        为笔记创建存储目录

        Args:
            note_id: 笔记 ID

        Returns:
            相对路径: notes/{note_id}
        """
        note_dir = self.notes_dir / note_id
        note_dir.mkdir(parents=True, exist_ok=True)

        # 创建 images 子目录
        images_dir = note_dir / "images"
        images_dir.mkdir(exist_ok=True)

        print(f"[STORAGE] Created note storage: notes/{note_id}")
        return f"notes/{note_id}"

    def delete_note_storage(self, note_id: str) -> bool:
        """
        删除笔记的所有存储内容

        Args:
            note_id: 笔记 ID

        Returns:
            是否成功
        """
        try:
            note_dir = self.notes_dir / note_id
            if note_dir.exists():
                shutil.rmtree(note_dir)
                print(f"[STORAGE] Deleted note storage: notes/{note_id}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to delete note storage {note_id}: {e}")
            return False

    # ========== 书橱存储方法 ==========

    def create_bookshelf_storage(self, bookshelf_id: str) -> str:
        """
        为书橱创建存储目录

        Args:
            bookshelf_id: 书橱 ID

        Returns:
            相对路径: bookshelves/{bookshelf_id}
        """
        bookshelf_dir = self.bookshelves_dir / bookshelf_id
        bookshelf_dir.mkdir(parents=True, exist_ok=True)

        print(f"[STORAGE] Created bookshelf storage: bookshelves/{bookshelf_id}")
        return f"bookshelves/{bookshelf_id}"

    def delete_bookshelf_storage(self, bookshelf_id: str) -> bool:
        """
        删除书橱的所有存储内容（包括封面图）

        Args:
            bookshelf_id: 书橱 ID

        Returns:
            是否成功
        """
        try:
            bookshelf_dir = self.bookshelves_dir / bookshelf_id
            if bookshelf_dir.exists():
                shutil.rmtree(bookshelf_dir)
                print(f"[STORAGE] Deleted bookshelf storage: bookshelves/{bookshelf_id}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to delete bookshelf storage {bookshelf_id}: {e}")
            return False

    def get_bookshelf_dir(self, bookshelf_id: str) -> Path:
        """获取书橱的完整路径"""
        return self.bookshelves_dir / bookshelf_id

    def get_bookshelf_cover_path(self, bookshelf_id: str) -> Path:
        """获取书橱封面图的目录"""
        bookshelf_dir = self.bookshelves_dir / bookshelf_id
        bookshelf_dir.mkdir(parents=True, exist_ok=True)
        return bookshelf_dir

    # ========== 辅助方法：获取路径 ==========

    def get_note_dir(self, note_id: str) -> Path:
        """获取笔记的完整路径"""
        return self.notes_dir / note_id

    def get_note_images_dir(self, note_id: str) -> Path:
        """获取笔记图片目录"""
        images_dir = self.notes_dir / note_id / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        return images_dir

    def get_storage_path_relative(self, note_id: str) -> str:
        """获取相对存储路径（用于数据库）"""
        return f"notes/{note_id}"

    def get_storage_path_absolute(self, note_id: str) -> Path:
        """获取绝对存储路径"""
        return self.notes_dir / note_id

    # ========== 清理方法 ==========

    def cleanup_orphaned_images(self, note_id: str, existing_image_names: list[str]) -> bool:
        """
        清理孤立的图片（存在于文件系统但不在 Note 内容中引用的图片）

        Args:
            note_id: 笔记 ID
            existing_image_names: 笔记中引用的图片文件名列表

        Returns:
            是否成功
        """
        try:
            images_dir = self.get_note_images_dir(note_id)

            if not images_dir.exists():
                return True

            # 遍历文件夹中的所有图片
            for image_file in images_dir.iterdir():
                if image_file.is_file() and image_file.name not in existing_image_names:
                    image_file.unlink()
                    print(f"[STORAGE] Cleaned orphaned image: {image_file.name}")

            return True
        except Exception as e:
            print(f"[ERROR] Failed to cleanup orphaned images for {note_id}: {e}")
            return False

    def exists(self, note_id: str) -> bool:
        """检查笔记存储是否存在"""
        return (self.notes_dir / note_id).exists()

    def list_note_ids(self) -> list[str]:
        """列出所有存储的笔记 ID"""
        if not self.notes_dir.exists():
            return []
        return [d.name for d in self.notes_dir.iterdir() if d.is_dir()]

