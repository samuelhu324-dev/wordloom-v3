#!/usr/bin/env python
"""Fix encoding issues in media module files"""

import os
from pathlib import Path

problem_files = [
    'd:\\Project\\Wordloom\\backend\\api\\app\\modules\\media\\application\\ports\\input.py',
    'd:\\Project\\Wordloom\\backend\\api\\app\\modules\\media\\application\\ports\\output.py',
]

for filepath_str in problem_files:
    filepath = Path(filepath_str)
    if not filepath.exists():
        print(f"⚠️  {filepath.name}: NOT FOUND")
        continue

    try:
        # Try to read with UTF-8
        content = filepath.read_text(encoding='utf-8')
        print(f"✅ {filepath.name}: UTF-8 OK")
    except UnicodeDecodeError:
        print(f"❌ {filepath.name}: UTF-8 decode error, trying latin-1...")
        try:
            # Read with latin-1 (more permissive)
            content = filepath.read_text(encoding='latin-1')
            # Write back as UTF-8
            filepath.write_text(content, encoding='utf-8')
            print(f"✅ {filepath.name}: Fixed to UTF-8")
        except Exception as e:
            print(f"❌ {filepath.name}: {e}")
