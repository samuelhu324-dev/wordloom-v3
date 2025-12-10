#!/usr/bin/env python3
"""
Test WSL2 PostgreSQL Connection
验证从Windows Python能否连接到WSL2的PostgreSQL
"""

import sys
import os

print("=" * 60)
print("WSL2 PostgreSQL Connection Test")
print("=" * 60)

# Test 1: Check psycopg installation
print("\n1️⃣  Checking psycopg installation...")
try:
    import psycopg
    print(f"✅ psycopg version: {psycopg.__version__}")
except ImportError as e:
    print(f"❌ psycopg not installed: {e}")
    print("   Run: pip install psycopg[binary]")
    sys.exit(1)

# Test 2: Try to connect to localhost:5432
print("\n2️⃣  Connecting to PostgreSQL at localhost:5432...")
try:
    conn = psycopg.connect(
        "postgresql://postgres:pgpass@localhost:5432/wordloom",
        connect_timeout=5
    )
    print("✅ Connection successful!")

    # Test 3: Check version
    with conn.cursor() as cur:
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        print(f"   PostgreSQL: {version.split(',')[0]}")

    conn.close()
    print("\n✅ All tests passed! WSL2 PostgreSQL is accessible from Windows.")

except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\n💡 Troubleshooting tips:")
    print("   1. Verify WSL2 PostgreSQL is running:")
    print("      wsl -d [distro] sudo service postgresql status")
    print("   2. Check if WSL2 can access localhost:5432")
    print("   3. Verify credentials: postgres:pgpass")
    sys.exit(1)

print("\n" + "=" * 60)
