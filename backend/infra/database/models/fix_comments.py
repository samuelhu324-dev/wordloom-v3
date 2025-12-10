#!/usr/bin/env python
"""Remove all comment= parameters from SQLAlchemy model definitions"""

import re
import os
from pathlib import Path

models_dir = Path('.')

for filepath in models_dir.glob('*.py'):
    if filepath.name in ('__init__.py', 'base.py', 'fix_comments.py'):
        continue

    print(f"Processing {filepath.name}...", end=" ")

    content = filepath.read_text(encoding='utf-8')
    original_len = len(content)

    # Remove comment="..." and comment='...' patterns, including newlines
    # Match patterns like: comment="..." or comment='...' with optional comma before/after
    content = re.sub(r',\s*comment\s*=\s*["\'][^"\']*["\']', '', content)
    content = re.sub(r'\s*comment\s*=\s*["\'][^"\']*["\'],', ',', content)

    if len(content) != original_len:
        filepath.write_text(content, encoding='utf-8')
        print("✅ Cleaned")
    else:
        print("No changes")

print("\n✅ All models processed!")
