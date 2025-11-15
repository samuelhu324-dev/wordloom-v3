#!/usr/bin/env python3
"""Initialize wordloom schema"""

import os
import sys
from pathlib import Path

try:
    import psycopg

    wordloom_url = 'postgresql://postgres:pgpass@127.0.0.1:5433/wordloom'
    schema_file = Path('backend/api/app/migrations/001_create_core_schema.sql')

    print(f"Step 1: Reading schema from {schema_file}")
    if not schema_file.exists():
        print(f"ERROR: File not found: {schema_file}")
        sys.exit(1)

    with open(schema_file, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    print(f"Read {len(schema_sql)} bytes of SQL")

    print("Step 2: Connecting to wordloom database...")
    conn = psycopg.connect(wordloom_url, connect_timeout=5)
    cur = conn.cursor()

    print("Step 3: Executing schema...")
    cur.execute(schema_sql)
    conn.commit()

    print("Step 4: Verifying tables...")
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
    tables = cur.fetchall()
    print(f"Success! Created {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")

    cur.close()
    conn.close()

    print("\nDatabase schema initialized successfully!")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
