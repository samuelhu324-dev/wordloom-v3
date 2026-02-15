# Run-004：Observability Tracing（API → Outbox → Workers）SOP

对应实验（操作与结论）：

- labs：`docs/architecture/runbook/labs/labs-007-observability-tracing-api-outbox-worker.md`
- 快照目录（证据留存）：`docs/architecture/runbook/labs/_snapshots/`
- 设计/落地日志：`docs/logs/logs/v2-logs/log-S2A-1A-observability-tracing.md`
- 快照治理策略：`docs/logs/logs/v2-logs/log-S3A-lab-snapshots-management.md`

---

## 1) 目的与范围

- 目标：让一次 API 请求在 Jaeger 里能看到 API spans + outbox worker spans（跨异步边界同一 trace）。
- 范围：FastAPI（inbound）+ SQLAlchemy（DB）+ httpx（outbound）+ outbox（trace context 持久化）+ workers（继续 trace）。
- 不在范围：APM 平台化、复杂采样策略（tail sampling）、生产告警体系（以 metrics 为主）。

---

## 2) 前置条件

- Postgres（dev/test：localhost:5435）
- Elasticsearch（search 投影验证用：localhost:9200）
- Jaeger all-in-one（UI：16686；OTLP/HTTP：4318）

---

## 3) 开关与环境变量（最小集）

> 说明：Tracing 默认关闭；只在显式开启时生效。

- `WORDLOOM_TRACING_ENABLED=1`
- `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318`（代码会自动拼 `/v1/traces`）
- `OTEL_TRACES_SAMPLER=always_on`（实验/排障建议 always_on）

---

## 4) 一次跑通（dev/test 快速清单）

### 4.1 启动 Jaeger（推荐：Docker Desktop 可“点按钮”管理）

```powershell
docker compose -f docker-compose.infra.yml up -d jaeger
```

停止（可选）：

```powershell
docker compose -f docker-compose.infra.yml stop jaeger
```

### 4.2 迁移 DB（确保 outbox 有 trace 列）

```powershell
.
\backend\scripts\devtest_db_5435_migrate.ps1 -Database wordloom_test
```

### 4.3 启动 API（Windows 推荐启动器）

```powershell
$env:WORDLOOM_TRACING_ENABLED = "1"
$env:OTEL_TRACES_SAMPLER = "always_on"
$env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4318"

$env:WORDLOOM_ENV = "test"
$env:DATABASE_URL = "postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test"

# Windows 下推荐使用仓库内置启动器：强制 SelectorEventLoop，避免 psycopg async 与 ProactorEventLoop 的兼容问题
python .\backend\scripts\run_api_win.py
```

### 4.4 触发一次会写 outbox 的 API 请求

（以创建 Tag 为例）

```powershell
$body = @{ name = "trace-run-004"; color = "#FFFFFF" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/tags -ContentType "application/json" -Body $body
```

### 4.5 启动 Search outbox worker

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

---

## 5) 验收点（高信噪比）

### 5.1 DB：outbox 行写入 trace 上下文

```sql
select id, status, traceparent, tracestate, created_at
from search_outbox_events
order by created_at desc
limit 10;
```

期望：相关 outbox 行 `traceparent` 非空。

### 5.2 Jaeger：同一个 trace 中包含 API + worker spans

- 打开：`http://localhost:16686`
- Services 应至少出现：
  - `wordloom-api`
  - `wordloom-search-outbox-worker`
- 找到某条 trace：
  - API 的 HTTP server span（例如 POST /api/v1/tags）
  - worker 的 `outbox.process` span
  - 两者应属于同一 trace_id

### 5.3 实验2（截图1）：worker 父 span + tags

在 worker trace 树上应出现（名称精确匹配）：

- `outbox_worker.loop`
- `outbox.claim_batch`
- `projection.process_batch`

并且 span tags 至少包含以下之一/多项（低基数、可检索）：

- `projection=search|chronicle`
- `batch_size=<n>`
- `attempt=<n>`
- `result=ok|failed`

---

## 6) 脚本化校验（推荐）

> 目的：把“肉眼看 Jaeger”升级为“脚本输出 PASS/FAIL + 产物快照”。

实验2推荐脚本（Jaeger 导出 + 验证 + 快照）：

```powershell
python .\backend\scripts\_labs_007_exp2_export_validate_jaeger.py \
  --service wordloom-search-outbox-worker \
  --base-url http://localhost:16686/api \
  --outdir docs\architecture\runbook\labs\_snapshots \
  --lookback 30m \
  --operation projection.process_batch
```

说明：在 Jaeger 某些情况下仅用 `service` 拉 trace 列表可能漏掉目标 trace；加 `--operation projection.process_batch` 更稳定。

---

## 7) 常见问题（快速排障）

### 7.1 Jaeger 里没有任何 trace

- 确认 Jaeger 在跑：`http://localhost:16686` 能打开
- 确认进程启用了 tracing：`WORDLOOM_TRACING_ENABLED=1`
- 确认 OTLP endpoint：`OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318`
- 确认采样：实验建议 `OTEL_TRACES_SAMPLER=always_on`

### 7.2 API 与 worker 没有串成同一个 trace

- DB 查询 outbox 行，确认 `traceparent` 是否为空：为空说明 enqueue 时未注入上下文（常见原因：tracing 未开启或未走 outbox enqueue 路径）。
- 确认 worker 读取 outbox 行时包含 `traceparent/tracestate` 字段（非空才能继续 parent）。

### 7.3 Windows 下启动报事件循环相关错误

- API：使用 `python .\backend\scripts\run_api_win.py`
- worker：若异常，优先确保“从 repo root 运行脚本”，并避免同时启动多个同类 worker。

---

## 8) 证据留存与快照治理（S3A 落地版）

- 原则：每个 labs 只保留“最小可验收集合”（1 套端到端证据 + 1 套 PASS 证据）；其余迭代快照归档或删除。
- 推荐以 labs-007 文档中的 Golden fixtures 清单为模板。
- 快照治理策略与 DoD：见 `docs/logs/logs/v2-logs/log-S3A-lab-snapshots-management.md`。
