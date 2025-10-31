# app/core/image_manager.py
"""
图片管理模块：
- 为新创建的 note 自动创建对应的图片文件夹
- 追踪 note 中引用的图片
- 在 note 更新或删除时自动清理未被引用的图片
"""
from __future__ import annotations
import os
import re
import shutil
from pathlib import Path
from typing import Set, Optional


class ImageManager:
    """图片生命周期管理器"""

    def __init__(self, upload_dir: str):
        """
        初始化图片管理器

        Args:
            upload_dir: 上传目录路径（如 storage/orbit_uploads）
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def create_note_folder(self, note_id: str) -> Path:
        """
        为新创建的 note 创建对应的图片文件夹

        Args:
            note_id: note 的唯一标识符（UUID）

        Returns:
            创建的文件夹路径
        """
        note_folder = self.upload_dir / note_id
        note_folder.mkdir(parents=True, exist_ok=True)
        return note_folder

    def delete_note_folder(self, note_id: str) -> bool:
        """
        删除 note 对应的整个图片文件夹

        Args:
            note_id: note 的唯一标识符

        Returns:
            是否删除成功
        """
        note_folder = self.upload_dir / note_id
        if note_folder.exists():
            try:
                shutil.rmtree(note_folder)
                return True
            except Exception as e:
                print(f"删除文件夹失败 {note_folder}: {e}")
                return False
        return False

    def extract_referenced_images(self, content_md: Optional[str]) -> Set[str]:
        """
        从 markdown 内容中提取所有被引用的图片文件名

        支持以下格式：
        - ![alt](url) - markdown 图片格式
        - ![](url) - 无描述的图片
        - <img src="url" ...> - HTML img 标签

        Args:
            content_md: markdown 格式的内容

        Returns:
            被引用的图片文件名集合（仅文件名，不包含路径）
        """
        if not content_md:
            return set()

        referenced_images = set()

        # 正则表达式匹配 markdown 图片格式: ![...](url)
        # 匹配 ![optional_alt_text](url) 中的 url 部分
        md_img_pattern = r'!\[.*?\]\(([^)]+)\)'
        for match in re.finditer(md_img_pattern, content_md):
            url = match.group(1).strip()
            filename = self._extract_filename_from_url(url)
            if filename:
                referenced_images.add(filename)

        # 正则表达式匹配 HTML img 标签
        # 匹配 <img ...src="url" ...> 或 <img ...src='url' ...> 或 <img ...src=url ...>
        html_img_pattern = r'<img\s+(?:[^>]*?\s+)?src=["\']?([^"\'>\s]+)["\']?'
        for match in re.finditer(html_img_pattern, content_md, re.IGNORECASE):
            url = match.group(1).strip()
            filename = self._extract_filename_from_url(url)
            if filename:
                referenced_images.add(filename)

        return referenced_images

    def _extract_filename_from_url(self, url: str) -> Optional[str]:
        """
        从 URL 中提取文件名

        支持以下格式：
        - /uploads/note_id/filename.png
        - uploads/note_id/filename.png
        - filename.png

        Args:
            url: URL 字符串

        Returns:
            文件名（带扩展名），或 None 如果无法解析
        """
        url = url.strip()

        # 移除 URL 协议和域名（如有）
        if "://" in url:
            url = url.split("://", 1)[1]
            if "/" in url:
                url = url.split("/", 1)[1]

        # 提取路径的最后部分（文件名）
        if "/" in url:
            parts = url.split("/")
            # 处理 /uploads/{note_id}/{filename} 格式
            if len(parts) >= 2:
                filename = parts[-1]
            else:
                filename = url
        else:
            filename = url

        # 移除查询参数
        if "?" in filename:
            filename = filename.split("?")[0]

        # 验证文件名有效性（必须有扩展名）
        if filename and "." in filename:
            return filename

        return None

    def get_unused_images(self, note_id: str, content_md: Optional[str]) -> Set[str]:
        """
        获取未被引用的图片文件列表

        Args:
            note_id: note 的唯一标识符
            content_md: markdown 格式的内容

        Returns:
            未被引用的文件名集合
        """
        note_folder = self.upload_dir / note_id

        # 如果文件夹不存在，返回空集
        if not note_folder.exists():
            return set()

        # 获取文件夹中的所有文件
        existing_files = set()
        try:
            for file_path in note_folder.iterdir():
                if file_path.is_file():
                    existing_files.add(file_path.name)
        except Exception as e:
            print(f"读取文件夹失败 {note_folder}: {e}")
            return set()

        # 获取被引用的图片
        referenced_images = self.extract_referenced_images(content_md)

        # 返回未被引用的图片
        return existing_files - referenced_images

    def cleanup_unused_images(self, note_id: str, content_md: Optional[str]) -> list[str]:
        """
        删除未被引用的图片

        Args:
            note_id: note 的唯一标识符
            content_md: markdown 格式的内容

        Returns:
            被删除的文件名列表
        """
        unused_images = self.get_unused_images(note_id, content_md)

        if not unused_images:
            return []

        note_folder = self.upload_dir / note_id
        deleted_files = []

        for filename in unused_images:
            try:
                file_path = note_folder / filename
                if file_path.exists() and file_path.is_file():
                    file_path.unlink()
                    deleted_files.append(filename)
            except Exception as e:
                print(f"删除文件失败 {note_folder / filename}: {e}")

        return deleted_files
