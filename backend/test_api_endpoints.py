#!/usr/bin/env python3
"""
测试所有后端 API 端点
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "api"))

async def test_endpoints():
    """测试所有端点"""
    import httpx

    base_url = "http://localhost:30001"

    tests = [
        ("GET", "/", "API Root"),
        ("GET", "/api/v1/health", "Health Check"),
        ("GET", "/api/v1/libraries", "List Libraries"),
        ("GET", "/docs", "Swagger Docs"),
    ]

    print("=" * 70)
    print("API Endpoints Test")
    print("=" * 70)

    async with httpx.AsyncClient() as client:
        for method, path, description in tests:
            url = f"{base_url}{path}"
            print(f"\n{method} {path}")
            print(f"  描述: {description}")
            try:
                if method == "GET":
                    response = await client.get(url, timeout=5)
                    print(f"  状态: {response.status_code}")
                    if response.status_code == 200:
                        print(f"  ✅ 成功")
                        if "application/json" in response.headers.get("content-type", ""):
                            print(f"  响应: {response.json()}")
                    else:
                        print(f"  ❌ 失败: {response.text[:100]}")
            except Exception as e:
                print(f"  ❌ 错误: {e}")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(test_endpoints())
