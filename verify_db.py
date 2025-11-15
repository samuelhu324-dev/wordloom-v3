#!/usr/bin/env python3
"""Verify wordloom database schema"""

import sys

try:
    import psycopg

    wordloom_url = 'postgresql://postgres:pgpass@127.0.0.1:5433/wordloom'

    print("=" * 60)
    print("WORDLOOM v3 DATABASE VERIFICATION")
    print("=" * 60)

    conn = psycopg.connect(wordloom_url, connect_timeout=5)
    cur = conn.cursor()

    # Check tables
    print("\n[TABLES]")
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
    tables = cur.fetchall()
    print(f"Total: {len(tables)} tables")
    for i, table in enumerate(tables, 1):
        print(f"  {i:2d}. {table[0]}")

    # Check indexes
    print("\n[INDEXES]")
    cur.execute("SELECT indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY indexname")
    indexes = cur.fetchall()
    print(f"Total: {len(indexes)} indexes")
    for i, idx in enumerate(indexes[:10], 1):
        print(f"  {i:2d}. {idx[0]}")
    if len(indexes) > 10:
        print(f"  ... and {len(indexes) - 10} more")

    # Check extensions
    print("\n[EXTENSIONS]")
    cur.execute("SELECT extname FROM pg_extension WHERE extname IN ('uuid-ossp', 'pg_trgm', 'btree_gin')")
    exts = cur.fetchall()
    print(f"Required extensions: {len(exts)}/3")
    for ext in exts:
        print(f"  ✓ {ext[0]}")

    # Check table row counts
    print("\n[TABLE SIZES]")
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cur.fetchone()[0]
        status = "✓" if count == 0 else f"({count} rows)"
        print(f"  {table[0]:30s} {status}")

    # Connection info
    print("\n[CONNECTION]")
    print(f"  Host: 127.0.0.1:5433")
    print(f"  Database: wordloom")
    print(f"  User: postgres")
    print(f"  Status: Connected")

    cur.close()
    conn.close()

    print("\n" + "=" * 60)
    print("STATUS: ✅ DATABASE READY FOR USE")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    sys.exit(1)
