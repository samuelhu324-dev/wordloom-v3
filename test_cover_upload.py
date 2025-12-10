#!/usr/bin/env python3
"""Test library cover upload endpoint"""
import requests
from pathlib import Path
from uuid import UUID
import sys

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_cover_upload():
    """Test POST /api/v1/libraries/{id}/cover"""

    # Create a minimal PNG for testing (8x8 red pixel)
    png_bytes = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D,  # IHDR chunk size
        0x49, 0x48, 0x44, 0x52,  # IHDR
        0x00, 0x00, 0x00, 0x08,  # width: 8
        0x00, 0x00, 0x00, 0x08,  # height: 8
        0x08, 0x02,  # bit depth, color type
        0x00, 0x00, 0x00,  # compression, filter, interlace
        0x90, 0x77, 0x53, 0xDE,  # CRC
        0x00, 0x00, 0x00, 0x1D,  # IDAT chunk size
        0x49, 0x44, 0x41, 0x54,  # IDAT
        0x08, 0x99, 0x01, 0x0C, 0x00, 0xF3, 0xFF,
        0xFF, 0x00, 0x00, 0x0C, 0x00, 0xF3, 0xFF,
        0xFF, 0x00, 0x00, 0x0C, 0x00, 0xF3, 0xFF,
        0xFF, 0x00, 0x00, 0x0C, 0x00, 0xF3, 0xFF,
        0xFF, 0x00, 0x00, 0xA1, 0xD9, 0xD4, 0x28,  # CRC
        0x00, 0x00, 0x00, 0x00,  # IEND chunk size
        0x49, 0x45, 0x4E, 0x44,  # IEND
        0xAE, 0x42, 0x60, 0x82,  # CRC
    ])

    # Use a known library ID from the database
    # First, get a library ID
    dev_user_id = "550e8400-e29b-41d4-a716-446655440000"

    try:
        # List libraries to get an ID
        print("[TEST] Fetching libraries...", flush=True)
        resp = requests.get(
            "http://127.0.0.1:30001/api/v1/libraries",
            headers={"Authorization": f"Bearer {dev_user_id}"},
            timeout=10
        )

        if resp.status_code != 200:
            print(f"[TEST] Failed to fetch libraries: {resp.status_code}", flush=True)
            print(f"[TEST] Response: {resp.text}", flush=True)
            return

        libraries = resp.json()
        print(f"[TEST] Got {len(libraries)} libraries", flush=True)

        if not libraries:
            print("[TEST] No libraries found, creating one...", flush=True)
            resp = requests.post(
                "http://127.0.0.1:30001/api/v1/libraries",
                json={"name": "Test Library"},
                headers={"Authorization": f"Bearer {dev_user_id}"},
                timeout=10
            )

            if resp.status_code not in (200, 201):
                print(f"[TEST] Failed to create library: {resp.status_code}", flush=True)
                print(f"[TEST] Response: {resp.text}", flush=True)
                return

            lib = resp.json()
            library_id = lib["id"]
            print(f"[TEST] Created library: {library_id}", flush=True)
        else:
            library_id = libraries[0]["id"]
            print(f"[TEST] Using library: {library_id}", flush=True)

        # Upload cover
        print(f"\n[TEST] Uploading cover to library {library_id}...", flush=True)
        files = {'file': ('test.png', png_bytes, 'image/png')}

        resp = requests.post(
            f"http://127.0.0.1:30001/api/v1/libraries/{library_id}/cover",
            files=files,
            headers={"Authorization": f"Bearer {dev_user_id}"},
            timeout=30
        )

        print(f"[TEST] Response status: {resp.status_code}", flush=True)
        print(f"[TEST] Response: {resp.text[:1000]}", flush=True)

        if resp.status_code in (200, 201):
            print("[TEST] ✅ SUCCESS!", flush=True)
        else:
            print(f"[TEST] ❌ FAILED with status {resp.status_code}", flush=True)
    except Exception as e:
        print(f"[TEST] Exception: {type(e).__name__}: {e}", flush=True)
        import traceback
        traceback.print_exc()
