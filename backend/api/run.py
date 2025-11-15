#!/usr/bin/env python3
"""
Wordloom API Startup Script - Minimal Mode
"""

import sys
import os

# Add backend/api to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
import uvicorn

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Starting Wordloom API (Minimal Mode)")
    print("="*60)
    print(f"Host: 0.0.0.0")
    print(f"Port: 30001")
    print(f"URL: http://localhost:30001")
    print(f"Docs: http://localhost:30001/docs")
    print("="*60 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=30001,
        log_level="info",
    )
