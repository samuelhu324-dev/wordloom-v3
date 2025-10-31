#!/usr/bin/env python3
"""
测试完整的 API 流程
"""

import sys
import json
sys.path.insert(0, '.')

from app.routers.orbit.notes import NoteOut, list_notes as list_notes_func
from app.database_orbit import SessionOrbit

print("[*] Testing complete API flow...")

try:
    # 首先创建应用
    from app.main_orbit import app

    print("\n[1] Direct function call...")
    db = SessionOrbit()
    try:
        # 直接调用 list_notes 函数
        # 模拟依赖注入
        notes = list_notes_func(
            q=None,
            tag=None,
            status=None,
            sort="-updated_at",
            limit=10,
            offset=0,
            db=db
        )

        print(f"    - Got {len(notes)} notes")
        if notes:
            note = notes[0]
            print(f"    - First note: {note.id}")

            # 尝试转换为 NoteOut
            note_out = NoteOut.model_validate(note)
            print(f"    - Converted to NoteOut: OK")

            # JSON 序列化
            json_data = json.dumps(note_out.model_dump(mode='json'), default=str, ensure_ascii=False)
            print(f"    - JSON serialization: OK")
            print(f"    - Response length: {len(json_data)} bytes")

    finally:
        db.close()

    print("\n[SUCCESS] Complete flow works!")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
