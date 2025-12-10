#!/usr/bin/env python3
"""
Test different WSL2 PostgreSQL connection methods
"""

import sys
import os
import psycopg

print("=" * 70)
print("WSL2 PostgreSQL Connection Tests - Multiple Methods")
print("=" * 70)

# Test different connection strings
test_cases = [
    {
        "name": "With password (pgpass)",
        "conn_str": "postgresql://postgres:pgpass@localhost:5432/wordloom"
    },
    {
        "name": "Without password",
        "conn_str": "postgresql://postgres@localhost:5432/wordloom"
    },
    {
        "name": "With empty password",
        "conn_str": "postgresql://postgres:@localhost:5432/wordloom"
    },
    {
        "name": "Using 127.0.0.1",
        "conn_str": "postgresql://postgres:pgpass@127.0.0.1:5432/wordloom"
    },
]

for i, test in enumerate(test_cases, 1):
    print(f"\n{i}️⃣  {test['name']}")
    print(f"   Connection: {test['conn_str'][:50]}...")
    try:
        conn = psycopg.connect(test["conn_str"], connect_timeout=3)
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
            print(f"   ✅ SUCCESS! PostgreSQL: {version.split(',')[0]}")
        conn.close()
        sys.exit(0)  # Success!
    except Exception as e:
        error_msg = str(e)
        # Only show first 60 chars of error
        if len(error_msg) > 60:
            error_msg = error_msg[:60] + "..."
        print(f"   ❌ Failed: {error_msg}")

print("\n" + "=" * 70)
print("❌ All connection attempts failed")
print("\n💡 Next steps:")
print("1. Check pg_hba.conf in WSL2 PostgreSQL")
print("2. Verify postgres user password in WSL2")
print("3. Or set connection without authentication")
print("=" * 70)
sys.exit(1)
