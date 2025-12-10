#!/usr/bin/env python3
"""
验证后端配置和数据库连接
"""

import sys
import os

# Add backend to path
sys.path.insert(0, str(os.path.join(os.path.dirname(__file__), 'api')))
sys.path.insert(0, str(os.path.join(os.path.dirname(__file__), 'api/app')))

print("=" * 70)
print("Backend Configuration Verification")
print("=" * 70)

# Test 1: Load settings
print("\n1️⃣  Loading settings...")
try:
    from api.app.config.setting import get_settings
    settings = get_settings()
    print(f"✅ Settings loaded")
    print(f"   Database URL: {settings.database_url}")
    print(f"   Environment: {settings.environment}")
    print(f"   Debug: {settings.debug}")
except Exception as e:
    print(f"❌ Failed to load settings: {e}")
    sys.exit(1)

# Test 2: Check database configuration
print("\n2️⃣  Checking database configuration...")
try:
    from api.app.config.database import _create_async_engine
    print(f"✅ Database module loaded")
except Exception as e:
    print(f"❌ Failed to load database module: {e}")
    sys.exit(1)

# Test 3: Test psycopg connection
print("\n3️⃣  Testing psycopg connection...")
try:
    import psycopg

    def _psycopg_conn_string(sqlalchemy_url: str) -> str:
        """Convert SQLAlchemy-style driver URLs into psycopg-compatible DSNs."""
        if "+psycopg" in sqlalchemy_url:
            return sqlalchemy_url.replace("+psycopg", "", 1)
        return sqlalchemy_url

    psycopg_url = _psycopg_conn_string(settings.database_url)
    conn = psycopg.connect(psycopg_url, connect_timeout=5)
    with conn.cursor() as cur:
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        print(f"✅ psycopg connected successfully")
        print(f"   PostgreSQL: {version.split(',')[0]}")
    conn.close()
except Exception as e:
    print(f"❌ psycopg connection failed: {e}")
    sys.exit(1)

# Test 4: Check async engine creation
print("\n4️⃣  Testing async engine creation...")
try:
    import asyncio
    from api.app.config.database import get_db_engine

    async def test_async_engine():
        engine = await get_db_engine()
        print(f"✅ Async engine created successfully")
        print(f"   Engine: {engine}")
        await engine.dispose()

    asyncio.run(test_async_engine())
except Exception as e:
    print(f"❌ Async engine creation failed: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ ALL VERIFICATION TESTS PASSED!")
print("=" * 70)
print("\n后端已成功配置为使用WSL2 PostgreSQL")
print(f"数据库: {settings.database_url}")
