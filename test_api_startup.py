#!/usr/bin/env python
"""Test API startup and router loading"""

import sys
import os
from pathlib import Path

# Setup paths
backend_root = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_root))

# Set database URL
os.environ["DATABASE_URL"] = "postgresql://postgres:pgpass@127.0.0.1:5433/wordloom"

print("\n" + "="*70)
print("Testing API Startup and Router Loading")
print("="*70 + "\n")

try:
    from api.app.main import app, _routers
    print(f"[OK] API app imported successfully")
    print(f"[OK] {len(_routers)} routers registered")

    for i, (router, prefix, tags) in enumerate(_routers, 1):
        print(f"     {i}. {prefix:20} - {tags[0]}")

    print("\n" + "="*70)
    print("Router Loading Status: SUCCESS")
    print("="*70 + "\n")

except Exception as e:
    import traceback
    print(f"[FAIL] API startup failed: {type(e).__name__}: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
