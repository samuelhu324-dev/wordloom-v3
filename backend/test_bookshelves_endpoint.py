#!/usr/bin/env python3
"""Quick sanity test for bookshelves endpoints after schema fix."""
import asyncio
import httpx
import os
import sys
from uuid import uuid4

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:30001")
LIB_ID = os.getenv("TEST_LIBRARY_ID", "2a4fbbcc-3528-47bb-bc0f-a81cae9fdb80")

async def main():
    async with httpx.AsyncClient() as client:
        # List
        list_url = f"{BASE_URL}/api/v1/bookshelves?library_id={LIB_ID}"
        print(f"GET {list_url}")
        r = await client.get(list_url, timeout=10)
        print("Status:", r.status_code)
        print("Body:", r.text[:300])
        # Create
        create_url = f"{BASE_URL}/api/v1/bookshelves"
        payload = {"library_id": LIB_ID, "name": f"TestShelf-{uuid4().hex[:6]}", "description": "Auto created"}
        print(f"POST {create_url} -> {payload}")
        r2 = await client.post(create_url, json=payload, timeout=10)
        print("Status:", r2.status_code)
        print("Body:", r2.text[:300])
        # Re-list
        r3 = await client.get(list_url, timeout=10)
        print("Re-list Status:", r3.status_code)
        print("Re-list Body:", r3.text[:300])

if __name__ == "__main__":
    asyncio.run(main())
