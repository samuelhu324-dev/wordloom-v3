# Log-S2A-1A: Observability — tracing (API + outbox workers)
<!-- Log-S2A-1A：可观测性——Tracing（API + outbox workers） -->

Status: adopted
<!-- 状态：已采纳 -->

links: [backend/api/app/main.py](../../../../backend/api/app/main.py), [backend/api/app/config/logging_config.py](../../../../backend/api/app/config/logging_config.py), [backend/infra/observability/tracing.py](../../../../backend/infra/observability/tracing.py), [backend/infra/database/models/search_outbox_models.py](../../../../backend/infra/database/models/search_outbox_models.py), [backend/infra/database/models/chronicle_outbox_models.py](../../../../backend/infra/database/models/chronicle_outbox_models.py), [backend/infra/search/search_outbox_repository.py](../../../../backend/infra/search/search_outbox_repository.py), [backend/infra/storage/chronicle_repository_impl.py](../../../../backend/infra/storage/chronicle_repository_impl.py), [backend/scripts/search_outbox_worker.py](../../../../backend/scripts/search_outbox_worker.py), [backend/scripts/chronicle_outbox_worker.py](../../../../backend/scripts/chronicle_outbox_worker.py), [backend/scripts/run_api_win.py](../../../../backend/scripts/run_api_win.py), [docs/architecture/runbook/labs/labs-007-observability-tracing-api-outbox-worker.md](../../../architecture/runbook/labs/labs-007-observability-tracing-api-outbox-worker.md)
<!-- 链接：现有 structured logs / metrics / runtime endpoints / outbox workers 与 outbox 表模型（用于核对 tracing 需要补齐的“缺口”）。 -->

## Background

Wordloom already has:
- Structured logs (JSON lines) designed for humans and tools (jq/ELK/Loki).
- Metrics for both API and worker processes (`/metrics` on API; embedded Prometheus exporter on workers).
- A request-scoped `correlation_id` context (ContextVar), which makes cross-module log correlation possible.

Tracing is the missing third leg: it explains *how one request/task flowed through multiple steps*, where time was spent, and where it broke.
<!-- 现状：日志（给人看）+ 指标（给人和机器看）已有；Tracing（把一次请求/一次任务的步骤串起来）缺失。 -->

Concrete repository gaps (based on current code/dependencies):
- No OpenTelemetry (OTel) dependencies are present in [backend/requirements.txt](../../../../backend/requirements.txt) today.
- No tracer provider initialization, no exporter configuration, and no collector/backend (Jaeger/Tempo) wiring in the repo.
- The outbox tables used by workers do not currently store trace context (no `traceparent`/`tracestate` or similar fields in outbox rows).
- The API exposes an `ErrorResponse.trace_id` field, but it is not yet backed by a real tracing system nor a standard propagation format.
<!-- 缺口：没有 OTel 依赖/初始化/导出；outbox 行里也没有 trace 上下文字段，所以 API→outbox→worker 的“链”无法天然接起来。 -->

## What/How to do
<!-- 怎么做 / 怎么推进 -->

### 1) Pick an implementation baseline (OTel + OTLP)
<!-- 1）选一条最小可行落地路线（OTel + OTLP） -->

draft:
- Adopt OpenTelemetry as the tracing API/SDK and standardize on OTLP export (HTTP or gRPC).
- Choose a trace backend for dev (one of: Jaeger all-in-one, Grafana Tempo) and add a minimal “collector/exporter” wiring plan.
- Define service naming conventions up-front:

  - API: `wordloom-api`
  - Workers: `wordloom-worker-search`, `wordloom-worker-chronicle`
- Define minimal environment knobs (names are illustrative; exact names can be refined when implementing):

  - `OTEL_SERVICE_NAME`
  - `OTEL_EXPORTER_OTLP_ENDPOINT`
  - `OTEL_TRACES_SAMPLER` / `OTEL_TRACES_SAMPLER_ARG`

adopted:

- 采用 OpenTelemetry SDK 作为 tracing 标准库，并通过 OTLP/HTTP exporter 输出到 Jaeger（本地实验）。
- tracing 默认为 opt-in：仅当 `WORDLOOM_TRACING_ENABLED=1` 且未设置 `OTEL_SDK_DISABLED=true` 时启用。
- `service.name` 命名约定在代码中落地为默认值（可被 `OTEL_SERVICE_NAME` 覆盖）：
  - API：`wordloom-api`
  - Search worker：`wordloom-search-outbox-worker`
  - Chronicle worker：`wordloom-chronicle-outbox-worker`
- 采样策略落地为 head-based：默认 `traceidratio`，默认比例 0.05，可用 `OTEL_TRACES_SAMPLER/OTEL_TRACES_SAMPLER_ARG` 覆盖；实验时可用 `always_on`。

### 2) Instrument the API request path (FastAPI)
<!-- 2）给 API 同步链路打通 tracing（FastAPI） -->

draft:
- Add OTel instrumentation around:

  - inbound HTTP (FastAPI/Starlette)
  - DB access (SQLAlchemy)
  - outbound HTTP calls (httpx) when applicable
- Ensure incoming trace context is honored (W3C `traceparent`), so external callers can stitch traces end-to-end.
- Bridge logs and traces:

  - Include `trace_id` and `span_id` into structured logs (as extra fields) for quick grep.
  - Populate `ErrorResponse.trace_id` from the active trace id (so error responses can be cross-linked to traces).
- Keep attributes low-cardinality and safe (no PII by default). Prefer ids already used operationally: `correlation_id`, `route`, `method`, `workspace_id`.

adopted:

- API 启动时初始化 tracing（`setup_tracing(default_service_name="wordloom-api")`），并启用：
  - inbound HTTP spans：FastAPI instrumentation
  - outbound HTTP spans：httpx instrumentation（如有外部调用）
  - DB spans：SQLAlchemy engine instrumentation（对 engine/sync_engine best-effort）
- Logs ⇄ Traces 关联已落地：当 tracing 启用时，structured logs 自动注入 `trace_id`/`span_id` 字段（best-effort，不影响原日志行为）。
- 错误响应的 `trace_id` 回填为 best-effort（用于把错误响应与 Jaeger trace 对齐）。

### 3) Instrument the worker task path (outbox processing)
<!-- 3）给 worker 异步链路打通 tracing（outbox processing） -->

draft:
- For each outbox event processing attempt, create a root span (or child span if context is available) such as:

  - `outbox.claim`
  - `outbox.process`
  - `outbox.ack`
- Attach operational attributes (low-cardinality where possible):

  - `projection` (`search` / `chronicle`)
  - `entity_type`, `entity_id`
  - `attempts`
  - `status` transition (`pending→processing→done/failed`)
  - `error_reason` on failure
- Record errors as span status + short message; do not dump full stack traces into span attributes (keep stack traces in logs).

adopted:

- Search/Chronicle 两个 outbox worker 均支持从 outbox 行读取 trace 上下文并继续 trace。
- 每次处理事件会创建 `outbox.process` span（如果 outbox 行携带 trace 上下文，则作为 parent；否则新 trace）。
- Search worker 对 ES 的 httpx 请求会产生子 span（便于在 trace 中看见外部依赖耗时）。
- 失败信息仍以 logs 为主；span 仅记录错误状态（避免把堆栈/大字段塞进 trace attributes）。
- 为了让 trace “从有变有用”，在 worker 关键路径补齐 3 个父 span（DB spans 会自然挂在这些父 span 下，trace depth 通常从 1 提升到 3–5）：
  - `outbox_worker.loop`：每轮主循环的外层节拍（用于判断 worker 在忙什么）
  - `outbox.claim_batch`：claim/lease/更新 claimed_at 等 DB 操作
  - `projection.process_batch`：处理一批 outbox（load → build → sink/ack/fail）
- 同时在这些父 span 上附加低基数 tags 以便 Jaeger 检索：
  - `projection`（例如 `search`/`chronicle`）
  - `batch_size`
  - `attempt`（batch 内最大 attempts）
  - `entity_type` / `op`（同质则写具体值；混合则 `mixed`）
  - `result`（`ok`/`failed`，best-effort）

### 4) Propagate trace context across the async boundary (API → outbox → worker)
<!-- 4）把异步边界“接起来”（API→outbox→worker）这是关键 -->

draft:
- Store trace context at enqueue time (same DB transaction as the source write + outbox insert).
- Preferred approach: add dedicated columns to outbox tables for propagation (e.g., `traceparent`, optional `tracestate`).

  - This is consistent with the current outbox schema style (explicit columns; no payload column today).
- Worker reads these columns when claiming events and uses them as the parent context when starting spans.
- Fall back policy: if no trace context exists, start a new trace but always emit `correlation_id` and outbox identifiers so operators can still join logs/metrics.

adopted:

- 在 outbox 表上新增传播字段：`traceparent`/`tracestate`（search_outbox_events + chronicle_outbox_events，均允许为空）。
- enqueue（同 DB 事务）时注入当前 trace 上下文并写入 outbox 行（best-effort；tracing 关闭时写入 NULL）。
- worker claim/读取 outbox 行时提取 `traceparent/tracestate`，attach 为 parent context 后再创建处理 span，从而把 API → outbox → worker 的链路“接起来”。

### 5) Sampling strategy and cost guardrails
<!-- 5）采样策略与成本护栏 -->

draft:
- Start with head-based sampling (e.g., a small fixed ratio) for prod safety; allow raising sampling for targeted debugging.
- Ensure high-signal error traces are kept (e.g., sample-on-error policy, if supported by backend/collector).
- Define an attribute allowlist to prevent accidental high-cardinality explosion.

adopted:

- 默认采样为 `traceidratio` 且默认比例较低（0.05），避免在非实验环境产生过量 trace。
- 采样/开关全部走标准 env knobs（无需改代码），便于按需提升采样用于问题定位。
- 日志/指标仍是主信号；trace 作为“链路解释器”，避免在 span attributes 中记录高基数字段或潜在敏感数据。

### 6) Verification and “evidence snapshots” (labs-style)
<!-- 6）验证与留证据（参考你现在的 labs 快照习惯） -->

draft:
- Define a minimal, repeatable verification flow:

  - Make one API call that enqueues an outbox event.
  - Confirm a single trace shows both the API spans and the worker spans (linked by propagation).
  - Confirm you can jump from a log line (has `trace_id`) to the trace UI and see the waterfall.
- Record evidence snapshots (console output + trace UI screenshots) in the same convention you used for v4 runtime hardening labs.

adopted:

- 已完成最小闭环实验并留存证据：见 [docs/architecture/runbook/labs/labs-007-observability-tracing-api-outbox-worker.md](../../../architecture/runbook/labs/labs-007-observability-tracing-api-outbox-worker.md) 及其 `_snapshots/`。
- 本地 Jaeger 推荐以 compose 方式启动（便于在 Docker Desktop 里“点按钮”管理容器），并通过 Jaeger UI/HTTP API 导出 trace 作为快照证据。
- Windows 下为规避 psycopg async + ProactorEventLoop 兼容问题，提供 API 专用启动器 `run_api_win.py`（强制 SelectorEventLoop；tracing 与业务无关的兼容层）。
