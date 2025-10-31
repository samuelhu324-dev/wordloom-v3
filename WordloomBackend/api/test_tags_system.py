#!/usr/bin/env python3
"""
验证后端标签系统是否正常工作
"""

import sys
sys.path.insert(0, '.')

from app.database_orbit import SessionOrbit, engine_orbit
from app.models.orbit.notes import OrbitNote
from app.models.orbit.tags import OrbitTag, OrbitNoteTag
from sqlalchemy import select, text

print("[*] Testing backend tag system...")

# 创建会话
db = SessionOrbit()

try:
    # 1. 检查表是否存在
    print("\n[1] Checking tables...")
    with engine_orbit.connect() as conn:
        # 检查 orbit_tags 表
        result = conn.execute(text("SELECT COUNT(*) FROM orbit_tags"))
        tag_count = result.scalar()
        print(f"    - orbit_tags: {tag_count} tags found")

        # 检查 orbit_note_tags 表
        result = conn.execute(text("SELECT COUNT(*) FROM orbit_note_tags"))
        assoc_count = result.scalar()
        print(f"    - orbit_note_tags: {assoc_count} associations found")

        # 检查 orbit_notes 表
        result = conn.execute(text("SELECT COUNT(*) FROM orbit_notes"))
        note_count = result.scalar()
        print(f"    - orbit_notes: {note_count} notes found")

    # 2. 测试查询（带 joinedload）
    print("\n[2] Testing queries with joinedload...")
    stmt = select(OrbitNote).limit(1)
    notes = db.execute(stmt).scalars().all()
    if notes:
        print(f"    - Found {len(notes)} note(s)")
        note = notes[0]
        print(f"    - Note ID: {note.id}")
        print(f"    - Note title: {note.title}")
        print(f"    - Note tags (old): {note.tags}")

        # 手动加载标签
        from sqlalchemy.orm import joinedload
        stmt = select(OrbitNote).where(OrbitNote.id == note.id).options(joinedload(OrbitNote.tags_rel))
        result = db.execute(stmt).unique().scalars().first()
        if result:
            print(f"    - Note tags_rel: {[t.name for t in result.tags_rel]}")
    else:
        print("    - No notes found")

    # 3. 测试 Tag 模型
    print("\n[3] Testing Tag models...")
    stmt = select(OrbitTag).limit(3)
    tags = db.execute(stmt).scalars().all()
    print(f"    - Found {len(tags)} tag(s)")
    for tag in tags:
        print(f"      * {tag.name}: color={tag.color}, count={tag.count}")

    print("\n[SUCCESS] All tests passed!")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
