"""
文件操作服务：处理文件复制、移动、删除等操作
"""
from __future__ import annotations
import shutil
from pathlib import Path
from typing import Optional


class FileService:
    """文件操作服务"""

    @staticmethod
    def copy_directory(src: str | Path, dest: str | Path) -> bool:
        """
        递归复制整个目录

        Args:
            src: 源目录路径
            dest: 目标目录路径

        Returns:
            复制是否成功
        """
        src_path = Path(src)
        dest_path = Path(dest)

        try:
            if not src_path.exists():
                return False

            if dest_path.exists():
                shutil.rmtree(dest_path)

            shutil.copytree(src_path, dest_path)
            return True
        except Exception as e:
            print(f"复制文件夹失败 {src} -> {dest}: {e}")
            return False

    @staticmethod
    def copy_file(src: str | Path, dest: str | Path) -> bool:
        """
        复制单个文件

        Args:
            src: 源文件路径
            dest: 目标文件路径

        Returns:
            复制是否成功
        """
        try:
            src_path = Path(src)
            dest_path = Path(dest)

            if not src_path.exists():
                return False

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest_path)
            return True
        except Exception as e:
            print(f"复制文件失败 {src} -> {dest}: {e}")
            return False

    @staticmethod
    def delete_directory(path: str | Path) -> bool:
        """
        删除整个目录

        Args:
            path: 目录路径

        Returns:
            删除是否成功
        """
        try:
            path_obj = Path(path)
            if path_obj.exists():
                shutil.rmtree(path_obj)
            return True
        except Exception as e:
            print(f"删除文件夹失败 {path}: {e}")
            return False

    @staticmethod
    def path_exists(path: str | Path) -> bool:
        """检查路径是否存在"""
        return Path(path).exists()

    @staticmethod
    def ensure_directory(path: str | Path) -> Path:
        """确保目录存在，如果不存在则创建"""
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj
