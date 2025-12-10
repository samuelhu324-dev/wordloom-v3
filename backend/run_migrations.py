#!/usr/bin/env python3
"""数据库迁移执行脚本 (改进版)

问题: 旧版本通过分号拆分语句, 导致包含 PL/pgSQL 函数 / DO $$ ... $$ / 触发器定义的文件被错误拆分, 事务中断后后续语句全部 InFailedSqlTransaction。
改进: 每个迁移文件整体执行一次 (exec_driver_sql), 单文件失败不中断其它文件。文件间独立事务; 成功后单独验证表结构。
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote_plus

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

DEFAULT_DB_USER = "postgres"
DEFAULT_DB_PASSWORD = "pgpass"
DEFAULT_DB_NAME = "wordloom"
DEFAULT_DB_HOST = "localhost"
DEFAULT_DB_PORT = 5432


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Wordloom SQL migrations against a PostgreSQL database.")
    parser.add_argument("--database-url", dest="database_url", help="Override DATABASE_URL (e.g. postgresql+psycopg://user:pass@host:port/db)")
    parser.add_argument("--host", help="PostgreSQL host override")
    parser.add_argument("--port", type=int, help="PostgreSQL port override")
    parser.add_argument("--user", help="Database user override")
    parser.add_argument("--password", help="Database password override")
    parser.add_argument("--database", help="Database name override")
    return parser.parse_args(argv)


def configure_database_url(args: argparse.Namespace) -> str | None:
    if args.database_url:
        os.environ["DATABASE_URL"] = args.database_url
        return args.database_url

    has_partial_override = any(
        value is not None
        for value in (args.host, args.port, args.user, args.password, args.database)
    )

    if not has_partial_override:
        return os.environ.get("DATABASE_URL")

    host = args.host or os.getenv("WORDLOOM_DB_HOST") or DEFAULT_DB_HOST
    port = args.port or int(os.getenv("WORDLOOM_DB_PORT", DEFAULT_DB_PORT))
    user = args.user or os.getenv("WORDLOOM_DB_USER") or DEFAULT_DB_USER
    password = args.password or os.getenv("WORDLOOM_DB_PASSWORD") or DEFAULT_DB_PASSWORD
    database = args.database or os.getenv("WORDLOOM_DB_NAME") or DEFAULT_DB_NAME

    safe_password = quote_plus(password)
    url = f"postgresql+psycopg://{user}:{safe_password}@{host}:{port}/{database}"
    os.environ["DATABASE_URL"] = url
    return url

async def run_migrations(get_engine_fn):
    migration_dir = Path(__file__).parent / "api" / "app" / "migrations"
    migration_files = sorted(migration_dir.glob("*.sql"))
    if not migration_files:
        print("❌ 未找到迁移文件！")
        return False

    print(f"📋 找到 {len(migration_files)} 个迁移文件")
    print("-" * 60)

    engine = await get_engine_fn()
    applied = 0
    failed = []

    for mf in migration_files:
        print(f"\n🔄 执行: {mf.name}")
        sql = mf.read_text(encoding="utf-8")
        # 跳过空文件
        if not sql.strip():
            print("  ⚠️  跳过空文件")
            continue
        try:
            async with engine.begin() as conn:
                # 使用底层 exec_driver_sql 保留原始语句 (包含分号, 函数体等)
                await conn.exec_driver_sql(sql)
            print(f"  ✅ {mf.name} 完成")
            applied += 1
        except SQLAlchemyError as e:
            print(f"  ❌ {mf.name} 失败: {e.__class__.__name__}: {e}")
            failed.append(mf.name)

    # 校验表结构
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='public' AND table_type='BASE TABLE'
            ORDER BY table_name
        """))
        tables = [r[0] for r in result.fetchall()]

    print("\n" + "=" * 60)
    print(f"✅ 成功执行 {applied}/{len(migration_files)} 个迁移文件")
    if failed:
        print(f"❌ 失败文件 ({len(failed)}): {', '.join(failed)}")
    print(f"📊 当前表: {len(tables)} → {tables}")
    print("=" * 60)

    await engine.dispose()
    return len(failed) == 0

async def main(argv: Optional[List[str]] = None):
    args = parse_args(argv)
    configure_database_url(args)

    # 延迟导入，确保 DATABASE_URL 已按参数覆盖
    from infra.database.session import get_engine  # pylint: disable=import-error,import-outside-toplevel

    ok = await run_migrations(get_engine)
    exit(0 if ok else 1)

if __name__ == "__main__":
    # Windows psycopg async requires SelectorEventLoop
    if sys.platform.startswith("win"):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass
    asyncio.run(main())
