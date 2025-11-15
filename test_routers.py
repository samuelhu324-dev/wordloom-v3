#!/usr/bin/env python
"""Test all router imports"""

import sys
sys.path.insert(0, 'd:\\Project\\Wordloom\\backend')

routers = [
    ('media', 'd:\\Project\\Wordloom\\backend\\api\\app\\modules\\media\\routers\\media_router.py'),
    ('search', 'd:\\Project\\Wordloom\\backend\\api\\app\\modules\\search\\routers\\search_router.py'),
    ('library', 'd:\\Project\\Wordloom\\backend\\api\\app\\modules\\library\\routers\\library_router.py'),
    ('book', 'd:\\Project\\Wordloom\\backend\\api\\app\\modules\\book\\routers\\book_router.py'),
    ('bookshelf', 'd:\\Project\\Wordloom\\backend\\api\\app\\modules\\bookshelf\\routers\\bookshelf_router.py'),
    ('block', 'd:\\Project\\Wordloom\\backend\\api\\app\\modules\\block\\routers\\block_router.py'),
    ('tag', 'd:\\Project\\Wordloom\\backend\\api\\app\\modules\\tag\\routers\\tag_router.py'),
]

print("\n=== Testing Router Imports ===\n")

for name, path in routers:
    try:
        if name == 'media':
            from api.app.modules.media.routers.media_router import router
        elif name == 'search':
            from api.app.modules.search.routers.search_router import router
        elif name == 'library':
            from api.app.modules.library.routers.library_router import router
        elif name == 'book':
            from api.app.modules.book.routers.book_router import router
        elif name == 'bookshelf':
            from api.app.modules.bookshelf.routers.bookshelf_router import router
        elif name == 'block':
            from api.app.modules.block.routers.block_router import router
        elif name == 'tag':
            from api.app.modules.tag.routers.tag_router import router

        print(f"[OK] {name:12} router imported successfully")
    except Exception as e:
        print(f"[FAIL] {name:12} router import failed: {type(e).__name__}: {str(e)[:80]}")

print("\n")
