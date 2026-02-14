"""Entry point: run Labs-009 ExpB (ES 429 injection) and collect evidence.

Goals:
- One command produces a self-contained run folder under docs/labs/_snapshot
- Uses legacy worker + legacy jaeger exporter (evolution-style, no risky refactors)

Notes:
- This does NOT create outbox events. You must ensure there is supply (avoid claimed=0).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
LEGACY_SCRIPTS_DIR = REPO_ROOT / "backend" / "scripts" / "legacy"
LABS_SNAPSHOT_ROOT = REPO_ROOT / "docs" / "labs" / "_snapshot"


def _now_run_id() -> str:
    return time.strftime("%Y%m%dT%H%M%S")


def _ensure_dirs(base: Path) -> dict[str, Path]:
    paths = {
        "base": base,
        "exports": base / "_exports",
        "logs": base / "_logs",
        "metrics": base / "_metrics",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Labs-009 ExpB runner (v2 wrapper)")

    p.add_argument("--service", default="wordloom-search-outbox-worker")
    p.add_argument("--lookback", default="24h")
    p.add_argument("--limit", type=int, default=20)

    p.add_argument("--duration", type=int, default=30, help="Seconds to run; 0 means run until it exits")
    p.add_argument("--run-id", default=None)
    p.add_argument("--outdir", default=None)

    # Fault injection knobs
    p.add_argument("--every-n", type=int, default=2)
    p.add_argument("--ratio", type=float, default=None)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--ops", default="delete", help="Comma-separated ops, e.g. upsert,delete")

    # Metrics port (optional)
    p.add_argument("--metrics-port", type=int, default=None)

    args = p.parse_args(argv)

    run_id = args.run_id or _now_run_id()
    base = Path(args.outdir) if args.outdir else (LABS_SNAPSHOT_ROOT / "manual" / "_lab-S3A-2A-3A-expB" / run_id)
    dirs = _ensure_dirs(base)

    notes = base / "_notes.md"
    if not notes.exists():
        notes.write_text(
            "# Labs-009 ExpB (ES 429)\n\n"
            f"run_id: {run_id}\n\n"
            "## Preconditions\n\n"
            "- Ensure there is outbox supply (avoid claimed=0).\n"
            "- Ensure Jaeger OTLP receiver is up (4317) and tracing is enabled.\n\n"
            "## Evidence\n\n"
            "- `_logs/`: worker log\n"
            "- `_exports/`: jaeger exports\n"
            "- `_metrics/`: metrics dumps (optional)\n",
            encoding="utf-8",
        )

    env = os.environ.copy()

    # Tracing: stable defaults
    env.setdefault("WORDLOOM_TRACING_ENABLED", "1")
    env.setdefault("OTEL_SERVICE_NAME", args.service)
    env.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    env.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    env.setdefault("OTEL_TRACES_SAMPLER", "always_on")

    # Injection knobs
    env["OUTBOX_EXPERIMENT_ES_429_EVERY_N"] = str(args.every_n)
    if args.ratio is not None:
        env["OUTBOX_EXPERIMENT_ES_429_RATIO"] = str(args.ratio)
    env["OUTBOX_EXPERIMENT_ES_429_SEED"] = str(args.seed)
    env["OUTBOX_EXPERIMENT_ES_429_OPS"] = args.ops

    if args.metrics_port is not None:
        env["OUTBOX_METRICS_PORT"] = str(args.metrics_port)

    worker = LEGACY_SCRIPTS_DIR / "search_outbox_worker.py"
    log_path = dirs["logs"] / f"worker-{run_id}.log"

    cmd = [sys.executable, "-u", str(worker)]
    print("[v2 expB] outdir:", base)
    print("[v2 expB] log:", log_path)
    print("[v2 expB] cmd:", " ".join(cmd))

    start = time.time()
    with open(log_path, "w", encoding="utf-8") as log_file:
        proc = subprocess.Popen(cmd, cwd=str(REPO_ROOT), env=env, stdout=log_file, stderr=subprocess.STDOUT)
        try:
            while True:
                if args.duration > 0 and (time.time() - start) >= args.duration:
                    proc.terminate()
                    break
                ret = proc.poll()
                if ret is not None:
                    break
                time.sleep(0.25)
        except KeyboardInterrupt:
            proc.terminate()

        proc.wait(timeout=30)

    # Export Jaeger snapshot
    jaeger_script = LEGACY_SCRIPTS_DIR / "labs_009_export_jaeger.py"
    export_cmd = [
        sys.executable,
        str(jaeger_script),
        "--outdir",
        str(dirs["exports"]),
        "--service",
        args.service,
        "--lookback",
        args.lookback,
        "--limit",
        str(args.limit),
    ]
    print("[v2 expB] export:", " ".join(export_cmd))
    subprocess.call(export_cmd, cwd=str(REPO_ROOT))

    print("[v2 expB] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
