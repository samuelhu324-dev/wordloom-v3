#!/usr/bin/env python3
"""
诊断后端 API 的具体问题
"""

import sys
import json
sys.path.insert(0, '.')

from app.database_orbit import SessionOrbit
from app.models.orbit.notes import OrbitNote
from app.routers.orbit.notes import NoteOut, TagOutNested
from sqlalchemy import select
from sqlalchemy.orm import joinedload

print("[*] Detailed API diagnostic...")

db = SessionOrbit()

try:
    # 1. 基础查询
    print("\n[1] Basic query (no joinedload)...")
    stmt = select(OrbitNote).limit(1)
    notes = db.execute(stmt).scalars().all()
    if notes:
        note = notes[0]
        print(f"    - Found note: {note.id}")
        print(f"    - Title: {note.title}")
        print(f"    - Tags (array): {note.tags}")

    # 2. 尝试转换为 NoteOut
    print("\n[2] Trying to convert to NoteOut...")
    if notes:
        note = notes[0]
        try:
            note_out = NoteOut.model_validate(note)
            print(f"    - Conversion successful!")
            print(f"    - NoteOut.id: {note_out.id}")
            print(f"    - NoteOut.tags: {note_out.tags}")
            print(f"    - NoteOut.tags_rel: {note_out.tags_rel}")
        except Exception as e:
            print(f"    - [ERROR] Conversion failed: {e}")
            import traceback
            traceback.print_exc()

    # 3. 使用 joinedload 查询
    print("\n[3] Query with joinedload...")
    stmt = select(OrbitNote).options(joinedload(OrbitNote.tags_rel)).limit(1)
    result = db.execute(stmt).unique().scalars().all()
    if result:
        note = result[0]
        print(f"    - Found note: {note.id}")
        print(f"    - tags_rel type: {type(note.tags_rel)}")
        print(f"    - tags_rel: {note.tags_rel}")

        # 尝试转换
        print("\n[4] Converting with tags_rel...")
        try:
            note_out = NoteOut.model_validate(note)
            print(f"    - Conversion successful!")
            # 转换为 JSON
            note_json = note_out.model_dump(mode='json')
            print(f"    - JSON dump successful!")
            print(f"    - JSON: {json.dumps(note_json, indent=2, default=str)}")
        except Exception as e:
            print(f"    - [ERROR] {e}")
            import traceback
            traceback.print_exc()

    print("\n[SUCCESS] Diagnostic complete!")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
