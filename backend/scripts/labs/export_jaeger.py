"""v2 entrypoint: export Jaeger snapshots for Labs (wraps v1 script).

This wrapper exists to:
- keep a stable command path under backend/scripts/labs
- standardize output directories under docs/labs/_snapshot

It intentionally reuses the proven v1 implementation.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
LEGACY_SCRIPTS_DIR = REPO_ROOT / "backend" / "scripts" / "legacy"
LABS_SNAPSHOT_ROOT = REPO_ROOT / "docs" / "labs" / "_snapshot"


def _now_run_id() -> str:
    return time.strftime("%Y%m%dT%H%M%S")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Labs: export Jaeger snapshots (v2 wrapper)")
    p.add_argument("--service", required=True)
    p.add_argument("--lookback", default="24h")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--operation")
    p.add_argument("--outbox-event-id")
    p.add_argument("--claim-batch-id")

    p.add_argument("--lab", default="_lab-S3A-2A-3A-common")
    p.add_argument("--run-id", default=None)
    p.add_argument("--outdir", default=None)

    args = p.parse_args(argv)

    run_id = args.run_id or _now_run_id()
    outdir = Path(args.outdir) if args.outdir else (LABS_SNAPSHOT_ROOT / "manual" / args.lab / run_id / "_exports")
    outdir.mkdir(parents=True, exist_ok=True)

    v1_script = LEGACY_SCRIPTS_DIR / "labs_009_export_jaeger.py"
    cmd = [
        sys.executable,
        str(v1_script),
        "--outdir",
        str(outdir),
        "--service",
        args.service,
        "--lookback",
        args.lookback,
        "--limit",
        str(args.limit),
    ]

    if args.operation:
        cmd += ["--operation", args.operation]
    if args.outbox_event_id:
        cmd += ["--outbox-event-id", args.outbox_event_id]
    if args.claim_batch_id:
        cmd += ["--claim-batch-id", args.claim_batch_id]

    print("[v2 export_jaeger] outdir:", outdir)
    print("[v2 export_jaeger] cmd:", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(REPO_ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
