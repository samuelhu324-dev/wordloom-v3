#!/usr/bin/env bash
# Wordloom Integration Test Suite - Quick Diagnostics and Repair Script
# Purpose: Identify and suggest fixes for test failures

set -e

cd "$(dirname "$0")/backend"

echo "=========================================="
echo "Wordloom Integration Test Diagnostics"
echo "=========================================="
echo ""

# Step 1: Check Python and pytest versions
echo "[1/6] Checking environment..."
python_version=$(python --version 2>&1 | awk '{print $2}')
pytest_version=$(pytest --version 2>&1 | awk '{print $2}')
echo "✓ Python: $python_version"
echo "✓ pytest: $pytest_version"
echo ""

# Step 2: Check pytest-asyncio installation
echo "[2/6] Checking async test support..."
if python -c "import pytest_asyncio" 2>/dev/null; then
    echo "✓ pytest-asyncio installed"
else
    echo "✗ pytest-asyncio NOT installed (required for async tests)"
    echo "  → Fix: pip install pytest-asyncio"
fi
echo ""

# Step 3: Check critical module imports
echo "[3/6] Checking critical imports..."

# Library
if python -c "from api.app.modules.library.domain import Library" 2>/dev/null; then
    echo "✓ Library module imports OK"
else
    echo "✗ Library module import failed"
fi

# Bookshelf
if python -c "from api.app.modules.bookshelf.domain import Bookshelf" 2>/dev/null; then
    echo "✓ Bookshelf module imports OK"
else
    echo "✗ Bookshelf module import failed"
fi

# Book
if python -c "from api.app.modules.book.domain import Book" 2>/dev/null; then
    echo "✓ Book module imports OK"
else
    echo "✗ Book module import failed"
fi

# Block
if python -c "from api.app.modules.block.domain import Block" 2>/dev/null; then
    echo "✓ Block module imports OK"
else
    echo "✗ Block module import FAILED (relative import error)"
    echo "  → See: ROOT_CAUSE_ANALYSIS.md - Problem #2"
fi
echo ""

# Step 4: Check syntax errors
echo "[4/6] Checking for syntax errors..."
if python -m py_compile api/app/tests/test_block/test_paperballs_recovery.py 2>/dev/null; then
    echo "✓ Block test file syntax OK"
else
    echo "✗ Block test file has SYNTAX ERROR"
    echo "  → See: ROOT_CAUSE_ANALYSIS.md - Problem #3"
fi
echo ""

# Step 5: Quick test collection
echo "[5/6] Test collection status..."
echo ""
echo "Library tests:"
pytest api/app/tests/test_library/ --co -q 2>&1 | head -1 || echo "  (Collection issues)"

echo ""
echo "Bookshelf tests:"
pytest api/app/tests/test_bookshelf/ --co -q 2>&1 | head -1 || echo "  (Collection issues)"

echo ""
echo "Book tests:"
pytest api/app/tests/test_book/ --co -q 2>&1 | head -1 || echo "  (Collection issues)"

echo ""
echo "Block tests:"
pytest api/app/tests/test_block/ --co -q 2>&1 | head -1 || echo "  (Collection issues)"
echo ""

# Step 6: Summary
echo "[6/6] Summary"
echo ""
echo "📊 For detailed analysis, see:"
echo "   - INTEGRATION_TEST_REPORT_NOV14.md (full test results)"
echo "   - ROOT_CAUSE_ANALYSIS.md (7 core issues)"
echo "   - QUICK_FIX_GUIDE.md (30-minute fix plan)"
echo ""
echo "🚀 Quick fixes (3 items, ~5 minutes):"
echo "   1. Enable asyncio_mode in pyproject.toml"
echo "   2. Fix Block module relative imports"
echo "   3. Fix class name syntax error"
echo ""
echo "✅ To implement all fixes, follow QUICK_FIX_GUIDE.md"
echo ""
