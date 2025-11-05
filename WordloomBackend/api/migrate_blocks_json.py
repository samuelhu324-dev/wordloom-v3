#!/usr/bin/env python
"""
数据库迁移脚本 - 添加 blocks_json 列到 orbit_notes 表
"""
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.database_orbit import engine_orbit

def add_blocks_json_column():
    """添加 blocks_json 列到 orbit_notes 表"""
    with engine_orbit.begin() as conn:
        # 检查列是否已存在
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'orbit_notes' AND column_name = 'blocks_json'
        """))

        if result.fetchone():
            print("✅ blocks_json 列已存在")
            return

        # 添加列
        print("添加 blocks_json 列...")
        conn.execute(text("""
            ALTER TABLE orbit_notes
            ADD COLUMN blocks_json TEXT DEFAULT '[]'
        """))
        print("✅ blocks_json 列已添加")

if __name__ == "__main__":
    try:
        add_blocks_json_column()
        print("✅ 数据库迁移完成")
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        sys.exit(1)
