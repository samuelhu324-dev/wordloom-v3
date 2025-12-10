#!/usr/bin/env python3
"""
Test WSL2 PostgreSQL Connection from Windows
"""

import sys
import os
import psycopg
import subprocess

print("=" * 70)
print("WSL2 PostgreSQL Connection Test - Windows")
print("=" * 70)

# Get WSL2 IP address
print("\n📍 Getting WSL2 IP address...")
try:
    result = subprocess.run(
        ['wsl', '-e', 'bash', '-c', 'hostname -I | awk \'{print $1}\''],
        capture_output=True,
        text=True,
        timeout=5
    )
    wsl2_ip = result.stdout.strip()
    print(f"✅ WSL2 IP: {wsl2_ip}")
except Exception as e:
    print(f"❌ Failed to get WSL2 IP: {e}")
    sys.exit(1)

# Test connection methods
test_cases = [
    {
        "name": f"Using WSL2 IP ({wsl2_ip}):5432 with password",
        "conn_str": f"postgresql://postgres:pgpass@{wsl2_ip}:5432/wordloom"
    },
    {
        "name": "Using localhost:5432 with password (direct)",
        "conn_str": "postgresql://postgres:pgpass@localhost:5432/wordloom"
    },
]

print("\n" + "=" * 70)
for i, test in enumerate(test_cases, 1):
    print(f"\n{i}️⃣  {test['name']}")
    try:
        conn = psycopg.connect(test["conn_str"], connect_timeout=5)
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
            print(f"   ✅ SUCCESS!")
            print(f"   PostgreSQL: {version.split(',')[0]}")
        conn.close()

        print("\n" + "=" * 70)
        print("✅ CONNECTION SUCCESSFUL!")
        print(f"   Use this connection string in .env:")
        print(f"   DATABASE_URL={test['conn_str']}")
        print("=" * 70)
        sys.exit(0)
    except Exception as e:
        error_msg = str(e)
        if len(error_msg) > 80:
            error_msg = error_msg[:80] + "..."
        print(f"   ❌ Failed: {error_msg}")

print("\n" + "=" * 70)
print("❌ All connection attempts failed")
print("\n💡 Troubleshooting:")
print("1. Verify PostgreSQL is running: wsl service postgresql status")
print("2. Check pg_hba.conf: wsl sudo cat /etc/postgresql/14/main/pg_hba.conf")
print("3. Verify password: wsl sudo -u postgres psql")
print("=" * 70)
sys.exit(1)
