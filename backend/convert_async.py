#!/usr/bin/env python3
"""Convert test_application_layer.py and test_infrastructure.py from async to sync"""

import re

def convert_file(filepath):
    """Convert async test file to sync"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 移除 @pytest.mark.asyncio 装饰器
    content = re.sub(r'@pytest\.mark\.asyncio\s+', '', content)

    # 更新 async def -> def (but not in comments)
    content = re.sub(r'^(\s*)async def ', r'\1def ', content, flags=re.MULTILINE)

    # 移除 await 关键字
    content = re.sub(r'\s*await\s+', ' ', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ Converted {filepath}")

# 转换两个文件
convert_file('api/app/tests/test_book/test_application_layer.py')
convert_file('api/app/tests/test_book/test_infrastructure.py')

print("✓ All files converted successfully")
