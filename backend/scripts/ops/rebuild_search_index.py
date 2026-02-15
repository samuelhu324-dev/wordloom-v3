"""Stable shim for rebuilding Postgres search_index.

The implementation currently lives under backend/scripts/legacy/.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    legacy_script = Path(__file__).resolve().parents[1] / "legacy" / "rebuild_search_index.py"
    if not legacy_script.exists():
        raise SystemExit(f"legacy tool not found: {legacy_script}")
    runpy.run_path(str(legacy_script), run_name="__main__")


if __name__ == "__main__":
    main()
