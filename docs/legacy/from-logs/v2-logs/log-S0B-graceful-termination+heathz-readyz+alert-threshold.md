# Log-S0B: Graceful termination, healthz/readyz, and alert thresholds (outbox workers)
<!-- Log-S0B：优雅退出 + healthz/readyz + 告警阈值（outbox workers 的 v4 运营化） -->

Status: adopted
<!-- 状态：草稿 -->

links: [backend/scripts/search_outbox_worker.py](../../../../backend/scripts/search_outbox_worker.py), [backend/scripts/chronicle_outbox_worker.py](../../../../backend/scripts/chronicle_outbox_worker.py), [infra/observability/outbox_metrics.py](../../../../backend/infra/observability/outbox_metrics.py)
<!-- 链接：两个 worker 实现 + 统一 outbox 指标定义 -->

## Background

Outbox workers currently have v1–v3 semantics (lease/reclaim, retry/backoff, terminal failed + replay) and metrics, but they still behave like “scripts” rather than long-running daemons.
<!-- outbox worker 现在基本具备 v1–v3（lease/reclaim、retry/backoff、failed+replay）以及 metrics，但更像“脚本”，而不是可长期运维的 daemon。 -->

This log defines the minimal v4 runtime hardening needed for production-grade operation: graceful SIGTERM shutdown, explicit health/readiness endpoints, and alert thresholds + guardrails.
<!-- 本 log 定义 v4 的最小运行时工程化闭环：SIGTERM 优雅退出、healthz/readyz、告警阈值与运行时护栏（guardrails）。 -->

## What/How to do

### 1) SIGTERM graceful shutdown (safe termination)

draft:
- Implement a SIGTERM handler that flips `stop_requested=true` and logs “draining”.
	<!-- 实现 SIGTERM handler：收到 SIGTERM 置 stop_requested=true，并明确打日志进入 draining。 -->
- Stop claiming new outbox rows when `stop_requested` is set (no new leases).
	<!-- stop_requested=true 时停止 claim 新任务（不再发新 lease）。 -->
- Drain the in-flight batch: finish processing or release ownership/lease within `shutdown_grace_seconds`.
	<!-- 收尾当前 batch：在 shutdown_grace_seconds 上限内尽量处理完；否则明确释放 claim/lease，避免 stuck。 -->
- Exit with clear final logs/metrics (reason, drained count, remaining lag).
	<!-- 退出前写清日志/指标：退出原因、drained 数、剩余 lag。 -->

adopted:

- Implemented SIGTERM/SIGINT draining + grace timeout in:
	- `backend/scripts/search_outbox_worker.py`
	- `backend/scripts/chronicle_outbox_worker.py`
- Behavior:
	- On stop request: stop claiming new outbox rows
	- Drain in-flight work best-effort within `OUTBOX_SHUTDOWN_GRACE_SECONDS`
	- On grace exceeded: exit (and release any best-effort claims where applicable)


### 2) /healthz and /readyz (platform integration)

draft:
- Add a lightweight HTTP server exposing `/healthz`, `/readyz`, and keep `/metrics`.
	<!-- 增加轻量 HTTP server：提供 /healthz、/readyz，同时保留 /metrics。 -->
- `/healthz`: return 200 if the event loop is alive and the main loop has ticked recently (e.g., `last_loop_at` within N seconds).
	<!-- /healthz：只要 event loop 活着 + 主循环最近 N 秒有 tick（last_loop_at 更新）就返回 200。 -->
- `/readyz`: return 200 only if the worker can safely claim work (not `stop_requested`, DB connectivity OK; ES ping OK if required).
	<!-- /readyz：只有“能安全接活”才 200（not stop_requested、DB ping OK；若强依赖 ES 则 es_ping OK）。 -->
- Make `/readyz` the external drain switch: when draining, return non-200 so the platform can remove it from service.
	<!-- 把 /readyz 做成外部摘流开关：draining 时 readyz 非 200，让平台自动摘流/滚更。 -->

adopted:

- Added lightweight runtime HTTP server (separate from `/metrics`) exposing:
	- `GET /healthz` (liveness: main loop ticks)
	- `GET /readyz` (readiness: not draining + DB ok (+ optional dependency gate))
- Implementation: `backend/infra/observability/runtime_endpoints.py`
- Ports:
	- `/metrics`: `OUTBOX_METRICS_PORT`
	- runtime endpoints: `OUTBOX_HTTP_PORT`


### 3) Alert thresholds and runtime guardrails

draft:
- Define SLO boundaries in terms of existing metrics (e.g., `outbox_oldest_age_seconds`, `outbox_stuck_processing_events`, `outbox_terminal_failed_total`).
	<!-- 用现有指标定义 SLO 边界（例如 outbox_oldest_age_seconds、stuck_processing_events、terminal_failed_total）。 -->
- Keep alert thresholds in Prometheus/Alertmanager, but add minimal in-code guardrails:
	<!-- 阈值仍放 Prometheus/Alertmanager，但代码里补最小护栏动作： -->
	- Maintain runtime states: `RUNNING`, `DEGRADED`, `DRAINING`, `STOPPED`.
		<!-- 运行时状态机：RUNNING/DEGRADED/DRAINING/STOPPED。 -->
	- Consecutive DB ping failures → enter `DRAINING` (stop claiming, backoff) and reflect via `/readyz`.
		<!-- DB ping 连续失败 → 进入 DRAINING（不 claim + backoff），并通过 /readyz 体现不可接活。 -->
	- If oldest age grows while throughput is ~0 → log “likely stuck/dependency down” and behave more conservatively.
		<!-- oldest_age 持续增长且吞吐≈0 → 打“可能卡死/依赖挂了”的日志，并更保守（少 claim/更长 backoff）。 -->

adopted:

- Guardrails implemented:
	- Consecutive DB ping failures >= `OUTBOX_DB_PING_FAILS_BEFORE_DRAINING` => enter DRAINING
	- While draining: stop claiming; `/readyz` returns 503
- Metrics remain the primary alert source; guardrails are the in-process “stop digging” safety net.


### 4) Validation plan (turn Labs-004 Experiment 6 from placeholder into executable)

draft:
- Add a new Labs-004 “v4” experiment verifying:
	<!-- 在 labs-004 补一个可执行的 v4 实验，用来验收： -->
	- SIGTERM causes drain (no new claims) and exits within grace period.
		<!-- SIGTERM 后进入 drain：不再 claim，新 batch 不增长，且在 grace 时间内退出。 -->
	- `/healthz` stays 200 while running; `/readyz` flips to non-200 during draining.
		<!-- /healthz 运行时 200；draining 时 /readyz 翻转为非 200。 -->
	- Alert rules trigger on oldest_age/stuck/terminal_failed signals.
		<!-- oldest_age/stuck/terminal_failed 的告警规则能触发。 -->

adopted:

- Labs-004 Experiment 6 (v4) is now executable and has runner scripts:
	- `backend/scripts/ops_labs_004_v4_runtime_search_worker.sh`
	- `backend/scripts/ops_labs_004_v4_runtime_search_worker_capture.sh`
- Labs-005 Experiment 6 (v4) validates chronicle worker runtime behavior:
	- `backend/scripts/ops_labs_005_chronicle_e6_runtime_worker_capture.sh`
- Evidence snapshots are stored under:
	- `docs/architecture/runbook/labs/_snapshots/`


## Executable snippets

See [backend/scripts/ops_s0b_smoke_runtime_endpoints.sh](../../../../backend/scripts/ops_s0b_smoke_runtime_endpoints.sh).
<!-- 见可执行脚本：backend/scripts/ops_s0b_smoke_runtime_endpoints.sh -->

### Smoke checks (WSL2/Bash)

```bash
# Metrics (already exists today)
curl -fsS "http://localhost:${OUTBOX_METRICS_PORT:-9109}/metrics" | egrep '^outbox_(lag_events|oldest_age_seconds|inflight_events|processed_total|failed_total|stuck_processing_events|retry_scheduled_total|terminal_failed_total)'

# Future endpoints (after v4 implementation)
curl -fsS "http://localhost:${OUTBOX_HTTP_PORT:-9112}/healthz" || true
curl -fsS "http://localhost:${OUTBOX_HTTP_PORT:-9112}/readyz" || true
```

### Example Prometheus alert ideas (draft only)

```yaml
# NOTE: thresholds depend on env/SLO. This is intentionally a sketch.
- alert: OutboxOldestAgeTooHigh
	expr: outbox_oldest_age_seconds > 300
	for: 10m
	labels: { severity: warning }
	annotations:
		summary: "Outbox oldest age exceeds 5 minutes"

- alert: OutboxStuckProcessing
	expr: outbox_stuck_processing_events > 0
	for: 5m
	labels: { severity: critical }
	annotations:
		summary: "Outbox stuck processing detected"
```