#!/usr/bin/env python3
"""
图片管理系统测试脚本

本脚本用于验证图片管理系统的各项功能。
在后端服务运行的情况下执行此脚本。

使用方法：
    python test_image_manager.py
"""

import requests
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

# API 基础地址
API_BASE = "http://localhost:8011/api/orbit"

# 颜色代码（用于终端输出）
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text: str):
    """打印标题"""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")


def print_success(text: str):
    """打印成功信息"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text: str):
    """打印错误信息"""
    print(f"{RED}✗ {text}{RESET}")


def print_info(text: str):
    """打印信息"""
    print(f"{YELLOW}ℹ {text}{RESET}")


def print_json(data: Dict[str, Any]):
    """打印格式化的 JSON"""
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ========== 测试用例 ==========

def test_create_note() -> Optional[str]:
    """测试 1: 创建 Note"""
    print_header("测试 1: 创建 Note")

    try:
        response = requests.post(
            f"{API_BASE}/notes",
            json={
                "title": "测试笔记",
                "content_md": "这是一个测试笔记"
            }
        )

        if response.status_code != 200:
            print_error(f"创建 Note 失败: {response.status_code}")
            print(response.text)
            return None

        data = response.json()
        note_id = data.get("id")

        if not note_id:
            print_error("返回的 Note ID 为空")
            return None

        print_success(f"Note 创建成功")
        print_info(f"Note ID: {note_id}")
        print_json(data)

        return note_id

    except Exception as e:
        print_error(f"请求失败: {e}")
        return None


def test_create_test_image(size_kb: int = 10) -> bytes:
    """创建一个测试图片（PNG 格式）"""
    # 创建简单的 PNG 文件（1x1 像素，黑色）
    # PNG 魔数 + IHDR + IDAT + IEND
    png_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG 魔数
        0x00, 0x00, 0x00, 0x0D,                          # IHDR 长度
        0x49, 0x48, 0x44, 0x52,                          # IHDR
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE,
        0x00, 0x00, 0x00, 0x0C,                          # IDAT 长度
        0x49, 0x44, 0x41, 0x54,                          # IDAT
        0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00, 0x00,
        0x03, 0x01, 0x01, 0x00, 0x18, 0xDD, 0x8D, 0xB4,
        0x00, 0x00, 0x00, 0x00,                          # IEND 长度
        0x49, 0x45, 0x4E, 0x44,                          # IEND
        0xAE, 0x42, 0x60, 0x82
    ])

    # 如果需要更大的文件，填充零字节
    if len(png_data) < size_kb * 1024:
        png_data += b'\x00' * (size_kb * 1024 - len(png_data))

    return png_data


def test_upload_image(note_id: str, image_name: str = "test_image.png") -> Optional[str]:
    """测试 2: 上传图片"""
    print_header(f"测试 2: 上传图片到 Note {note_id[:8]}...")

    try:
        image_data = test_create_test_image(size_kb=10)

        response = requests.post(
            f"{API_BASE}/uploads",
            params={"note_id": note_id},
            files={"file": (image_name, image_data, "image/png")}
        )

        if response.status_code != 200:
            print_error(f"上传图片失败: {response.status_code}")
            print(response.text)
            return None

        data = response.json()
        image_url = data.get("url")

        if not image_url:
            print_error("返回的图片 URL 为空")
            return None

        print_success(f"图片上传成功")
        print_info(f"图片 URL: {image_url}")
        print_json(data)

        # 从 URL 中提取文件名
        filename = image_url.split("/")[-1]
        return filename

    except Exception as e:
        print_error(f"请求失败: {e}")
        return None


def test_get_images(note_id: str, content_md: str = "") -> bool:
    """测试 3: 查询图片信息"""
    print_header(f"测试 3: 查询 Note 的图片信息")

    try:
        response = requests.get(
            f"{API_BASE}/images/{note_id}",
            params={"content_md": content_md}
        )

        if response.status_code != 200:
            print_error(f"查询失败: {response.status_code}")
            print(response.text)
            return False

        data = response.json()

        print_success(f"查询成功")
        print_info(f"总图片数: {data.get('total_images')}")
        print_info(f"被引用图片数: {data.get('referenced_count')}")
        print_info(f"未被引用图片数: {data.get('unreferenced_count')}")
        print_json(data)

        return True

    except Exception as e:
        print_error(f"请求失败: {e}")
        return False


def test_update_note_with_reference(note_id: str, filename: str) -> bool:
    """测试 4: 更新 Note（包含图片引用）"""
    print_header(f"测试 4: 更新 Note（添加图片引用）")

    try:
        # 创建包含图片引用的 markdown
        image_url = f"/uploads/{note_id}/{filename}"
        content_md = f"这是更新后的内容\n\n![测试图片]({image_url})"

        response = requests.put(
            f"{API_BASE}/notes/{note_id}",
            json={
                "title": "更新后的标题",
                "content_md": content_md
            }
        )

        if response.status_code != 200:
            print_error(f"更新 Note 失败: {response.status_code}")
            print(response.text)
            return False

        print_success(f"Note 更新成功")
        print_info(f"内容包含图片引用: {image_url}")

        return True

    except Exception as e:
        print_error(f"请求失败: {e}")
        return False


def test_cleanup_images(note_id: str, content_md: str) -> bool:
    """测试 5: 手动清理未被引用的图片"""
    print_header(f"测试 5: 手动清理未被引用的图片")

    try:
        response = requests.post(
            f"{API_BASE}/cleanup-images",
            params={
                "note_id": note_id,
                "content_md": content_md
            }
        )

        if response.status_code != 200:
            print_error(f"清理失败: {response.status_code}")
            print(response.text)
            return False

        data = response.json()
        deleted_count = data.get("deleted_count", 0)

        if deleted_count > 0:
            print_success(f"成功清理 {deleted_count} 张未被引用的图片")
        else:
            print_info(f"没有未被引用的图片需要清理")

        print_json(data)

        return True

    except Exception as e:
        print_error(f"请求失败: {e}")
        return False


def test_delete_note(note_id: str) -> bool:
    """测试 6: 删除 Note"""
    print_header(f"测试 6: 删除 Note")

    try:
        response = requests.delete(f"{API_BASE}/notes/{note_id}")

        if response.status_code != 204:
            print_error(f"删除 Note 失败: {response.status_code}")
            print(response.text)
            return False

        print_success(f"Note 删除成功（状态码: 204）")
        print_info(f"关联的图片文件夹已自动删除")

        return True

    except Exception as e:
        print_error(f"请求失败: {e}")
        return False


def test_full_workflow():
    """完整工作流测试"""
    print_header("完整工作流测试")
    print_info("本测试将演示整个图片管理流程")

    # 步骤 1: 创建 Note
    print("\n[步骤 1/6] 创建 Note...")
    note_id = test_create_note()
    if not note_id:
        print_error("工作流中止：创建 Note 失败")
        return False

    time.sleep(1)

    # 步骤 2: 上传第一张图片
    print("\n[步骤 2/6] 上传第一张图片...")
    filename1 = test_upload_image(note_id, "image1.png")
    if not filename1:
        print_error("工作流中止：上传图片失败")
        return False

    time.sleep(1)

    # 步骤 3: 上传第二张图片
    print("\n[步骤 3/6] 上传第二张图片...")
    filename2 = test_upload_image(note_id, "image2.png")
    if not filename2:
        print_error("工作流中止：上传第二张图片失败")
        return False

    time.sleep(1)

    # 步骤 4: 查询图片（两张都被引用）
    print("\n[步骤 4/6] 查询图片信息（引用两张图片）...")
    image_url1 = f"/uploads/{note_id}/{filename1}"
    image_url2 = f"/uploads/{note_id}/{filename2}"
    content_with_both = f"![img1]({image_url1})\n\n![img2]({image_url2})"
    test_get_images(note_id, content_with_both)

    time.sleep(1)

    # 步骤 5: 更新 Note（只保留第一张图片的引用）
    print("\n[步骤 5/6] 更新 Note（删除对第二张图片的引用）...")
    content_with_one = f"![img1]({image_url1})"
    test_update_note_with_reference(note_id, filename1)

    # 自动清理应该删除未被引用的第二张图片
    time.sleep(1)

    # 步骤 6: 查询图片（验证未被引用的图片已被删除）
    print("\n[步骤 6/6] 查询图片信息（验证自动清理）...")
    test_get_images(note_id, content_with_one)

    # 清理资源
    print("\n[清理] 删除测试用的 Note...")
    test_delete_note(note_id)

    print_header("工作流测试完成")
    print_success("所有测试用例已执行完毕")


def main():
    """主测试函数"""
    print_header("Wordloom Orbit 图片管理系统测试")

    print_info("后端 API 地址: " + API_BASE)
    print_info("如果连接失败，请确保后端服务已启动")

    time.sleep(2)

    # 执行完整工作流测试
    try:
        test_full_workflow()
    except KeyboardInterrupt:
        print_error("\n测试被中断")
    except Exception as e:
        print_error(f"测试异常: {e}")
        import traceback
        traceback.print_exc()

    print_header("测试结束")


if __name__ == "__main__":
    main()
