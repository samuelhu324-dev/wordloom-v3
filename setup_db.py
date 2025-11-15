#!/usr/bin/env python3
"""Test database connection and create wordloom database"""

import os
import sys

# Set connection string
os.environ['DATABASE_URL'] = 'postgresql://postgres:pgpass@127.0.0.1:5433/wordloom'

try:
    import psycopg
    print("Step 1: Checking psycopg...")

    # Connect to postgres (admin) database
    admin_url = 'postgresql://postgres:pgpass@127.0.0.1:5433/postgres'
    print(f"Connecting to: {admin_url}")

    conn = psycopg.connect(admin_url, autocommit=True, connect_timeout=5)
    print("Connected!")

    cur = conn.cursor()

    # List existing databases
    print("\nStep 2: Checking existing databases...")
    cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname")
    dbs = cur.fetchall()
    print(f"Found {len(dbs)} databases:")
    for db in dbs:
        print(f"  - {db[0]}")

    # Check if wordloom exists
    print("\nStep 3: Checking wordloom database...")
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'wordloom'")
    exists = cur.fetchone()

    if not exists:
        print("Creating wordloom database...")
        cur.execute("CREATE DATABASE wordloom ENCODING 'UTF8'")
        print("wordloom database created!")
    else:
        print("wordloom database already exists")

    cur.close()
    conn.close()
    print("\nStep 4: Database setup complete!")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
