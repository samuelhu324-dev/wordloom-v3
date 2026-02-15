# Log-S3A/2A/3B：automation/automated failure drills

---

**id**: `S3A-2A-3B`
**kind**: `log`               # log | lab | runbook | adr | note
**title**: `automation/automated failure drills`
**status**: `stable`          # draft | stable | archived
**scope**: `S3A`
**tags**: `EVOLOTION, Docs, Observability, lab, sub/2`
**links**: ``
  **issue**: `#39, #40, #46, #47`
  **pr**: ``
  **adr**: ``
  **runbook**: ``
**created**: `2026-02-14`
**updated**: `2026-02-14`

---

## Background

当前 failure drills 的痛点不是“不会触发失败”，而是：触发/验证/取证高度依赖人工流程，且每次都要重新拼命令、重复看图、手动导出证据。
这会直接导致两类浪费：

- 工程效率：每次演练都是一次“临场操作”，不可复用、不可批处理。
- 质量风险：缺少机器可判定的 PASS/FAIL，导致结论不稳定、难以回放与交接。

这份 log 的目标是把 failure drills 从“人肉实验”升级为“可编排的演练产品”：

- 一条命令稳定触发（run）
- 一条命令自动验收（verify）
- 一条命令自动打包证据（export）
- 一条命令清理历史产物（clean）

> 约束：本文只定义结构、契约与最小可行落地路径；具体实现以 `backend/scripts/cli.py` 为统一入口逐步推进。

## Malfunction

本节记录“按钮化落地过程”中真实发生的故障（malfunction），用于复盘与防再发。它不替代 runbook；只沉淀：现象 → 根因 → 修复 → 预防。

### 1) Windows 端口绑定失败（Prometheus metrics server）

- **现象**：worker 启动后很快退出；日志出现 `PermissionError: [WinError 10013] ... socket.bind`。
- **根因**：Windows 存在 TCP excluded port range（`netsh int ipv4 show excludedportrange protocol=tcp`），默认使用的 metrics 端口 `9129` 落在被系统保留的区间内（例如 `9129-9228`）。
- **修复**：改用非保留端口（例如 `9109`），并在按钮命令支持 `--metrics-port`。
- **预防**：将 `9129` 视为“不可靠默认值”；在 Windows 环境优先选择 `910x/920x` 等端口，或在 run 前做端口可用性探测。

### 2) WSL/Windows Python 解释器混用导致脚本 rc=2

- **现象**：在 WSL2/bash 中运行按钮时，触发脚本插入 outbox 事件失败（`failed to insert outbox event: rc=2`）。
- **根因**：脚本选择到了 Windows `.venv/Scripts/python.exe`，但在 WSL 下工作目录/路径是 POSIX 风格，导致解释器/路径不兼容。
- **修复**：解释器选择逻辑改为 OS-aware：Linux/WSL 不再误用 Windows venv；Windows 下才优先 `.venv`。
- **预防**：在文档中明确：WSL 路径与 Windows venv 不能混用；如需 WSL 运行，应使用 WSL 内的 Python 环境。

### 3) 缺失依赖导致 worker 启动失败

- **现象**：worker 抛 `ModuleNotFoundError: No module named 'prometheus_client'`。
- **根因**：当前 Python 环境未安装 `prometheus-client`。
- **修复**：在使用的 venv 安装缺失依赖；并将“缺依赖即失败”视为环境前置条件。
- **预防**：将 `prometheus-client` 纳入后端依赖清单（例如 requirements/lock），避免“按钮运行到一半才发现缺包”。

### 4) ExpC 触发成功但 verify 误判（delta=0）

- **现象**：worker 日志里已经出现 ES 403，但 verify 仍失败：`outbox_failed_total{reason="es_4xx"}` 的 delta 为 0。
- **根因**：run 的步骤顺序导致 `metrics-before` 抓取发生在“失败已经发生之后”（失败太快，第一次 scrape 就包含失败计数），因此 delta 断言不成立。
- **修复**：调整 run 顺序为：先启动 worker → 等待指标端点可用并抓取基线 → 再注入 write-block → 再插入 outbox 事件 → 结束前抓取 after。
- **预防**：所有 delta 型断言都必须保证“before 在刺激之前”。必要时引入更明确的阶段标记（baseline/trigger/after）。

### 5) ExpC 事件被标记 done（未实际写 ES）

- **现象**：outbox row 状态为 `done`，但并未产生 ES 写失败指标（无 `reason="es_4xx"`），verify 持续失败。
- **根因**：触发脚本只插入 `search_outbox_events`，但未确保对应的 `search_index` 数据存在；worker 的 upsert 路径可能在数据缺失时走了“无写入/早返回”路径，导致 outbox 被当作已处理。
- **修复**：触发脚本增加可选行为：同时 upsert 一条匹配的 `search_index` 行（`OUTBOX_CREATE_SEARCH_INDEX_ROW=1`），确保 worker 必然发起 ES 写入，从而命中 write-block 403。
- **预防**：所有“驱动负载”脚本都必须保证业务前置数据齐全；否则会出现“事件流形式上跑完，但关键外部副作用未发生”。

### 6) Jaeger 导出按钮参数不匹配

- **现象**：`labs export es_write_block_4xx` 失败，提示 `unrecognized arguments: --operation outbox.process`。
- **根因**：按钮封装向 `labs_009_export_jaeger.py` 传了 `--operation`，但该脚本的 operation 是由 `--outbox-event-id/--claim-batch-id` 内部推导，不接受 `--operation` 参数。
- **修复**：移除 `--operation` 传参，仅用 `--outbox-event-id` 定位导出（脚本内部会使用 `operation=outbox.process`）。
- **预防**：按钮封装应与底层脚本保持“契约对齐”；对外暴露参数前先对齐底层 CLI 形态，避免“wrapper 漂移”。

## What/How to do

1) 把失败变成“开关 + 配方”（统一故障注入契约）

**draft**:

- 目标：任何失败场景都必须能用一条命令稳定触发；不再依赖“临场停容器/手改配置”。
- 做法：在 adapter 层保留细粒度注入开关（例如现有 `OUTBOX_EXPERIMENT_ES_429_*`），同时引入一个更高层的统一契约，作为自动化 harness 的输入。

建议统一契约（环境变量，作为 run/verify 的共同参数）：

- `FAULT_SCENARIO`：场景名（枚举）
  - 例：`es_429_inject` / `es_down` / `es_write_block_4xx` / `collector_down` / `db_lock`
- `FAULT_RATE`：注入比例（可选；0~1）
- `FAULT_EVERY_N`：确定性注入（可选；优先级高于 rate）
- `FAULT_DURATION_S`：持续时间（可选；到期自动恢复）
- `FAULT_MATCH`：匹配范围（可选；例如 `projection=search` / `op=upsert,delete`）

落地规则：

- harness 只识别 `FAULT_*`，并在内部映射到当前实现的细项开关（避免上层调用方知道各脚本/各组件的私有参数）。
- 所有注入必须输出结构化“配方回显”日志（便于审计/复盘），并落到证据包。

**stable**:

- 现状：尚未引入文档中设想的统一 `FAULT_*` 契约；当前实现采取“场景级别的细粒度开关（env vars）+ 统一入口（cli）”的折中方案，先保证可复现与可验收。
- 已可稳定复现的注入/故障开关（代表性示例）：
  - ExpB（ES 429）：`OUTBOX_EXPERIMENT_ES_429_EVERY_N` / `OUTBOX_EXPERIMENT_ES_429_RATIO` / `OUTBOX_EXPERIMENT_ES_429_SEED`
  - ExpC（ES write-block -> 4xx）：通过 controller 对 ES index settings 置 `index.blocks.write=true`，再触发 outbox 事件
  - ExpD（bulk partial）：`OUTBOX_EXPERIMENT_ES_BULK_PARTIAL=1` + `OUTBOX_EXPERIMENT_ES_BULK_PARTIAL_STATUS`
  - ExpE（DB claim contention）：`OUTBOX_EXPERIMENT_BREAK_CLAIM=1` + `OUTBOX_EXPERIMENT_BREAK_CLAIM_SLEEP_SECONDS`
  - ExpF（stuck/reclaim）：`OUTBOX_EXPERIMENT_PROCESS_SLEEP_SECONDS`（用于让 processing 状态可被 reclaim）
  - ExpH（projection_version）：`CHRONICLE_PROJECTION_VERSION`（Chronicle projector 的规则版本开关）
- 约束：上述开关被 `backend/scripts/cli.py` 以“场景参数”方式封装，避免调用者直接拼 env；但跨场景统一的 `FAULT_*` 映射仍处于 draft。

**archived**:

2) 把实验固化成 Test Harness（统一入口：run/verify/export/clean）

**draft**:

- 目标：不再让人记“脚本文件名/参数组合”，而是记“场景名 + 环境”。
- 统一入口：`backend/scripts/cli.py`（已存在，作为命令空间路由器）。

建议命令形态（示意，不要求一次性全做完）：

- `python backend/scripts/cli.py labs run <scenario> --env .env.test [--duration 120] [--load profile]`
- `python backend/scripts/cli.py labs verify <scenario> --since 10m --env .env.test`
- `python backend/scripts/cli.py labs export <scenario> --since 10m --env .env.test`
- `python backend/scripts/cli.py labs clean --keep-last 20`

run 的最小职责：

- 启动/确认依赖（ES/DB/Jaeger 可选）
- 应用故障配方（注入/阻断/停服务）
- 驱动负载（插入 outbox、API loadgen 或 DB 注入脚本）

verify 的最小职责（机器判定）：

- Metrics 断言（最低成本）
- Logs 断言（最高可信）
- Tracing 断言（最高可解释性，可选）

export 的最小职责（证据包）：

- 导出代表性 Jaeger traces（若开启 tracing）
- 抓取 metrics 片段（或 PromQL 导出）
- 截取结构化日志（过滤 200~500 行）
- 写 `result.json`（PASS/FAIL + why + 配方参数）

clean 的最小职责：

- 基于保留策略清理历史产物（按次数/按天数）

**stable**:

- 已落地统一入口：`backend/scripts/cli.py`，并以 `labs run|verify|export|clean <scenario>` 作为稳定命令空间。
- 已按钮化（run/verify/export/clean 全链路具备）的场景清单（对应 Lab-S3A-2A-3A 的实验 A–H）：
  - `es_down_connect`（ExpA）
  - `es_429_inject`（ExpB）
  - `es_write_block_4xx`（ExpC）
  - `es_bulk_partial`（ExpD）
  - `db_claim_contention`（ExpE）
  - `stuck_reclaim`（ExpF）
  - `duplicate_delivery`（ExpG）
  - `projection_version`（ExpH，Chronicle projector）
- 额外稳定命令：`labs export-jaeger` 作为 Jaeger 导出脚本的统一 wrapper（减少“记脚本文件名/参数”的成本）。

**archived**:

3) 统一证据包结构（每次运行自动落盘，可回放/可交接）

**draft**:

- 目标：证据包是“可验收产物”，不是“随手截图”。
- 建议统一输出根：
  - Labs：`docs/labs/_snapshot/`
  - 其中自动化产物建议独立子目录：`docs/labs/_snapshot/auto/`（避免和 manual 混在一起）

推荐目录结构：

- `docs/labs/_snapshot/auto/<lab_id>/<scenario>/<run_id>/`
  - `_recipe.json`（注入配方与参数回显）
  - `_result.json`（PASS/FAIL + why + 关键计数）
  - `_metrics.txt`（抓取片段/导出）
  - `_logs.ndjson`（结构化日志片段，带 trace_id/span_id）
  - `_traces.json`（Jaeger 导出，可选）
  - `_notes.md`（人工补充：解释异常/下一步）

落地规则：

- `run_id` 必须包含时间戳 + env（避免覆盖与混淆）。
- 所有导出都要带上 `WORDLOOM_ENV` / `env` / `projection` 的关键过滤条件。

**stable**:

- 已落地统一快照根：`docs/labs/_snapshot/auto/`，并按 `<lab_id>/<scenario>/<run_id>/` 归档（run_id 使用本地时间戳，避免覆盖）。
- 已落地的证据包目录结构（与 draft 相比做了“目录分桶”，更利于审计与 diff）：
  - `_recipe.json`：本次 run 的配方/参数回显（场景、端口、注入开关、触发次数等）
  - `_result.json`：run 的过程性结果/关键 IDs（部分 verify 也会写入）
  - `_verify_result.json`：verify 的机器判定结果（若场景需要独立输出，例如 ExpH）
  - `_logs/`：worker/controller 产出的日志（单文件或多 worker 文件）
  - `_metrics/`：`metrics-before*.txt` / `metrics-after*.txt`（用于 delta 断言与离线复核）
  - `_exports/`：Jaeger 导出等补充证据（`jaeger-traces-*.json`）
- 已落实“自动化产物与手工产物分离”：`auto/` 只放可复现 harness 的产物，避免与 manual 混淆。

**archived**:

4) 自动判定：把“看图”变成“断言”（verify 规则清单）

**draft**:

将验收拆成三层（由快到慢、由稳到强解释）：

- Metrics 断言（最优先）：
  - 示例：`outbox_retry_scheduled_total{reason="es_429"} > 0`
  - 示例：实验 C（不可恢复 4xx）应满足：`outbox_failed_total > 0` 且 `outbox_retry_scheduled_total` 不增长
  - 注意：label 只允许低基数枚举（`reason` 不能塞错误字符串）

- Logs 断言（最可信）：
  - 必须能 grep 到结构化字段组合（projection/op/attempt/result/reason + trace_id/span_id）
  - 必须能定位到“失败摘要/响应码/堆栈”细节

- Tracing 断言（最直观，可选）：
  - `operation=projection.process_batch` 必须带 `result=retry|failed`
  - 能按 `wordloom.outbox_event_id` 精确定位 `operation=outbox.process`

输出要求：

- verify 必须生成 `_result.json`，包含：
  - `pass`（bool）
  - `checks`（每条断言的 observed 值、阈值、是否通过）
  - `why`（失败原因短句）

**stable**:

- verify 已实现“机器可判定”最小闭环：
  - 优先使用 metrics delta（before/after）做阈值断言（例如 retry/fail/processed 的最小增量与最大容许值）。
  - 对时序敏感场景（例如 ExpF）引入 logs 作为 fallback 证据：允许出现 `metrics delta=0` 但 logs 已明确取证时判定 OK，避免 scrape 时序导致的误判。
- verify 输出：每次 verify 至少生成一个 JSON 结果文件（`_result.json` 或 `_verify_result.json`），包含 `ok/pass`、`checks` 与 `observed`，便于 CI/回放。
- Tracing 断言当前以“可解释性导出”为主（export），而不是强制 PASS/FAIL；原因：Jaeger/OTLP 的可用性与采样策略会引入环境噪声。

**archived**:

5) 演进策略：先自动化 Top 3 场景，再扩展长尾

**draft**:

建议优先级（按收益/稳定性排序）：

- P0：可控注入（干净信号，可复验）
  - 实验 B：`es_429_inject`
  - 实验 C：`es_write_block_4xx`（索引写阻断 → 稳定 403）
- P1：基础外部故障（接近真实，但噪声更大）
  - 实验 A：`es_down`
  - `collector_down`

落地节奏：

- 每落地一个 scenario，必须同时交付：`run` + `verify` + `export` + 证据包示例。
- 文档（labs）只引用统一入口；不再扩写分散脚本命令（最多保留“原理解释 + 参数表”）。

**stable**:

- 已按“先 P0 再 P1”的顺序落地并扩展：最初的 P0（ExpB/ExpC）已具备稳定按钮；随后 P1/P2（ExpA/ExpD/ExpE/ExpF/ExpG/ExpH）也已完成 run/verify/export/clean 的自动化闭环。
- 当前节奏约束落地为规则：每新增一个 scenario，必须同步交付 `run + verify + export`（以及可选 `clean`），否则不算完成。
- 后续长尾扩展建议：优先补齐“统一 `FAULT_*` 契约映射”（把场景参数统一到文档契约），再考虑引入更多外部故障（collector/db/network）与负载模型。

**archived**:
