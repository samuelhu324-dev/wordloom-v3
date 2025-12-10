#!/usr/bin/env python3
"""Debug upload - detailed error capture"""
import sys
import json
import urllib.request
import urllib.error

try:
    # Create a simple PNG
    png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x08\x00\x00\x00\x08\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x1dIDAT\x08\x99\x01\x0c\x00\xf3\xff\xff\x00\x00\x0c\x00\xf3\xff\xff\x00\x00\x0c\x00\xf3\xff\xff\x00\x00\x0c\x00\xf3\xff\xff\x00\x00\xa1\xd9\xd4(\x00\x00\x00\x00IEND\xaeB`\x82'

    print("[DEBUG] Creating request...", file=sys.stderr, flush=True)

    # Get library ID
    req = urllib.request.Request(
        "http://127.0.0.1:30001/api/v1/libraries",
        headers={"Authorization": "Bearer 550e8400-e29b-41d4-a716-446655440000"}
    )
    with urllib.request.urlopen(req, timeout=10) as f:
        libs = json.loads(f.read().decode())
        if not libs:
            print("[DEBUG] No libraries", file=sys.stderr)
            sys.exit(1)
        lib_id = libs[0]["id"]
        print(f"[DEBUG] Using library: {lib_id}", file=sys.stderr)

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

    print("[DEBUG] Sending upload request to upload endpoint...", file=sys.stderr, flush=True)
    try:
        with urllib.request.urlopen(req, timeout=30) as f:
            resp = f.read().decode()
            print(f"[DEBUG] Success! Status: {f.status}", file=sys.stderr, flush=True)
            print(f"[DEBUG] Response: {resp[:500]}", file=sys.stderr, flush=True)
    except urllib.error.HTTPError as e:
        print(f"[DEBUG] HTTP Error: {e.code}", file=sys.stderr, flush=True)
        resp_bytes = e.read()
        resp_str = resp_bytes.decode('utf-8', errors='replace')
        print(f"[DEBUG] Raw Error Response ({len(resp_bytes)} bytes):", file=sys.stderr, flush=True)
        print(f"{resp_str}", file=sys.stderr, flush=True)

        try:
            error_json = json.loads(resp_str)
            print(f"[DEBUG] Parsed Error JSON:", file=sys.stderr, flush=True)
            print(f"  code: {error_json.get('detail', {}).get('code')}", file=sys.stderr, flush=True)
            print(f"  message: {error_json.get('detail', {}).get('message')}", file=sys.stderr, flush=True)
            print(f"  details: {error_json.get('detail', {}).get('details')}", file=sys.stderr, flush=True)
        except:
            pass

        raise

except Exception as e:
    print(f"[DEBUG] Exception: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("[DEBUG] Done", file=sys.stderr, flush=True)
