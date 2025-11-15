#!/usr/bin/env python3
"""
Wordloom Database Initialization Script
创建 wordloom 数据库并执行 schema.sql
"""

import os
import sys
from pathlib import Path

# 尝试导入 psycopg
try:
    import psycopg
except ImportError:
    print("❌ psycopg 包未安装。尝试安装...")
    os.system(f"{sys.executable} -m pip install psycopg -q")
    import psycopg

# 配置
POSTGRES_URL = "postgresql://postgres:pgpass@127.0.0.1:5433/postgres"
WORDLOOM_URL = "postgresql://postgres:pgpass@127.0.0.1:5433/wordloom"
SCHEMA_FILE = Path("backend/api/app/migrations/001_create_core_schema.sql")

def create_database():
    """创建 wordloom 数据库"""
    print("📦 创建 wordloom 数据库...")

    try:
        # 使用 autocommit 模式（必需，因为 CREATE DATABASE 不能在事务中运行）
        conn = psycopg.connect(POSTGRES_URL, autocommit=True)
        cur = conn.cursor()

        # 检查数据库是否存在
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'wordloom'")
        if cur.fetchone():
            print("✅ wordloom 数据库已存在，跳过创建")
            cur.close()
            conn.close()
            return True

        # 创建数据库
        cur.execute("CREATE DATABASE wordloom;")
        print("✅ wordloom 数据库创建成功")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ 数据库创建失败: {e}")
        return False

def init_schema():
    """执行 schema.sql 初始化数据库表"""
    print("📋 初始化数据库表结构...")

    if not SCHEMA_FILE.exists():
        print(f"❌ Schema 文件不存在: {SCHEMA_FILE}")
        return False

    try:
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        conn = psycopg.connect(WORDLOOM_URL)
        cur = conn.cursor()
        cur.execute(schema_sql)
        conn.commit()
        cur.close()
        conn.close()

        print("✅ 数据库表结构初始化成功")
        return True
    except Exception as e:
        print(f"❌ 表结构初始化失败: {e}")
        return False

def verify_tables():
    """验证表是否成功创建"""
    print("🔍 验证表结构...")

    try:
        conn = psycopg.connect(WORDLOOM_URL)
        cur = conn.cursor()

        cur.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        tables = cur.fetchall()
        cur.close()
        conn.close()

        if not tables:
            print("❌ 未找到任何表")
            return False

        print(f"✅ 发现 {len(tables)} 个表:")
        for table in tables:
            print(f"   - {table[0]}")
        return True
    except Exception as e:
        print(f"❌ 表验证失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Wordloom 数据库初始化工具")
    print("=" * 60)

    # 步骤 1: 创建数据库
    if not create_database():
        sys.exit(1)

    # 步骤 2: 初始化表结构
    if not init_schema():
        sys.exit(1)

    # 步骤 3: 验证
    if not verify_tables():
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ 数据库初始化完成！")
    print("=" * 60)
    print(f"连接字符串: {WORDLOOM_URL}")
