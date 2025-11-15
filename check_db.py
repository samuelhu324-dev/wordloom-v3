import psycopg

POSTGRES_URL = "postgresql://postgres:pgpass@127.0.0.1:5433/postgres"

try:
    conn = psycopg.connect(POSTGRES_URL, autocommit=True)
    cur = conn.cursor()

    # Check if wordloom exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'wordloom'")
    exists = cur.fetchone()

    if exists:
        print("Database wordloom exists")
    else:
        print("Creating wordloom database...")
        cur.execute("CREATE DATABASE wordloom")
        print("Database wordloom created")

    cur.close()
    conn.close()
    print("Success")

except Exception as e:
    print(f"Error: {e}")
    import sys
    sys.exit(1)
