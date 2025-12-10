"""
Note 业务逻辑服务：处理 Note 相关的业务操作
包括复制、创建等
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.orbit.notes import OrbitNote
from app.models.orbit.tags import OrbitTag, OrbitNoteTag
from app.services.file_service import FileService
from app.database_orbit import ORBIT_UPLOAD_DIR
from pathlib import Path


class NoteService:
    """Note 业务服务"""

    def __init__(self, upload_dir: str = ORBIT_UPLOAD_DIR):
        """初始化 Note 服务"""
        self.upload_dir = Path(upload_dir)
        self.file_service = FileService()

    def duplicate_note(
        self,
        original_note_id: str,
        db: Session,
        title_suffix: str = "(副本)",
    ) -> OrbitNote:
        """
        完全复制一个 Note，包括数据库记录和文件

        流程：
        1. 查询原 Note
        2. 创建新 Note 记录（新 ID、重置统计数据）
        3. 复制标签关联
        4. 复制上传文件夹
        5. 复制到原 Bookshelf（如果有）
        6. 返回新 Note

        Args:
            original_note_id: 原 Note 的 ID
            db: 数据库会话
            title_suffix: 新标题的后缀（默认 "(副本)"）

        Returns:
            新创建的 Note 对象

        Raises:
            ValueError: 如果原 Note 不存在
            Exception: 文件复制失败等其他异常
        """
        # 1️⃣ 查询原 Note
        original_note = db.query(OrbitNote).filter_by(id=original_note_id).first()
        if not original_note:
            raise ValueError(f"Note not found: {original_note_id}")

        # 2️⃣ 创建新 Note 记录
        import uuid
        new_note_id = str(uuid.uuid4())
        storage_path = f"notes/{new_note_id}"

        new_note = OrbitNote(
            id=new_note_id,
            storage_path=storage_path,  # SET storage_path BEFORE db.add()
            title=f"{original_note.title} {title_suffix}" if original_note.title else None,
            content_md=original_note.content_md or "",
            status=original_note.status or "open",
            priority=original_note.priority or 3,
            urgency=original_note.urgency or 3,
            usage_level=original_note.usage_level or 3,
            usage_count=0,  # 重置使用次数
            tags=original_note.tags or [],  # 保持旧字段向后兼容
            due_at=original_note.due_at,
            bookshelf_id=original_note.bookshelf_id,  # 新 Note 落在原 Bookshelf
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(new_note)
        db.flush()  # 获取生成的新 ID

        # 3️⃣ 复制标签关联
        if original_note.tags_rel:
            for tag in original_note.tags_rel:
                # 创建新的关联
                assoc = OrbitNoteTag(note_id=str(new_note.id), tag_id=tag.id)
                db.add(assoc)

        # 5️⃣ 如果原 Note 属于某个 Bookshelf，增加该 Bookshelf 的 note_count
        if original_note.bookshelf_id:
            from app.models.orbit.bookshelves import OrbitBookshelf
            bs = db.get(OrbitBookshelf, original_note.bookshelf_id)
            if bs:
                bs.note_count += 1
                db.add(bs)

        db.commit()
        db.refresh(new_note, ["tags_rel"])

        # 4️⃣ 复制上传文件夹
        try:
            self._copy_note_uploads(original_note_id, str(new_note.id))
        except Exception as e:
            # 文件复制失败时，回滚数据库并抛出异常
            db.delete(new_note)
            db.query(OrbitNoteTag).filter_by(note_id=str(new_note.id)).delete()
            db.commit()
            raise Exception(f"Failed to copy files: {str(e)}")

        return new_note

    def _copy_note_uploads(self, src_note_id: str, dest_note_id: str) -> bool:
        """
        复制 Note 的上传文件夹 (Fixed-path architecture)

        固定路径架构: storage/{notes/{note_id}/}

        Args:
            src_note_id: 源 Note ID
            dest_note_id: 目标 Note ID

        Returns:
            复制是否成功
        """
        # 使用固定路径: notes/{id}/
        src_folder = self.upload_dir / "notes" / src_note_id
        dest_folder = self.upload_dir / "notes" / dest_note_id

        # 如果源文件夹不存在，直接创建目标空文件夹
        if not src_folder.exists():
            self.file_service.ensure_directory(dest_folder)
            return True

        # 复制文件夹
        success = self.file_service.copy_directory(src_folder, dest_folder)
        if not success:
            raise Exception(f"Failed to copy uploads: {src_folder} -> {dest_folder}")

        return True

    def get_note_by_id(self, note_id: str, db: Session) -> Optional[OrbitNote]:
        """
        根据 ID 获取 Note

        Args:
            note_id: Note ID
            db: 数据库会话

        Returns:
            Note 对象或 None
        """
        return db.query(OrbitNote).filter_by(id=note_id).first()

    def delete_note(self, note_id: str, db: Session) -> bool:
        """
        删除 Note 及其相关数据

        Args:
            note_id: Note ID
            db: 数据库会话

        Returns:
            删除是否成功
        """
        note = db.query(OrbitNote).filter_by(id=note_id).first()
        if not note:
            return False

        # 删除标签关联
        db.query(OrbitNoteTag).filter_by(note_id=note_id).delete()

        # 删除 Note 记录
        db.delete(note)
        db.commit()

        # 删除上传文件夹
        self._delete_note_uploads(note_id)

        return True

    def _delete_note_uploads(self, note_id: str) -> bool:
        """
        删除 Note 的上传文件夹 (Fixed-path architecture)

        固定路径架构: storage/{notes/{note_id}/}

        Args:
            note_id: Note ID

        Returns:
            删除是否成功
        """
        # 使用固定路径: notes/{id}/
        folder = self.upload_dir / "notes" / note_id
        return self.file_service.delete_directory(folder)
