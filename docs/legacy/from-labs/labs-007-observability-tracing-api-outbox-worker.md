````markdown
# Labs-007：Tracing（API → Outbox → Worker）最小闭环（操作指南 + 判定模板）

Status: draft

目标：在已有的 structured logs + metrics 基础上，把 tracing 的最小闭环跑通并可验证：

- API（FastAPI）接收请求 → 产生 root span（HTTP server span）
- enqueue outbox 时把上下文写入 outbox：`traceparent` / `tracestate`
- worker 消费 outbox 时从 DB 取回上下文并继续 trace（产生 `outbox.process` span）
- 日志中可看到 `trace_id` / `span_id`（仅在 `WORDLOOM_TRACING_ENABLED=1` 时注入）

快照目录（证据留存）：`docs/architecture/runbook/labs/_snapshots/`

---

## 0) 前置条件

- Postgres（dev/test：localhost:5435）
- Elasticsearch（localhost:9200）
- Docker（用于启动 Jaeger）

实现入口（与当前仓库对齐）：

- API：`backend/api/app/main.py`
- search worker：`backend/scripts/search_outbox_worker.py`
- outbox trace 字段：`search_outbox_events.traceparent/tracestate`（同理 chronicle_outbox_events）

---

## 1) 启动 tracing backend（Jaeger all-in-one，OTLP/HTTP）

选择其一即可。

### 1.0 推荐：用 docker compose 启动（Docker Desktop 可“点按钮”启动/停止）

> 该仓库已在 `docker-compose.infra.yml` 中内置 `jaeger` 服务。
> 一旦用 compose 启动过，Docker Desktop 的 Containers 里会出现 `wordloom-v3` 项目组，里面有 `jaeger` 容器，可直接用 UI 的 Start/Stop 按钮管理。

```powershell
# Jaeger UI: http://localhost:16686
# OTLP HTTP: http://localhost:4318

docker compose -f docker-compose.infra.yml up -d jaeger
```

### 1.1 Windows PowerShell

```powershell
# Jaeger UI: http://localhost:16686
# OTLP gRPC: 4317 (可选)
# OTLP HTTP: 4318 (本仓库 OTLP HTTP exporter 默认用这个)

docker run --rm `
  -e COLLECTOR_OTLP_ENABLED=true `
  -p 16686:16686 `
  -p 4317:4317 `
  -p 4318:4318 `
  jaegertracing/all-in-one:latest
```

### 1.2 WSL / bash

```bash
docker run --rm \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

---

## 2) 迁移数据库（确保 outbox 有 trace 列）

### 2.1 Windows PowerShell（推荐：仓库自带安全脚本）

```powershell
# test
.\backend\scripts\devtest_db_5435_migrate.ps1 -Database wordloom_test

# 或 dev
.\backend\scripts\devtest_db_5435_migrate.ps1 -Database wordloom_dev
```

---

## 3) 启动 API（开启 tracing）

### 3.1 Windows PowerShell

```powershell
$env:WORDLOOM_TRACING_ENABLED = "1"
$env:OTEL_TRACES_SAMPLER = "always_on"
$env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4318"

# 按你的环境选择 dev/test
$env:WORDLOOM_ENV = "test"
$env:DATABASE_URL = "postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test"

# Windows 下推荐使用仓库内置启动器：强制 SelectorEventLoop，避免 psycopg async 与 ProactorEventLoop 的兼容问题
python .\backend\scripts\run_api_win.py
```

---

## 4) 触发一次会写入 search outbox 的 API 请求

下面用“创建 Tag”作为最小触发器（当前开发模式不需要 token；user_id 来自 DEV_USER_ID 或默认值）。

### 4.1 Windows PowerShell

```powershell
$body = @{ name = "trace-labs-007"; color = "#FFFFFF" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/tags -ContentType "application/json" -Body $body
```

期望：API stdout 中的 JSONL 日志包含 `trace_id`/`span_id` 字段。

---

## 5) 启动 search outbox worker（开启 tracing）

### 5.1 Windows PowerShell

```powershell
$env:WORDLOOM_TRACING_ENABLED = "1"
$env:OTEL_TRACES_SAMPLER = "always_on"
$env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4318"

$env:WORDLOOM_ENV = "test"
$env:DATABASE_URL = "postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test"
$env:ELASTIC_URL = "http://localhost:9200"
$env:ELASTIC_INDEX = "wordloom-test-search-index"

$env:OUTBOX_WORKER_ID = "w-trace"
$env:OUTBOX_METRICS_PORT = "9109"
$env:OUTBOX_HTTP_PORT = "9111"

python .\backend\scripts\search_outbox_worker.py
```

期望：worker stdout 的 JSONL 日志包含 `trace_id`/`span_id` 字段；并且 Jaeger 中可以看到 worker 的 `outbox.process` span。

---

## 6) 验证点（判定模板）

### 6.1 DB：outbox 行写入 trace 上下文

任选其一：

- 用你习惯的 DB 工具查询 `search_outbox_events` 最近行，确认 `traceparent` 非空
- 或 `psql`：

```sql
select id, status, traceparent, tracestate, created_at
from search_outbox_events
order by created_at desc
limit 10;
```

### 6.2 Jaeger：同一个 trace 中包含 API + worker spans

- 打开 Jaeger UI：`http://localhost:16686`
- Services 应至少出现：
  - `wordloom-api`
  - `wordloom-search-outbox-worker`
- 找到某条 trace：
  - API 的 HTTP server span（通常是 POST /api/v1/tags）
  - worker 的 `outbox.process` span（应与 API span 处于同一 trace_id）

### 6.3 Logs：trace_id / span_id 注入

- 在 API 与 worker 日志中检索 `trace_id`
- 期望：
  - API 请求日志带 `trace_id`
  - outbox worker 处理日志带 `trace_id`
  - 两者相同（同一条链路）

---

## 7) 快照（证据留存建议）

把下面内容落到 `docs/architecture/runbook/labs/_snapshots/`：

- API 一次请求的 stdout 片段（含 `trace_id`）
- worker 处理该 outbox 的 stdout 片段（含同一个 `trace_id`）
- Jaeger trace UI 截图（包含 service + span tree）

命名建议：

- `labs-007-api-log.jsonl`
- `labs-007-worker-log.jsonl`
- `labs-007-jaeger-trace.png`

### 7.1 Golden fixtures（截图1 对应：已清理后的“最小保留集”）

> 说明：以 2026-02-08 的一次端到端验证为基线，仅保留“可验收、可复查、可回放”的最小证据集。
> 其余 `labs-007*` 迭代快照已归档到：`docs/architecture/runbook/labs/_snapshots/_archive/labs-007-20260208/`。

实验1（API → outbox → worker）保留：

- `labs-007-api-20260208T125812.jsonl`
- `labs-007-worker-20260208T125458.jsonl`
- `labs-007-request-20260208T125858.json`
- `labs-007-response-20260208T125858.json`
- `labs-007-jaeger-services-20260208T125932.json`
- `labs-007-jaeger-traces-20260208T125932.json`
- `labs-007-jaeger-trace-20260208T125945.json`

实验2（worker 父 span + tags，PASS 证据集）保留：

- `labs-007-exp2-validate-20260208T090524Z.txt`
- `labs-007-exp2-jaeger-traces-operation-projection_process_batch-20260208T090524Z.json`
- `labs-007-exp2-jaeger-trace-outbox_worker_loop-20260208T090524Z.json`
- `labs-007-exp2-jaeger-trace-outbox_claim_batch-20260208T090524Z.json`
- `labs-007-exp2-jaeger-trace-projection_process_batch-20260208T090524Z.json`

---

## 实验2：Worker 父 span（让 trace depth 从“有”变“有用”）

目标：在 Jaeger 里能一眼看出 worker 的关键阶段，并能通过 tags 快速检索。

### 2.1 操作步骤

1) 按实验1启动 Jaeger / API / worker，并触发一次会写入 outbox 的 API 请求（例如 POST /api/v1/tags）。
2) 打开 Jaeger UI：`http://localhost:16686`
3) 选择 worker service（例如 `wordloom-search-outbox-worker`），找到对应 trace。

### 2.2 期望结果（验收点）

在 worker 的 trace 树上应出现以下父 span（名称精确匹配）：

- `outbox_worker.loop`
- `outbox.claim_batch`
- `projection.process_batch`

并且这些 span 上应带有可用于搜索的低基数 tags（至少包含以下之一/多项）：

- `projection=search`（或 `projection=chronicle`）
- `batch_size=<n>`
- `attempt=<n>`
- `result=ok|failed`

观察要点：DB spans（SQLAlchemy instrumentation 产生）应更自然地挂在 `outbox.claim_batch` / `projection.process_batch` 之下，trace depth 通常会从 1 提升到 3–5。

### 2.3 快照建议（新增）

- Jaeger UI 截图：包含 span tree（能看到上述 3 个父 span）
- （可选）用 Jaeger tags 搜索过滤的截图（例如 `projection=search` + `result=ok`）

---

## 结论（回填）

2026-02-08：

- 实验1：Tracing 最小闭环已跑通（API → outbox 写入 `traceparent/tracestate` → worker 取回并延续），并在 logs/Jaeger 侧可验证同一 `trace_id`。
- 实验2：worker trace depth 已增强，可在同一条 trace 中稳定观察到：
  - `outbox_worker.loop`
  - `outbox.claim_batch`
  - `projection.process_batch`
  且 span tags 满足低基数可检索要求（例如 `projection/batch_size/attempt/result`）。
- 证据集已整理为 Golden fixtures（见 7.1），其余迭代快照已归档到 `_archive/labs-007-20260208/`。

````
