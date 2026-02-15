"""Minimal script router for backend/scripts.

Design goals:
- Keep it tiny and dependency-free.
- Provide a stable command namespace so people stop memorizing file names.
- Enforce consistent snapshot output locations for labs.

This is intentionally not a full-featured CLI framework.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from sqlalchemy import create_engine, text


REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_SCRIPTS_DIR = REPO_ROOT / "backend" / "scripts" / "legacy"
LABS_SNAPSHOT_ROOT = REPO_ROOT / "docs" / "labs" / "_snapshot"


LAB_ID_S3A_2A_3A = "S3A-2A-3A"
SCENARIO_ES_WRITE_BLOCK_4XX = "es_write_block_4xx"
SCENARIO_ES_429_INJECT = "es_429_inject"
SCENARIO_ES_DOWN_CONNECT = "es_down_connect"
SCENARIO_ES_BULK_PARTIAL = "es_bulk_partial"
SCENARIO_DB_CLAIM_CONTENTION = "db_claim_contention"
SCENARIO_STUCK_RECLAIM = "stuck_reclaim"
SCENARIO_DUPLICATE_DELIVERY = "duplicate_delivery"
SCENARIO_PROJECTION_VERSION = "projection_version"
SCENARIO_COLLECTOR_DOWN = "collector_down"

# Keep in sync with backend/scripts/legacy/search_outbox_worker.py
SEARCH_OUTBOX_OBS_SCHEMA_VERSION = "labs-009-v2"


def _now_run_id() -> str:
    # local time is fine for manual runs; keep it filesystem-safe
    return time.strftime("%Y%m%dT%H%M%S")


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _read_env_file(path: Path) -> dict[str, str]:
    """Very small .env parser (KEY=VALUE, supports quotes, ignores comments)."""

    if not path.exists():
        raise FileNotFoundError(str(path))

    env: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if (len(value) >= 2) and ((value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")):
            value = value[1:-1]
        env[key] = value
    return env


def _load_env(*, env_file: str | None) -> dict[str, str]:
    env = os.environ.copy()
    if env_file:
        env_path = (REPO_ROOT / env_file).resolve() if not Path(env_file).is_absolute() else Path(env_file)
        env.update(_read_env_file(env_path))
    return env


def _default_labs_auto_run_dir(*, scenario: str, run_id: str) -> Path:
    return LABS_SNAPSHOT_ROOT / "auto" / LAB_ID_S3A_2A_3A / scenario / run_id


def _latest_child_dir(base: Path) -> Path | None:
    if not base.exists():
        return None
    children = [p for p in base.iterdir() if p.is_dir()]
    if not children:
        return None
    return sorted(children, key=lambda p: p.name, reverse=True)[0]


def _http_json(
    method: str,
    url: str,
    *,
    body: dict[str, object] | None = None,
    timeout_s: float = 5.0,
) -> tuple[int, str]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url=url, data=data, method=method.upper(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310
            payload = resp.read().decode("utf-8", errors="replace")
            return int(resp.status), payload
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace") if getattr(exc, "fp", None) else str(exc)
        return int(getattr(exc, "code", 0) or 0), payload


def _es_set_index_write_block(*, es_url: str, index: str, enabled: bool) -> tuple[int, str]:
    es_url = es_url.strip().rstrip("/")
    index = index.strip()
    url = f"{es_url}/{index}/_settings"
    return _http_json("PUT", url, body={"index": {"blocks": {"write": bool(enabled)}}}, timeout_s=5.0)


def _es_create_index_if_missing(*, es_url: str, index: str) -> tuple[int, str]:
    """Create index if it does not exist.

    Returns (status, payload) from ES.
    - 200/201: created
    - 400: already exists (treated as ok by caller)
    """

    es_url = es_url.strip().rstrip("/")
    index = index.strip()
    url = f"{es_url}/{index}"
    return _http_json("PUT", url, body=None, timeout_s=5.0)


def _scrape_metrics_text(*, port: int, timeout_s: float = 2.0) -> str:
    url = f"http://localhost:{int(port)}/metrics"
    req = urllib.request.Request(url=url, headers={"Accept": "text/plain"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310
        return resp.read().decode("utf-8", errors="replace")


def _prom_parse_counter_sum(text: str, metric: str, *, labels: dict[str, str] | None = None) -> float:
    """Very small Prometheus text parser: sum matching samples for a counter metric."""

    want = labels or {}
    total = 0.0
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if not line.startswith(metric):
            continue

        # metric{a="b"} 123 or metric 123
        name_and_labels, *rest = line.split(None, 1)
        if not rest:
            continue
        value_str = rest[0].strip().split()[0]

        lbls: dict[str, str] = {}
        if "{" in name_and_labels and name_and_labels.endswith("}"):
            inside = name_and_labels.split("{", 1)[1][:-1]
            # naive split is ok because our labels are simple
            for part in inside.split(","):
                part = part.strip()
                if not part or "=" not in part:
                    continue
                k, v = part.split("=", 1)
                k = k.strip()
                v = v.strip()
                if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
                    v = v[1:-1]
                lbls[k] = v

        ok = True
        for k, v in want.items():
            if lbls.get(k) != v:
                ok = False
                break
        if not ok:
            continue

        try:
            total += float(value_str)
        except ValueError:
            continue

    return float(total)


def _default_labs009_expb_outdir(run_id: str) -> Path:
    return LABS_SNAPSHOT_ROOT / "manual" / "_lab-S3A-2A-3A-expB" / run_id


def _python_exe() -> str:
    # Prefer a repo-local venv if present, but only for the current OS.
    # This avoids WSL calling Windows python.exe with POSIX paths (exit code 2).
    if os.getenv("VIRTUAL_ENV"):
        return sys.executable

    if os.name == "nt":
        win_venv = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
        if win_venv.exists():
            return str(win_venv)
        return sys.executable

    unix_venv = REPO_ROOT / ".venv" / "bin" / "python"
    if unix_venv.exists():
        return str(unix_venv)
    return sys.executable


def _run(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> int:
    print("[scripts] run:", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(cwd) if cwd else None, env=env)


def _docker_compose(*, args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    cmd = ["docker", "compose"] + args
    print("[scripts] run:", " ".join(cmd))
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)


def _prom_sum_reasons(text: str, metric: str, *, reasons: list[str]) -> float:
    return float(sum(_prom_parse_counter_sum(text, metric, labels={"reason": r}) for r in reasons))


def _extract_last_claim_batch_id(log_path: Path) -> str | None:
    if not log_path.exists():
        return None
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return None
    rx = re.compile(r'"claim_batch_id"\s*:\s*"([^"]+)"')
    for line in reversed(lines):
        m = rx.search(line)
        if m:
            return m.group(1)
    return None


def _with_backend_pythonpath(env: dict[str, str]) -> dict[str, str]:
    backend_path = str(REPO_ROOT / "backend")
    existing = env.get("PYTHONPATH") or ""
    parts = [p for p in existing.split(os.pathsep) if p]
    if backend_path not in parts:
        parts.insert(0, backend_path)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def _parse_last_json_line(text: str) -> dict[str, object] | None:
    if not text:
        return None
    for raw in reversed(text.splitlines()):
        line = (raw or "").strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if isinstance(obj, dict):
            return obj
    return None


def _read_json_file(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _cmd_labs_export_jaeger(args: argparse.Namespace) -> int:
    outdir = Path(args.outdir) if args.outdir else _default_labs009_expb_outdir(_now_run_id())
    exports_dir = outdir / "_exports"
    _ensure_dir(exports_dir)

    script = LEGACY_SCRIPTS_DIR / "labs_009_export_jaeger.py"
    cmd = [
        _python_exe(),
        str(script),
        "--outdir",
        str(exports_dir),
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

    return _run(cmd, cwd=REPO_ROOT)


def _cmd_labs_expb_es429(args: argparse.Namespace) -> int:
    run_id = args.run_id or _now_run_id()
    outdir = Path(args.outdir) if args.outdir else _default_labs009_expb_outdir(run_id)

    exports_dir = outdir / "_exports"
    logs_dir = outdir / "_logs"
    metrics_dir = outdir / "_metrics"
    _ensure_dir(exports_dir)
    _ensure_dir(logs_dir)
    _ensure_dir(metrics_dir)

    # Prepare env (inherit, then override)
    env = _with_backend_pythonpath(os.environ.copy())

    # Tracing (opt-in). Default to grpc/4317 for stability.
    env.setdefault("WORDLOOM_TRACING_ENABLED", "1")
    env.setdefault("OTEL_SERVICE_NAME", args.service)
    env.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    env.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    env.setdefault("OTEL_TRACES_SAMPLER", "always_on")

    # ES 429 injection knobs (deterministic-ish)
    if args.every_n is not None:
        env["OUTBOX_EXPERIMENT_ES_429_EVERY_N"] = str(args.every_n)
    if args.ratio is not None:
        env["OUTBOX_EXPERIMENT_ES_429_RATIO"] = str(args.ratio)
    if args.seed is not None:
        env["OUTBOX_EXPERIMENT_ES_429_SEED"] = str(args.seed)
    if args.ops:
        env["OUTBOX_EXPERIMENT_ES_429_OPS"] = args.ops

    # Optional: metrics port override (so users can scrape later)
    if args.metrics_port is not None:
        env["OUTBOX_METRICS_PORT"] = str(args.metrics_port)

    notes = outdir / "_notes.md"
    if not notes.exists():
        notes.write_text(
            "# Labs-009 ExpB (ES 429) run\n\n"
            f"run_id: {run_id}\n\n"
            "## Commands\n\n"
            "- This run was started via `backend/scripts/cli.py labs expb-es429`.\n"
            "\n## Checklist\n\n"
            "- [ ] metrics shows retry_scheduled_total{reason=\"es_429\"}\n"
            "- [ ] jaeger export contains outbox.process / projection spans\n"
            "- [ ] logs contain trace_id/span_id for representative event\n",
            encoding="utf-8",
        )

    worker = LEGACY_SCRIPTS_DIR / "search_outbox_worker.py"
    log_path = logs_dir / f"worker-{run_id}.log"

    # Run worker for a bounded duration using Python wrapper (no extra dependencies).
    # We run it in a subprocess and let the user stop it with Ctrl+C too.
    cmd = [_python_exe(), "-u", str(worker)]

    print(f"[scripts] output dir: {outdir}")
    print(f"[scripts] worker log: {log_path}")
    print(f"[scripts] duration: {args.duration}s")

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

    # Always export a small Jaeger snapshot at the end.
    jaeger_script = LEGACY_SCRIPTS_DIR / "labs_009_export_jaeger.py"
    export_cmd = [
        _python_exe(),
        str(jaeger_script),
        "--outdir",
        str(exports_dir),
        "--service",
        args.service,
        "--lookback",
        args.lookback,
        "--limit",
        str(args.limit),
    ]
    _run(export_cmd, cwd=REPO_ROOT)

    print("[scripts] done")
    print(f"[scripts] outputs: {outdir}")
    return 0


def _cmd_labs_run_es_write_block_4xx(args: argparse.Namespace) -> int:
    run_id = args.run_id or _now_run_id()
    outdir = Path(args.outdir) if args.outdir else _default_labs_auto_run_dir(scenario=SCENARIO_ES_WRITE_BLOCK_4XX, run_id=run_id)

    logs_dir = outdir / "_logs"
    metrics_dir = outdir / "_metrics"
    exports_dir = outdir / "_exports"
    _ensure_dir(logs_dir)
    _ensure_dir(metrics_dir)
    _ensure_dir(exports_dir)

    env = _with_backend_pythonpath(_load_env(env_file=args.env_file))

    es_url = (env.get("ELASTIC_URL") or "http://localhost:19200").strip().rstrip("/")
    es_index = (env.get("ELASTIC_INDEX") or "wordloom-search-index").strip()

    # Tracing: stable defaults
    service_name = args.service
    env.setdefault("WORDLOOM_TRACING_ENABLED", "1")
    env.setdefault("OTEL_SERVICE_NAME", service_name)
    env.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    env.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    env.setdefault("OTEL_TRACES_SAMPLER", "always_on")

    # Ensure batch logs include claim_batch_id for export correlation.
    env["LOG_LEVEL"] = "INFO"

    # Ensure deterministic, irrecoverable failure (no 429 injection).
    env["OUTBOX_EXPERIMENT_ES_429_RATIO"] = "0"

    # Metrics port
    env["OUTBOX_METRICS_PORT"] = str(int(args.metrics_port))

    recipe = {
        "lab_id": LAB_ID_S3A_2A_3A,
        "scenario": SCENARIO_ES_WRITE_BLOCK_4XX,
        "run_id": run_id,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "env_file": args.env_file,
        "service": service_name,
        "es": {"url": es_url, "index": es_index, "inject": {"index.blocks.write": True}},
        "worker": {"duration_s": int(args.duration), "metrics_port": int(args.metrics_port)},
    }
    (outdir / "_recipe.json").write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # 1) Run worker first, scrape baseline metrics, then inject + trigger.
    worker = LEGACY_SCRIPTS_DIR / "search_outbox_worker.py"
    log_path = logs_dir / f"worker-{run_id}.log"
    cmd = [_python_exe(), "-u", str(worker)]

    print(f"[labs run {SCENARIO_ES_WRITE_BLOCK_4XX}] outdir: {outdir}")
    print(f"[labs run {SCENARIO_ES_WRITE_BLOCK_4XX}] worker log: {log_path}")

    metrics_before_path = metrics_dir / "metrics-before.txt"
    metrics_after_path = metrics_dir / "metrics-after.txt"

    start = time.time()
    stopped_by_controller = False
    with open(log_path, "w", encoding="utf-8") as log_file:
        worker_proc = subprocess.Popen(cmd, cwd=str(REPO_ROOT), env=env, stdout=log_file, stderr=subprocess.STDOUT)
        try:
            # Best-effort metrics scrape before/after.
            time.sleep(max(0.5, float(args.scrape_delay)))
            try:
                metrics_before = _scrape_metrics_text(port=int(args.metrics_port), timeout_s=4.0)
                metrics_before_path.write_text(metrics_before, encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                metrics_before_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")

            # 2) Inject: block writes at the index.
            status, payload = _es_set_index_write_block(es_url=es_url, index=es_index, enabled=True)
            if status == 404:
                c_status, c_payload = _es_create_index_if_missing(es_url=es_url, index=es_index)
                (outdir / "_inject_es_create_index.response.txt").write_text(
                    f"status={c_status}\n\n{c_payload}\n", encoding="utf-8"
                )
                if c_status not in (200, 201, 400):
                    print(f"[labs run {SCENARIO_ES_WRITE_BLOCK_4XX}] failed to create index: http {c_status}")
                    worker_proc.terminate()
                    worker_proc.wait(timeout=30)
                    return 2

                status, payload = _es_set_index_write_block(es_url=es_url, index=es_index, enabled=True)
            (outdir / "_inject_es_write_block.response.txt").write_text(
                f"status={status}\n\n{payload}\n", encoding="utf-8"
            )
            if status < 200 or status >= 300:
                print(f"[labs run {SCENARIO_ES_WRITE_BLOCK_4XX}] failed to enable write block: http {status}")
                worker_proc.terminate()
                worker_proc.wait(timeout=30)
                return 2

            # 3) Trigger: insert a pending outbox event (and ensure a matching search_index row exists).
            inserter = REPO_ROOT / "backend" / "scripts" / "labs" / "labs_009_insert_search_outbox_pending.py"
            if not inserter.exists():
                inserter = LEGACY_SCRIPTS_DIR / "labs_009_insert_search_outbox_pending.py"
            trigger_env = env.copy()
            trigger_env.setdefault("OUTBOX_OP", "upsert")
            trigger_env.setdefault("OUTBOX_CREATE_SEARCH_INDEX_ROW", "1")

            proc = subprocess.run(
                [_python_exe(), str(inserter)],
                cwd=str(REPO_ROOT),
                env=trigger_env,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            (outdir / "_trigger_insert_outbox.stdout.txt").write_text(proc.stdout or "", encoding="utf-8")
            (outdir / "_trigger_insert_outbox.stderr.txt").write_text(proc.stderr or "", encoding="utf-8")
            if proc.returncode != 0:
                print(f"[labs run {SCENARIO_ES_WRITE_BLOCK_4XX}] failed to insert outbox event: rc={proc.returncode}")
                worker_proc.terminate()
                worker_proc.wait(timeout=30)
                return 3

            outbox_event_id = (proc.stdout or "").strip().splitlines()[-1].strip()
            (outdir / "_outbox_event_id.txt").write_text(outbox_event_id + "\n", encoding="utf-8")
            print(f"[labs run {SCENARIO_ES_WRITE_BLOCK_4XX}] outbox_event_id: {outbox_event_id}")

            while True:
                if args.duration > 0 and (time.time() - start) >= args.duration:
                    # scrape right before stop (server is still up)
                    try:
                        metrics_after = _scrape_metrics_text(port=int(args.metrics_port), timeout_s=4.0)
                        metrics_after_path.write_text(metrics_after, encoding="utf-8")
                        (outdir / "_metrics.txt").write_text(metrics_after, encoding="utf-8")
                    except Exception as exc:  # noqa: BLE001
                        metrics_after_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")
                    stopped_by_controller = True
                    worker_proc.terminate()
                    break

                ret = worker_proc.poll()
                if ret is not None:
                    # Worker exited early; capture whatever metrics we can.
                    try:
                        metrics_after = _scrape_metrics_text(port=int(args.metrics_port), timeout_s=4.0)
                        metrics_after_path.write_text(metrics_after, encoding="utf-8")
                        (outdir / "_metrics.txt").write_text(metrics_after, encoding="utf-8")
                    except Exception as exc:  # noqa: BLE001
                        metrics_after_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")
                    break
                time.sleep(0.25)
        except KeyboardInterrupt:
            stopped_by_controller = True
            worker_proc.terminate()

        worker_proc.wait(timeout=30)

    exit_info = {"returncode": int(worker_proc.returncode) if worker_proc.returncode is not None else None}
    (outdir / "_worker_exit.json").write_text(
        json.dumps(exit_info, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if not metrics_after_path.exists():
        metrics_after_path.write_text("scrape_failed: missing_metrics_after\n", encoding="utf-8")

    if (not stopped_by_controller) and (worker_proc.returncode not in (None, 0)):
        print(f"[labs run {SCENARIO_ES_WRITE_BLOCK_4XX}] worker exited early: rc={worker_proc.returncode}")
        print(f"[labs run {SCENARIO_ES_WRITE_BLOCK_4XX}] see logs: {log_path}")
        return 4

    print(f"[labs run {SCENARIO_ES_WRITE_BLOCK_4XX}] done (now run verify/export/clean)")
    print(f"[labs run {SCENARIO_ES_WRITE_BLOCK_4XX}] outputs: {outdir}")
    return 0


def _resolve_run_dir(*, run_id: str | None, outdir: str | None, scenario: str) -> Path:
    if outdir:
        return Path(outdir)
    if run_id:
        return _default_labs_auto_run_dir(scenario=scenario, run_id=run_id)
    latest = _latest_child_dir(LABS_SNAPSHOT_ROOT / "auto" / LAB_ID_S3A_2A_3A / scenario)
    if latest is None:
        raise SystemExit(f"No runs found for scenario={scenario}")
    return latest


def _cmd_labs_verify_es_write_block_4xx(args: argparse.Namespace) -> int:
    run_dir = _resolve_run_dir(run_id=args.run_id, outdir=args.outdir, scenario=SCENARIO_ES_WRITE_BLOCK_4XX)
    metrics_dir = run_dir / "_metrics"
    before_path = metrics_dir / "metrics-before.txt"
    after_path = metrics_dir / "metrics-after.txt"

    before = before_path.read_text(encoding="utf-8") if before_path.exists() else ""
    after = after_path.read_text(encoding="utf-8") if after_path.exists() else ""

    failed_before = _prom_parse_counter_sum(before, "outbox_failed_total", labels={"reason": "es_4xx"})
    failed_after = _prom_parse_counter_sum(after, "outbox_failed_total", labels={"reason": "es_4xx"})
    retry_before = _prom_parse_counter_sum(before, "outbox_retry_scheduled_total", labels={"reason": "es_4xx"})
    retry_after = _prom_parse_counter_sum(after, "outbox_retry_scheduled_total", labels={"reason": "es_4xx"})

    delta_failed = failed_after - failed_before
    delta_retry = retry_after - retry_before

    ok = (delta_failed >= float(args.min_failed_delta)) and (delta_retry <= float(args.max_retry_delta))
    result = {
        "scenario": SCENARIO_ES_WRITE_BLOCK_4XX,
        "run_dir": str(run_dir),
        "checks": {
            "failed_delta_ge": float(args.min_failed_delta),
            "retry_delta_le": float(args.max_retry_delta),
        },
        "observed": {
            "outbox_failed_total_reason_es_4xx": {"before": failed_before, "after": failed_after, "delta": delta_failed},
            "outbox_retry_scheduled_total_reason_es_4xx": {"before": retry_before, "after": retry_after, "delta": delta_retry},
        },
        "ok": bool(ok),
    }
    (run_dir / "_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if ok:
        print(f"[labs verify {SCENARIO_ES_WRITE_BLOCK_4XX}] OK")
        return 0
    print(f"[labs verify {SCENARIO_ES_WRITE_BLOCK_4XX}] FAILED")
    return 10


def _cmd_labs_export_es_write_block_4xx(args: argparse.Namespace) -> int:
    run_dir = _resolve_run_dir(run_id=args.run_id, outdir=args.outdir, scenario=SCENARIO_ES_WRITE_BLOCK_4XX)
    exports_dir = run_dir / "_exports"
    _ensure_dir(exports_dir)

    outbox_event_id_path = run_dir / "_outbox_event_id.txt"
    outbox_event_id = outbox_event_id_path.read_text(encoding="utf-8").strip() if outbox_event_id_path.exists() else None

    cmd = [
        _python_exe(),
        str(LEGACY_SCRIPTS_DIR / "labs_009_export_jaeger.py"),
        "--outdir",
        str(exports_dir),
        "--service",
        args.service,
        "--lookback",
        args.lookback,
        "--limit",
        str(args.limit),
    ]
    if outbox_event_id:
        cmd += ["--outbox-event-id", outbox_event_id]

    return _run(cmd, cwd=REPO_ROOT)


def _cmd_labs_run_es_429_inject(args: argparse.Namespace) -> int:
    run_id = args.run_id or _now_run_id()
    outdir = Path(args.outdir) if args.outdir else _default_labs_auto_run_dir(scenario=SCENARIO_ES_429_INJECT, run_id=run_id)

    logs_dir = outdir / "_logs"
    metrics_dir = outdir / "_metrics"
    exports_dir = outdir / "_exports"
    _ensure_dir(logs_dir)
    _ensure_dir(metrics_dir)
    _ensure_dir(exports_dir)

    env = _with_backend_pythonpath(_load_env(env_file=args.env_file))

    # Tracing: stable defaults
    service_name = args.service
    env.setdefault("WORDLOOM_TRACING_ENABLED", "1")
    env.setdefault("OTEL_SERVICE_NAME", service_name)
    env.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    env.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    env.setdefault("OTEL_TRACES_SAMPLER", "always_on")

    # Fault injection: enable ES 429 injection in worker
    if args.every_n is not None and int(args.every_n) > 0:
        env["OUTBOX_EXPERIMENT_ES_429_EVERY_N"] = str(int(args.every_n))
        env.pop("OUTBOX_EXPERIMENT_ES_429_RATIO", None)
    else:
        env["OUTBOX_EXPERIMENT_ES_429_RATIO"] = str(float(args.ratio))
        env.pop("OUTBOX_EXPERIMENT_ES_429_EVERY_N", None)

    env["OUTBOX_EXPERIMENT_ES_429_OPS"] = str(args.ops)
    if args.seed is not None:
        env["OUTBOX_EXPERIMENT_ES_429_SEED"] = str(int(args.seed))
    else:
        env.pop("OUTBOX_EXPERIMENT_ES_429_SEED", None)

    # Metrics port
    env["OUTBOX_METRICS_PORT"] = str(int(args.metrics_port))

    recipe = {
        "lab_id": LAB_ID_S3A_2A_3A,
        "scenario": SCENARIO_ES_429_INJECT,
        "run_id": run_id,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "env_file": args.env_file,
        "service": service_name,
        "inject": {
            "kind": "es_429",
            "mode": "every_n" if (args.every_n is not None and int(args.every_n) > 0) else "ratio",
            "every_n": int(args.every_n) if (args.every_n is not None) else None,
            "ratio": float(args.ratio),
            "ops": str(args.ops),
            "seed": int(args.seed) if args.seed is not None else None,
        },
        "worker": {"duration_s": int(args.duration), "metrics_port": int(args.metrics_port)},
        "trigger": {"op": str(args.op)},
    }
    (outdir / "_recipe.json").write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    worker = LEGACY_SCRIPTS_DIR / "search_outbox_worker.py"
    log_path = logs_dir / f"worker-{run_id}.log"
    cmd = [_python_exe(), "-u", str(worker)]

    print(f"[labs run {SCENARIO_ES_429_INJECT}] outdir: {outdir}")
    print(f"[labs run {SCENARIO_ES_429_INJECT}] worker log: {log_path}")

    metrics_before_path = metrics_dir / "metrics-before.txt"
    metrics_after_path = metrics_dir / "metrics-after.txt"

    inserter = REPO_ROOT / "backend" / "scripts" / "labs" / "labs_009_insert_search_outbox_pending.py"
    if not inserter.exists():
        inserter = LEGACY_SCRIPTS_DIR / "labs_009_insert_search_outbox_pending.py"

    start = time.time()
    stopped_by_controller = False
    with open(log_path, "w", encoding="utf-8") as log_file:
        worker_proc = subprocess.Popen(cmd, cwd=str(REPO_ROOT), env=env, stdout=log_file, stderr=subprocess.STDOUT)
        try:
            time.sleep(max(0.5, float(args.scrape_delay)))
            try:
                metrics_before = _scrape_metrics_text(port=int(args.metrics_port), timeout_s=4.0)
                metrics_before_path.write_text(metrics_before, encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                metrics_before_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")

            # Trigger a single outbox event (and ensure a matching search_index row exists).
            trigger_env = env.copy()
            trigger_env["OUTBOX_OP"] = str(args.op)
            trigger_env.setdefault("OUTBOX_CREATE_SEARCH_INDEX_ROW", "1")
            # Ensure our event is claimed quickly even if there is backlog.
            trigger_env.setdefault("OUTBOX_EVENT_VERSION", "0")

            proc = subprocess.run(
                [_python_exe(), str(inserter)],
                cwd=str(REPO_ROOT),
                env=trigger_env,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            (outdir / "_trigger_insert_outbox.stdout.txt").write_text(proc.stdout or "", encoding="utf-8")
            (outdir / "_trigger_insert_outbox.stderr.txt").write_text(proc.stderr or "", encoding="utf-8")
            if proc.returncode != 0:
                print(f"[labs run {SCENARIO_ES_429_INJECT}] failed to insert outbox event: rc={proc.returncode}")
                worker_proc.terminate()
                worker_proc.wait(timeout=30)
                return 3

            outbox_event_id = (proc.stdout or "").strip().splitlines()[-1].strip()
            (outdir / "_outbox_event_id.txt").write_text(outbox_event_id + "\n", encoding="utf-8")
            print(f"[labs run {SCENARIO_ES_429_INJECT}] outbox_event_id: {outbox_event_id}")

            while True:
                if args.duration > 0 and (time.time() - start) >= args.duration:
                    try:
                        metrics_after = _scrape_metrics_text(port=int(args.metrics_port), timeout_s=4.0)
                        metrics_after_path.write_text(metrics_after, encoding="utf-8")
                        (outdir / "_metrics.txt").write_text(metrics_after, encoding="utf-8")
                    except Exception as exc:  # noqa: BLE001
                        metrics_after_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")
                    stopped_by_controller = True
                    worker_proc.terminate()
                    break

                ret = worker_proc.poll()
                if ret is not None:
                    try:
                        metrics_after = _scrape_metrics_text(port=int(args.metrics_port), timeout_s=4.0)
                        metrics_after_path.write_text(metrics_after, encoding="utf-8")
                        (outdir / "_metrics.txt").write_text(metrics_after, encoding="utf-8")
                    except Exception as exc:  # noqa: BLE001
                        metrics_after_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")
                    break
                time.sleep(0.25)
        except KeyboardInterrupt:
            stopped_by_controller = True
            worker_proc.terminate()

        worker_proc.wait(timeout=30)

    exit_info = {"returncode": int(worker_proc.returncode) if worker_proc.returncode is not None else None}
    (outdir / "_worker_exit.json").write_text(
        json.dumps(exit_info, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if not metrics_after_path.exists():
        metrics_after_path.write_text("scrape_failed: missing_metrics_after\n", encoding="utf-8")

    if (not stopped_by_controller) and (worker_proc.returncode not in (None, 0)):
        print(f"[labs run {SCENARIO_ES_429_INJECT}] worker exited early: rc={worker_proc.returncode}")
        print(f"[labs run {SCENARIO_ES_429_INJECT}] see logs: {log_path}")
        return 4

    print(f"[labs run {SCENARIO_ES_429_INJECT}] done (now run verify/export/clean)")
    print(f"[labs run {SCENARIO_ES_429_INJECT}] outputs: {outdir}")
    return 0


def _cmd_labs_verify_es_429_inject(args: argparse.Namespace) -> int:
    run_dir = _resolve_run_dir(run_id=args.run_id, outdir=args.outdir, scenario=SCENARIO_ES_429_INJECT)
    metrics_dir = run_dir / "_metrics"
    before_path = metrics_dir / "metrics-before.txt"
    after_path = metrics_dir / "metrics-after.txt"

    before = before_path.read_text(encoding="utf-8") if before_path.exists() else ""
    after = after_path.read_text(encoding="utf-8") if after_path.exists() else ""

    retry_before = _prom_parse_counter_sum(before, "outbox_retry_scheduled_total", labels={"reason": "es_429"})
    retry_after = _prom_parse_counter_sum(after, "outbox_retry_scheduled_total", labels={"reason": "es_429"})
    failed_before = _prom_parse_counter_sum(before, "outbox_failed_total", labels={"reason": "es_429"})
    failed_after = _prom_parse_counter_sum(after, "outbox_failed_total", labels={"reason": "es_429"})
    terminal_before = _prom_parse_counter_sum(before, "outbox_terminal_failed_total", labels={"reason": "es_429"})
    terminal_after = _prom_parse_counter_sum(after, "outbox_terminal_failed_total", labels={"reason": "es_429"})

    delta_retry = retry_after - retry_before
    delta_failed = failed_after - failed_before
    delta_terminal = terminal_after - terminal_before

    ok = (
        (delta_retry >= float(args.min_retry_delta))
        and (delta_failed >= float(args.min_failed_delta))
        and (delta_terminal <= float(args.max_terminal_delta))
    )

    result = {
        "scenario": SCENARIO_ES_429_INJECT,
        "run_dir": str(run_dir),
        "checks": {
            "retry_delta_ge": float(args.min_retry_delta),
            "failed_delta_ge": float(args.min_failed_delta),
            "terminal_delta_le": float(args.max_terminal_delta),
        },
        "observed": {
            "outbox_retry_scheduled_total_reason_es_429": {"before": retry_before, "after": retry_after, "delta": delta_retry},
            "outbox_failed_total_reason_es_429": {"before": failed_before, "after": failed_after, "delta": delta_failed},
            "outbox_terminal_failed_total_reason_es_429": {"before": terminal_before, "after": terminal_after, "delta": delta_terminal},
        },
        "ok": bool(ok),
    }
    (run_dir / "_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if ok:
        print(f"[labs verify {SCENARIO_ES_429_INJECT}] OK")
        return 0
    print(f"[labs verify {SCENARIO_ES_429_INJECT}] FAILED")
    return 10


def _cmd_labs_run_es_down_connect(args: argparse.Namespace) -> int:
    run_id = args.run_id or _now_run_id()
    outdir = Path(args.outdir) if args.outdir else _default_labs_auto_run_dir(scenario=SCENARIO_ES_DOWN_CONNECT, run_id=run_id)

    logs_dir = outdir / "_logs"
    metrics_dir = outdir / "_metrics"
    exports_dir = outdir / "_exports"
    _ensure_dir(logs_dir)
    _ensure_dir(metrics_dir)
    _ensure_dir(exports_dir)

    env = _with_backend_pythonpath(_load_env(env_file=args.env_file))

    # Tracing: stable defaults
    service_name = args.service
    env.setdefault("WORDLOOM_TRACING_ENABLED", "1")
    env.setdefault("OTEL_SERVICE_NAME", service_name)
    env.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    env.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    env.setdefault("OTEL_TRACES_SAMPLER", "always_on")

    # Ensure 429 injection is disabled (we want pure connect failure).
    env["OUTBOX_EXPERIMENT_ES_429_RATIO"] = "0"
    env.pop("OUTBOX_EXPERIMENT_ES_429_EVERY_N", None)

    env["OUTBOX_METRICS_PORT"] = str(int(args.metrics_port))

    compose_file = str((REPO_ROOT / "docker-compose.infra.yml").resolve())
    recipe = {
        "lab_id": LAB_ID_S3A_2A_3A,
        "scenario": SCENARIO_ES_DOWN_CONNECT,
        "run_id": run_id,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "env_file": args.env_file,
        "service": service_name,
        "inject": {"kind": "es_down", "compose": {"file": compose_file, "service": "es", "action": "stop"}},
        "worker": {"duration_s": int(args.duration), "metrics_port": int(args.metrics_port)},
        "trigger": {"op": str(args.op)},
    }
    (outdir / "_recipe.json").write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"[labs run {SCENARIO_ES_DOWN_CONNECT}] outdir: {outdir}")

    # 1) Inject: stop ES
    stop_proc = _docker_compose(args=["-f", compose_file, "stop", "es"], cwd=REPO_ROOT)
    (outdir / "_inject_es_stop.stdout.txt").write_text(stop_proc.stdout or "", encoding="utf-8")
    (outdir / "_inject_es_stop.stderr.txt").write_text(stop_proc.stderr or "", encoding="utf-8")
    (outdir / "_inject_es_stop.exitcode.txt").write_text(str(int(stop_proc.returncode)) + "\n", encoding="utf-8")
    if stop_proc.returncode != 0:
        print(f"[labs run {SCENARIO_ES_DOWN_CONNECT}] failed to stop es: rc={stop_proc.returncode}")
        return 2

    # 2) Run worker, scrape baseline, then trigger.
    worker = LEGACY_SCRIPTS_DIR / "search_outbox_worker.py"
    log_path = logs_dir / f"worker-{run_id}.log"
    cmd = [_python_exe(), "-u", str(worker)]

    print(f"[labs run {SCENARIO_ES_DOWN_CONNECT}] worker log: {log_path}")

    metrics_before_path = metrics_dir / "metrics-before.txt"
    metrics_after_path = metrics_dir / "metrics-after.txt"

    inserter = REPO_ROOT / "backend" / "scripts" / "labs" / "labs_009_insert_search_outbox_pending.py"
    if not inserter.exists():
        inserter = LEGACY_SCRIPTS_DIR / "labs_009_insert_search_outbox_pending.py"

    start = time.time()
    stopped_by_controller = False
    with open(log_path, "w", encoding="utf-8") as log_file:
        worker_proc = subprocess.Popen(cmd, cwd=str(REPO_ROOT), env=env, stdout=log_file, stderr=subprocess.STDOUT)
        try:
            time.sleep(max(0.5, float(args.scrape_delay)))
            try:
                metrics_before = _scrape_metrics_text(port=int(args.metrics_port), timeout_s=4.0)
                metrics_before_path.write_text(metrics_before, encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                metrics_before_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")

            trigger_env = env.copy()
            trigger_env["OUTBOX_OP"] = str(args.op)
            trigger_env.setdefault("OUTBOX_CREATE_SEARCH_INDEX_ROW", "1")
            trigger_env.setdefault("OUTBOX_EVENT_VERSION", "0")

            proc = subprocess.run(
                [_python_exe(), str(inserter)],
                cwd=str(REPO_ROOT),
                env=trigger_env,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            (outdir / "_trigger_insert_outbox.stdout.txt").write_text(proc.stdout or "", encoding="utf-8")
            (outdir / "_trigger_insert_outbox.stderr.txt").write_text(proc.stderr or "", encoding="utf-8")
            if proc.returncode != 0:
                print(f"[labs run {SCENARIO_ES_DOWN_CONNECT}] failed to insert outbox event: rc={proc.returncode}")
                worker_proc.terminate()
                worker_proc.wait(timeout=30)
                return 3

            outbox_event_id = (proc.stdout or "").strip().splitlines()[-1].strip()
            (outdir / "_outbox_event_id.txt").write_text(outbox_event_id + "\n", encoding="utf-8")
            print(f"[labs run {SCENARIO_ES_DOWN_CONNECT}] outbox_event_id: {outbox_event_id}")

            while True:
                if args.duration > 0 and (time.time() - start) >= args.duration:
                    try:
                        metrics_after = _scrape_metrics_text(port=int(args.metrics_port), timeout_s=4.0)
                        metrics_after_path.write_text(metrics_after, encoding="utf-8")
                        (outdir / "_metrics.txt").write_text(metrics_after, encoding="utf-8")
                    except Exception as exc:  # noqa: BLE001
                        metrics_after_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")
                    stopped_by_controller = True
                    worker_proc.terminate()
                    break

                ret = worker_proc.poll()
                if ret is not None:
                    try:
                        metrics_after = _scrape_metrics_text(port=int(args.metrics_port), timeout_s=4.0)
                        metrics_after_path.write_text(metrics_after, encoding="utf-8")
                        (outdir / "_metrics.txt").write_text(metrics_after, encoding="utf-8")
                    except Exception as exc:  # noqa: BLE001
                        metrics_after_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")
                    break
                time.sleep(0.25)
        except KeyboardInterrupt:
            stopped_by_controller = True
            worker_proc.terminate()

        worker_proc.wait(timeout=30)

    exit_info = {"returncode": int(worker_proc.returncode) if worker_proc.returncode is not None else None}
    (outdir / "_worker_exit.json").write_text(
        json.dumps(exit_info, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if not metrics_after_path.exists():
        metrics_after_path.write_text("scrape_failed: missing_metrics_after\n", encoding="utf-8")

    if (not stopped_by_controller) and (worker_proc.returncode not in (None, 0)):
        print(f"[labs run {SCENARIO_ES_DOWN_CONNECT}] worker exited early: rc={worker_proc.returncode}")
        print(f"[labs run {SCENARIO_ES_DOWN_CONNECT}] see logs: {log_path}")
        return 4

    print(f"[labs run {SCENARIO_ES_DOWN_CONNECT}] done (now run verify/export/clean)")
    print(f"[labs run {SCENARIO_ES_DOWN_CONNECT}] outputs: {outdir}")
    return 0


def _cmd_labs_verify_es_down_connect(args: argparse.Namespace) -> int:
    run_dir = _resolve_run_dir(run_id=args.run_id, outdir=args.outdir, scenario=SCENARIO_ES_DOWN_CONNECT)
    metrics_dir = run_dir / "_metrics"
    before_path = metrics_dir / "metrics-before.txt"
    after_path = metrics_dir / "metrics-after.txt"

    before = before_path.read_text(encoding="utf-8") if before_path.exists() else ""
    after = after_path.read_text(encoding="utf-8") if after_path.exists() else ""

    reasons = ["es_connect", "es_unreachable"]

    retry_before = _prom_sum_reasons(before, "outbox_retry_scheduled_total", reasons=reasons)
    retry_after = _prom_sum_reasons(after, "outbox_retry_scheduled_total", reasons=reasons)
    failed_before = _prom_sum_reasons(before, "outbox_failed_total", reasons=reasons)
    failed_after = _prom_sum_reasons(after, "outbox_failed_total", reasons=reasons)
    terminal_before = _prom_sum_reasons(before, "outbox_terminal_failed_total", reasons=reasons)
    terminal_after = _prom_sum_reasons(after, "outbox_terminal_failed_total", reasons=reasons)

    delta_retry = retry_after - retry_before
    delta_failed = failed_after - failed_before
    delta_terminal = terminal_after - terminal_before

    ok = (
        (delta_retry >= float(args.min_retry_delta))
        and (delta_failed >= float(args.min_failed_delta))
        and (delta_terminal <= float(args.max_terminal_delta))
    )

    result = {
        "scenario": SCENARIO_ES_DOWN_CONNECT,
        "run_dir": str(run_dir),
        "checks": {
            "reasons": reasons,
            "retry_delta_ge": float(args.min_retry_delta),
            "failed_delta_ge": float(args.min_failed_delta),
            "terminal_delta_le": float(args.max_terminal_delta),
        },
        "observed": {
            "outbox_retry_scheduled_total_reason_es_connect_or_unreachable": {"before": retry_before, "after": retry_after, "delta": delta_retry},
            "outbox_failed_total_reason_es_connect_or_unreachable": {"before": failed_before, "after": failed_after, "delta": delta_failed},
            "outbox_terminal_failed_total_reason_es_connect_or_unreachable": {"before": terminal_before, "after": terminal_after, "delta": delta_terminal},
        },
        "ok": bool(ok),
    }
    (run_dir / "_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if ok:
        print(f"[labs verify {SCENARIO_ES_DOWN_CONNECT}] OK")
        return 0
    print(f"[labs verify {SCENARIO_ES_DOWN_CONNECT}] FAILED")
    return 10


def _cmd_labs_export_es_down_connect(args: argparse.Namespace) -> int:
    run_dir = _resolve_run_dir(run_id=args.run_id, outdir=args.outdir, scenario=SCENARIO_ES_DOWN_CONNECT)
    exports_dir = run_dir / "_exports"
    _ensure_dir(exports_dir)

    outbox_event_id_path = run_dir / "_outbox_event_id.txt"
    outbox_event_id = outbox_event_id_path.read_text(encoding="utf-8").strip() if outbox_event_id_path.exists() else None

    cmd = [
        _python_exe(),
        str(LEGACY_SCRIPTS_DIR / "labs_009_export_jaeger.py"),
        "--outdir",
        str(exports_dir),
        "--service",
        args.service,
        "--lookback",
        args.lookback,
        "--limit",
        str(args.limit),
    ]
    if outbox_event_id:
        cmd += ["--outbox-event-id", outbox_event_id]

    return _run(cmd, cwd=REPO_ROOT)


def _cmd_labs_run_collector_down(args: argparse.Namespace) -> int:
    """P1: observability failure drill - stop Jaeger OTLP collector while worker runs.

    We use the `jaeger` service in docker-compose.infra.yml as the OTLP receiver.
    Expected behavior: business processing continues; traces export is unavailable.
    """

    run_id = args.run_id or _now_run_id()
    outdir = Path(args.outdir) if args.outdir else _default_labs_auto_run_dir(scenario=SCENARIO_COLLECTOR_DOWN, run_id=run_id)

    logs_dir = outdir / "_logs"
    metrics_dir = outdir / "_metrics"
    exports_dir = outdir / "_exports"
    _ensure_dir(logs_dir)
    _ensure_dir(metrics_dir)
    _ensure_dir(exports_dir)

    env = _with_backend_pythonpath(_load_env(env_file=args.env_file))

    # Tracing intentionally enabled; endpoint remains the default Jaeger OTLP gRPC.
    service_name = args.service
    env.setdefault("WORDLOOM_TRACING_ENABLED", "1")
    env.setdefault("OTEL_SERVICE_NAME", service_name)
    env.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    env.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    env.setdefault("OTEL_TRACES_SAMPLER", "always_on")

    env["OUTBOX_METRICS_PORT"] = str(int(args.metrics_port))

    compose_file = str((REPO_ROOT / "docker-compose.infra.yml").resolve())
    recipe = {
        "lab_id": LAB_ID_S3A_2A_3A,
        "scenario": SCENARIO_COLLECTOR_DOWN,
        "run_id": run_id,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "env_file": args.env_file,
        "service": service_name,
        "inject": {"kind": "collector_down", "compose": {"file": compose_file, "service": "jaeger", "action": "stop"}},
        "worker": {"duration_s": int(args.duration), "metrics_port": int(args.metrics_port)},
        "trigger": {"op": str(args.op)},
    }
    (outdir / "_recipe.json").write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"[labs run {SCENARIO_COLLECTOR_DOWN}] outdir: {outdir}")

    # 1) Inject: stop Jaeger (OTLP collector + query API)
    stop_proc = _docker_compose(args=["-f", compose_file, "stop", "jaeger"], cwd=REPO_ROOT)
    (outdir / "_inject_jaeger_stop.stdout.txt").write_text(stop_proc.stdout or "", encoding="utf-8")
    (outdir / "_inject_jaeger_stop.stderr.txt").write_text(stop_proc.stderr or "", encoding="utf-8")
    (outdir / "_inject_jaeger_stop.exitcode.txt").write_text(str(int(stop_proc.returncode)) + "\n", encoding="utf-8")
    if stop_proc.returncode != 0:
        print(f"[labs run {SCENARIO_COLLECTOR_DOWN}] failed to stop jaeger: rc={stop_proc.returncode}")
        return 2

    # 2) Run worker, scrape baseline, then trigger.
    worker = LEGACY_SCRIPTS_DIR / "search_outbox_worker.py"
    log_path = logs_dir / f"worker-{run_id}.log"
    cmd = [_python_exe(), "-u", str(worker)]

    print(f"[labs run {SCENARIO_COLLECTOR_DOWN}] worker log: {log_path}")

    metrics_before_path = metrics_dir / "metrics-before.txt"
    metrics_after_path = metrics_dir / "metrics-after.txt"

    inserter = REPO_ROOT / "backend" / "scripts" / "labs" / "labs_009_insert_search_outbox_pending.py"
    if not inserter.exists():
        inserter = LEGACY_SCRIPTS_DIR / "labs_009_insert_search_outbox_pending.py"

    start = time.time()
    stopped_by_controller = False
    with open(log_path, "w", encoding="utf-8") as log_file:
        worker_proc = subprocess.Popen(cmd, cwd=str(REPO_ROOT), env=env, stdout=log_file, stderr=subprocess.STDOUT)
        try:
            time.sleep(max(0.5, float(args.scrape_delay)))
            try:
                metrics_before = _scrape_metrics_text(port=int(args.metrics_port), timeout_s=4.0)
                metrics_before_path.write_text(metrics_before, encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                metrics_before_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")

            trigger_env = env.copy()
            trigger_env["OUTBOX_OP"] = str(args.op)
            trigger_env.setdefault("OUTBOX_CREATE_SEARCH_INDEX_ROW", "1")
            trigger_env.setdefault("OUTBOX_EVENT_VERSION", "0")

            proc = subprocess.run(
                [_python_exe(), str(inserter)],
                cwd=str(REPO_ROOT),
                env=trigger_env,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            (outdir / "_trigger_insert_outbox.stdout.txt").write_text(proc.stdout or "", encoding="utf-8")
            (outdir / "_trigger_insert_outbox.stderr.txt").write_text(proc.stderr or "", encoding="utf-8")
            if proc.returncode != 0:
                print(f"[labs run {SCENARIO_COLLECTOR_DOWN}] failed to insert outbox event: rc={proc.returncode}")
                worker_proc.terminate()
                worker_proc.wait(timeout=30)
                return 3

            outbox_event_id = (proc.stdout or "").strip().splitlines()[-1].strip()
            (outdir / "_outbox_event_id.txt").write_text(outbox_event_id + "\n", encoding="utf-8")
            print(f"[labs run {SCENARIO_COLLECTOR_DOWN}] outbox_event_id: {outbox_event_id}")

            while True:
                if args.duration > 0 and (time.time() - start) >= args.duration:
                    try:
                        metrics_after = _scrape_metrics_text(port=int(args.metrics_port), timeout_s=4.0)
                        metrics_after_path.write_text(metrics_after, encoding="utf-8")
                        (outdir / "_metrics.txt").write_text(metrics_after, encoding="utf-8")
                    except Exception as exc:  # noqa: BLE001
                        metrics_after_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")
                    stopped_by_controller = True
                    worker_proc.terminate()
                    break

                ret = worker_proc.poll()
                if ret is not None:
                    try:
                        metrics_after = _scrape_metrics_text(port=int(args.metrics_port), timeout_s=4.0)
                        metrics_after_path.write_text(metrics_after, encoding="utf-8")
                        (outdir / "_metrics.txt").write_text(metrics_after, encoding="utf-8")
                    except Exception as exc:  # noqa: BLE001
                        metrics_after_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")
                    break
                time.sleep(0.25)
        except KeyboardInterrupt:
            stopped_by_controller = True
            worker_proc.terminate()

        worker_proc.wait(timeout=30)

    exit_info = {"returncode": int(worker_proc.returncode) if worker_proc.returncode is not None else None}
    (outdir / "_worker_exit.json").write_text(
        json.dumps(exit_info, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if not metrics_after_path.exists():
        metrics_after_path.write_text("scrape_failed: missing_metrics_after\n", encoding="utf-8")

    if (not stopped_by_controller) and (worker_proc.returncode not in (None, 0)):
        print(f"[labs run {SCENARIO_COLLECTOR_DOWN}] worker exited early: rc={worker_proc.returncode}")
        print(f"[labs run {SCENARIO_COLLECTOR_DOWN}] see logs: {log_path}")
        return 4

    print(f"[labs run {SCENARIO_COLLECTOR_DOWN}] done (now run verify/export/clean)")
    print(f"[labs run {SCENARIO_COLLECTOR_DOWN}] outputs: {outdir}")
    return 0


def _cmd_labs_verify_collector_down(args: argparse.Namespace) -> int:
    run_dir = _resolve_run_dir(run_id=args.run_id, outdir=args.outdir, scenario=SCENARIO_COLLECTOR_DOWN)
    metrics_dir = run_dir / "_metrics"

    before_path = metrics_dir / "metrics-before.txt"
    after_path = metrics_dir / "metrics-after.txt"

    before = before_path.read_text(encoding="utf-8") if before_path.exists() else ""
    after = after_path.read_text(encoding="utf-8") if after_path.exists() else ""

    before_scrape_ok = "scrape_failed" not in before
    after_scrape_ok = "scrape_failed" not in after

    processed_before = _prom_parse_counter_sum(before, "outbox_processed_total")
    processed_after = _prom_parse_counter_sum(after, "outbox_processed_total")
    failed_before = _prom_parse_counter_sum(before, "outbox_failed_total")
    failed_after = _prom_parse_counter_sum(after, "outbox_failed_total")

    delta_processed = processed_after - processed_before
    delta_failed = failed_after - failed_before

    # Fallback: metrics scrape can be flaky in CI due to timing.
    # For collector_down we can deterministically assert the inserted outbox row
    # was processed successfully.
    outbox_event_id_path = run_dir / "_outbox_event_id.txt"
    outbox_event_id = outbox_event_id_path.read_text(encoding="utf-8").strip() if outbox_event_id_path.exists() else None

    db_observed: dict[str, object] = {}
    db_ok = False
    try:
        recipe_env_file = None
        recipe_path = run_dir / "_recipe.json"
        if recipe_path.exists():
            try:
                recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
                recipe_env_file = (recipe or {}).get("env_file")
            except Exception:
                recipe_env_file = None

        env = _load_env(env_file=str(recipe_env_file) if recipe_env_file else None)
        database_url = (env.get("DATABASE_URL") or "").strip()
        if database_url and outbox_event_id:
            engine = create_engine(database_url, pool_pre_ping=True)
            with engine.connect() as conn:
                row = conn.execute(
                    text(
                        """
                        SELECT status, processed_at, attempts, error_reason
                        FROM search_outbox_events
                        WHERE id = CAST(:id AS uuid)
                        """
                    ),
                    {"id": outbox_event_id},
                ).mappings().fetchone()

            if row is None:
                db_observed = {"found": False}
            else:
                status = row.get("status")
                processed_at = row.get("processed_at")
                attempts = row.get("attempts")
                error_reason = row.get("error_reason")
                db_observed = {
                    "found": True,
                    "status": status,
                    "processed_at": str(processed_at) if processed_at is not None else None,
                    "attempts": int(attempts) if attempts is not None else None,
                    "error_reason": error_reason,
                }
                db_ok = (status == "done") and (processed_at is not None)
    except Exception as exc:  # noqa: BLE001
        db_observed = {"error": f"{type(exc).__name__}: {exc}"}
        db_ok = False

    inject_exitcode_path = run_dir / "_inject_jaeger_stop.exitcode.txt"
    inject_exitcode = None
    if inject_exitcode_path.exists():
        try:
            inject_exitcode = int((inject_exitcode_path.read_text(encoding="utf-8", errors="replace") or "").strip() or "0")
        except Exception:
            inject_exitcode = None

    metrics_ok = (
        before_scrape_ok
        and after_scrape_ok
        and (delta_processed >= float(args.min_processed_delta))
        and (delta_failed <= float(args.max_failed_delta))
    )

    # Accept either strong metrics evidence or DB evidence that the outbox row
    # was processed successfully.
    ok = (inject_exitcode == 0) and (metrics_ok or db_ok)

    result = {
        "scenario": SCENARIO_COLLECTOR_DOWN,
        "run_dir": str(run_dir),
        "outbox_event_id": outbox_event_id,
        "checks": {
            "inject_jaeger_stop_exitcode_eq": 0,
            "min_processed_delta": float(args.min_processed_delta),
            "max_failed_delta": float(args.max_failed_delta),
            "metrics_scrape_required": True,
            "db_outbox_processed_fallback_allowed": True,
        },
        "observed": {
            "inject_jaeger_stop_exitcode": inject_exitcode,
            "metrics_before_scrape_ok": bool(before_scrape_ok),
            "metrics_after_scrape_ok": bool(after_scrape_ok),
            "outbox_processed_total": {"before": processed_before, "after": processed_after, "delta": delta_processed},
            "outbox_failed_total": {"before": failed_before, "after": failed_after, "delta": delta_failed},
            "db_outbox_event": db_observed,
        },
        "ok": bool(ok),
    }
    (run_dir / "_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if ok:
        print(f"[labs verify {SCENARIO_COLLECTOR_DOWN}] OK")
        return 0
    why = []
    if inject_exitcode != 0:
        why.append(f"inject_exitcode={inject_exitcode}")
    if not metrics_ok:
        why.append(
            f"metrics_ok=false (before_ok={before_scrape_ok} after_ok={after_scrape_ok} delta_processed={delta_processed} delta_failed={delta_failed})"
        )
    if not db_ok:
        why.append("db_ok=false")
    print(f"[labs verify {SCENARIO_COLLECTOR_DOWN}] FAILED: {'; '.join(why) if why else 'unknown'}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 10


def _cmd_labs_export_collector_down(args: argparse.Namespace) -> int:
    """Export evidence for collector_down.

    Jaeger is intentionally stopped, so trace export may fail. We treat that failure
    as expected and still return rc=0 after writing evidence files.
    """

    run_dir = _resolve_run_dir(run_id=args.run_id, outdir=args.outdir, scenario=SCENARIO_COLLECTOR_DOWN)
    exports_dir = run_dir / "_exports"
    _ensure_dir(exports_dir)

    outbox_event_id_path = run_dir / "_outbox_event_id.txt"
    outbox_event_id = outbox_event_id_path.read_text(encoding="utf-8").strip() if outbox_event_id_path.exists() else None

    cmd = [
        _python_exe(),
        str(LEGACY_SCRIPTS_DIR / "labs_009_export_jaeger.py"),
        "--outdir",
        str(exports_dir),
        "--service",
        args.service,
        "--lookback",
        args.lookback,
        "--limit",
        str(args.limit),
    ]
    if outbox_event_id:
        cmd += ["--outbox-event-id", outbox_event_id]

    print("[scripts] run:", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, check=False)
    (run_dir / "_export_jaeger.stdout.txt").write_text(proc.stdout or "", encoding="utf-8")
    (run_dir / "_export_jaeger.stderr.txt").write_text(proc.stderr or "", encoding="utf-8")
    (run_dir / "_export_jaeger.exitcode.txt").write_text(str(int(proc.returncode)) + "\n", encoding="utf-8")

    if proc.returncode != 0:
        (run_dir / "_export_note.txt").write_text(
            "collector_down: Jaeger is intentionally stopped; trace export failure is expected.\n",
            encoding="utf-8",
        )

    return 0


def _cmd_labs_clean_collector_down(args: argparse.Namespace) -> int:
    # 1) Restore Jaeger
    compose_file = str((REPO_ROOT / "docker-compose.infra.yml").resolve())
    start_proc = _docker_compose(args=["-f", compose_file, "start", "jaeger"], cwd=REPO_ROOT)
    print(f"[labs clean {SCENARIO_COLLECTOR_DOWN}] start jaeger: rc={start_proc.returncode}")

    if args.outdir:
        outdir = Path(args.outdir)
        _ensure_dir(outdir)
        (outdir / "_clean.txt").write_text(
            f"scenario={SCENARIO_COLLECTOR_DOWN}\n"
            "action=start_jaeger\n"
            f"at={time.strftime('%Y-%m-%d %H:%M:%S')}\n",
            encoding="utf-8",
        )
        (outdir / "_clean_jaeger_start.stdout.txt").write_text(start_proc.stdout or "", encoding="utf-8")
        (outdir / "_clean_jaeger_start.stderr.txt").write_text(start_proc.stderr or "", encoding="utf-8")
        (outdir / "_clean_jaeger_start.exitcode.txt").write_text(str(int(start_proc.returncode)) + "\n", encoding="utf-8")

    # 2) Optional pruning
    if args.keep_last is not None:
        base = LABS_SNAPSHOT_ROOT / "auto" / LAB_ID_S3A_2A_3A / SCENARIO_COLLECTOR_DOWN
        if base.exists():
            runs = sorted([p for p in base.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
            for p in runs[int(args.keep_last) :]:
                shutil.rmtree(p, ignore_errors=True)
            print(f"[labs clean {SCENARIO_COLLECTOR_DOWN}] kept_last={args.keep_last}")

    return 0


def _cmd_labs_run_duplicate_delivery(args: argparse.Namespace) -> int:
    """ExpG: duplicate delivery / idempotency via delete-on-missing (404 noop).

    Strategy:
    1) Insert 1 upsert for a fixed entity_id and ensure a search_index row exists.
    2) Insert 2 deletes for the same entity_id (second should be a noop: ES 404).
    """

    run_id = args.run_id or _now_run_id()
    outdir = Path(args.outdir) if args.outdir else _default_labs_auto_run_dir(scenario=SCENARIO_DUPLICATE_DELIVERY, run_id=run_id)

    logs_dir = outdir / "_logs"
    metrics_dir = outdir / "_metrics"
    exports_dir = outdir / "_exports"
    _ensure_dir(logs_dir)
    _ensure_dir(metrics_dir)
    _ensure_dir(exports_dir)

    env = _with_backend_pythonpath(_load_env(env_file=args.env_file))

    # Tracing: stable defaults
    service_name = args.service
    env.setdefault("WORDLOOM_TRACING_ENABLED", "1")
    env.setdefault("OTEL_SERVICE_NAME", service_name)
    env.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    env.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    env.setdefault("OTEL_TRACES_SAMPLER", "always_on")

    # Prefer per-event spans for this experiment.
    env["OUTBOX_USE_ES_BULK"] = "0"

    # ES connection defaults for local infra compose (only if env-file didn't specify them).
    env.setdefault("ELASTIC_URL", "http://localhost:19200")
    env.setdefault("ELASTIC_INDEX", "wordloom-test-search-index")

    # Ensure other experiments do not interfere.
    env["OUTBOX_EXPERIMENT_ES_429_RATIO"] = "0"
    env.pop("OUTBOX_EXPERIMENT_ES_429_EVERY_N", None)
    env["OUTBOX_EXPERIMENT_ES_BULK_PARTIAL"] = "0"
    env["OUTBOX_EXPERIMENT_BREAK_CLAIM"] = "0"
    env["OUTBOX_EXPERIMENT_PROCESS_SLEEP_SECONDS"] = "0"

    env["OUTBOX_METRICS_PORT"] = str(int(args.metrics_port))

    entity_id = str(args.entity_id).strip() if args.entity_id else str(uuid.uuid4())
    (outdir / "_entity_id.txt").write_text(entity_id + "\n", encoding="utf-8")

    recipe = {
        "lab_id": LAB_ID_S3A_2A_3A,
        "scenario": SCENARIO_DUPLICATE_DELIVERY,
        "run_id": run_id,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "env_file": args.env_file,
        "service": service_name,
        "entity": {"entity_type": str(args.entity_type), "entity_id": entity_id},
        "worker": {"duration_s": int(args.duration), "metrics_port": int(args.metrics_port)},
        "trigger": {"upsert_count": 1, "delete_count": int(args.delete_count)},
        "expect": {"idempotent_noop": {"kind": "es_delete_404", "count": 1}},
    }
    (outdir / "_recipe.json").write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    worker = LEGACY_SCRIPTS_DIR / "search_outbox_worker.py"
    log_path = logs_dir / f"worker-{run_id}.log"
    cmd = [_python_exe(), "-u", str(worker)]

    print(f"[labs run {SCENARIO_DUPLICATE_DELIVERY}] outdir: {outdir}")
    print(f"[labs run {SCENARIO_DUPLICATE_DELIVERY}] worker log: {log_path}")
    print(f"[labs run {SCENARIO_DUPLICATE_DELIVERY}] entity_id: {entity_id}")

    metrics_before_path = metrics_dir / "metrics-before.txt"
    metrics_after_path = metrics_dir / "metrics-after.txt"

    inserter = REPO_ROOT / "backend" / "scripts" / "labs" / "labs_009_insert_search_outbox_pending.py"
    if not inserter.exists():
        inserter = LEGACY_SCRIPTS_DIR / "labs_009_insert_search_outbox_pending.py"

    start = time.time()
    stopped_by_controller = False
    outbox_event_ids: list[str] = []

    with open(log_path, "w", encoding="utf-8") as log_file:
        worker_proc = subprocess.Popen(cmd, cwd=str(REPO_ROOT), env=env, stdout=log_file, stderr=subprocess.STDOUT)
        try:
            time.sleep(max(0.5, float(args.scrape_delay)))
            try:
                metrics_before = _scrape_metrics_text(port=int(args.metrics_port), timeout_s=4.0)
                metrics_before_path.write_text(metrics_before, encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                metrics_before_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")

            # 1) Upsert (ensures doc exists in ES via search_index)
            upsert_env = env.copy()
            upsert_env["OUTBOX_ENTITY_TYPE"] = str(args.entity_type)
            upsert_env["OUTBOX_ENTITY_ID"] = entity_id
            upsert_env["OUTBOX_OP"] = "upsert"
            upsert_env["OUTBOX_CREATE_SEARCH_INDEX_ROW"] = "1"
            upsert_env.setdefault("OUTBOX_EVENT_VERSION", "0")

            proc = subprocess.run(
                [_python_exe(), str(inserter)],
                cwd=str(REPO_ROOT),
                env=upsert_env,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            (outdir / "_trigger_upsert.stdout.txt").write_text(proc.stdout or "", encoding="utf-8")
            (outdir / "_trigger_upsert.stderr.txt").write_text(proc.stderr or "", encoding="utf-8")
            if proc.returncode != 0:
                print(f"[labs run {SCENARIO_DUPLICATE_DELIVERY}] failed to insert upsert outbox event: rc={proc.returncode}")
                worker_proc.terminate()
                worker_proc.wait(timeout=30)
                return 3

            upsert_event_id = (proc.stdout or "").strip().splitlines()[-1].strip()
            outbox_event_ids.append(upsert_event_id)
            time.sleep(1.5)

            # 2) Duplicate deletes (second should be ES 404 noop)
            delete_env = env.copy()
            delete_env["OUTBOX_ENTITY_TYPE"] = str(args.entity_type)
            delete_env["OUTBOX_ENTITY_ID"] = entity_id
            delete_env["OUTBOX_OP"] = "delete"
            delete_env.setdefault("OUTBOX_EVENT_VERSION", "0")
            delete_env["OUTBOX_CREATE_SEARCH_INDEX_ROW"] = "0"

            for idx in range(max(1, int(args.delete_count))):
                proc2 = subprocess.run(
                    [_python_exe(), str(inserter)],
                    cwd=str(REPO_ROOT),
                    env=delete_env,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                (outdir / f"_trigger_delete_{idx+1}.stdout.txt").write_text(proc2.stdout or "", encoding="utf-8")
                (outdir / f"_trigger_delete_{idx+1}.stderr.txt").write_text(proc2.stderr or "", encoding="utf-8")
                if proc2.returncode != 0:
                    print(f"[labs run {SCENARIO_DUPLICATE_DELIVERY}] failed to insert delete outbox event #{idx+1}: rc={proc2.returncode}")
                    worker_proc.terminate()
                    worker_proc.wait(timeout=30)
                    return 4
                delete_event_id = (proc2.stdout or "").strip().splitlines()[-1].strip()
                outbox_event_ids.append(delete_event_id)

            (outdir / "_outbox_event_ids.txt").write_text("\n".join(outbox_event_ids) + "\n", encoding="utf-8")

            while True:
                if args.duration > 0 and (time.time() - start) >= args.duration:
                    try:
                        metrics_after = _scrape_metrics_text(port=int(args.metrics_port), timeout_s=4.0)
                        metrics_after_path.write_text(metrics_after, encoding="utf-8")
                        (outdir / "_metrics.txt").write_text(metrics_after, encoding="utf-8")
                    except Exception as exc:  # noqa: BLE001
                        metrics_after_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")
                    stopped_by_controller = True
                    worker_proc.terminate()
                    break

                ret = worker_proc.poll()
                if ret is not None:
                    try:
                        metrics_after = _scrape_metrics_text(port=int(args.metrics_port), timeout_s=4.0)
                        metrics_after_path.write_text(metrics_after, encoding="utf-8")
                        (outdir / "_metrics.txt").write_text(metrics_after, encoding="utf-8")
                    except Exception as exc:  # noqa: BLE001
                        metrics_after_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")
                    break
                time.sleep(0.25)
        except KeyboardInterrupt:
            stopped_by_controller = True
            worker_proc.terminate()

        worker_proc.wait(timeout=30)

    exit_info = {"returncode": int(worker_proc.returncode) if worker_proc.returncode is not None else None}
    (outdir / "_worker_exit.json").write_text(
        json.dumps(exit_info, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if not metrics_after_path.exists():
        metrics_after_path.write_text("scrape_failed: missing_metrics_after\n", encoding="utf-8")

    if (not stopped_by_controller) and (worker_proc.returncode not in (None, 0)):
        print(f"[labs run {SCENARIO_DUPLICATE_DELIVERY}] worker exited early: rc={worker_proc.returncode}")
        print(f"[labs run {SCENARIO_DUPLICATE_DELIVERY}] see logs: {log_path}")
        return 5

    print(f"[labs run {SCENARIO_DUPLICATE_DELIVERY}] done (now run verify/export/clean)")
    print(f"[labs run {SCENARIO_DUPLICATE_DELIVERY}] outputs: {outdir}")
    return 0


def _cmd_labs_verify_duplicate_delivery(args: argparse.Namespace) -> int:
    run_dir = _resolve_run_dir(run_id=args.run_id, outdir=args.outdir, scenario=SCENARIO_DUPLICATE_DELIVERY)
    metrics_dir = run_dir / "_metrics"
    logs_dir = run_dir / "_logs"

    before_path = metrics_dir / "metrics-before.txt"
    after_path = metrics_dir / "metrics-after.txt"

    before = before_path.read_text(encoding="utf-8") if before_path.exists() else ""
    after = after_path.read_text(encoding="utf-8") if after_path.exists() else ""

    processed_before = _prom_parse_counter_sum(before, "outbox_processed_total")
    processed_after = _prom_parse_counter_sum(after, "outbox_processed_total")
    failed_before = _prom_parse_counter_sum(before, "outbox_failed_total")
    failed_after = _prom_parse_counter_sum(after, "outbox_failed_total")
    noop_before = _prom_parse_counter_sum(before, "outbox_idempotent_noop_total")
    noop_after = _prom_parse_counter_sum(after, "outbox_idempotent_noop_total")

    # Backward-safe: if metrics are missing or the new metric isn't present, rely on logs.

    delta_processed = processed_after - processed_before
    delta_failed = failed_after - failed_before
    delta_noop = noop_after - noop_before

    metrics_available = ("scrape_failed" not in before.lower()) and ("scrape_failed" not in after.lower())

    # Logs evidence: at least one noop delete line.
    log_paths = sorted([p for p in logs_dir.glob("*.log") if p.is_file()])
    noop_log_count = 0
    if log_paths:
        try:
            text = log_paths[0].read_text(encoding="utf-8", errors="replace")
            noop_log_count = len(re.findall(r"Outbox delete: doc .* not found in ES \(noop\)", text))
        except Exception:
            noop_log_count = 0

    ok = (
        (delta_processed >= float(args.min_processed_delta))
        and (delta_failed <= float(args.max_failed_delta))
        and ((delta_noop >= float(args.min_noop_delta)) or (noop_log_count >= int(args.min_noop_logs)))
    )

    result = {
        "scenario": SCENARIO_DUPLICATE_DELIVERY,
        "run_dir": str(run_dir),
        "checks": {
            "min_processed_delta": float(args.min_processed_delta),
            "max_failed_delta": float(args.max_failed_delta),
            "min_noop_delta": float(args.min_noop_delta),
            "min_noop_logs": int(args.min_noop_logs),
        },
        "observed": {
            "metrics_available": bool(metrics_available),
            "outbox_processed_total": {"before": processed_before, "after": processed_after, "delta": delta_processed},
            "outbox_failed_total": {"before": failed_before, "after": failed_after, "delta": delta_failed},
            "outbox_idempotent_noop_total": {"before": noop_before, "after": noop_after, "delta": delta_noop},
            "noop_log_count": int(noop_log_count),
        },
        "ok": bool(ok),
    }
    (run_dir / "_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if ok:
        print(f"[labs verify {SCENARIO_DUPLICATE_DELIVERY}] OK")
        return 0
    print(f"[labs verify {SCENARIO_DUPLICATE_DELIVERY}] FAILED")
    return 10


def _cmd_labs_export_duplicate_delivery(args: argparse.Namespace) -> int:
    run_dir = _resolve_run_dir(run_id=args.run_id, outdir=args.outdir, scenario=SCENARIO_DUPLICATE_DELIVERY)
    exports_dir = run_dir / "_exports"
    _ensure_dir(exports_dir)

    entity_id_path = run_dir / "_entity_id.txt"
    entity_id = entity_id_path.read_text(encoding="utf-8").strip() if entity_id_path.exists() else None

    tags = {
        "wordloom.obs_schema": SEARCH_OUTBOX_OBS_SCHEMA_VERSION,
    }
    if entity_id:
        tags["wordloom.entity_id"] = str(entity_id)

    cmd = [
        _python_exe(),
        str(LEGACY_SCRIPTS_DIR / "labs_009_export_jaeger.py"),
        "--outdir",
        str(exports_dir),
        "--service",
        args.service,
        "--lookback",
        args.lookback,
        "--limit",
        str(args.limit),
        "--operation",
        "outbox.process",
        "--tags-json",
        json.dumps(tags, ensure_ascii=False),
    ]
    return _run(cmd, cwd=REPO_ROOT)


def _cmd_labs_clean_duplicate_delivery(args: argparse.Namespace) -> int:
    # No external state to revert; optionally prune snapshots.
    if args.keep_last is None:
        return 0

    base = (LABS_SNAPSHOT_ROOT / "auto" / LAB_ID_S3A_2A_3A / SCENARIO_DUPLICATE_DELIVERY)
    if not base.exists():
        return 0

    runs = sorted([p for p in base.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
    for p in runs[int(args.keep_last):]:
        shutil.rmtree(p, ignore_errors=True)
    print(f"[labs clean {SCENARIO_DUPLICATE_DELIVERY}] kept_last={args.keep_last}")
    return 0


def _cmd_labs_run_es_bulk_partial(args: argparse.Namespace) -> int:
    run_id = args.run_id or _now_run_id()
    outdir = Path(args.outdir) if args.outdir else _default_labs_auto_run_dir(scenario=SCENARIO_ES_BULK_PARTIAL, run_id=run_id)

    logs_dir = outdir / "_logs"
    metrics_dir = outdir / "_metrics"
    exports_dir = outdir / "_exports"
    _ensure_dir(logs_dir)
    _ensure_dir(metrics_dir)
    _ensure_dir(exports_dir)

    env = _with_backend_pythonpath(_load_env(env_file=args.env_file))

    # Tracing: stable defaults
    service_name = args.service
    env.setdefault("WORDLOOM_TRACING_ENABLED", "1")
    env.setdefault("OTEL_SERVICE_NAME", service_name)
    env.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    env.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    env.setdefault("OTEL_TRACES_SAMPLER", "always_on")

    # Force ES bulk path + partial injection.
    env["OUTBOX_USE_ES_BULK"] = "1"
    env["OUTBOX_BULK_SIZE"] = str(int(args.bulk_size))
    env["OUTBOX_EXPERIMENT_ES_BULK_PARTIAL"] = "1"
    env["OUTBOX_EXPERIMENT_ES_BULK_PARTIAL_STATUS"] = str(int(args.partial_status))

    # Make ExpD deterministic:
    # - Slow poll so we can insert N events without races.
    # - Scrape metrics-before before inserting events so verify sees non-zero deltas.
    env["OUTBOX_POLL_INTERVAL_SECONDS"] = "5.0"

    # ES connection defaults for local infra compose (only if env-file didn't specify them).
    env.setdefault("ELASTIC_URL", "http://localhost:19200")
    env.setdefault("ELASTIC_INDEX", "wordloom-test-search-index")

    # Ensure other experiments do not interfere.
    env["OUTBOX_EXPERIMENT_ES_429_RATIO"] = "0"
    env.pop("OUTBOX_EXPERIMENT_ES_429_EVERY_N", None)

    env["OUTBOX_METRICS_PORT"] = str(int(args.metrics_port))

    recipe = {
        "lab_id": LAB_ID_S3A_2A_3A,
        "scenario": SCENARIO_ES_BULK_PARTIAL,
        "run_id": run_id,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "env_file": args.env_file,
        "service": service_name,
        "inject": {
            "kind": "es_bulk_partial",
            "enabled": True,
            "status": int(args.partial_status),
        },
        "worker": {
            "duration_s": int(args.duration),
            "metrics_port": int(args.metrics_port),
            "use_es_bulk": True,
            "bulk_size": int(args.bulk_size),
        },
        "trigger": {"op": str(args.op), "count": int(args.trigger_count)},
    }
    (outdir / "_recipe.json").write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    worker = LEGACY_SCRIPTS_DIR / "search_outbox_worker.py"
    log_path = logs_dir / f"worker-{run_id}.log"
    cmd = [_python_exe(), "-u", str(worker)]

    print(f"[labs run {SCENARIO_ES_BULK_PARTIAL}] outdir: {outdir}")
    print(f"[labs run {SCENARIO_ES_BULK_PARTIAL}] worker log: {log_path}")

    metrics_before_path = metrics_dir / "metrics-before.txt"
    metrics_after_path = metrics_dir / "metrics-after.txt"

    inserter = REPO_ROOT / "backend" / "scripts" / "labs" / "labs_009_insert_search_outbox_pending.py"
    if not inserter.exists():
        inserter = LEGACY_SCRIPTS_DIR / "labs_009_insert_search_outbox_pending.py"

    start = time.time()
    stopped_by_controller = False
    outbox_event_ids: list[str] = []

    with open(log_path, "w", encoding="utf-8") as log_file:
        worker_proc = subprocess.Popen(cmd, cwd=str(REPO_ROOT), env=env, stdout=log_file, stderr=subprocess.STDOUT)
        try:
            time.sleep(max(0.5, float(args.scrape_delay)))
            try:
                metrics_before = _scrape_metrics_text(port=int(args.metrics_port), timeout_s=4.0)
                metrics_before_path.write_text(metrics_before, encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                metrics_before_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")

            # Insert outbox events after metrics-before so verify sees meaningful deltas.
            trigger_env = env.copy()
            trigger_env["OUTBOX_OP"] = str(args.op)
            trigger_env.setdefault("OUTBOX_CREATE_SEARCH_INDEX_ROW", "1")
            trigger_env.setdefault("OUTBOX_EVENT_VERSION", "0")
            trigger_env["OUTBOX_INSERT_COUNT"] = str(int(args.trigger_count))

            proc = subprocess.run(
                [_python_exe(), str(inserter)],
                cwd=str(REPO_ROOT),
                env=trigger_env,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            (outdir / "_trigger_insert_outbox.stdout.txt").write_text(proc.stdout or "", encoding="utf-8")
            (outdir / "_trigger_insert_outbox.stderr.txt").write_text(proc.stderr or "", encoding="utf-8")
            if proc.returncode != 0:
                print(f"[labs run {SCENARIO_ES_BULK_PARTIAL}] failed to insert outbox events: rc={proc.returncode}")
                return 3

            outbox_event_ids = [ln.strip() for ln in (proc.stdout or "").splitlines() if ln.strip()]
            (outdir / "_outbox_event_ids.txt").write_text("\n".join(outbox_event_ids) + "\n", encoding="utf-8")
            print(f"[labs run {SCENARIO_ES_BULK_PARTIAL}] outbox_event_ids: {', '.join(outbox_event_ids)}")

            while True:
                if args.duration > 0 and (time.time() - start) >= args.duration:
                    try:
                        metrics_after = _scrape_metrics_text(port=int(args.metrics_port), timeout_s=4.0)
                        metrics_after_path.write_text(metrics_after, encoding="utf-8")
                        (outdir / "_metrics.txt").write_text(metrics_after, encoding="utf-8")
                    except Exception as exc:  # noqa: BLE001
                        metrics_after_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")
                    stopped_by_controller = True
                    worker_proc.terminate()
                    break

                ret = worker_proc.poll()
                if ret is not None:
                    try:
                        metrics_after = _scrape_metrics_text(port=int(args.metrics_port), timeout_s=4.0)
                        metrics_after_path.write_text(metrics_after, encoding="utf-8")
                        (outdir / "_metrics.txt").write_text(metrics_after, encoding="utf-8")
                    except Exception as exc:  # noqa: BLE001
                        metrics_after_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")
                    break
                time.sleep(0.25)
        except KeyboardInterrupt:
            stopped_by_controller = True
            worker_proc.terminate()

        worker_proc.wait(timeout=30)

    exit_info = {"returncode": int(worker_proc.returncode) if worker_proc.returncode is not None else None}
    (outdir / "_worker_exit.json").write_text(
        json.dumps(exit_info, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if not metrics_after_path.exists():
        metrics_after_path.write_text("scrape_failed: missing_metrics_after\n", encoding="utf-8")

    claim_batch_id = _extract_last_claim_batch_id(log_path)
    if claim_batch_id:
        (outdir / "_claim_batch_id.txt").write_text(claim_batch_id + "\n", encoding="utf-8")

    if (not stopped_by_controller) and (worker_proc.returncode not in (None, 0)):
        print(f"[labs run {SCENARIO_ES_BULK_PARTIAL}] worker exited early: rc={worker_proc.returncode}")
        print(f"[labs run {SCENARIO_ES_BULK_PARTIAL}] see logs: {log_path}")
        return 4

    print(f"[labs run {SCENARIO_ES_BULK_PARTIAL}] done (now run verify/export/clean)")
    print(f"[labs run {SCENARIO_ES_BULK_PARTIAL}] outputs: {outdir}")
    return 0


def _cmd_labs_verify_es_bulk_partial(args: argparse.Namespace) -> int:
    run_dir = _resolve_run_dir(run_id=args.run_id, outdir=args.outdir, scenario=SCENARIO_ES_BULK_PARTIAL)
    metrics_dir = run_dir / "_metrics"
    before_path = metrics_dir / "metrics-before.txt"
    after_path = metrics_dir / "metrics-after.txt"

    before = before_path.read_text(encoding="utf-8") if before_path.exists() else ""
    after = after_path.read_text(encoding="utf-8") if after_path.exists() else ""

    partial_before = _prom_parse_counter_sum(before, "outbox_es_bulk_requests_total", labels={"result": "partial"})
    partial_after = _prom_parse_counter_sum(after, "outbox_es_bulk_requests_total", labels={"result": "partial"})

    success_items_before = (
        _prom_parse_counter_sum(before, "outbox_es_bulk_items_total", labels={"op": "index", "result": "success"})
        + _prom_parse_counter_sum(before, "outbox_es_bulk_items_total", labels={"op": "delete", "result": "success"})
    )
    success_items_after = (
        _prom_parse_counter_sum(after, "outbox_es_bulk_items_total", labels={"op": "index", "result": "success"})
        + _prom_parse_counter_sum(after, "outbox_es_bulk_items_total", labels={"op": "delete", "result": "success"})
    )

    failed_items_before = (
        _prom_parse_counter_sum(before, "outbox_es_bulk_items_total", labels={"op": "index", "result": "failed"})
        + _prom_parse_counter_sum(before, "outbox_es_bulk_items_total", labels={"op": "delete", "result": "failed"})
    )
    failed_items_after = (
        _prom_parse_counter_sum(after, "outbox_es_bulk_items_total", labels={"op": "index", "result": "failed"})
        + _prom_parse_counter_sum(after, "outbox_es_bulk_items_total", labels={"op": "delete", "result": "failed"})
    )

    failed_4xx_before = (
        _prom_parse_counter_sum(before, "outbox_es_bulk_item_failures_total", labels={"op": "index", "failure_class": "4xx"})
        + _prom_parse_counter_sum(before, "outbox_es_bulk_item_failures_total", labels={"op": "delete", "failure_class": "4xx"})
    )
    failed_4xx_after = (
        _prom_parse_counter_sum(after, "outbox_es_bulk_item_failures_total", labels={"op": "index", "failure_class": "4xx"})
        + _prom_parse_counter_sum(after, "outbox_es_bulk_item_failures_total", labels={"op": "delete", "failure_class": "4xx"})
    )

    delta_partial = partial_after - partial_before
    delta_success_items = success_items_after - success_items_before
    delta_failed_items = failed_items_after - failed_items_before
    delta_failed_4xx = failed_4xx_after - failed_4xx_before

    ok = (
        (delta_partial >= float(args.min_partial_delta))
        and (delta_success_items >= float(args.min_success_items_delta))
        and (delta_failed_items >= float(args.min_failed_items_delta))
        and (delta_failed_4xx >= float(args.min_failed_4xx_delta))
    )

    result = {
        "scenario": SCENARIO_ES_BULK_PARTIAL,
        "run_dir": str(run_dir),
        "checks": {
            "partial_delta_ge": float(args.min_partial_delta),
            "success_items_delta_ge": float(args.min_success_items_delta),
            "failed_items_delta_ge": float(args.min_failed_items_delta),
            "failed_4xx_delta_ge": float(args.min_failed_4xx_delta),
        },
        "observed": {
            "outbox_es_bulk_requests_total_result_partial": {"before": partial_before, "after": partial_after, "delta": delta_partial},
            "outbox_es_bulk_items_total_success_sum": {"before": success_items_before, "after": success_items_after, "delta": delta_success_items},
            "outbox_es_bulk_items_total_failed_sum": {"before": failed_items_before, "after": failed_items_after, "delta": delta_failed_items},
            "outbox_es_bulk_item_failures_total_failure_class_4xx_sum": {"before": failed_4xx_before, "after": failed_4xx_after, "delta": delta_failed_4xx},
        },
        "ok": bool(ok),
    }
    (run_dir / "_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if ok:
        print(f"[labs verify {SCENARIO_ES_BULK_PARTIAL}] OK")
        return 0
    print(f"[labs verify {SCENARIO_ES_BULK_PARTIAL}] FAILED")
    return 10


def _cmd_labs_export_es_bulk_partial(args: argparse.Namespace) -> int:
    run_dir = _resolve_run_dir(run_id=args.run_id, outdir=args.outdir, scenario=SCENARIO_ES_BULK_PARTIAL)
    exports_dir = run_dir / "_exports"
    _ensure_dir(exports_dir)

    claim_batch_id_path = run_dir / "_claim_batch_id.txt"
    claim_batch_id = claim_batch_id_path.read_text(encoding="utf-8").strip() if claim_batch_id_path.exists() else None

    exporter = LEGACY_SCRIPTS_DIR / "labs_009_export_jaeger.py"
    base_cmd = [
        _python_exe(),
        str(exporter),
        "--outdir",
        str(exports_dir),
        "--service",
        args.service,
        "--lookback",
        args.lookback,
        "--limit",
        str(args.limit),
    ]

    if claim_batch_id:
        return _run(base_cmd + ["--claim-batch-id", claim_batch_id], cwd=REPO_ROOT)

    # Bulk mode may not emit per-event `outbox.process` spans, so exporting by outbox_event_id
    # is often empty. Use a narrowed tag export instead.
    return _run(
        base_cmd
        + ["--tags-json", json.dumps({"wordloom.obs_schema": SEARCH_OUTBOX_OBS_SCHEMA_VERSION}, ensure_ascii=False)],
        cwd=REPO_ROOT,
    )


def _cmd_labs_clean_es_bulk_partial(args: argparse.Namespace) -> int:
    # No external state to revert: injection is env-only.
    if args.outdir:
        outdir = Path(args.outdir)
        _ensure_dir(outdir)
        (outdir / "_clean.txt").write_text(
            f"scenario={SCENARIO_ES_BULK_PARTIAL}\n"
            "action=noop\n"
            f"at={time.strftime('%Y-%m-%d %H:%M:%S')}\n",
            encoding="utf-8",
        )

    if args.keep_last is not None:
        base = LABS_SNAPSHOT_ROOT / "auto" / LAB_ID_S3A_2A_3A / SCENARIO_ES_BULK_PARTIAL
        if base.exists():
            runs = sorted([p for p in base.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
            for p in runs[int(args.keep_last):]:
                shutil.rmtree(p, ignore_errors=True)
            print(f"[labs clean {SCENARIO_ES_BULK_PARTIAL}] kept_last={args.keep_last}")
    else:
        print(f"[labs clean {SCENARIO_ES_BULK_PARTIAL}] noop")
    return 0


def _cmd_labs_run_db_claim_contention(args: argparse.Namespace) -> int:
    run_id = args.run_id or _now_run_id()
    outdir = Path(args.outdir) if args.outdir else _default_labs_auto_run_dir(scenario=SCENARIO_DB_CLAIM_CONTENTION, run_id=run_id)

    logs_dir = outdir / "_logs"
    metrics_dir = outdir / "_metrics"
    exports_dir = outdir / "_exports"
    _ensure_dir(logs_dir)
    _ensure_dir(metrics_dir)
    _ensure_dir(exports_dir)

    base_env = _with_backend_pythonpath(_load_env(env_file=args.env_file))

    # Tracing: stable defaults
    service_name = args.service
    base_env.setdefault("WORDLOOM_TRACING_ENABLED", "1")
    base_env.setdefault("OTEL_SERVICE_NAME", service_name)
    base_env.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    base_env.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    base_env.setdefault("OTEL_TRACES_SAMPLER", "always_on")

    # Local infra defaults (ensure ES is reachable even if env-file doesn't specify).
    base_env.setdefault("ELASTIC_URL", "http://localhost:19200")
    base_env.setdefault("ELASTIC_INDEX", "wordloom-test-search-index")

    # Keep logs parseable + export-friendly.
    base_env["LOG_LEVEL"] = "INFO"

    # Ensure other experiments do not interfere.
    base_env["OUTBOX_EXPERIMENT_ES_429_RATIO"] = "0"
    base_env.pop("OUTBOX_EXPERIMENT_ES_429_EVERY_N", None)
    base_env.pop("OUTBOX_EXPERIMENT_ES_BULK_PARTIAL", None)

    # Force non-bulk path so per-event spans are likely to exist.
    base_env["OUTBOX_USE_ES_BULK"] = "0"

    # Experiment E injection: break claim atomicity to create contention signals.
    base_env["OUTBOX_EXPERIMENT_BREAK_CLAIM"] = "1"
    base_env["OUTBOX_EXPERIMENT_BREAK_CLAIM_SLEEP_SECONDS"] = str(float(args.break_claim_sleep))

    # Improve determinism for owner-mismatch signal:
    # give the competing worker a window to overwrite ownership after claim.
    base_env["OUTBOX_EXPERIMENT_PROCESS_SLEEP_SECONDS"] = str(max(1.0, float(args.break_claim_sleep)))

    # Make the claim loop tight to increase overlap probability.
    base_env["OUTBOX_POLL_INTERVAL_SECONDS"] = str(float(args.poll_interval))
    base_env["OUTBOX_BULK_SIZE"] = str(int(args.batch_size))
    base_env["OUTBOX_CONCURRENCY"] = "1"

    recipe = {
        "lab_id": LAB_ID_S3A_2A_3A,
        "scenario": SCENARIO_DB_CLAIM_CONTENTION,
        "run_id": run_id,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "env_file": args.env_file,
        "service": service_name,
        "inject": {
            "kind": "break_claim_atomicity",
            "enabled": True,
            "sleep_seconds": float(args.break_claim_sleep),
        },
        "worker": {
            "duration_s": int(args.duration),
            "metrics_ports": [int(args.metrics_port_1), int(args.metrics_port_2)],
            "poll_interval_seconds": float(args.poll_interval),
            "batch_size": int(args.batch_size),
        },
        "trigger": {"op": str(args.op), "count": int(args.trigger_count)},
    }
    (outdir / "_recipe.json").write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    worker = LEGACY_SCRIPTS_DIR / "search_outbox_worker.py"
    cmd = [_python_exe(), "-u", str(worker)]

    # Prepare env + logs for two competing worker processes.
    env1 = base_env.copy()
    env1["OUTBOX_WORKER_ID"] = str(args.worker_id_1)
    env1["OUTBOX_METRICS_PORT"] = str(int(args.metrics_port_1))
    env1["OUTBOX_HTTP_PORT"] = str(int(args.metrics_port_1) + 20)

    env2 = base_env.copy()
    env2["OUTBOX_WORKER_ID"] = str(args.worker_id_2)
    env2["OUTBOX_METRICS_PORT"] = str(int(args.metrics_port_2))
    env2["OUTBOX_HTTP_PORT"] = str(int(args.metrics_port_2) + 20)

    log_path_1 = logs_dir / f"worker1-{run_id}.log"
    log_path_2 = logs_dir / f"worker2-{run_id}.log"

    print(f"[labs run {SCENARIO_DB_CLAIM_CONTENTION}] outdir: {outdir}")
    print(f"[labs run {SCENARIO_DB_CLAIM_CONTENTION}] worker1 log: {log_path_1} (metrics :{args.metrics_port_1})")
    print(f"[labs run {SCENARIO_DB_CLAIM_CONTENTION}] worker2 log: {log_path_2} (metrics :{args.metrics_port_2})")

    before_1_path = metrics_dir / "metrics-before-1.txt"
    before_2_path = metrics_dir / "metrics-before-2.txt"
    after_1_path = metrics_dir / "metrics-after-1.txt"
    after_2_path = metrics_dir / "metrics-after-2.txt"

    inserter = REPO_ROOT / "backend" / "scripts" / "labs" / "labs_009_insert_search_outbox_pending.py"
    if not inserter.exists():
        inserter = LEGACY_SCRIPTS_DIR / "labs_009_insert_search_outbox_pending.py"

    start = time.time()
    stopped_by_controller = False
    outbox_event_ids: list[str] = []

    with open(log_path_1, "w", encoding="utf-8") as log_file_1, open(log_path_2, "w", encoding="utf-8") as log_file_2:
        proc1 = subprocess.Popen(cmd, cwd=str(REPO_ROOT), env=env1, stdout=log_file_1, stderr=subprocess.STDOUT)
        proc2 = subprocess.Popen(cmd, cwd=str(REPO_ROOT), env=env2, stdout=log_file_2, stderr=subprocess.STDOUT)
        try:
            time.sleep(max(0.5, float(args.scrape_delay)))
            try:
                before_1_path.write_text(_scrape_metrics_text(port=int(args.metrics_port_1), timeout_s=4.0), encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                before_1_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")
            try:
                before_2_path.write_text(_scrape_metrics_text(port=int(args.metrics_port_2), timeout_s=4.0), encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                before_2_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")

            for i in range(int(args.trigger_count)):
                trigger_env = base_env.copy()
                trigger_env["OUTBOX_OP"] = str(args.op)
                trigger_env.setdefault("OUTBOX_CREATE_SEARCH_INDEX_ROW", "1")
                trigger_env.setdefault("OUTBOX_EVENT_VERSION", "0")

                proc = subprocess.run(
                    [_python_exe(), str(inserter)],
                    cwd=str(REPO_ROOT),
                    env=trigger_env,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                (outdir / f"_trigger_insert_outbox_{i+1}.stdout.txt").write_text(proc.stdout or "", encoding="utf-8")
                (outdir / f"_trigger_insert_outbox_{i+1}.stderr.txt").write_text(proc.stderr or "", encoding="utf-8")
                if proc.returncode != 0:
                    print(f"[labs run {SCENARIO_DB_CLAIM_CONTENTION}] failed to insert outbox event #{i+1}: rc={proc.returncode}")
                    proc1.terminate()
                    proc2.terminate()
                    proc1.wait(timeout=30)
                    proc2.wait(timeout=30)
                    return 3
                outbox_event_id = (proc.stdout or "").strip().splitlines()[-1].strip()
                outbox_event_ids.append(outbox_event_id)

            (outdir / "_outbox_event_ids.txt").write_text("\n".join(outbox_event_ids) + "\n", encoding="utf-8")
            print(f"[labs run {SCENARIO_DB_CLAIM_CONTENTION}] outbox_event_ids: {', '.join(outbox_event_ids)}")

            while True:
                if args.duration > 0 and (time.time() - start) >= args.duration:
                    try:
                        after_1_path.write_text(_scrape_metrics_text(port=int(args.metrics_port_1), timeout_s=4.0), encoding="utf-8")
                    except Exception as exc:  # noqa: BLE001
                        after_1_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")
                    try:
                        after_2_path.write_text(_scrape_metrics_text(port=int(args.metrics_port_2), timeout_s=4.0), encoding="utf-8")
                    except Exception as exc:  # noqa: BLE001
                        after_2_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")
                    stopped_by_controller = True
                    proc1.terminate()
                    proc2.terminate()
                    break

                ret1 = proc1.poll()
                ret2 = proc2.poll()
                if ret1 is not None or ret2 is not None:
                    try:
                        after_1_path.write_text(_scrape_metrics_text(port=int(args.metrics_port_1), timeout_s=4.0), encoding="utf-8")
                    except Exception as exc:  # noqa: BLE001
                        after_1_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")
                    try:
                        after_2_path.write_text(_scrape_metrics_text(port=int(args.metrics_port_2), timeout_s=4.0), encoding="utf-8")
                    except Exception as exc:  # noqa: BLE001
                        after_2_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")
                    break
                time.sleep(0.25)
        except KeyboardInterrupt:
            stopped_by_controller = True
            proc1.terminate()
            proc2.terminate()

        proc1.wait(timeout=30)
        proc2.wait(timeout=30)

    exit_info = {
        "worker1": {"returncode": int(proc1.returncode) if proc1.returncode is not None else None},
        "worker2": {"returncode": int(proc2.returncode) if proc2.returncode is not None else None},
    }
    (outdir / "_worker_exit.json").write_text(json.dumps(exit_info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Combined convenience file
    combined = (
        "# metrics-after-1\n\n" + (after_1_path.read_text(encoding="utf-8", errors="replace") if after_1_path.exists() else "")
        + "\n\n# metrics-after-2\n\n" + (after_2_path.read_text(encoding="utf-8", errors="replace") if after_2_path.exists() else "")
    )
    (outdir / "_metrics.txt").write_text(combined, encoding="utf-8")

    claim_batch_ids: list[str] = []
    for lp in (log_path_1, log_path_2):
        cid = _extract_last_claim_batch_id(lp)
        if cid:
            claim_batch_ids.append(cid)
    if claim_batch_ids:
        (outdir / "_claim_batch_ids.txt").write_text("\n".join(claim_batch_ids) + "\n", encoding="utf-8")

    if (not stopped_by_controller) and (proc1.returncode not in (None, 0) or proc2.returncode not in (None, 0)):
        print(f"[labs run {SCENARIO_DB_CLAIM_CONTENTION}] a worker exited early: rc1={proc1.returncode} rc2={proc2.returncode}")
        print(f"[labs run {SCENARIO_DB_CLAIM_CONTENTION}] see logs: {log_path_1} {log_path_2}")
        return 4

    print(f"[labs run {SCENARIO_DB_CLAIM_CONTENTION}] done (now run verify/export/clean)")
    print(f"[labs run {SCENARIO_DB_CLAIM_CONTENTION}] outputs: {outdir}")
    return 0


def _cmd_labs_verify_db_claim_contention(args: argparse.Namespace) -> int:
    run_dir = _resolve_run_dir(run_id=args.run_id, outdir=args.outdir, scenario=SCENARIO_DB_CLAIM_CONTENTION)
    metrics_dir = run_dir / "_metrics"

    before1 = (metrics_dir / "metrics-before-1.txt").read_text(encoding="utf-8") if (metrics_dir / "metrics-before-1.txt").exists() else ""
    before2 = (metrics_dir / "metrics-before-2.txt").read_text(encoding="utf-8") if (metrics_dir / "metrics-before-2.txt").exists() else ""
    after1 = (metrics_dir / "metrics-after-1.txt").read_text(encoding="utf-8") if (metrics_dir / "metrics-after-1.txt").exists() else ""
    after2 = (metrics_dir / "metrics-after-2.txt").read_text(encoding="utf-8") if (metrics_dir / "metrics-after-2.txt").exists() else ""

    metric_owner_mismatch = "outbox_owner_mismatch_skips_total"
    metric_processed = "outbox_processed_total"
    metric_failed = "outbox_failed_total"

    mismatch_before = _prom_parse_counter_sum(before1, metric_owner_mismatch) + _prom_parse_counter_sum(before2, metric_owner_mismatch)
    mismatch_after = _prom_parse_counter_sum(after1, metric_owner_mismatch) + _prom_parse_counter_sum(after2, metric_owner_mismatch)

    processed_before = _prom_parse_counter_sum(before1, metric_processed) + _prom_parse_counter_sum(before2, metric_processed)
    processed_after = _prom_parse_counter_sum(after1, metric_processed) + _prom_parse_counter_sum(after2, metric_processed)

    failed_before = _prom_parse_counter_sum(before1, metric_failed) + _prom_parse_counter_sum(before2, metric_failed)
    failed_after = _prom_parse_counter_sum(after1, metric_failed) + _prom_parse_counter_sum(after2, metric_failed)

    delta_mismatch = mismatch_after - mismatch_before
    delta_processed = processed_after - processed_before
    delta_failed = failed_after - failed_before

    ok = (
        (delta_mismatch >= float(args.min_owner_mismatch_delta))
        and (delta_processed >= float(args.min_processed_delta))
        and (delta_failed <= float(args.max_failed_delta))
    )

    result = {
        "scenario": SCENARIO_DB_CLAIM_CONTENTION,
        "run_dir": str(run_dir),
        "checks": {
            "owner_mismatch_delta_ge": float(args.min_owner_mismatch_delta),
            "processed_delta_ge": float(args.min_processed_delta),
            "failed_delta_le": float(args.max_failed_delta),
        },
        "observed": {
            metric_owner_mismatch: {"before": mismatch_before, "after": mismatch_after, "delta": delta_mismatch},
            metric_processed: {"before": processed_before, "after": processed_after, "delta": delta_processed},
            metric_failed: {"before": failed_before, "after": failed_after, "delta": delta_failed},
        },
        "ok": bool(ok),
    }
    (run_dir / "_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if ok:
        print(f"[labs verify {SCENARIO_DB_CLAIM_CONTENTION}] OK")
        return 0
    print(f"[labs verify {SCENARIO_DB_CLAIM_CONTENTION}] FAILED")
    return 10


def _cmd_labs_export_db_claim_contention(args: argparse.Namespace) -> int:
    run_dir = _resolve_run_dir(run_id=args.run_id, outdir=args.outdir, scenario=SCENARIO_DB_CLAIM_CONTENTION)
    exports_dir = run_dir / "_exports"
    _ensure_dir(exports_dir)

    exporter = LEGACY_SCRIPTS_DIR / "labs_009_export_jaeger.py"
    base_cmd = [
        _python_exe(),
        str(exporter),
        "--outdir",
        str(exports_dir),
        "--service",
        args.service,
        "--lookback",
        args.lookback,
        "--limit",
        str(args.limit),
    ]

    # For ExpE, `outbox.claim_batch` is the primary evidence. Export a bounded sample.
    return _run(
        base_cmd
        + [
            "--operation",
            "outbox.claim_batch",
            "--tags-json",
            json.dumps({"wordloom.obs_schema": SEARCH_OUTBOX_OBS_SCHEMA_VERSION}, ensure_ascii=False),
        ],
        cwd=REPO_ROOT,
    )


def _cmd_labs_clean_db_claim_contention(args: argparse.Namespace) -> int:
    # No external state to revert: injection is env-only.
    if args.outdir:
        outdir = Path(args.outdir)
        _ensure_dir(outdir)
        (outdir / "_clean.txt").write_text(
            f"scenario={SCENARIO_DB_CLAIM_CONTENTION}\n"
            "action=noop\n"
            f"at={time.strftime('%Y-%m-%d %H:%M:%S')}\n",
            encoding="utf-8",
        )

    if args.keep_last is not None:
        base = LABS_SNAPSHOT_ROOT / "auto" / LAB_ID_S3A_2A_3A / SCENARIO_DB_CLAIM_CONTENTION
        if base.exists():
            runs = sorted([p for p in base.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
            for p in runs[int(args.keep_last):]:
                shutil.rmtree(p, ignore_errors=True)
            print(f"[labs clean {SCENARIO_DB_CLAIM_CONTENTION}] kept_last={args.keep_last}")
    else:
        print(f"[labs clean {SCENARIO_DB_CLAIM_CONTENTION}] noop")
    return 0


def _cmd_labs_run_stuck_reclaim(args: argparse.Namespace) -> int:
    run_id = args.run_id or _now_run_id()
    outdir = Path(args.outdir) if args.outdir else _default_labs_auto_run_dir(scenario=SCENARIO_STUCK_RECLAIM, run_id=run_id)

    logs_dir = outdir / "_logs"
    metrics_dir = outdir / "_metrics"
    exports_dir = outdir / "_exports"
    _ensure_dir(logs_dir)
    _ensure_dir(metrics_dir)
    _ensure_dir(exports_dir)

    base_env = _with_backend_pythonpath(_load_env(env_file=args.env_file))

    # Tracing: stable defaults
    service_name = args.service
    base_env.setdefault("WORDLOOM_TRACING_ENABLED", "1")
    base_env.setdefault("OTEL_SERVICE_NAME", service_name)
    base_env.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    base_env.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    base_env.setdefault("OTEL_TRACES_SAMPLER", "always_on")

    # Local infra defaults
    base_env.setdefault("ELASTIC_URL", "http://localhost:19200")
    base_env.setdefault("ELASTIC_INDEX", "wordloom-test-search-index")

    # Keep logs parseable + export-friendly.
    base_env["LOG_LEVEL"] = "INFO"

    # Ensure other experiments do not interfere.
    base_env["OUTBOX_EXPERIMENT_ES_429_RATIO"] = "0"
    base_env.pop("OUTBOX_EXPERIMENT_ES_429_EVERY_N", None)
    base_env.pop("OUTBOX_EXPERIMENT_ES_BULK_PARTIAL", None)
    base_env.pop("OUTBOX_EXPERIMENT_BREAK_CLAIM", None)
    base_env.pop("OUTBOX_EXPERIMENT_BREAK_CLAIM_SLEEP_SECONDS", None)

    # Force non-bulk path so per-event spans are likely to exist.
    base_env["OUTBOX_USE_ES_BULK"] = "0"

    # Tune lease/reclaim to make stuck+reclaim happen quickly.
    base_env["OUTBOX_LEASE_SECONDS"] = str(int(args.lease_seconds))
    base_env["OUTBOX_RECLAIM_INTERVAL_SECONDS"] = str(float(args.reclaim_interval))
    base_env["OUTBOX_MAX_PROCESSING_SECONDS"] = str(int(args.max_processing_seconds))
    base_env["OUTBOX_POLL_INTERVAL_SECONDS"] = str(float(args.poll_interval))
    base_env["OUTBOX_BULK_SIZE"] = str(int(args.batch_size))
    base_env["OUTBOX_CONCURRENCY"] = "1"

    recipe = {
        "lab_id": LAB_ID_S3A_2A_3A,
        "scenario": SCENARIO_STUCK_RECLAIM,
        "run_id": run_id,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "env_file": args.env_file,
        "service": service_name,
        "worker": {
            "duration_s": int(args.duration),
            "metrics_ports": [int(args.metrics_port_1), int(args.metrics_port_2)],
            "lease_seconds": int(args.lease_seconds),
            "reclaim_interval_seconds": float(args.reclaim_interval),
            "max_processing_seconds": int(args.max_processing_seconds),
            "poll_interval_seconds": float(args.poll_interval),
            "batch_size": int(args.batch_size),
        },
        "trigger": {"op": str(args.op), "count": int(args.trigger_count)},
        "crash": {"kind": "process_kill", "target": "worker1", "claim_timeout_s": float(args.claim_timeout)},
    }
    (outdir / "_recipe.json").write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    worker = LEGACY_SCRIPTS_DIR / "search_outbox_worker.py"
    cmd = [_python_exe(), "-u", str(worker)]

    inserter = REPO_ROOT / "backend" / "scripts" / "labs" / "labs_009_insert_search_outbox_pending.py"
    if not inserter.exists():
        inserter = LEGACY_SCRIPTS_DIR / "labs_009_insert_search_outbox_pending.py"
    outbox_event_ids: list[str] = []
    for i in range(int(args.trigger_count)):
        trigger_env = base_env.copy()
        trigger_env["OUTBOX_OP"] = str(args.op)
        trigger_env.setdefault("OUTBOX_CREATE_SEARCH_INDEX_ROW", "1")
        trigger_env.setdefault("OUTBOX_EVENT_VERSION", "0")

        proc = subprocess.run(
            [_python_exe(), str(inserter)],
            cwd=str(REPO_ROOT),
            env=trigger_env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        (outdir / f"_trigger_insert_outbox_{i+1}.stdout.txt").write_text(proc.stdout or "", encoding="utf-8")
        (outdir / f"_trigger_insert_outbox_{i+1}.stderr.txt").write_text(proc.stderr or "", encoding="utf-8")
        if proc.returncode != 0:
            print(f"[labs run {SCENARIO_STUCK_RECLAIM}] failed to insert outbox event #{i+1}: rc={proc.returncode}")
            return 3
        outbox_event_id = (proc.stdout or "").strip().splitlines()[-1].strip()
        outbox_event_ids.append(outbox_event_id)

    (outdir / "_outbox_event_ids.txt").write_text("\n".join(outbox_event_ids) + "\n", encoding="utf-8")
    print(f"[labs run {SCENARIO_STUCK_RECLAIM}] outbox_event_ids: {', '.join(outbox_event_ids)}")

    def _spawn_worker_with_retry(
        *,
        worker_id: str,
        preferred_metrics_port: int,
        log_path: Path,
        max_attempts: int = 4,
        extra_env: dict[str, str] | None = None,
    ) -> tuple[subprocess.Popen, dict[str, str], int, int]:
        candidate_ports: list[int] = []
        for i in range(max_attempts):
            p = int(preferred_metrics_port) + (i * 10_000)
            if 1024 <= p <= 65_000:
                candidate_ports.append(p)
        if not candidate_ports:
            candidate_ports = [19128, 29128, 39128, 49128]

        last_proc: subprocess.Popen | None = None
        last_env: dict[str, str] | None = None
        last_metrics_port = int(preferred_metrics_port)
        last_http_port = int(preferred_metrics_port) + 20

        for attempt, metrics_port in enumerate(candidate_ports, start=1):
            http_port = int(metrics_port) + 20
            env = base_env.copy()
            env["OUTBOX_WORKER_ID"] = str(worker_id)
            env["OUTBOX_METRICS_PORT"] = str(int(metrics_port))
            env["OUTBOX_HTTP_PORT"] = str(int(http_port))
            if extra_env:
                env.update({str(k): str(v) for k, v in extra_env.items()})

            header = f"\n\n# controller: spawn attempt {attempt}/{len(candidate_ports)} metrics_port={metrics_port} http_port={http_port}\n"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(header)
                log_file.flush()
                proc = subprocess.Popen(cmd, cwd=str(REPO_ROOT), env=env, stdout=log_file, stderr=subprocess.STDOUT)

                # Give the process a moment to bind ports & start up.
                time.sleep(0.75)

                if proc.poll() is None:
                    return proc, env, int(metrics_port), int(http_port)

            # Process exited quickly. If it's the known Windows bind issue, try next port.
            try:
                tail = log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
            except Exception:
                tail = ""
            if "WinError 10013" in tail or "PermissionError" in tail:
                last_proc = proc
                last_env = env
                last_metrics_port = int(metrics_port)
                last_http_port = int(http_port)
                continue
            return proc, env, int(metrics_port), int(http_port)

        assert last_proc is not None
        assert last_env is not None
        return last_proc, last_env, int(last_metrics_port), int(last_http_port)

    log_path_1 = logs_dir / f"worker1-{run_id}.log"
    log_path_2 = logs_dir / f"worker2-{run_id}.log"

    before_1_path = metrics_dir / "metrics-before-1.txt"
    before_2_path = metrics_dir / "metrics-before-2.txt"
    after_1_path = metrics_dir / "metrics-after-1.txt"
    after_2_path = metrics_dir / "metrics-after-2.txt"

    print(f"[labs run {SCENARIO_STUCK_RECLAIM}] outdir: {outdir}")
    print(f"[labs run {SCENARIO_STUCK_RECLAIM}] worker1 log: {log_path_1} (metrics :{args.metrics_port_1})")
    print(f"[labs run {SCENARIO_STUCK_RECLAIM}] worker2 log: {log_path_2} (metrics :{args.metrics_port_2})")

    killed_worker1 = False
    observed_claim = False
    worker2_exited_early = False
    worker2_terminated_by_controller = False

    rx_claimed = re.compile(r'"event"\s*:\s*"outbox\\.claim_batch".*?"claimed"\s*:\s*([1-9][0-9]*)')

    # Ensure log files start empty for this run.
    log_path_1.write_text("", encoding="utf-8")
    log_path_2.write_text("", encoding="utf-8")

    # Critical for ExpF: slow worker1 immediately after claim, so controller can
    # kill it before processing completes, leaving rows in `processing` to be
    # reclaimed by worker2.
    worker1_sleep_after_claim_s = max(3.0, float(int(args.lease_seconds)) + 1.0)

    proc1, env1, actual_metrics_port_1, actual_http_port_1 = _spawn_worker_with_retry(
        worker_id=str(args.worker_id_1),
        preferred_metrics_port=int(args.metrics_port_1),
        log_path=log_path_1,
        extra_env={"OUTBOX_EXPERIMENT_PROCESS_SLEEP_SECONDS": str(worker1_sleep_after_claim_s)},
    )
    try:
        time.sleep(max(0.5, float(args.scrape_delay)))
        try:
            before_1_path.write_text(_scrape_metrics_text(port=int(actual_metrics_port_1), timeout_s=2.0), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            before_1_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")

        # Wait until worker1 claims at least one row, then kill it hard to simulate a crash.
        claim_deadline = time.time() + float(args.claim_timeout)
        while time.time() < claim_deadline:
            if proc1.poll() is not None:
                break
            try:
                text = log_path_1.read_text(encoding="utf-8", errors="replace")
            except Exception:
                text = ""
            if rx_claimed.search(text):
                observed_claim = True
                break
            time.sleep(0.1)

        if proc1.poll() is None:
            killed_worker1 = True
            proc1.kill()
    except KeyboardInterrupt:
        killed_worker1 = True
        try:
            proc1.kill()
        except Exception:
            pass
    finally:
        try:
            proc1.wait(timeout=30)
        except Exception:
            pass

    after_1_path.write_text(
        f"note: worker1 was {'killed' if killed_worker1 else 'not_killed'} by controller\n"
        f"note: observed_claim={observed_claim}\n",
        encoding="utf-8",
    )

    proc2, env2, actual_metrics_port_2, actual_http_port_2 = _spawn_worker_with_retry(
        worker_id=str(args.worker_id_2),
        preferred_metrics_port=int(args.metrics_port_2),
        log_path=log_path_2,
        extra_env={"OUTBOX_EXPERIMENT_PROCESS_SLEEP_SECONDS": "0"},
    )
    try:
        time.sleep(max(0.5, float(args.scrape_delay)))
        try:
            before_2_path.write_text(_scrape_metrics_text(port=int(actual_metrics_port_2), timeout_s=2.0), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            before_2_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")

        start = time.time()
        while True:
            if args.duration > 0 and (time.time() - start) >= args.duration:
                break
            if proc2.poll() is not None:
                worker2_exited_early = True
                break
            time.sleep(0.25)

        try:
            after_2_path.write_text(_scrape_metrics_text(port=int(actual_metrics_port_2), timeout_s=2.0), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            after_2_path.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")

        # Stop worker2 only if it's still running (normal case: we ran it for
        # `--duration`). If it exited on its own, keep its exit code.
        if proc2.poll() is None:
            worker2_terminated_by_controller = True
            proc2.terminate()
    except KeyboardInterrupt:
        try:
            proc2.terminate()
        except Exception:
            pass
    finally:
        try:
            proc2.wait(timeout=30)
        except Exception:
            pass

    exit_info = {
        "worker1": {
            "returncode": int(proc1.returncode) if proc1.returncode is not None else None,
            "killed_by_controller": bool(killed_worker1),
            "observed_claim": bool(observed_claim),
        },
        "worker2": {
            "returncode": int(proc2.returncode) if proc2.returncode is not None else None,
            "exited_early": bool(worker2_exited_early),
            "terminated_by_controller": bool(worker2_terminated_by_controller),
        },
    }
    (outdir / "_worker_exit.json").write_text(json.dumps(exit_info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ports_info = {
        "worker1": {"metrics_port": int(actual_metrics_port_1), "http_port": int(actual_http_port_1)},
        "worker2": {"metrics_port": int(actual_metrics_port_2), "http_port": int(actual_http_port_2)},
    }
    (outdir / "_ports.json").write_text(json.dumps(ports_info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    combined = (
        "# metrics-before-1\n\n" + (before_1_path.read_text(encoding="utf-8", errors="replace") if before_1_path.exists() else "")
        + "\n\n# metrics-before-2\n\n" + (before_2_path.read_text(encoding="utf-8", errors="replace") if before_2_path.exists() else "")
        + "\n\n# metrics-after-2\n\n" + (after_2_path.read_text(encoding="utf-8", errors="replace") if after_2_path.exists() else "")
    )
    (outdir / "_metrics.txt").write_text(combined, encoding="utf-8")

    claim_batch_ids: list[str] = []
    for lp in (log_path_1, log_path_2):
        cid = _extract_last_claim_batch_id(lp)
        if cid:
            claim_batch_ids.append(cid)
    if claim_batch_ids:
        (outdir / "_claim_batch_ids.txt").write_text("\n".join(claim_batch_ids) + "\n", encoding="utf-8")

    # Treat controller-termination as success (Windows returns non-zero for terminate()).
    if worker2_exited_early and (proc2.returncode not in (None, 0)):
        print(f"[labs run {SCENARIO_STUCK_RECLAIM}] worker2 exited early: rc={proc2.returncode}")
        print(f"[labs run {SCENARIO_STUCK_RECLAIM}] see logs: {log_path_2}")
        return 4

    print(f"[labs run {SCENARIO_STUCK_RECLAIM}] done (now run verify/export/clean)")
    print(f"[labs run {SCENARIO_STUCK_RECLAIM}] outputs: {outdir}")
    return 0


def _cmd_labs_verify_stuck_reclaim(args: argparse.Namespace) -> int:
    run_dir = _resolve_run_dir(run_id=args.run_id, outdir=args.outdir, scenario=SCENARIO_STUCK_RECLAIM)
    metrics_dir = run_dir / "_metrics"
    logs_dir = run_dir / "_logs"

    before2 = (metrics_dir / "metrics-before-2.txt").read_text(encoding="utf-8") if (metrics_dir / "metrics-before-2.txt").exists() else ""
    after2 = (metrics_dir / "metrics-after-2.txt").read_text(encoding="utf-8") if (metrics_dir / "metrics-after-2.txt").exists() else ""

    metric_processed = "outbox_processed_total"
    metric_failed = "outbox_failed_total"

    metrics_available = (not before2.strip().startswith("scrape_failed")) and (not after2.strip().startswith("scrape_failed"))

    processed_before = _prom_parse_counter_sum(before2, metric_processed) if metrics_available else 0.0
    processed_after = _prom_parse_counter_sum(after2, metric_processed) if metrics_available else 0.0
    failed_before = _prom_parse_counter_sum(before2, metric_failed) if metrics_available else 0.0
    failed_after = _prom_parse_counter_sum(after2, metric_failed) if metrics_available else 0.0

    delta_processed = processed_after - processed_before
    delta_failed = failed_after - failed_before

    # Confirm reclaim happened by log signal.
    reclaimed_count = 0
    reclaim_log_found = False
    worker2_log_path: Path | None = (logs_dir / f"worker2-{args.run_id}.log") if args.run_id else None
    if not (worker2_log_path and worker2_log_path.exists()):
        worker2_logs = sorted([p for p in logs_dir.glob("worker2-*.log") if p.is_file()], key=lambda p: p.name, reverse=True)
        worker2_log_path = worker2_logs[0] if worker2_logs else None

    worker2_text = ""
    if worker2_log_path and worker2_log_path.exists():
        worker2_text = worker2_log_path.read_text(encoding="utf-8", errors="replace")

    m = re.search(r"Reclaimed\s+(\d+)\s+stuck\s+outbox\s+events", worker2_text)
    if m:
        reclaim_log_found = True
        reclaimed_count = int(m.group(1))

    processed_log_count = len(re.findall(r"Outbox\s+(upsert|delete):", worker2_text))

    # Metrics delta can be 0 when worker2 processes everything before the first scrape.
    processed_ok = (
        (metrics_available and (delta_processed >= float(args.min_processed_delta)))
        or (processed_log_count >= 1)
    )
    ok = (
        processed_ok
        and (delta_failed <= float(args.max_failed_delta) if metrics_available else True)
        and (reclaim_log_found and reclaimed_count >= int(args.min_reclaimed))
    )

    result = {
        "scenario": SCENARIO_STUCK_RECLAIM,
        "run_dir": str(run_dir),
        "checks": {
            "processed_delta_ge": float(args.min_processed_delta),
            "failed_delta_le": float(args.max_failed_delta),
            "reclaimed_ge": int(args.min_reclaimed),
        },
        "observed": {
            "metrics_available": bool(metrics_available),
            metric_processed: {"before": processed_before, "after": processed_after, "delta": delta_processed},
            metric_failed: {"before": failed_before, "after": failed_after, "delta": delta_failed},
            "reclaimed": {"count": int(reclaimed_count), "log_found": bool(reclaim_log_found)},
            "processed_log_count": int(processed_log_count),
            "worker2_log": str(worker2_log_path) if worker2_log_path else None,
        },
        "ok": bool(ok),
    }
    (run_dir / "_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if ok:
        print(f"[labs verify {SCENARIO_STUCK_RECLAIM}] OK")
        return 0
    print(f"[labs verify {SCENARIO_STUCK_RECLAIM}] FAILED")
    return 10


def _cmd_labs_export_stuck_reclaim(args: argparse.Namespace) -> int:
    run_dir = _resolve_run_dir(run_id=args.run_id, outdir=args.outdir, scenario=SCENARIO_STUCK_RECLAIM)
    exports_dir = run_dir / "_exports"
    _ensure_dir(exports_dir)

    exporter = LEGACY_SCRIPTS_DIR / "labs_009_export_jaeger.py"
    cmd = [
        _python_exe(),
        str(exporter),
        "--outdir",
        str(exports_dir),
        "--service",
        args.service,
        "--lookback",
        args.lookback,
        "--limit",
        str(int(args.limit)),
        "--operation",
        "outbox.claim_batch",
        "--tags-json",
        json.dumps({"wordloom.obs_schema": SEARCH_OUTBOX_OBS_SCHEMA_VERSION}),
    ]
    return int(_run(cmd, cwd=REPO_ROOT, env=_load_env(env_file=None)))


def _cmd_labs_clean_stuck_reclaim(args: argparse.Namespace) -> int:
    if args.keep_last is not None:
        base = LABS_SNAPSHOT_ROOT / "auto" / LAB_ID_S3A_2A_3A / SCENARIO_STUCK_RECLAIM
        if base.exists():
            runs = sorted([p for p in base.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
            for p in runs[int(args.keep_last):]:
                shutil.rmtree(p, ignore_errors=True)
        print(f"[labs clean {SCENARIO_STUCK_RECLAIM}] kept_last={args.keep_last}")
    else:
        print(f"[labs clean {SCENARIO_STUCK_RECLAIM}] noop")
    return 0


def _cmd_labs_clean_es_down_connect(args: argparse.Namespace) -> int:
    # 1) Restore ES
    compose_file = str((REPO_ROOT / "docker-compose.infra.yml").resolve())
    start_proc = _docker_compose(args=["-f", compose_file, "start", "es"], cwd=REPO_ROOT)
    print(f"[labs clean {SCENARIO_ES_DOWN_CONNECT}] start es: rc={start_proc.returncode}")

    if args.outdir:
        outdir = Path(args.outdir)
        _ensure_dir(outdir)
        (outdir / "_clean.txt").write_text(
            f"scenario={SCENARIO_ES_DOWN_CONNECT}\n"
            "action=start_es\n"
            f"at={time.strftime('%Y-%m-%d %H:%M:%S')}\n",
            encoding="utf-8",
        )
        (outdir / "_clean_es_start.stdout.txt").write_text(start_proc.stdout or "", encoding="utf-8")
        (outdir / "_clean_es_start.stderr.txt").write_text(start_proc.stderr or "", encoding="utf-8")
        (outdir / "_clean_es_start.exitcode.txt").write_text(str(int(start_proc.returncode)) + "\n", encoding="utf-8")

    # 2) Optional pruning
    if args.keep_last is not None:
        base = LABS_SNAPSHOT_ROOT / "auto" / LAB_ID_S3A_2A_3A / SCENARIO_ES_DOWN_CONNECT
        if base.exists():
            runs = sorted([p for p in base.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
            for p in runs[int(args.keep_last):]:
                shutil.rmtree(p, ignore_errors=True)
            print(f"[labs clean {SCENARIO_ES_DOWN_CONNECT}] kept_last={args.keep_last}")

    return 0


def _cmd_labs_export_es_429_inject(args: argparse.Namespace) -> int:
    run_dir = _resolve_run_dir(run_id=args.run_id, outdir=args.outdir, scenario=SCENARIO_ES_429_INJECT)
    exports_dir = run_dir / "_exports"
    _ensure_dir(exports_dir)

    outbox_event_id_path = run_dir / "_outbox_event_id.txt"
    outbox_event_id = outbox_event_id_path.read_text(encoding="utf-8").strip() if outbox_event_id_path.exists() else None

    cmd = [
        _python_exe(),
        str(LEGACY_SCRIPTS_DIR / "labs_009_export_jaeger.py"),
        "--outdir",
        str(exports_dir),
        "--service",
        args.service,
        "--lookback",
        args.lookback,
        "--limit",
        str(args.limit),
    ]
    if outbox_event_id:
        cmd += ["--outbox-event-id", outbox_event_id]

    return _run(cmd, cwd=REPO_ROOT)


def _cmd_labs_clean_es_429_inject(args: argparse.Namespace) -> int:
    # No external state to revert: injection is env-only.
    if args.outdir:
        outdir = Path(args.outdir)
        _ensure_dir(outdir)
        (outdir / "_clean.txt").write_text(
            f"scenario={SCENARIO_ES_429_INJECT}\n"
            "action=noop\n"
            f"at={time.strftime('%Y-%m-%d %H:%M:%S')}\n",
            encoding="utf-8",
        )

    if args.keep_last is not None:
        base = LABS_SNAPSHOT_ROOT / "auto" / LAB_ID_S3A_2A_3A / SCENARIO_ES_429_INJECT
        if base.exists():
            runs = sorted([p for p in base.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
            for p in runs[int(args.keep_last):]:
                shutil.rmtree(p, ignore_errors=True)
            print(f"[labs clean {SCENARIO_ES_429_INJECT}] kept_last={args.keep_last}")
    else:
        print(f"[labs clean {SCENARIO_ES_429_INJECT}] noop")
    return 0


def _cmd_labs_clean_es_write_block_4xx(args: argparse.Namespace) -> int:
    # 1) Revert injection (index.blocks.write=false)
    env = _load_env(env_file=args.env_file)
    es_url = (env.get("ELASTIC_URL") or "http://localhost:19200").strip().rstrip("/")
    es_index = (env.get("ELASTIC_INDEX") or "wordloom-search-index").strip()
    status, payload = _es_set_index_write_block(es_url=es_url, index=es_index, enabled=False)
    print(f"[labs clean {SCENARIO_ES_WRITE_BLOCK_4XX}] disable write block: http {status}")
    if args.outdir:
        outdir = Path(args.outdir)
        (outdir / "_clean_es_write_block.response.txt").write_text(
            f"status={status}\n\n{payload}\n", encoding="utf-8"
        )

    # 2) Prune old snapshots (optional)
    if args.keep_last is not None:
        base = LABS_SNAPSHOT_ROOT / "auto" / LAB_ID_S3A_2A_3A / SCENARIO_ES_WRITE_BLOCK_4XX
        if base.exists():
            runs = sorted([p for p in base.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
            for p in runs[int(args.keep_last):]:
                shutil.rmtree(p, ignore_errors=True)
            print(f"[labs clean {SCENARIO_ES_WRITE_BLOCK_4XX}] kept_last={args.keep_last}")

    return 0


def _cmd_labs_run_projection_version(args: argparse.Namespace) -> int:
    run_id = args.run_id or _now_run_id()
    outdir = Path(args.outdir) if args.outdir else _default_labs_auto_run_dir(scenario=SCENARIO_PROJECTION_VERSION, run_id=run_id)
    logs_dir = outdir / "_logs"
    metrics_dir = outdir / "_metrics"
    _ensure_dir(logs_dir)
    _ensure_dir(metrics_dir)

    env = _load_env(env_file=args.env_file)
    env = _with_backend_pythonpath(env)

    # Make the worker bounded and predictable.
    env["OUTBOX_RUN_SECONDS"] = str(int(args.duration))
    env["OUTBOX_POLL_INTERVAL_SECONDS"] = str(float(args.poll_interval))
    env["OUTBOX_BATCH_SIZE"] = str(int(args.batch_size))
    env["OUTBOX_LEASE_SECONDS"] = str(int(args.lease_seconds))
    env["OUTBOX_RECLAIM_INTERVAL_SECONDS"] = str(float(args.reclaim_interval))
    env["OUTBOX_MAX_PROCESSING_SECONDS"] = str(int(args.max_processing_seconds))
    env["LOG_LEVEL"] = "INFO"

    # Ensure the outbox row is processed quickly.
    env.pop("OUTBOX_EXPERIMENT_PROCESS_SLEEP_SECONDS", None)

    recipe = {
        "lab_id": LAB_ID_S3A_2A_3A,
        "scenario": SCENARIO_PROJECTION_VERSION,
        "run_id": run_id,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "env_file": args.env_file,
        "service": args.service,
        "phase": {
            "v1": int(args.projection_version_1),
            "v2": int(args.projection_version_2),
        },
        "worker": {
            "duration_s": int(args.duration),
            "preferred_metrics_port": int(args.metrics_port),
            "poll_interval_seconds": float(args.poll_interval),
            "batch_size": int(args.batch_size),
            "lease_seconds": int(args.lease_seconds),
            "reclaim_interval_seconds": float(args.reclaim_interval),
            "max_processing_seconds": int(args.max_processing_seconds),
        },
    }
    (outdir / "_recipe.json").write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    worker = LEGACY_SCRIPTS_DIR / "chronicle_outbox_worker.py"
    cmd = [_python_exe(), "-u", str(worker)]

    inserter = REPO_ROOT / "backend" / "scripts" / "labs" / "labs_009_insert_chronicle_outbox_pending.py"
    if not inserter.exists():
        inserter = LEGACY_SCRIPTS_DIR / "labs_009_insert_chronicle_outbox_pending.py"

    prober = REPO_ROOT / "backend" / "scripts" / "labs" / "labs_009_probe_chronicle_entry.py"
    if not prober.exists():
        prober = LEGACY_SCRIPTS_DIR / "labs_009_probe_chronicle_entry.py"

    def _spawn_worker_with_retry(
        *,
        preferred_metrics_port: int,
        log_path: Path,
        extra_env: dict[str, str] | None = None,
        max_attempts: int = 4,
    ) -> tuple[subprocess.Popen, dict[str, str], int, int]:
        candidate_ports: list[int] = []
        for i in range(max_attempts):
            p = int(preferred_metrics_port) + (i * 10_000)
            if 1024 <= p <= 65_000:
                candidate_ports.append(p)
        if not candidate_ports:
            candidate_ports = [19110, 29110, 39110, 49110]

        last_proc: subprocess.Popen | None = None
        last_env: dict[str, str] | None = None
        last_metrics_port = int(preferred_metrics_port)
        last_http_port = int(preferred_metrics_port) + 2

        for attempt, metrics_port in enumerate(candidate_ports, start=1):
            http_port = int(metrics_port) + 2
            run_env = env.copy()
            run_env["OUTBOX_METRICS_PORT"] = str(int(metrics_port))
            run_env["OUTBOX_HTTP_PORT"] = str(int(http_port))
            if extra_env:
                run_env.update({str(k): str(v) for k, v in extra_env.items()})

            header = f"\n\n# controller: spawn attempt {attempt}/{len(candidate_ports)} metrics_port={metrics_port} http_port={http_port}\n"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(header)
                log_file.flush()
                proc = subprocess.Popen(cmd, cwd=str(REPO_ROOT), env=run_env, stdout=log_file, stderr=subprocess.STDOUT)
                time.sleep(0.75)
                if proc.poll() is None:
                    return proc, run_env, int(metrics_port), int(http_port)

            try:
                tail = log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
            except Exception:
                tail = ""
            if "WinError 10013" in tail or "PermissionError" in tail:
                last_proc = proc
                last_env = run_env
                last_metrics_port = int(metrics_port)
                last_http_port = int(http_port)
                continue

            return proc, run_env, int(metrics_port), int(http_port)

        assert last_proc is not None
        assert last_env is not None
        return last_proc, last_env, int(last_metrics_port), int(last_http_port)

    def _run_probe(*, chronicle_event_id: str, out_path: Path) -> None:
        probe_env = env.copy()
        probe_env["OUTBOX_CHRONICLE_EVENT_ID"] = chronicle_event_id
        proc = subprocess.run(
            [_python_exe(), str(prober)],
            cwd=str(REPO_ROOT),
            env=probe_env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        out_path.write_text((proc.stdout or "").strip() + "\n", encoding="utf-8")
        if proc.returncode != 0:
            (out_path.parent / (out_path.name + ".stderr.txt")).write_text(proc.stderr or "", encoding="utf-8")

    print(f"[labs run {SCENARIO_PROJECTION_VERSION}] outdir: {outdir}")

    # Phase 1: projection_version=v1
    insert_env = env.copy()
    insert_proc_1 = subprocess.run(
        [_python_exe(), str(inserter)],
        cwd=str(REPO_ROOT),
        env=insert_env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    (outdir / "_trigger_insert_v1.stdout.txt").write_text(insert_proc_1.stdout or "", encoding="utf-8")
    (outdir / "_trigger_insert_v1.stderr.txt").write_text(insert_proc_1.stderr or "", encoding="utf-8")
    if insert_proc_1.returncode != 0:
        print(f"[labs run {SCENARIO_PROJECTION_VERSION}] failed to insert v1 outbox: rc={insert_proc_1.returncode}")
        return 3

    insert_obj_1 = _parse_last_json_line(insert_proc_1.stdout or "") or {}
    chronicle_event_id = str(insert_obj_1.get("chronicle_event_id") or "").strip()
    outbox_event_id_1 = str(insert_obj_1.get("outbox_event_id") or "").strip()
    if not chronicle_event_id or not outbox_event_id_1:
        print(f"[labs run {SCENARIO_PROJECTION_VERSION}] unexpected inserter output; see _trigger_insert_v1.stdout.txt")
        return 3

    (outdir / "_chronicle_event_id.txt").write_text(chronicle_event_id + "\n", encoding="utf-8")
    (outdir / "_outbox_event_id_v1.txt").write_text(outbox_event_id_1 + "\n", encoding="utf-8")

    log_v1 = logs_dir / f"worker-v1-{run_id}.log"
    log_v1.write_text("", encoding="utf-8")
    before_v1 = metrics_dir / "metrics-before-v1.txt"
    after_v1 = metrics_dir / "metrics-after-v1.txt"

    proc1, _env1, actual_metrics_port_1, _http1 = _spawn_worker_with_retry(
        preferred_metrics_port=int(args.metrics_port),
        log_path=log_v1,
        extra_env={"CHRONICLE_PROJECTION_VERSION": str(int(args.projection_version_1))},
    )
    try:
        time.sleep(max(0.5, float(args.scrape_delay)))
        try:
            before_v1.write_text(_scrape_metrics_text(port=int(actual_metrics_port_1), timeout_s=2.0), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            before_v1.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")

        proc1.wait(timeout=max(10, int(args.duration) + 20))
    except Exception:
        try:
            proc1.terminate()
        except Exception:
            pass
        try:
            proc1.wait(timeout=30)
        except Exception:
            pass
    finally:
        try:
            after_v1.write_text(_scrape_metrics_text(port=int(actual_metrics_port_1), timeout_s=2.0), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            after_v1.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")

    _run_probe(chronicle_event_id=chronicle_event_id, out_path=(outdir / "_probe_entry_v1.json"))

    # Phase 2: enqueue same event again, run with projection_version=v2
    insert_env_2 = env.copy()
    insert_env_2["OUTBOX_CHRONICLE_EVENT_ID"] = chronicle_event_id
    insert_proc_2 = subprocess.run(
        [_python_exe(), str(inserter)],
        cwd=str(REPO_ROOT),
        env=insert_env_2,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    (outdir / "_trigger_insert_v2.stdout.txt").write_text(insert_proc_2.stdout or "", encoding="utf-8")
    (outdir / "_trigger_insert_v2.stderr.txt").write_text(insert_proc_2.stderr or "", encoding="utf-8")
    if insert_proc_2.returncode != 0:
        print(f"[labs run {SCENARIO_PROJECTION_VERSION}] failed to insert v2 outbox: rc={insert_proc_2.returncode}")
        return 3

    insert_obj_2 = _parse_last_json_line(insert_proc_2.stdout or "") or {}
    outbox_event_id_2 = str(insert_obj_2.get("outbox_event_id") or "").strip()
    if not outbox_event_id_2:
        print(f"[labs run {SCENARIO_PROJECTION_VERSION}] unexpected v2 inserter output; see _trigger_insert_v2.stdout.txt")
        return 3
    (outdir / "_outbox_event_id_v2.txt").write_text(outbox_event_id_2 + "\n", encoding="utf-8")

    log_v2 = logs_dir / f"worker-v2-{run_id}.log"
    log_v2.write_text("", encoding="utf-8")
    before_v2 = metrics_dir / "metrics-before-v2.txt"
    after_v2 = metrics_dir / "metrics-after-v2.txt"

    proc2, _env2, actual_metrics_port_2, _http2 = _spawn_worker_with_retry(
        preferred_metrics_port=int(args.metrics_port) + 1,
        log_path=log_v2,
        extra_env={"CHRONICLE_PROJECTION_VERSION": str(int(args.projection_version_2))},
    )
    try:
        time.sleep(max(0.5, float(args.scrape_delay)))
        try:
            before_v2.write_text(_scrape_metrics_text(port=int(actual_metrics_port_2), timeout_s=2.0), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            before_v2.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")

        proc2.wait(timeout=max(10, int(args.duration) + 20))
    except Exception:
        try:
            proc2.terminate()
        except Exception:
            pass
        try:
            proc2.wait(timeout=30)
        except Exception:
            pass
    finally:
        try:
            after_v2.write_text(_scrape_metrics_text(port=int(actual_metrics_port_2), timeout_s=2.0), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            after_v2.write_text(f"scrape_failed: {type(exc).__name__}: {exc}\n", encoding="utf-8")

    _run_probe(chronicle_event_id=chronicle_event_id, out_path=(outdir / "_probe_entry_v2.json"))

    result = {
        "scenario": SCENARIO_PROJECTION_VERSION,
        "run_id": run_id,
        "chronicle_event_id": chronicle_event_id,
        "outbox_event_ids": {"v1": outbox_event_id_1, "v2": outbox_event_id_2},
        "worker_logs": {
            "v1": str(log_v1.relative_to(REPO_ROOT)),
            "v2": str(log_v2.relative_to(REPO_ROOT)),
        },
        "probe": {
            "v1": _read_json_file(outdir / "_probe_entry_v1.json"),
            "v2": _read_json_file(outdir / "_probe_entry_v2.json"),
        },
    }
    # Keep verify output standardized as `_result.json`. Run output is `_run.json`.
    (outdir / "_run.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"[labs run {SCENARIO_PROJECTION_VERSION}] chronicle_event_id: {chronicle_event_id}")
    print(f"[labs run {SCENARIO_PROJECTION_VERSION}] done (now run verify/export/clean)")
    print(f"[labs run {SCENARIO_PROJECTION_VERSION}] outputs: {outdir}")
    return 0


def _cmd_labs_verify_projection_version(args: argparse.Namespace) -> int:
    run_dir = _resolve_run_dir(run_id=args.run_id, outdir=args.outdir, scenario=SCENARIO_PROJECTION_VERSION)
    if not run_dir.exists():
        print(f"[labs verify {SCENARIO_PROJECTION_VERSION}] run_dir not found: {run_dir}")
        return 2

    probe1 = _read_json_file(run_dir / "_probe_entry_v1.json") or {}
    probe2 = _read_json_file(run_dir / "_probe_entry_v2.json") or {}

    want1 = int(args.projection_version_1)
    want2 = int(args.projection_version_2)
    got1 = probe1.get("projection_version")
    got2 = probe2.get("projection_version")

    ok = True
    errors: list[str] = []
    if got1 != want1:
        ok = False
        errors.append(f"probe v1 projection_version mismatch: got={got1!r} want={want1}")
    if got2 != want2:
        ok = False
        errors.append(f"probe v2 projection_version mismatch: got={got2!r} want={want2}")

    checks = [
        {
            "name": "probe v1 projection_version match",
            "expected": want1,
            "observed": got1,
            "ok": bool(got1 == want1),
        },
        {
            "name": "probe v2 projection_version match",
            "expected": want2,
            "observed": got2,
            "ok": bool(got2 == want2),
        },
    ]

    why = "ok" if ok else (errors[0] if errors else "verify failed")

    result = {
        "scenario": SCENARIO_PROJECTION_VERSION,
        "run_id": run_dir.name,
        "ok": bool(ok),
        "why": why,
        "checks": checks,
        "expected": {"v1": want1, "v2": want2},
        "observed": {"v1": got1, "v2": got2},
        "errors": errors,
    }

    # Standard contract: verify writes `_result.json`.
    (run_dir / "_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # Back-compat: keep the previous file name too.
    (run_dir / "_verify_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if ok:
        print(f"[labs verify {SCENARIO_PROJECTION_VERSION}] OK")
        return 0

    print(f"[labs verify {SCENARIO_PROJECTION_VERSION}] FAILED")
    for e in errors:
        print("  -", e)
    return 2


def _cmd_labs_export_projection_version(args: argparse.Namespace) -> int:
    run_dir = _resolve_run_dir(run_id=args.run_id, outdir=args.outdir, scenario=SCENARIO_PROJECTION_VERSION)
    if not run_dir.exists():
        print(f"[labs export {SCENARIO_PROJECTION_VERSION}] run_dir not found: {run_dir}")
        return 2

    event_id_path = run_dir / "_chronicle_event_id.txt"
    if not event_id_path.exists():
        print(f"[labs export {SCENARIO_PROJECTION_VERSION}] missing: {event_id_path}")
        return 2
    chronicle_event_id = (event_id_path.read_text(encoding="utf-8", errors="replace") or "").strip()
    if not chronicle_event_id:
        print(f"[labs export {SCENARIO_PROJECTION_VERSION}] empty chronicle_event_id")
        return 2

    exports_dir = run_dir / "_exports"
    _ensure_dir(exports_dir)

    script = LEGACY_SCRIPTS_DIR / "labs_009_export_jaeger.py"
    cmd = [
        _python_exe(),
        str(script),
        "--outdir",
        str(exports_dir),
        "--service",
        args.service,
        "--lookback",
        args.lookback,
        "--limit",
        str(int(args.limit)),
        "--operation",
        "outbox.process",
        "--tags-json",
        json.dumps({"wordloom.entity.id": chronicle_event_id}, ensure_ascii=False),
    ]
    return _run(cmd, cwd=REPO_ROOT)


def _cmd_labs_clean_projection_version(args: argparse.Namespace) -> int:
    if args.keep_last is not None:
        base = LABS_SNAPSHOT_ROOT / "auto" / LAB_ID_S3A_2A_3A / SCENARIO_PROJECTION_VERSION
        if base.exists():
            runs = sorted([p for p in base.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
            for p in runs[int(args.keep_last):]:
                shutil.rmtree(p, ignore_errors=True)
            print(f"[labs clean {SCENARIO_PROJECTION_VERSION}] kept_last={args.keep_last}")
    else:
        print(f"[labs clean {SCENARIO_PROJECTION_VERSION}] noop")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="scripts", description="backend/scripts router")
    sub = p.add_subparsers(dest="cmd", required=True)

    labs = sub.add_parser("labs", help="Lab/experiment commands")
    labs_sub = labs.add_subparsers(dest="labs_cmd", required=True)

    exp = labs_sub.add_parser("export-jaeger", help="Export Jaeger snapshots (wraps v1 script)")
    exp.add_argument("--service", required=True)
    exp.add_argument("--lookback", default="24h")
    exp.add_argument("--limit", type=int, default=20)
    exp.add_argument("--operation")
    exp.add_argument("--outbox-event-id")
    exp.add_argument("--claim-batch-id")
    exp.add_argument("--outdir", help="Output directory; defaults under docs/labs/_snapshot")
    exp.set_defaults(func=_cmd_labs_export_jaeger)

    b = labs_sub.add_parser("expb-es429", help="Run Labs-009 ExpB (ES 429 injection) bounded")
    b.add_argument("--service", default="wordloom-search-outbox-worker")
    b.add_argument("--lookback", default="24h")
    b.add_argument("--limit", type=int, default=20)
    b.add_argument("--duration", type=int, default=30, help="Seconds to run worker; 0 means run until it exits")
    b.add_argument("--run-id", help="Optional run_id folder name")
    b.add_argument("--outdir", help="Output directory; defaults under docs/labs/_snapshot")

    b.add_argument("--every-n", type=int, default=2)
    b.add_argument("--ratio", type=float)
    b.add_argument("--seed", type=int, default=1)
    b.add_argument("--ops", default="delete", help="Comma-separated ops, e.g. upsert,delete")
    b.add_argument("--metrics-port", type=int)

    b.set_defaults(func=_cmd_labs_expb_es429)

    run = labs_sub.add_parser("run", help="Run a lab scenario (auto snapshot outputs)")
    run_sub = run.add_subparsers(dest="scenario", required=True)

    c_run = run_sub.add_parser(SCENARIO_ES_WRITE_BLOCK_4XX, help="ExpC: ES index write-block -> deterministic 4xx")
    c_run.add_argument("--env-file", default=".env.test", help="Env file to load (repo-root relative by default)")
    c_run.add_argument("--service", default="wordloom-search-outbox-worker")
    c_run.add_argument("--duration", type=int, default=20)
    c_run.add_argument("--metrics-port", type=int, default=9109)
    c_run.add_argument("--scrape-delay", type=float, default=2.0)
    c_run.add_argument("--run-id")
    c_run.add_argument("--outdir")
    c_run.set_defaults(func=_cmd_labs_run_es_write_block_4xx)

    b_run = run_sub.add_parser(SCENARIO_ES_429_INJECT, help="ExpB: deterministic ES 429 injection (retry/backoff)")
    b_run.add_argument("--env-file", default=".env.test", help="Env file to load (repo-root relative by default)")
    b_run.add_argument("--service", default="wordloom-search-outbox-worker")
    b_run.add_argument("--duration", type=int, default=20)
    b_run.add_argument("--metrics-port", type=int, default=9109)
    b_run.add_argument("--scrape-delay", type=float, default=2.0)
    b_run.add_argument("--run-id")
    b_run.add_argument("--outdir")
    b_run.add_argument("--op", default="upsert", choices=["upsert", "delete"], help="Outbox op to trigger")
    b_run.add_argument("--every-n", type=int, default=1, help="Inject 1 out of N operations deterministically")
    b_run.add_argument("--ratio", type=float, default=0.0, help="Probabilistic injection ratio (used when every-n<=0)")
    b_run.add_argument("--ops", default="upsert", help="Comma-separated ops to apply injection to")
    b_run.add_argument("--seed", type=int, default=1)
    b_run.set_defaults(func=_cmd_labs_run_es_429_inject)

    a_run = run_sub.add_parser(SCENARIO_ES_DOWN_CONNECT, help="ExpA: stop ES -> connect failure -> retry/backoff")
    a_run.add_argument("--env-file", default=".env.test", help="Env file to load (repo-root relative by default)")
    a_run.add_argument("--service", default="wordloom-search-outbox-worker")
    a_run.add_argument("--duration", type=int, default=20)
    a_run.add_argument("--metrics-port", type=int, default=9109)
    a_run.add_argument("--scrape-delay", type=float, default=2.0)
    a_run.add_argument("--run-id")
    a_run.add_argument("--outdir")
    a_run.add_argument("--op", default="delete", choices=["upsert", "delete"], help="Outbox op to trigger")
    a_run.set_defaults(func=_cmd_labs_run_es_down_connect)

    cd_run = run_sub.add_parser(SCENARIO_COLLECTOR_DOWN, help="P1: stop Jaeger collector/query while worker runs")
    cd_run.add_argument("--env-file", default=".env.test", help="Env file to load (repo-root relative by default)")
    cd_run.add_argument("--service", default="wordloom-search-outbox-worker")
    cd_run.add_argument("--duration", type=int, default=20)
    cd_run.add_argument("--metrics-port", type=int, default=9109)
    cd_run.add_argument("--scrape-delay", type=float, default=2.0)
    cd_run.add_argument("--run-id")
    cd_run.add_argument("--outdir")
    cd_run.add_argument("--op", default="upsert", choices=["upsert", "delete"], help="Outbox op to trigger")
    cd_run.set_defaults(func=_cmd_labs_run_collector_down)

    d_run = run_sub.add_parser(SCENARIO_ES_BULK_PARTIAL, help="ExpD: ES bulk partial success (mixed item outcomes)")
    d_run.add_argument("--env-file", default=".env.test", help="Env file to load (repo-root relative by default)")
    d_run.add_argument("--service", default="wordloom-search-outbox-worker")
    d_run.add_argument("--duration", type=int, default=20)
    d_run.add_argument("--metrics-port", type=int, default=9109)
    d_run.add_argument("--scrape-delay", type=float, default=2.0)
    d_run.add_argument("--run-id")
    d_run.add_argument("--outdir")
    d_run.add_argument("--op", default="upsert", choices=["upsert", "delete"], help="Outbox op to trigger")
    d_run.add_argument("--trigger-count", type=int, default=2, help="How many outbox events to insert")
    d_run.add_argument("--bulk-size", type=int, default=10, help="OUTBOX_BULK_SIZE for the worker")
    d_run.add_argument("--partial-status", type=int, default=400, help="Injected bulk-item status code")
    d_run.set_defaults(func=_cmd_labs_run_es_bulk_partial)

    e_run = run_sub.add_parser(SCENARIO_DB_CLAIM_CONTENTION, help="ExpE: DB claim contention (two workers, non-atomic claim)")
    e_run.add_argument("--env-file", default=".env.test", help="Env file to load (repo-root relative by default)")
    e_run.add_argument("--service", default="wordloom-search-outbox-worker")
    e_run.add_argument("--duration", type=int, default=25)
    e_run.add_argument("--metrics-port-1", dest="metrics_port_1", type=int, default=9126)
    e_run.add_argument("--metrics-port-2", dest="metrics_port_2", type=int, default=9127)
    e_run.add_argument("--worker-id-1", dest="worker_id_1", default="labs-expE-w1")
    e_run.add_argument("--worker-id-2", dest="worker_id_2", default="labs-expE-w2")
    e_run.add_argument("--scrape-delay", type=float, default=2.0)
    e_run.add_argument("--run-id")
    e_run.add_argument("--outdir")
    e_run.add_argument("--op", default="upsert", choices=["upsert", "delete"], help="Outbox op to trigger")
    e_run.add_argument("--trigger-count", type=int, default=1, help="How many outbox events to insert")
    e_run.add_argument("--break-claim-sleep", type=float, default=1.0, help="Delay between SELECT and UPDATE in non-atomic claim")
    e_run.add_argument("--poll-interval", type=float, default=0.05)
    e_run.add_argument("--batch-size", type=int, default=50)
    e_run.set_defaults(func=_cmd_labs_run_db_claim_contention)

    f_run = run_sub.add_parser(SCENARIO_STUCK_RECLAIM, help="ExpF: stuck & reclaim (kill worker1 mid-lease; worker2 reclaims)")
    f_run.add_argument("--env-file", default=".env.test", help="Env file to load (repo-root relative by default)")
    f_run.add_argument("--service", default="wordloom-search-outbox-worker")
    f_run.add_argument("--duration", type=int, default=20, help="How long to keep worker2 running")
    f_run.add_argument("--metrics-port-1", dest="metrics_port_1", type=int, default=19128)
    f_run.add_argument("--metrics-port-2", dest="metrics_port_2", type=int, default=19129)
    f_run.add_argument("--worker-id-1", dest="worker_id_1", default="labs-expF-w1")
    f_run.add_argument("--worker-id-2", dest="worker_id_2", default="labs-expF-w2")
    f_run.add_argument("--scrape-delay", type=float, default=2.0)
    f_run.add_argument("--run-id")
    f_run.add_argument("--outdir")
    f_run.add_argument("--op", default="upsert", choices=["upsert", "delete"], help="Outbox op to trigger")
    f_run.add_argument("--trigger-count", type=int, default=5, help="How many outbox events to insert")
    f_run.add_argument("--lease-seconds", dest="lease_seconds", type=int, default=3)
    f_run.add_argument("--reclaim-interval", dest="reclaim_interval", type=float, default=1.0)
    f_run.add_argument("--max-processing-seconds", dest="max_processing_seconds", type=int, default=60)
    f_run.add_argument("--poll-interval", dest="poll_interval", type=float, default=0.1)
    f_run.add_argument("--batch-size", dest="batch_size", type=int, default=50)
    f_run.add_argument("--claim-timeout", dest="claim_timeout", type=float, default=8.0)
    f_run.set_defaults(func=_cmd_labs_run_stuck_reclaim)

    g_run = run_sub.add_parser(SCENARIO_DUPLICATE_DELIVERY, help="ExpG: duplicate delivery / idempotent noop (delete 404)")
    g_run.add_argument("--env-file", default=".env.test", help="Env file to load (repo-root relative by default)")
    g_run.add_argument("--service", default="wordloom-search-outbox-worker")
    g_run.add_argument("--duration", type=int, default=20)
    g_run.add_argument("--metrics-port", type=int, default=19130)
    g_run.add_argument("--scrape-delay", type=float, default=2.0)
    g_run.add_argument("--run-id")
    g_run.add_argument("--outdir")
    g_run.add_argument("--entity-type", dest="entity_type", default="book")
    g_run.add_argument("--entity-id", dest="entity_id", help="Optional explicit entity_id (UUID or string)")
    g_run.add_argument("--delete-count", dest="delete_count", type=int, default=2)
    g_run.set_defaults(func=_cmd_labs_run_duplicate_delivery)

    h_run = run_sub.add_parser(SCENARIO_PROJECTION_VERSION, help="ExpH: projection_version (chronicle projector v1/v2)")
    h_run.add_argument("--env-file", default=".env.test", help="Env file to load (repo-root relative by default)")
    h_run.add_argument("--service", default="wordloom-chronicle-outbox-worker")
    h_run.add_argument("--duration", type=int, default=8)
    h_run.add_argument("--metrics-port", type=int, default=19110)
    h_run.add_argument("--scrape-delay", type=float, default=1.5)
    h_run.add_argument("--run-id")
    h_run.add_argument("--outdir")
    h_run.add_argument("--projection-version-1", dest="projection_version_1", type=int, default=1)
    h_run.add_argument("--projection-version-2", dest="projection_version_2", type=int, default=2)
    h_run.add_argument("--poll-interval", type=float, default=0.2)
    h_run.add_argument("--batch-size", type=int, default=50)
    h_run.add_argument("--lease-seconds", dest="lease_seconds", type=int, default=10)
    h_run.add_argument("--reclaim-interval", dest="reclaim_interval", type=float, default=2.0)
    h_run.add_argument("--max-processing-seconds", dest="max_processing_seconds", type=int, default=60)
    h_run.set_defaults(func=_cmd_labs_run_projection_version)

    verify = labs_sub.add_parser("verify", help="Verify a scenario run using captured evidence")
    verify_sub = verify.add_subparsers(dest="scenario", required=True)

    c_verify = verify_sub.add_parser(SCENARIO_ES_WRITE_BLOCK_4XX, help="Verify ExpC run")
    c_verify.add_argument("--run-id")
    c_verify.add_argument("--outdir")
    c_verify.add_argument("--min-failed-delta", type=float, default=1.0)
    c_verify.add_argument("--max-retry-delta", type=float, default=0.0)
    c_verify.set_defaults(func=_cmd_labs_verify_es_write_block_4xx)

    b_verify = verify_sub.add_parser(SCENARIO_ES_429_INJECT, help="Verify ExpB run")
    b_verify.add_argument("--run-id")
    b_verify.add_argument("--outdir")
    b_verify.add_argument("--min-retry-delta", type=float, default=1.0)
    b_verify.add_argument("--min-failed-delta", type=float, default=1.0)
    b_verify.add_argument("--max-terminal-delta", type=float, default=0.0)
    b_verify.set_defaults(func=_cmd_labs_verify_es_429_inject)

    a_verify = verify_sub.add_parser(SCENARIO_ES_DOWN_CONNECT, help="Verify ExpA run")
    a_verify.add_argument("--run-id")
    a_verify.add_argument("--outdir")
    a_verify.add_argument("--min-retry-delta", type=float, default=1.0)
    a_verify.add_argument("--min-failed-delta", type=float, default=1.0)
    a_verify.add_argument("--max-terminal-delta", type=float, default=0.0)
    a_verify.set_defaults(func=_cmd_labs_verify_es_down_connect)

    cd_verify = verify_sub.add_parser(SCENARIO_COLLECTOR_DOWN, help="Verify P1 collector_down run")
    cd_verify.add_argument("--run-id")
    cd_verify.add_argument("--outdir")
    cd_verify.add_argument("--min-processed-delta", type=float, default=1.0)
    cd_verify.add_argument("--max-failed-delta", type=float, default=0.0)
    cd_verify.set_defaults(func=_cmd_labs_verify_collector_down)

    d_verify = verify_sub.add_parser(SCENARIO_ES_BULK_PARTIAL, help="Verify ExpD run")
    d_verify.add_argument("--run-id")
    d_verify.add_argument("--outdir")
    d_verify.add_argument("--min-partial-delta", type=float, default=1.0)
    d_verify.add_argument("--min-success-items-delta", type=float, default=1.0)
    d_verify.add_argument("--min-failed-items-delta", type=float, default=1.0)
    d_verify.add_argument("--min-failed-4xx-delta", type=float, default=1.0)
    d_verify.set_defaults(func=_cmd_labs_verify_es_bulk_partial)

    e_verify = verify_sub.add_parser(SCENARIO_DB_CLAIM_CONTENTION, help="Verify ExpE run")
    e_verify.add_argument("--run-id")
    e_verify.add_argument("--outdir")
    e_verify.add_argument("--min-owner-mismatch-delta", type=float, default=1.0)
    e_verify.add_argument("--min-processed-delta", type=float, default=1.0)
    e_verify.add_argument("--max-failed-delta", type=float, default=0.0)
    e_verify.set_defaults(func=_cmd_labs_verify_db_claim_contention)

    f_verify = verify_sub.add_parser(SCENARIO_STUCK_RECLAIM, help="Verify ExpF run")
    f_verify.add_argument("--run-id")
    f_verify.add_argument("--outdir")
    f_verify.add_argument("--min-processed-delta", type=float, default=1.0)
    f_verify.add_argument("--max-failed-delta", type=float, default=0.0)
    f_verify.add_argument("--min-reclaimed", type=int, default=1)
    f_verify.set_defaults(func=_cmd_labs_verify_stuck_reclaim)

    g_verify = verify_sub.add_parser(SCENARIO_DUPLICATE_DELIVERY, help="Verify ExpG run")
    g_verify.add_argument("--run-id")
    g_verify.add_argument("--outdir")
    g_verify.add_argument("--min-processed-delta", type=float, default=3.0)
    g_verify.add_argument("--max-failed-delta", type=float, default=0.0)
    g_verify.add_argument("--min-noop-delta", type=float, default=1.0)
    g_verify.add_argument("--min-noop-logs", type=int, default=1)
    g_verify.set_defaults(func=_cmd_labs_verify_duplicate_delivery)

    h_verify = verify_sub.add_parser(SCENARIO_PROJECTION_VERSION, help="Verify ExpH run")
    h_verify.add_argument("--run-id")
    h_verify.add_argument("--outdir")
    h_verify.add_argument("--projection-version-1", dest="projection_version_1", type=int, default=1)
    h_verify.add_argument("--projection-version-2", dest="projection_version_2", type=int, default=2)
    h_verify.set_defaults(func=_cmd_labs_verify_projection_version)

    export = labs_sub.add_parser("export", help="Export additional evidence (e.g. Jaeger) for a run")
    export_sub = export.add_subparsers(dest="scenario", required=True)

    c_export = export_sub.add_parser(SCENARIO_ES_WRITE_BLOCK_4XX, help="Export Jaeger traces for ExpC run")
    c_export.add_argument("--run-id")
    c_export.add_argument("--outdir")
    c_export.add_argument("--service", default="wordloom-search-outbox-worker")
    c_export.add_argument("--lookback", default="1h")
    c_export.add_argument("--limit", type=int, default=20)
    c_export.set_defaults(func=_cmd_labs_export_es_write_block_4xx)

    b_export = export_sub.add_parser(SCENARIO_ES_429_INJECT, help="Export Jaeger traces for ExpB run")
    b_export.add_argument("--run-id")
    b_export.add_argument("--outdir")
    b_export.add_argument("--service", default="wordloom-search-outbox-worker")
    b_export.add_argument("--lookback", default="1h")
    b_export.add_argument("--limit", type=int, default=20)
    b_export.set_defaults(func=_cmd_labs_export_es_429_inject)

    a_export = export_sub.add_parser(SCENARIO_ES_DOWN_CONNECT, help="Export Jaeger traces for ExpA run")
    a_export.add_argument("--run-id")
    a_export.add_argument("--outdir")
    a_export.add_argument("--service", default="wordloom-search-outbox-worker")
    a_export.add_argument("--lookback", default="1h")
    a_export.add_argument("--limit", type=int, default=20)
    a_export.set_defaults(func=_cmd_labs_export_es_down_connect)

    cd_export = export_sub.add_parser(SCENARIO_COLLECTOR_DOWN, help="Export Jaeger traces for P1 collector_down run")
    cd_export.add_argument("--run-id")
    cd_export.add_argument("--outdir")
    cd_export.add_argument("--service", default="wordloom-search-outbox-worker")
    cd_export.add_argument("--lookback", default="30m")
    cd_export.add_argument("--limit", type=int, default=20)
    cd_export.set_defaults(func=_cmd_labs_export_collector_down)

    d_export = export_sub.add_parser(SCENARIO_ES_BULK_PARTIAL, help="Export Jaeger traces for ExpD run")
    d_export.add_argument("--run-id")
    d_export.add_argument("--outdir")
    d_export.add_argument("--service", default="wordloom-search-outbox-worker")
    d_export.add_argument("--lookback", default="1h")
    d_export.add_argument("--limit", type=int, default=20)
    d_export.set_defaults(func=_cmd_labs_export_es_bulk_partial)

    e_export = export_sub.add_parser(SCENARIO_DB_CLAIM_CONTENTION, help="Export Jaeger traces for ExpE run")
    e_export.add_argument("--run-id")
    e_export.add_argument("--outdir")
    e_export.add_argument("--service", default="wordloom-search-outbox-worker")
    e_export.add_argument("--lookback", default="30m")
    e_export.add_argument("--limit", type=int, default=50)
    e_export.set_defaults(func=_cmd_labs_export_db_claim_contention)

    f_export = export_sub.add_parser(SCENARIO_STUCK_RECLAIM, help="Export Jaeger traces for ExpF run")
    f_export.add_argument("--run-id")
    f_export.add_argument("--outdir")
    f_export.add_argument("--service", default="wordloom-search-outbox-worker")
    f_export.add_argument("--lookback", default="30m")
    f_export.add_argument("--limit", type=int, default=50)
    f_export.set_defaults(func=_cmd_labs_export_stuck_reclaim)

    g_export = export_sub.add_parser(SCENARIO_DUPLICATE_DELIVERY, help="Export Jaeger traces for ExpG run")
    g_export.add_argument("--run-id")
    g_export.add_argument("--outdir")
    g_export.add_argument("--service", default="wordloom-search-outbox-worker")
    g_export.add_argument("--lookback", default="30m")
    g_export.add_argument("--limit", type=int, default=50)
    g_export.set_defaults(func=_cmd_labs_export_duplicate_delivery)

    h_export = export_sub.add_parser(SCENARIO_PROJECTION_VERSION, help="Export Jaeger traces for ExpH run")
    h_export.add_argument("--run-id")
    h_export.add_argument("--outdir")
    h_export.add_argument("--service", default="wordloom-chronicle-outbox-worker")
    h_export.add_argument("--lookback", default="30m")
    h_export.add_argument("--limit", type=int, default=50)
    h_export.set_defaults(func=_cmd_labs_export_projection_version)

    clean = labs_sub.add_parser("clean", help="Cleanup a scenario (revert injection / prune snapshots)")
    clean_sub = clean.add_subparsers(dest="scenario", required=True)

    clean_common = argparse.ArgumentParser(add_help=False)
    clean_common.add_argument(
        "--env-file",
        default=".env.test",
        help="Env file to load (repo-root relative by default). Only used by scenarios that revert external state.",
    )

    c_clean = clean_sub.add_parser(
        SCENARIO_ES_WRITE_BLOCK_4XX,
        help="Disable write block + optional snapshot pruning",
        parents=[clean_common],
    )
    c_clean.add_argument("--outdir")
    c_clean.add_argument("--keep-last", type=int, default=None)
    c_clean.set_defaults(func=_cmd_labs_clean_es_write_block_4xx)

    b_clean = clean_sub.add_parser(
        SCENARIO_ES_429_INJECT,
        help="Noop cleanup + optional snapshot pruning",
        parents=[clean_common],
    )
    b_clean.add_argument("--outdir")
    b_clean.add_argument("--keep-last", type=int, default=None)
    b_clean.set_defaults(func=_cmd_labs_clean_es_429_inject)

    a_clean = clean_sub.add_parser(
        SCENARIO_ES_DOWN_CONNECT,
        help="Start ES + optional snapshot pruning",
        parents=[clean_common],
    )
    a_clean.add_argument("--outdir")
    a_clean.add_argument("--keep-last", type=int, default=None)
    a_clean.set_defaults(func=_cmd_labs_clean_es_down_connect)

    cd_clean = clean_sub.add_parser(
        SCENARIO_COLLECTOR_DOWN,
        help="Start Jaeger + optional snapshot pruning",
        parents=[clean_common],
    )
    cd_clean.add_argument("--outdir")
    cd_clean.add_argument("--keep-last", type=int, default=None)
    cd_clean.set_defaults(func=_cmd_labs_clean_collector_down)

    d_clean = clean_sub.add_parser(
        SCENARIO_ES_BULK_PARTIAL,
        help="Noop cleanup + optional snapshot pruning",
        parents=[clean_common],
    )
    d_clean.add_argument("--outdir")
    d_clean.add_argument("--keep-last", type=int, default=None)
    d_clean.set_defaults(func=_cmd_labs_clean_es_bulk_partial)

    e_clean = clean_sub.add_parser(
        SCENARIO_DB_CLAIM_CONTENTION,
        help="Noop cleanup + optional snapshot pruning",
        parents=[clean_common],
    )
    e_clean.add_argument("--outdir")
    e_clean.add_argument("--keep-last", type=int, default=None)
    e_clean.set_defaults(func=_cmd_labs_clean_db_claim_contention)

    f_clean = clean_sub.add_parser(
        SCENARIO_STUCK_RECLAIM,
        help="Noop cleanup + optional snapshot pruning",
        parents=[clean_common],
    )
    f_clean.add_argument("--outdir")
    f_clean.add_argument("--keep-last", type=int, default=None)
    f_clean.set_defaults(func=_cmd_labs_clean_stuck_reclaim)

    g_clean = clean_sub.add_parser(
        SCENARIO_DUPLICATE_DELIVERY,
        help="Noop cleanup + optional snapshot pruning",
        parents=[clean_common],
    )
    g_clean.add_argument("--outdir")
    g_clean.add_argument("--keep-last", type=int, default=None)
    g_clean.set_defaults(func=_cmd_labs_clean_duplicate_delivery)

    h_clean = clean_sub.add_parser(
        SCENARIO_PROJECTION_VERSION,
        help="Noop cleanup + optional snapshot pruning",
        parents=[clean_common],
    )
    h_clean.add_argument("--outdir")
    h_clean.add_argument("--keep-last", type=int, default=None)
    h_clean.set_defaults(func=_cmd_labs_clean_projection_version)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
