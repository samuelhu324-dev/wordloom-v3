"""Labs-009 helper: export Jaeger traces reliably (avoids shell quoting/URL-encoding pitfalls).

Why this exists:
- Jaeger query API parameters (especially `tags`) are easy to break in shells.
- Jaeger v1.76 may return response metadata like `limit=0`/`total=0` even when
  `data` contains traces (see Jaeger issue #6321). This script treats `data`
  length as the source of truth.

Usage (WSL/bash, from repo root):
    python backend/scripts/labs/labs_009_export_jaeger.py --outdir docs/.../_labs009_expB \
    --service wordloom-search-outbox-worker --outbox-event-id <uuid>

    python backend/scripts/labs/labs_009_export_jaeger.py --outdir docs/.../_labs009_expB \
    --service wordloom-search-outbox-worker --claim-batch-id <uuid>

"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import httpx


@dataclass(frozen=True)
class JaegerResponse:
    data: list[dict[str, Any]]
    raw: dict[str, Any]


def _utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _get_json(client: httpx.Client, url: str, *, params: dict[str, str] | None = None) -> dict[str, Any]:
    resp = client.get(url, params=params, timeout=20.0)
    resp.raise_for_status()
    return resp.json()


def _jaeger_traces(
    client: httpx.Client,
    base_api: str,
    *,
    service: str,
    lookback: str,
    limit: int,
    operation: str | None = None,
    tags: dict[str, str] | None = None,
) -> JaegerResponse:
    params: dict[str, str] = {
        "service": service,
        "lookback": lookback,
        "limit": str(limit),
    }
    if operation:
        params["operation"] = operation
    if tags:
        params["tags"] = json.dumps(tags, separators=(",", ":"), ensure_ascii=False)

    raw = _get_json(client, f"{base_api}/traces", params=params)
    data = raw.get("data") or []
    if not isinstance(data, list):
        data = []
    return JaegerResponse(data=data, raw=raw)


def _extract_outbox_event_ids(traces: Iterable[dict[str, Any]]) -> list[str]:
    out: set[str] = set()
    for trace in traces:
        for span in trace.get("spans", []) or []:
            for tag in span.get("tags", []) or []:
                if tag.get("key") == "wordloom.outbox_event_id" and isinstance(tag.get("value"), str):
                    out.add(tag["value"])
    return sorted(out)


def _extract_tag_values(traces: Iterable[dict[str, Any]], key: str) -> list[str]:
    out: set[str] = set()
    for trace in traces:
        for span in trace.get("spans", []) or []:
            for tag in span.get("tags", []) or []:
                if tag.get("key") == key and isinstance(tag.get("value"), str):
                    out.add(tag["value"])
    return sorted(out)


def _any_operation(traces: Iterable[dict[str, Any]], op_name: str) -> bool:
    for trace in traces:
        for span in trace.get("spans", []) or []:
            if span.get("operationName") == op_name:
                return True
    return False


def _extract_claimed_counts(traces: Iterable[dict[str, Any]]) -> list[int]:
    counts: list[int] = []
    for trace in traces:
        for span in trace.get("spans", []) or []:
            if span.get("operationName") != "outbox.claim_batch":
                continue
            for tag in span.get("tags", []) or []:
                if tag.get("key") == "claimed":
                    value = tag.get("value")
                    if isinstance(value, int):
                        counts.append(value)
    return counts


def main() -> int:
    p = argparse.ArgumentParser(description="Labs-009: export Jaeger traces with safe encoding")
    p.add_argument("--base-api", default="http://localhost:16686/api", help="Jaeger query base API URL")
    p.add_argument("--outdir", required=True, help="Output directory for snapshots")

    p.add_argument("--service", required=True, help="Jaeger service name")
    p.add_argument("--lookback", default="1h", help="Jaeger lookback window (e.g., 15m, 1h, 24h)")
    p.add_argument("--limit", type=int, default=20, help="Max traces to request")

    p.add_argument(
        "--operation",
        help="Optional operation filter (e.g. outbox.claim_batch). Useful with --tags-json.",
    )

    group = p.add_mutually_exclusive_group(required=False)
    group.add_argument("--outbox-event-id", help="Query by wordloom.outbox_event_id (operation=outbox.process)")
    group.add_argument("--claim-batch-id", help="Query by wordloom.claim_batch_id (operation=projection.process_batch)")
    group.add_argument("--tags-json", help='Raw tags JSON, e.g. {"k":"v"}')

    args = p.parse_args()

    base_api = str(args.base_api).rstrip("/")
    outdir = Path(args.outdir)
    ts = _utc_ts()

    with httpx.Client() as client:
        services = _get_json(client, f"{base_api}/services")
        _write_json(outdir / f"jaeger-services-{ts}.json", services)

        operations = _get_json(client, f"{base_api}/operations", params={"service": args.service})
        _write_json(outdir / f"jaeger-operations-{ts}.json", operations)

        operation: str | None = str(args.operation) if args.operation else None
        tags: dict[str, str] | None = None
        label = "traces"

        if args.outbox_event_id:
            operation = "outbox.process"
            tags = {"wordloom.outbox_event_id": args.outbox_event_id}
            label = f"outbox_event_id-{args.outbox_event_id}"
        elif args.claim_batch_id:
            operation = "projection.process_batch"
            tags = {"wordloom.claim_batch_id": args.claim_batch_id}
            label = f"claim_batch_id-{args.claim_batch_id}"
        elif args.tags_json:
            try:
                tags_raw = json.loads(args.tags_json)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid --tags-json: {exc}")
            if not isinstance(tags_raw, dict):
                raise SystemExit("--tags-json must be a JSON object")
            tags = {str(k): str(v) for k, v in tags_raw.items()}
            label = "tags"

        traces = _jaeger_traces(
            client,
            base_api,
            service=args.service,
            lookback=args.lookback,
            limit=max(1, int(args.limit)),
            operation=operation,
            tags=tags,
        )

        out_path = outdir / f"jaeger-traces-{label}-{ts}.json"
        _write_json(out_path, traces.raw)

        returned = len(traces.data)
        print(f"[labs-009] jaeger traces returned: {returned} (snapshot={out_path})")
        if traces.raw.get("limit", None) == 0 and returned > 0:
            print("[labs-009] note: Jaeger API metadata may show limit=0/total=0 even when data is non-empty (see Jaeger #6321)")

        if returned == 0 and args.outbox_event_id:
            # Broader fallback: in some runs, the worker is polling (claim_batch)
            # but not processing any events (no outbox.process spans).
            print("[labs-009] No traces matched this outbox_event_id.")

            recent_any = _jaeger_traces(
                client,
                base_api,
                service=args.service,
                lookback=args.lookback,
                limit=50,
                operation=None,
                tags=None,
            )

            has_outbox_process = _any_operation(recent_any.data, "outbox.process")
            claimed_counts = _extract_claimed_counts(recent_any.data)

            if not has_outbox_process:
                print("[labs-009] Also: no 'outbox.process' spans found in the current lookback window.")
                if claimed_counts and max(claimed_counts) == 0:
                    print(
                        "[labs-009] Observed outbox.claim_batch claimed=0 in recent traces (worker is polling but not claiming events)."
                    )
                print("[labs-009] Tip: generate/trigger outbox events, then retry this export.")

            claim_batch_candidates = _extract_tag_values(recent_any.data, "wordloom.claim_batch_id")
            if claim_batch_candidates:
                print("[labs-009] Recent claim_batch_id candidates (sample):")
                for c in claim_batch_candidates[-5:]:
                    print(f"  - {c}")
                print("[labs-009] Tip: export by claim batch id via --claim-batch-id <uuid>.")

            # If outbox.process exists, provide a few recent outbox_event_id candidates.
            if has_outbox_process:
                recent_outbox = _jaeger_traces(
                    client,
                    base_api,
                    service=args.service,
                    lookback=args.lookback,
                    limit=20,
                    operation="outbox.process",
                    tags=None,
                )
                candidates = _extract_outbox_event_ids(recent_outbox.data)
                if candidates:
                    print("[labs-009] Recent outbox_event_id candidates (sample):")
                    for c in candidates[-5:]:
                        print(f"  - {c}")
                    print("[labs-009] Tip: ensure you are using the OUTBOX_EVENT_ID (outbox row PK), not entity_id.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
