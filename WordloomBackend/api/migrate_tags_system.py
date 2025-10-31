#!/usr/bin/env python3
"""
Wordloom Orbit Tags System Migration Script
执行数据库迁移以创建新的标签系统
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

def run_migration():
    # 获取数据库 URL
    db_url = os.getenv("ORBIT_DB_URL") or "postgresql+psycopg2://postgres:pgpass@127.0.0.1:5433/wordloomorbit"

    # 创建引擎
    engine = create_engine(db_url, echo=True)

    # 读取迁移 SQL 文件
    migration_file = Path(__file__).parent / "migrations" / "001_create_tags_system.sql"

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)

    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_script = f.read()

    print(f"📂 Reading migration from: {migration_file}")
    print(f"📊 Connecting to database: {db_url}")

    try:
        with engine.begin() as conn:
            # 分割 SQL 脚本，执行每个语句
            # 过滤掉注释和空行
            statements = []
            current_stmt = []

            for line in sql_script.split('\n'):
                # 移除注释
                if '--' in line:
                    line = line[:line.index('--')]

                line = line.strip()
                if line:
                    current_stmt.append(line)
                    if line.endswith(';'):
                        statements.append(' '.join(current_stmt))
                        current_stmt = []

            # 执行所有 SQL 语句
            for i, stmt in enumerate(statements, 1):
                if stmt.strip():
                    print(f"\n[{i}/{len(statements)}] Executing: {stmt[:80]}...")
                    conn.execute(text(stmt))

            print(f"\n✅ Successfully executed {len(statements)} migration statements!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

    print("\n🎉 Tags system migration completed successfully!")
    print("📋 The following tables were created/updated:")
    print("   - orbit_tags: 存储标签信息（名称、颜色、描述、计数）")
    print("   - orbit_note_tags: 多对多关联表（note 与 tag 的关系）")
    print("   - Indexes created for performance optimization")
    print("\n✨ Your data has been migrated from orbit_notes.tags array to the new structure.")

if __name__ == "__main__":
    run_migration()
