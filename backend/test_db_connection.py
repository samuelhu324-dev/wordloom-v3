#!/usr/bin/env python3
"""测试数据库连接和表查询"""

import asyncio
from sqlalchemy import text
from infra.database.session import get_engine

async def test_db_connection():
    """测试数据库连接和查询"""
    engine = await get_engine()

    try:
        async with engine.begin() as conn:
            # 测试libraries表
            result = await conn.execute(text('SELECT count(*) FROM libraries'))
            lib_count = result.scalar()
            print(f"✅ Libraries table count: {lib_count}")

            # 测试所有表
            result = await conn.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema='public' AND table_type='BASE TABLE'
                ORDER BY table_name
            """))
            tables = result.fetchall()
            print(f"\n✅ Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")

        print("\n✅ Database connection successful!")
        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()

if __name__ == "__main__":
    success = asyncio.run(test_db_connection())
    exit(0 if success else 1)
