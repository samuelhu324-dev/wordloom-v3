#!/usr/bin/env python3
"""详细测试 - 捕获完整错误信息"""
import sys
import json
import urllib.request
import io

try:
    # Create a simple PNG
    png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x08\x00\x00\x00\x08\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x1dIDAT\x08\x99\x01\x0c\x00\xf3\xff\xff\x00\x00\x0c\x00\xf3\xff\xff\x00\x00\x0c\x00\xf3\xff\xff\x00\x00\x0c\x00\xf3\xff\xff\x00\x00\xa1\xd9\xd4(\x00\x00\x00\x00IEND\xaeB`\x82'

    print("[TEST] Getting libraries...", file=sys.stderr, flush=True)
    req = urllib.request.Request("http://127.0.0.1:30001/api/v1/libraries", headers={"Authorization": "Bearer 550e8400-e29b-41d4-a716-446655440000"})
    with urllib.request.urlopen(req, timeout=10) as f:
        libs = json.loads(f.read().decode())
        if not libs:
            print("[TEST] No libraries", file=sys.stderr, flush=True)
            sys.exit(1)
        lib_id = libs[0]["id"]
        print(f"[TEST] Library: {lib_id}", file=sys.stderr, flush=True)

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

    print("[TEST] Uploading...", file=sys.stderr, flush=True)
    try:
        with urllib.request.urlopen(req, timeout=30) as f:
            resp = f.read().decode()
            print(f"[TEST] Success: {resp[:200]}", file=sys.stderr, flush=True)
    except urllib.error.HTTPError as e:
        print(f"[TEST] HTTP {e.code}", file=sys.stderr, flush=True)
        resp = e.read().decode()
        print(f"[TEST] Response: {resp}", file=sys.stderr, flush=True)

        # Try to parse error details
        try:
            err_json = json.loads(resp)
            print("[TEST] Parsed error:", file=sys.stderr, flush=True)
            print(json.dumps(err_json, indent=2), file=sys.stderr, flush=True)
        except:
            pass
        raise

except Exception as e:
    print(f"[TEST] Exception: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("[TEST] Done", file=sys.stderr, flush=True)
