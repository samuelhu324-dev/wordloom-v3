#!/usr/bin/env python3
"""
快速测试脚本：验证 Note 复制功能

使用方法:
  python test_duplicate_note.py

前置条件:
  - 后端服务正在运行
  - 数据库已初始化
"""

import requests
import json
from typing import Optional

# 配置
API_BASE = "http://localhost:8000/api/orbit"
NOTES_ENDPOINT = f"{API_BASE}/notes"

def print_section(title: str):
    """打印分隔符"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def create_test_note() -> Optional[dict]:
    """创建测试 Note"""
    print("📝 创建测试 Note...")
    payload = {
        "title": "Test Note for Duplication",
        "content_md": "# 测试内容\n\n这是一个测试 Note",
        "status": "open",
        "priority": 3,
        "urgency": 2,
        "tags": ["test", "demo"],
    }

    try:
        resp = requests.post(NOTES_ENDPOINT, json=payload, timeout=5)
        if resp.status_code == 200:
            note = resp.json()
            print(f"✅ 创建成功！")
            print(f"   ID: {note['id']}")
            print(f"   标题: {note['title']}")
            print(f"   标签: {note['tags']}")
            return note
        else:
            print(f"❌ 创建失败: {resp.status_code}")
            print(f"   {resp.text}")
            return None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def duplicate_note(note_id: str, title_suffix: str = "(副本)") -> Optional[dict]:
    """复制 Note"""
    print(f"📋 复制 Note: {note_id}...")
    payload = {
        "title_suffix": title_suffix,
    }

    endpoint = f"{NOTES_ENDPOINT}/{note_id}/duplicate"
    try:
        resp = requests.post(endpoint, json=payload, timeout=10)
        if resp.status_code == 200:
            note = resp.json()
            print(f"✅ 复制成功！")
            print(f"   新 ID: {note['id']}")
            print(f"   新标题: {note['title']}")
            print(f"   使用次数: {note['usage_count']} (应为 0)")
            print(f"   标签: {note['tags']}")
            return note
        else:
            print(f"❌ 复制失败: {resp.status_code}")
            print(f"   {resp.text}")
            return None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def get_note(note_id: str) -> Optional[dict]:
    """获取 Note 详情"""
    endpoint = f"{NOTES_ENDPOINT}/{note_id}"
    try:
        resp = requests.get(endpoint, timeout=5)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"❌ 获取失败: {resp.status_code}")
            return None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def list_notes() -> list:
    """列出所有 Note"""
    try:
        resp = requests.get(NOTES_ENDPOINT, timeout=5)
        if resp.status_code == 200:
            return resp.json()
        else:
            return []
    except Exception as e:
        print(f"❌ 错误: {e}")
        return []

def delete_note(note_id: str) -> bool:
    """删除 Note"""
    endpoint = f"{NOTES_ENDPOINT}/{note_id}"
    try:
        resp = requests.delete(endpoint, timeout=5)
        return resp.status_code == 204
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def run_tests():
    """运行测试"""
    print_section("🧪 Note 复制功能测试")

    # 测试 1: 创建 Note
    print_section("测试 1: 创建原始 Note")
    original = create_test_note()
    if not original:
        print("❌ 测试失败：无法创建 Note")
        return False

    # 测试 2: 复制 Note
    print_section("测试 2: 复制 Note")
    duplicated = duplicate_note(original['id'], "(副本)")
    if not duplicated:
        print("❌ 测试失败：无法复制 Note")
        return False

    # 验证复制结果
    print_section("测试 3: 验证复制结果")
    print("✓ 验证项:")

    checks = [
        ("ID 不同", original['id'] != duplicated['id']),
        ("使用次数重置", duplicated['usage_count'] == 0),
        ("标题包含后缀", "(副本)" in duplicated['title']),
        ("保留标签", set(original['tags']) == set(duplicated['tags'])),
        ("保留优先级", original['priority'] == duplicated['priority']),
        ("保留紧急程度", original['urgency'] == duplicated['urgency']),
        ("保留内容", original['content_md'] == duplicated['content_md']),
    ]

    all_passed = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False

    # 测试 4: 列出 Note
    print_section("测试 4: 列出所有 Note")
    notes = list_notes()
    print(f"✅ 共 {len(notes)} 个 Note")

    # 清理
    print_section("清理")
    print("🗑️  删除测试数据...")
    delete_note(original['id'])
    delete_note(duplicated['id'])
    print("✅ 清理完成")

    # 总结
    print_section("测试结果")
    if all_passed:
        print("✅ 所有测试通过！")
        return True
    else:
        print("❌ 某些测试失败")
        return False

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
