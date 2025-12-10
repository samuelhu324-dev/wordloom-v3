#!/usr/bin/env python
"""
测试媒体上传 API
"""
import requests
import os
from pathlib import Path
import io

# 创建一个测试图片
test_image_path = Path("test_image.jpg")
if not test_image_path.exists():
    # 创建一个简单的 JPG 文件
    import struct
    jpg_header = bytes([0xFF, 0xD8, 0xFF, 0xE0])  # JPEG SOI marker
    jpg_data = jpg_header + b"test" * 100
    test_image_path.write_bytes(jpg_data)
    print(f"✓ Created test image: {test_image_path}")

# 测试参数
workspace_id = "12345678-1234-5678-1234-567812345678"
entity_type = "checkpoint_marker"
entity_id = "87654321-4321-8765-4321-876543218765"
display_order = 0

# 构建 URL
url = f"http://localhost:8000/api/orbit/media/upload?workspace_id={workspace_id}&entity_type={entity_type}&entity_id={entity_id}&display_order={display_order}"

print(f"\n📤 Testing upload to: {url}")

# 上传文件
with open(test_image_path, 'rb') as f:
    files = {'file': f}
    try:
        response = requests.post(url, files=files)
        print(f"\n✓ Response Status: {response.status_code}")
        print(f"✓ Response Body: {response.text}")

        if response.status_code == 200:
            print("\n✅ Upload successful!")
        else:
            print(f"\n❌ Upload failed with status {response.status_code}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

# 清理
test_image_path.unlink()
print("\n✓ Cleaned up test image")
