"""
Bookshelf 业务逻辑服务：处理 Bookshelf 相关的业务操作
包括 CRUD、Note 转移、数据一致性保障等
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from app.models.orbit.bookshelves import OrbitBookshelf
from app.models.orbit.notes import OrbitNote


class BookshelfService:
    """Bookshelf 业务服务"""

    @staticmethod
    def create_bookshelf(
        name: str,
        description: Optional[str] = None,
        cover_url: Optional[str] = None,
        icon: Optional[str] = None,
        priority: int = 3,
        urgency: int = 3,
        tags: Optional[List[str]] = None,
        color: Optional[str] = None,
        db: Session = None,
    ) -> OrbitBookshelf:
        """
        创建新 Bookshelf

        Args:
            name: 书橱名称
            description: 描述
            cover_url: 封面图 URL
            icon: 图标名称
            priority: 优先级 (1-5)
            urgency: 紧急度 (1-5)
            tags: 标签列表
            color: 主题色
            db: 数据库会话

        Returns:
            新创建的 Bookshelf 对象
        """
        if not name or name.strip() == "":
            raise ValueError("Bookshelf name cannot be empty")

        bs = OrbitBookshelf(
            name=name.strip(),
            description=description or "",
            cover_url=cover_url,
            icon=icon,
            priority=priority,
            urgency=urgency,
            tags=tags or [],
            color=color,
            status="active",
            note_count=0,
            usage_count=0,
        )
        db.add(bs)
        db.commit()
        db.refresh(bs)
        return bs

    @staticmethod
    def get_bookshelf(bookshelf_id: str, db: Session = None) -> Optional[OrbitBookshelf]:
        """根据 ID 获取 Bookshelf"""
        return db.query(OrbitBookshelf).filter_by(id=bookshelf_id).first()

    @staticmethod
    def list_bookshelves(
        status: str = "active",
        sort_by: str = "-created_at",
        limit: int = 100,
        offset: int = 0,
        db: Session = None,
    ) -> List[OrbitBookshelf]:
        """
        列出 Bookshelf

        Args:
            status: 状态过滤 (active | archived | deleted | all)
            sort_by: 排序字段 (created_at, -created_at, updated_at, -updated_at, name, priority, urgency, note_count, usage_count)
            limit: 查询限制
            offset: 查询偏移
            db: 数据库会话

        Returns:
            Bookshelf 列表
        """
        query = db.query(OrbitBookshelf)

        # 状态过滤
        if status != "all":
            query = query.filter_by(status=status)

        # 排序
        sort_map = {
            "created_at": lambda m: m.created_at,
            "-created_at": lambda m: m.created_at.desc() if m.created_at else None,
            "updated_at": lambda m: m.updated_at,
            "-updated_at": lambda m: m.updated_at.desc() if m.updated_at else None,
            "name": lambda m: m.name,
            "priority": lambda m: m.priority,
            "urgency": lambda m: m.urgency,
            "note_count": lambda m: m.note_count,
            "usage_count": lambda m: m.usage_count,
        }

        if sort_by in sort_map:
            sort_fn = sort_map[sort_by]
            if "-" in sort_by:
                from sqlalchemy import desc
                if sort_by == "-created_at":
                    query = query.order_by(desc(OrbitBookshelf.created_at))
                elif sort_by == "-updated_at":
                    query = query.order_by(desc(OrbitBookshelf.updated_at))
            else:
                if sort_by == "created_at":
                    query = query.order_by(OrbitBookshelf.created_at)
                elif sort_by == "updated_at":
                    query = query.order_by(OrbitBookshelf.updated_at)
                elif sort_by == "name":
                    query = query.order_by(OrbitBookshelf.name)
                elif sort_by == "priority":
                    query = query.order_by(OrbitBookshelf.priority)
                elif sort_by == "urgency":
                    query = query.order_by(OrbitBookshelf.urgency)
                elif sort_by == "note_count":
                    query = query.order_by(OrbitBookshelf.note_count)
                elif sort_by == "usage_count":
                    query = query.order_by(OrbitBookshelf.usage_count)

        return query.limit(limit).offset(offset).all()

    @staticmethod
    def update_bookshelf(
        bookshelf_id: str,
        **kwargs
    ) -> OrbitBookshelf:
        """
        更新 Bookshelf

        更新字段：name, description, cover_url, icon, priority, urgency, tags, color, is_favorite
        """
        from app.database_orbit import get_orbit_db
        db = next(get_orbit_db())

        bs = db.get(OrbitBookshelf, bookshelf_id)
        if not bs:
            raise ValueError(f"Bookshelf not found: {bookshelf_id}")

        allowed_fields = {"name", "description", "cover_url", "icon", "priority", "urgency", "tags", "color", "is_favorite"}
        for field in kwargs:
            if field in allowed_fields:
                setattr(bs, field, kwargs[field])

        bs.updated_at = datetime.utcnow()
        db.add(bs)
        db.commit()
        db.refresh(bs)
        return bs

    @staticmethod
    def delete_bookshelf(
        bookshelf_id: str,
        cascade: str = "orphan",  # "orphan" 或 "delete"
        db: Session = None,
    ) -> bool:
        """
        删除 Bookshelf

        Args:
            bookshelf_id: Bookshelf ID
            cascade: "orphan" - Notes 变为自由, "delete" - 级联删除所有 Notes
            db: 数据库会话

        Returns:
            删除是否成功
        """
        bs = db.get(OrbitBookshelf, bookshelf_id)
        if not bs:
            return False

        if cascade == "delete":
            # 级联删除
            db.query(OrbitNote).filter_by(bookshelf_id=bookshelf_id).delete()
        else:
            # 孤立（推荐）
            db.query(OrbitNote).filter_by(bookshelf_id=bookshelf_id).update(
                {OrbitNote.bookshelf_id: None}
            )

        db.delete(bs)
        db.commit()
        return True

    @staticmethod
    def add_note_to_bookshelf(
        bookshelf_id: str,
        note_id: str,
        db: Session = None,
    ) -> OrbitNote:
        """
        将 Note 添加到 Bookshelf

        如果 Note 已在其他 Bookshelf，先移除旧关联

        Args:
            bookshelf_id: 目标 Bookshelf ID
            note_id: Note ID
            db: 数据库会话

        Returns:
            更新后的 Note
        """
        note = db.get(OrbitNote, note_id)
        bookshelf = db.get(OrbitBookshelf, bookshelf_id)

        if not note:
            raise ValueError(f"Note not found: {note_id}")
        if not bookshelf:
            raise ValueError(f"Bookshelf not found: {bookshelf_id}")

        # 如果 Note 已在其他 Bookshelf，先移除
        if note.bookshelf_id and note.bookshelf_id != bookshelf_id:
            old_bs = db.get(OrbitBookshelf, note.bookshelf_id)
            if old_bs:
                old_bs.note_count = max(0, old_bs.note_count - 1)
                db.add(old_bs)

        # 如果还未在任何 Bookshelf，增加计数
        if not note.bookshelf_id:
            bookshelf.note_count += 1

        note.bookshelf_id = bookshelf_id
        db.add(note)
        db.add(bookshelf)
        db.commit()
        db.refresh(note)
        return note

    @staticmethod
    def remove_note_from_bookshelf(
        note_id: str,
        db: Session = None,
    ) -> OrbitNote:
        """
        从 Bookshelf 中移除 Note（使其成为自由 Note）

        Args:
            note_id: Note ID
            db: 数据库会话

        Returns:
            更新后的 Note
        """
        note = db.get(OrbitNote, note_id)
        if not note:
            raise ValueError(f"Note not found: {note_id}")

        if note.bookshelf_id:
            bs = db.get(OrbitBookshelf, note.bookshelf_id)
            if bs:
                bs.note_count = max(0, bs.note_count - 1)
                db.add(bs)

            note.bookshelf_id = None
            db.add(note)
            db.commit()

        db.refresh(note)
        return note

    @staticmethod
    def move_note_to_bookshelf(
        note_id: str,
        target_bookshelf_id: str,
        db: Session = None,
    ) -> OrbitNote:
        """
        将 Note 从一个 Bookshelf 转移到另一个

        Args:
            note_id: Note ID
            target_bookshelf_id: 目标 Bookshelf ID
            db: 数据库会话

        Returns:
            更新后的 Note
        """
        note = db.get(OrbitNote, note_id)
        target_bs = db.get(OrbitBookshelf, target_bookshelf_id)

        if not note:
            raise ValueError(f"Note not found: {note_id}")
        if not target_bs:
            raise ValueError(f"Target Bookshelf not found: {target_bookshelf_id}")

        # 如果转移到同一个 Bookshelf，无操作
        if note.bookshelf_id == target_bookshelf_id:
            return note

        # 从原 Bookshelf 移除
        if note.bookshelf_id:
            old_bs = db.get(OrbitBookshelf, note.bookshelf_id)
            if old_bs:
                old_bs.note_count = max(0, old_bs.note_count - 1)
                db.add(old_bs)

        # 加入新 Bookshelf
        note.bookshelf_id = target_bookshelf_id
        target_bs.note_count += 1

        db.add(note)
        db.add(target_bs)
        db.commit()
        db.refresh(note)
        return note

    @staticmethod
    def get_bookshelf_notes(
        bookshelf_id: str,
        sort_by: str = "-updated_at",
        limit: int = 100,
        offset: int = 0,
        db: Session = None,
    ) -> List[OrbitNote]:
        """
        获取 Bookshelf 内的所有 Notes

        Args:
            bookshelf_id: Bookshelf ID
            sort_by: 排序字段
            limit: 查询限制
            offset: 查询偏移
            db: 数据库会话

        Returns:
            Notes 列表
        """
        query = db.query(OrbitNote).filter_by(bookshelf_id=bookshelf_id)

        # 排序（同 notes.py 中的实现）
        if sort_by == "created_at":
            query = query.order_by(OrbitNote.created_at)
        elif sort_by == "-created_at":
            from sqlalchemy import desc
            query = query.order_by(desc(OrbitNote.created_at))
        elif sort_by == "updated_at":
            query = query.order_by(OrbitNote.updated_at)
        elif sort_by == "-updated_at":
            from sqlalchemy import desc
            query = query.order_by(desc(OrbitNote.updated_at))
        elif sort_by == "priority":
            from sqlalchemy import desc
            query = query.order_by(desc(OrbitNote.priority))
        elif sort_by == "usage_count":
            from sqlalchemy import desc
            query = query.order_by(desc(OrbitNote.usage_count))

        return query.limit(limit).offset(offset).all()

    @staticmethod
    def audit_bookshelf_counts(db: Session = None) -> dict:
        """
        审计并修复 Bookshelf 的 note_count 一致性

        定期运行此函数以确保数据一致性

        Returns:
            修复统计信息
        """
        from app.database_orbit import get_orbit_db
        if db is None:
            db = next(get_orbit_db())

        fixed_count = 0
        total_count = 0

        for bs in db.query(OrbitBookshelf).all():
            total_count += 1
            actual_count = db.query(OrbitNote).filter_by(bookshelf_id=bs.id).count()

            if bs.note_count != actual_count:
                print(f"[Audit] Bookshelf {bs.id} ({bs.name}): {bs.note_count} -> {actual_count}")
                bs.note_count = actual_count
                db.add(bs)
                fixed_count += 1

        db.commit()
        return {
            "total_bookshelves": total_count,
            "fixed_bookshelves": fixed_count,
        }

    @staticmethod
    def increment_usage_count(
        bookshelf_id: str,
        db: Session = None,
    ) -> OrbitBookshelf:
        """
        增加 Bookshelf 的使用次数

        Args:
            bookshelf_id: Bookshelf ID
            db: 数据库会话

        Returns:
            更新后的 Bookshelf
        """
        bs = db.get(OrbitBookshelf, bookshelf_id)
        if not bs:
            raise ValueError(f"Bookshelf not found: {bookshelf_id}")

        bs.usage_count = (bs.usage_count or 0) + 1
        db.add(bs)
        db.commit()
        db.refresh(bs)
        return bs
