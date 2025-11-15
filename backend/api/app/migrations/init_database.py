#!/usr/bin/env python3
"""
Wordloom Database Initialization Script
数据库初始化工具 - 创建表、验证、插入演示数据
"""

import os
import sys
from pathlib import Path
import psycopg
from psycopg import sql

# 配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:pgpass@127.0.0.1:5433/wordloom")

def init_database():
    """初始化数据库（执行 schema.sql）"""
    print("🔄 初始化数据库..." )

    schema_path = Path(__file__).parent / "migrations" / "001_create_core_schema.sql"

    if not schema_path.exists():
        print(f"❌ Schema 文件不存在: {schema_path}")
        return False

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                    cur.execute(schema_sql)
                conn.commit()
        print("✅ 数据库初始化完成")
        return True
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False

def verify_schema():
    """验证表结构"""
    print("\n🔍 验证表结构...")

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # 查询所有表
                cur.execute("""
                    SELECT tablename FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                """)
                tables = cur.fetchall()

                if not tables:
                    print("⚠️  没有找到表")
                    return False

                print(f"✅ 找到 {len(tables)} 张表:")
                for (table,) in tables:
                    print(f"   • {table}")

                # 验证关键约束
                cur.execute("""
                    SELECT constraint_name, table_name
                    FROM information_schema.table_constraints
                    WHERE constraint_type = 'UNIQUE' AND table_name IN (
                        'libraries', 'bookshelves', 'books', 'tags'
                    )
                    ORDER BY table_name
                """)
                constraints = cur.fetchall()
                print(f"\n✅ 找到 {len(constraints)} 个 UNIQUE 约束")

                # 验证索引
                cur.execute("""
                    SELECT indexname FROM pg_indexes
                    WHERE schemaname = 'public'
                    ORDER BY indexname
                """)
                indexes = cur.fetchall()
                print(f"✅ 找到 {len(indexes)} 个索引")

                return True
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def seed_demo_data():
    """插入演示数据"""
    print("\n🌱 插入演示数据...")

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # 插入库
                cur.execute("""
                    INSERT INTO libraries (user_id, name, description)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (1, "My First Library", "Demo library for testing Wordloom v3"))
                library_id = cur.fetchone()[0]
                print(f"   ✅ 创建库: {library_id}")

                # 查询自动创建的 Basement
                cur.execute("""
                    SELECT id FROM bookshelves
                    WHERE library_id = %s AND is_basement = TRUE
                """, (library_id,))
                basement_id = cur.fetchone()[0]
                print(f"   ✅ Basement 自动创建: {basement_id}")

                # 创建书架
                cur.execute("""
                    INSERT INTO bookshelves (library_id, name, color)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (library_id, "Reading List", "#3B82F6"))
                shelf_id = cur.fetchone()[0]
                print(f"   ✅ 创建书架: {shelf_id}")

                # 创建书
                book_ids = []
                for i in range(3):
                    cur.execute("""
                        INSERT INTO books (library_id, bookshelf_id, title, author, status)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (library_id, shelf_id, f"Sample Book {i+1}", "Demo Author", "ACTIVE"))
                    book_id = cur.fetchone()[0]
                    book_ids.append(book_id)
                print(f"   ✅ 创建 {len(book_ids)} 本书")

                # 为第一本书创建块
                if book_ids:
                    for i in range(5):
                        cur.execute("""
                            INSERT INTO blocks (book_id, content, block_type, sort_key)
                            VALUES (%s, %s, %s, %s)
                        """, (book_ids[0], f"This is block {i+1} content", "text", i * 1.0))
                    print(f"   ✅ 为第一本书创建 5 个块")

                # 创建标签
                cur.execute("""
                    INSERT INTO tags (user_id, name, color)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (1, "Important", "#EF4444"))
                tag_id = cur.fetchone()[0]
                print(f"   ✅ 创建标签: {tag_id}")

                conn.commit()
                print("✅ 演示数据插入完成")
                return True
    except Exception as e:
        print(f"❌ 演示数据插入失败: {e}")
        return False

def test_connection():
    """测试数据库连接"""
    print(f"🔗 测试数据库连接: {DATABASE_URL[:50]}...")

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
                print(f"✅ 连接成功: PostgreSQL {version.split(',')[0]}")
                return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def main():
    print("=" * 60)
    print("Wordloom v3 Database Initialization")
    print("=" * 60)

    # Step 1: 测试连接
    if not test_connection():
        sys.exit(1)

    # Step 2: 初始化数据库
    if not init_database():
        sys.exit(1)

    # Step 3: 验证表结构
    if not verify_schema():
        sys.exit(1)

    # Step 4: 插入演示数据
    if not seed_demo_data():
        print("⚠️  演示数据插入失败，但数据库已正确初始化")

    print("\n" + "=" * 60)
    print("✅ 数据库初始化完成！")
    print("=" * 60)
    print("\n下一步:")
    print("1. 启动后端: python -m uvicorn api.app.main:app --port 30001")
    print("2. 启动前端: cd ../frontend && npm run dev")
    print("3. 测试 API: curl http://localhost:30001/api/libraries")

if __name__ == "__main__":
    main()
