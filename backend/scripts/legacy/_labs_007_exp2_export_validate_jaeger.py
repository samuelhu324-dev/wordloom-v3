from __future__ import annotations

import argparse
import json
import pathlib
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Result:
    ok: bool
    trace_id: str | None
    traces_snapshot: pathlib.Path
    trace_snapshot: pathlib.Path | None
    report_snapshot: pathlib.Path


REQUIRED_SPANS = (
    "outbox_worker.loop",
    "outbox.claim_batch",
    "projection.process_batch",
)
KEY_TAGS = ("projection", "batch_size", "attempt", "result")


def _utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _get_json(url: str, timeout_seconds: float) -> Any:
    with urllib.request.urlopen(url, timeout=timeout_seconds) as resp:
        raw = resp.read()
    try:
        return json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError:
        return json.loads(raw.decode("utf-8-sig"))


def _tags_to_dict(tags: list[dict[str, Any]] | None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for t in tags or []:
        key = t.get("key")
        if key is None:
            continue
        out[str(key)] = t.get("value")
    return out


def _trace_matches(full: dict[str, Any]) -> tuple[bool, dict[str, list[dict[str, Any]]]]:
    data = full.get("data") or []
    if not data:
        return False, {k: [] for k in REQUIRED_SPANS}

    spans = (data[0].get("spans") or [])
    found: dict[str, list[dict[str, Any]]] = {k: [] for k in REQUIRED_SPANS}

    for s in spans:
        op = s.get("operationName")
        if op in found:
            found[op].append(_tags_to_dict(s.get("tags")))

    if not all(found[name] for name in REQUIRED_SPANS):
        return False, found

    def has_key_tags(tagdict: dict[str, Any]) -> bool:
        return any(k in tagdict for k in KEY_TAGS)

    if not all(has_key_tags(found[name][0]) for name in REQUIRED_SPANS):
        return False, found

    return True, found


def _span_has_key_tags(tagdict: dict[str, Any]) -> bool:
    return any(k in tagdict for k in KEY_TAGS)


def export_and_validate(*, base_url: str, service: str, outdir: pathlib.Path, lookback: str, limit: int, timeout_seconds: float) -> Result:
    outdir.mkdir(parents=True, exist_ok=True)
    ts = _utc_ts()

    traces_snapshot = outdir / f"labs-007-exp2-jaeger-traces-{ts}.json"
    trace_snapshot = outdir / f"labs-007-exp2-jaeger-trace-{ts}.json"
    report_snapshot = outdir / f"labs-007-exp2-validate-{ts}.txt"

    query = urllib.parse.urlencode({"service": service, "lookback": lookback, "limit": str(limit)})
    traces_url = f"{base_url.rstrip('/')}/traces?{query}"
    traces = _get_json(traces_url, timeout_seconds)
    traces_snapshot.write_text(json.dumps(traces, indent=2, ensure_ascii=False), encoding="utf-8")

    trace_ids = [t.get("traceID") for t in (traces.get("data") or []) if t.get("traceID")]

    # We accept that some spans might show up in different traces
    # (e.g., worker-internal spans vs. propagated per-event spans).
    exemplar_by_span: dict[str, tuple[str, dict[str, Any]]] = {}

    for tid in trace_ids:
        full = _get_json(f"{base_url.rstrip('/')}/traces/{tid}", timeout_seconds)
        _ok, found = _trace_matches(full)
        for name in REQUIRED_SPANS:
            if name in exemplar_by_span:
                continue
            if not found.get(name):
                continue
            tags = found[name][0]
            if not _span_has_key_tags(tags):
                continue
            exemplar_by_span[name] = (tid, full)
        if len(exemplar_by_span) == len(REQUIRED_SPANS):
            break

    lines: list[str] = []
    lines.append(f"service={service}")
    lines.append(f"required={','.join(REQUIRED_SPANS)}")

    ok_all = all(name in exemplar_by_span for name in REQUIRED_SPANS)
    lines.append("overall=" + ("PASS" if ok_all else "FAIL"))

    for name in REQUIRED_SPANS:
        lines.append(f"--- {name}")
        if name not in exemplar_by_span:
            lines.append("MISSING")
            continue

        tid, full = exemplar_by_span[name]
        # Write per-span trace snapshot so evidence is explicit.
        per_trace_path = outdir / f"labs-007-exp2-jaeger-trace-{name.replace('.', '_')}-{ts}.json"
        per_trace_path.write_text(json.dumps(full, indent=2, ensure_ascii=False), encoding="utf-8")
        # Extract tag dict for reporting.
        _ok, found = _trace_matches(full)
        tags = (found.get(name) or [{}])[0]
        lines.append(f"traceID={tid}")
        present = [k for k in KEY_TAGS if k in tags]
        lines.append("tags_present=" + (",".join(present) if present else "<none>"))
        for k in ("projection", "wordloom.projection", "batch_size", "attempt", "op", "entity_type", "result", "claimed"):
            if k in tags:
                lines.append(f"  {k}={tags[k]}")
        lines.append(f"trace_snapshot={per_trace_path}")

    report_snapshot.write_text("\n".join(lines), encoding="utf-8")

    # Keep backward-compatible fields (trace_snapshot is optional)
    if trace_ids:
        trace_snapshot.write_text(
            json.dumps(_get_json(f"{base_url.rstrip('/')}/traces/{trace_ids[0]}", timeout_seconds), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return Result(
        ok=ok_all,
        trace_id=(trace_ids[0] if trace_ids else None),
        traces_snapshot=traces_snapshot,
        trace_snapshot=(trace_snapshot if trace_ids else None),
        report_snapshot=report_snapshot,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:16686/api", help="Jaeger query base URL")
    parser.add_argument("--service", required=True, help="Jaeger service name")
    parser.add_argument(
        "--operation",
        default=None,
        help="Optional Jaeger operation filter (e.g., projection.process_batch). Useful when traces are hard to find via service-only queries.",
    )
    parser.add_argument("--outdir", default="docs/architecture/runbook/labs/_snapshots", help="Snapshot output dir")
    parser.add_argument("--lookback", default="15m", help="Jaeger lookback window")
    parser.add_argument("--limit", type=int, default=20, help="Max traces to query")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout seconds")
    args = parser.parse_args()

    outdir = pathlib.Path(args.outdir)
    if args.operation:
        # Prefer operation-filtered queries to avoid missing traces where the service's spans
        # are not considered the trace root (e.g., remote parent not present in storage).
        ts = _utc_ts()
        traces_snapshot = outdir / f"labs-007-exp2-jaeger-traces-operation-{args.operation.replace('.', '_')}-{ts}.json"
        query = urllib.parse.urlencode(
            {"service": args.service, "operation": args.operation, "lookback": args.lookback, "limit": str(args.limit)}
        )
        traces_url = f"{args.base_url.rstrip('/')}/traces?{query}"
        traces = _get_json(traces_url, args.timeout)
        outdir.mkdir(parents=True, exist_ok=True)
        traces_snapshot.write_text(json.dumps(traces, indent=2, ensure_ascii=False), encoding="utf-8")

        # Feed the operation-filtered trace IDs into the existing validator by temporarily
        # overriding the service-only traces snapshot.
        # (We keep export_and_validate's output format intact.)
        #
        # To avoid changing export_and_validate signature, we simply run it with a shorter
        # lookback/limit and then merge in any operation-filtered trace IDs.
        res = export_and_validate(
            base_url=args.base_url,
            service=args.service,
            outdir=outdir,
            lookback=args.lookback,
            limit=args.limit,
            timeout_seconds=args.timeout,
        )

        # If the default query missed traces but operation query has them, re-run exemplar scan
        # using the operation-filtered trace IDs (without rewriting the other snapshots).
        if not res.ok:
            trace_ids = [t.get("traceID") for t in (traces.get("data") or []) if t.get("traceID")]

            exemplar_by_span: dict[str, tuple[str, dict[str, Any]]] = {}
            for tid in trace_ids:
                full = _get_json(f"{args.base_url.rstrip('/')}/traces/{tid}", args.timeout)
                _ok, found = _trace_matches(full)
                for name in REQUIRED_SPANS:
                    if name in exemplar_by_span:
                        continue
                    if not found.get(name):
                        continue
                    tags = found[name][0]
                    if not _span_has_key_tags(tags):
                        continue
                    exemplar_by_span[name] = (tid, full)
                if len(exemplar_by_span) == len(REQUIRED_SPANS):
                    break

            ok_all = all(name in exemplar_by_span for name in REQUIRED_SPANS)
            if ok_all:
                # Write a fresh report file that points at the new per-span snapshots.
                ts2 = _utc_ts()
                report_snapshot = outdir / f"labs-007-exp2-validate-{ts2}.txt"
                lines: list[str] = []
                lines.append(f"service={args.service}")
                lines.append(f"required={','.join(REQUIRED_SPANS)}")
                lines.append("overall=PASS")
                lines.append(f"source_operation={args.operation}")

                for name in REQUIRED_SPANS:
                    lines.append(f"--- {name}")
                    tid, full = exemplar_by_span[name]
                    per_trace_path = outdir / f"labs-007-exp2-jaeger-trace-{name.replace('.', '_')}-{ts2}.json"
                    per_trace_path.write_text(json.dumps(full, indent=2, ensure_ascii=False), encoding="utf-8")
                    _ok, found = _trace_matches(full)
                    tags = (found.get(name) or [{}])[0]
                    present = [k for k in KEY_TAGS if k in tags]
                    lines.append(f"traceID={tid}")
                    lines.append("tags_present=" + (",".join(present) if present else "<none>"))
                    for k in (
                        "projection",
                        "wordloom.projection",
                        "batch_size",
                        "attempt",
                        "op",
                        "entity_type",
                        "result",
                        "claimed",
                    ):
                        if k in tags:
                            lines.append(f"  {k}={tags[k]}")
                    lines.append(f"trace_snapshot={per_trace_path}")

                report_snapshot.write_text("\n".join(lines), encoding="utf-8")

                print("ok=True")
                print("traceID=<see per-span snapshots>")
                print(f"traces_snapshot={traces_snapshot}")
                print("trace_snapshot=<see per-span snapshots>")
                print(f"report_snapshot={report_snapshot}")
                return 0
    else:
        res = export_and_validate(
            base_url=args.base_url,
            service=args.service,
            outdir=pathlib.Path(args.outdir),
            lookback=args.lookback,
            limit=args.limit,
            timeout_seconds=args.timeout,
        )

    print(f"ok={res.ok}")
    print(f"traceID={res.trace_id}")
    print(f"traces_snapshot={res.traces_snapshot}")
    print(f"trace_snapshot={res.trace_snapshot if res.trace_snapshot else '<none>'}")
    print(f"report_snapshot={res.report_snapshot}")
    return 0 if res.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
