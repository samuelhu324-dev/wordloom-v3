#!/usr/bin/env python3
import sys
import json

# Simple test: make HTTP request and print everything
try:
    import urllib.request
    import io

    # Create a simple PNG
    png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x08\x00\x00\x00\x08\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x1dIDAT\x08\x99\x01\x0c\x00\xf3\xff\xff\x00\x00\x0c\x00\xf3\xff\xff\x00\x00\x0c\x00\xf3\xff\xff\x00\x00\x0c\x00\xf3\xff\xff\x00\x00\xa1\xd9\xd4(\x00\x00\x00\x00IEND\xaeB`\x82'

    print("[SIMPLE] Creating request...", file=sys.stderr, flush=True)

    # First get a library ID
    req = urllib.request.Request("http://127.0.0.1:30001/api/v1/libraries", headers={"Authorization": "Bearer 550e8400-e29b-41d4-a716-446655440000"})
    with urllib.request.urlopen(req, timeout=10) as f:
        libs = json.loads(f.read().decode())
        print(f"[SIMPLE] Got {len(libs)} libraries", file=sys.stderr, flush=True)
        if not libs:
            print("[SIMPLE] No libraries", file=sys.stderr, flush=True)
            sys.exit(1)
        lib_id = libs[0]["id"]
        print(f"[SIMPLE] Using library: {lib_id}", file=sys.stderr, flush=True)

    # Build multipart form data
    boundary = '----WebKitFormBoundary1234567890'
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="test.png"\r\n'
        f'Content-Type: image/png\r\n'
        f'\r\n'
    ).encode() + png_bytes + f'\r\n--{boundary}--\r\n'.encode()

    req = urllib.request.Request(
        f"http://127.0.0.1:30001/api/v1/libraries/{lib_id}/cover",
        data=body,
        headers={
            "Authorization": "Bearer 550e8400-e29b-41d4-a716-446655440000",
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        },
        method="POST"
    )

    print("[SIMPLE] Sending upload request...", file=sys.stderr, flush=True)
    try:
        with urllib.request.urlopen(req, timeout=30) as f:
            resp = f.read().decode()
            print(f"[SIMPLE] Status: {f.status}", file=sys.stderr, flush=True)
            print(f"[SIMPLE] Response: {resp[:500]}", file=sys.stderr, flush=True)
    except urllib.error.HTTPError as e:
        print(f"[SIMPLE] HTTP Error: {e.code}", file=sys.stderr, flush=True)
        resp = e.read().decode()
        print(f"[SIMPLE] Error Response: {resp[:500]}", file=sys.stderr, flush=True)
        raise

except Exception as e:
    print(f"[SIMPLE] Exception: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("[SIMPLE] Done", file=sys.stderr, flush=True)
