# Log-S3A/2A/4B：automation/failure-drills-&-gitactions-&-dashboard

---

**id**: `S3A-2A-4B`
**kind**: `log`               # log | lab | runbook | adr | note
**title**: `automation/failure drills & git actions & dashboard`
**status**: `stable`          # draft | stable | archived
**scope**: `S3A`
**tags**: `EVOLOTION, Observability, lab, sub/2`
**links**: ``
  **issue**: `#49`
  **pr**: ``
  **adr**: ``
  **runbook**: ``
**created**: `2026-02-14`
**updated**: `2026-02-15`

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
  - 例：`es_429_inject` / `es_down_connect` / `es_write_block_4xx` / `collector_down` / `db_lock`
- `FAULT_RATE`：注入比例（可选；0~1）
- `FAULT_EVERY_N`：确定性注入（可选；优先级高于 rate）
- `FAULT_DURATION_S`：持续时间（可选；到期自动恢复）
- `FAULT_MATCH`：匹配范围（可选；例如 `projection=search` / `op=upsert,delete`）

落地规则：

- harness 只识别 `FAULT_*`，并在内部映射到当前实现的细项开关（避免上层调用方知道各脚本/各组件的私有参数）。
- 所有注入必须输出结构化“配方回显”日志（便于审计/复盘），并落到证据包。

**stable**:

- 当前“统一契约”已形成最小可用形态：
  - GitHub Actions 入口以 `scenario` 作为主输入，并把 `FAULT_SCENARIO` 注入到 job 环境中（便于后续把 workflow 与底层开关解耦）。
  - Harness（`backend/scripts/cli.py`）对外以 `scenario`（命令参数）作为唯一识别，不要求调用方理解 legacy 的细项环境变量。
- 细粒度注入开关（例如 `OUTBOX_EXPERIMENT_*`）仍由各场景实现内部管理；统一的 `FAULT_* → 细项开关` 映射策略保留在 draft 以支持后续收敛。

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

- 已落地统一入口：`backend/scripts/cli.py` 提供 `labs run/verify/export/clean <scenario>` 的稳定路由。
- 已落地场景（P0–P3 覆盖 A–H）：
  - P0：`es_429_inject`、`es_write_block_4xx`、`es_bulk_partial`
  - P1：`es_down_connect`、`collector_down`
  - P2：`db_claim_contention`、`stuck_reclaim`
  - P3：`duplicate_delivery`、`projection_version`
- Run/Verify/Export/Clean 的“证据包产出 + 机器判定”已能端到端跑通（见第 5 节 smoke 证据包示例）。

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

- 已采用统一输出根：`docs/labs/_snapshot/auto/`（自动化产物）并按 `lab_id/scenario/run_id` 分层落盘。
- 证据包已稳定包含（最少集合）：
  - `_recipe.json`：本次运行的配方与关键参数回显
  - `_result.json`：机器判定（PASS/FAIL + why + checks）
  - `_logs/`：worker stdout/stderr 证据
  - `_metrics/`：关键指标抓取（before/after 或片段）
  - `_exports/`：Jaeger 导出（如开启 tracing；`collector_down` 允许导出失败但必须落盘失败证据）

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

- 已落地 `verify` 的机器判定输出：每次 verify 都生成 `_result.json`，并包含 `pass/why/checks[]`。
- 已覆盖的断言类型：
  - Metrics delta 断言（处理 “before 在刺激之前” 的竞态，run 顺序已调整以保证 delta 可判定）
  - Worker 运行日志证据落盘（用于复核与交接）
  - Tracing 导出（作为解释性证据；对 `collector_down` 允许缺失，但必须落盘 export 失败说明）

**archived**:

5) 演进策略：先自动化 Top 3 场景，再扩展长尾

**draft**:

建议优先级（按收益/稳定性排序）：

优先级评估维度（用于把 A–H 分层）：

- **可控性**：是否能用“注入开关/配方”稳定复现（而不是靠手工停服务/抢时序）。
- **信号干净程度**：metrics/logs/traces 是否能给出低噪声的 PASS/FAIL。
- **实现成本**：run 阶段要做多少编排（起/停依赖、插入数据、同步等待等）。
- **时序/竞态风险**：是否依赖 before/after scrape 窗口或多 worker 竞争（更容易 flaky）。

- P0：可控注入（干净信号，可复验；优先按钮化）
  - 实验 B：`es_429_inject`（确定性/概率性 429 注入 → retry/backoff 指标稳定）
  - 实验 C：`es_write_block_4xx`（索引写阻断 → 稳定 403；验证规则清晰：failed 增、retry 不增）
  - 实验 D：`es_bulk_partial`（bulk item 级部分失败 → partial/success/failed/4xx 计数器稳定）

- P1：外部故障 / 真实感更强（实现成本中等；噪声较大）
  - 实验 A：`es_down_connect`（ES 不可达 → connect failure；需要明确 run 阶段的“停/起”窗口与 before/after）
  - `collector_down`（停 Jaeger collector/query；预期：业务处理仍继续；export 可能失败但需落盘失败证据）

- P2：并发/竞态类（可复验但更容易 flaky；需要更强的阶段化与证据）
  - 实验 E：`db_claim_contention`（双 worker 非原子 claim 竞争 → owner_mismatch 等信号；需要人为扩大竞争窗口）
  - 实验 F：`stuck_reclaim`（kill worker mid-lease → reclaim；需要过程控制与超时策略）

- P3：语义验证/边界行为（信号规模小但解释性强；通常用于回归/防退化）
  - 实验 G：`duplicate_delivery`（幂等/重复投递：delete 404 等可接受失败形态）
  - 实验 H：`projection_version`（v1/v2 投影一致性：probe 校验 + traces 辅助）

落地节奏：

- 每落地一个 scenario，必须同时交付：`run` + `verify` + `export` + 证据包示例。
- 文档（labs）只引用统一入口；不再扩写分散脚本命令（最多保留“原理解释 + 参数表”）。

证据包示例（smoke runs, 2026-02-14）：

- P0 / `es_429_inject`
  - run_dir: [docs/labs/_snapshot/auto/S3A-2A-3A/es_429_inject/smoke-es-429-inject-20260214T222547/](../labs/_snapshot/auto/S3A-2A-3A/es_429_inject/smoke-es-429-inject-20260214T222547/)
  - result: [docs/labs/_snapshot/auto/S3A-2A-3A/es_429_inject/smoke-es-429-inject-20260214T222547/_result.json](../labs/_snapshot/auto/S3A-2A-3A/es_429_inject/smoke-es-429-inject-20260214T222547/_result.json)
  - traces: [docs/labs/_snapshot/auto/S3A-2A-3A/es_429_inject/smoke-es-429-inject-20260214T222547/_exports/jaeger-traces-outbox_event_id-56acd97e-84dc-46a9-bccd-30e78be3eb22-20260214T142602.json](../labs/_snapshot/auto/S3A-2A-3A/es_429_inject/smoke-es-429-inject-20260214T222547/_exports/jaeger-traces-outbox_event_id-56acd97e-84dc-46a9-bccd-30e78be3eb22-20260214T142602.json)

- P0 / `es_write_block_4xx`
  - run_dir: [docs/labs/_snapshot/auto/S3A-2A-3A/es_write_block_4xx/smoke-es-write-block-4xx-20260214T222602/](../labs/_snapshot/auto/S3A-2A-3A/es_write_block_4xx/smoke-es-write-block-4xx-20260214T222602/)
  - result: [docs/labs/_snapshot/auto/S3A-2A-3A/es_write_block_4xx/smoke-es-write-block-4xx-20260214T222602/_result.json](../labs/_snapshot/auto/S3A-2A-3A/es_write_block_4xx/smoke-es-write-block-4xx-20260214T222602/_result.json)
  - traces: [docs/labs/_snapshot/auto/S3A-2A-3A/es_write_block_4xx/smoke-es-write-block-4xx-20260214T222602/_exports/jaeger-traces-outbox_event_id-f0938244-fb2a-4196-8fa4-42051e976a7a-20260214T142619.json](../labs/_snapshot/auto/S3A-2A-3A/es_write_block_4xx/smoke-es-write-block-4xx-20260214T222602/_exports/jaeger-traces-outbox_event_id-f0938244-fb2a-4196-8fa4-42051e976a7a-20260214T142619.json)

- P0 / `es_bulk_partial`
  - run_dir: [docs/labs/_snapshot/auto/S3A-2A-3A/es_bulk_partial/smoke-es-bulk-partial-20260214T222622/](../labs/_snapshot/auto/S3A-2A-3A/es_bulk_partial/smoke-es-bulk-partial-20260214T222622/)
  - result: [docs/labs/_snapshot/auto/S3A-2A-3A/es_bulk_partial/smoke-es-bulk-partial-20260214T222622/_result.json](../labs/_snapshot/auto/S3A-2A-3A/es_bulk_partial/smoke-es-bulk-partial-20260214T222622/_result.json)
  - traces: [docs/labs/_snapshot/auto/S3A-2A-3A/es_bulk_partial/smoke-es-bulk-partial-20260214T222622/_exports/jaeger-traces-tags-20260214T142638.json](../labs/_snapshot/auto/S3A-2A-3A/es_bulk_partial/smoke-es-bulk-partial-20260214T222622/_exports/jaeger-traces-tags-20260214T142638.json)

- P1 / `collector_down`
  - run_dir: [docs/labs/_snapshot/auto/S3A-2A-3A/collector_down/smoke-collector-down-20260214T221732/](../labs/_snapshot/auto/S3A-2A-3A/collector_down/smoke-collector-down-20260214T221732/)
  - result: [docs/labs/_snapshot/auto/S3A-2A-3A/collector_down/smoke-collector-down-20260214T221732/_result.json](../labs/_snapshot/auto/S3A-2A-3A/collector_down/smoke-collector-down-20260214T221732/_result.json)
  - export note (expected failure allowed): [docs/labs/_snapshot/auto/S3A-2A-3A/collector_down/smoke-collector-down-20260214T221732/_export_note.txt](../labs/_snapshot/auto/S3A-2A-3A/collector_down/smoke-collector-down-20260214T221732/_export_note.txt)

- P1 / `es_down_connect`
  - run_dir: [docs/labs/_snapshot/auto/S3A-2A-3A/es_down_connect/smoke-es-down-connect-20260214T222122/](../labs/_snapshot/auto/S3A-2A-3A/es_down_connect/smoke-es-down-connect-20260214T222122/)
  - result: [docs/labs/_snapshot/auto/S3A-2A-3A/es_down_connect/smoke-es-down-connect-20260214T222122/_result.json](../labs/_snapshot/auto/S3A-2A-3A/es_down_connect/smoke-es-down-connect-20260214T222122/_result.json)
  - traces: [docs/labs/_snapshot/auto/S3A-2A-3A/es_down_connect/smoke-es-down-connect-20260214T222122/_exports/jaeger-traces-outbox_event_id-e2504dab-2e39-4e6d-b62c-0ca906ba7237-20260214T142139.json](../labs/_snapshot/auto/S3A-2A-3A/es_down_connect/smoke-es-down-connect-20260214T222122/_exports/jaeger-traces-outbox_event_id-e2504dab-2e39-4e6d-b62c-0ca906ba7237-20260214T142139.json)

- P2 / `db_claim_contention`
  - run_dir: [docs/labs/_snapshot/auto/S3A-2A-3A/db_claim_contention/smoke-db-claim-contention-20260214T223922/](../labs/_snapshot/auto/S3A-2A-3A/db_claim_contention/smoke-db-claim-contention-20260214T223922/)
  - result: [docs/labs/_snapshot/auto/S3A-2A-3A/db_claim_contention/smoke-db-claim-contention-20260214T223922/_result.json](../labs/_snapshot/auto/S3A-2A-3A/db_claim_contention/smoke-db-claim-contention-20260214T223922/_result.json)
  - traces: [docs/labs/_snapshot/auto/S3A-2A-3A/db_claim_contention/smoke-db-claim-contention-20260214T223922/_exports/jaeger-traces-tags-20260214T143947.json](../labs/_snapshot/auto/S3A-2A-3A/db_claim_contention/smoke-db-claim-contention-20260214T223922/_exports/jaeger-traces-tags-20260214T143947.json)

- P2 / `stuck_reclaim`
  - run_dir: [docs/labs/_snapshot/auto/S3A-2A-3A/stuck_reclaim/smoke-stuck-reclaim-20260214T224105/](../labs/_snapshot/auto/S3A-2A-3A/stuck_reclaim/smoke-stuck-reclaim-20260214T224105/)
  - result: [docs/labs/_snapshot/auto/S3A-2A-3A/stuck_reclaim/smoke-stuck-reclaim-20260214T224105/_result.json](../labs/_snapshot/auto/S3A-2A-3A/stuck_reclaim/smoke-stuck-reclaim-20260214T224105/_result.json)
  - traces: [docs/labs/_snapshot/auto/S3A-2A-3A/stuck_reclaim/smoke-stuck-reclaim-20260214T224105/_exports/jaeger-traces-tags-20260214T144148.json](../labs/_snapshot/auto/S3A-2A-3A/stuck_reclaim/smoke-stuck-reclaim-20260214T224105/_exports/jaeger-traces-tags-20260214T144148.json)

- P3 / `duplicate_delivery`
  - run_dir: [docs/labs/_snapshot/auto/S3A-2A-3A/duplicate_delivery/smoke-duplicate-delivery-20260214T224157/](../labs/_snapshot/auto/S3A-2A-3A/duplicate_delivery/smoke-duplicate-delivery-20260214T224157/)
  - result: [docs/labs/_snapshot/auto/S3A-2A-3A/duplicate_delivery/smoke-duplicate-delivery-20260214T224157/_result.json](../labs/_snapshot/auto/S3A-2A-3A/duplicate_delivery/smoke-duplicate-delivery-20260214T224157/_result.json)
  - traces: [docs/labs/_snapshot/auto/S3A-2A-3A/duplicate_delivery/smoke-duplicate-delivery-20260214T224157/_exports/jaeger-traces-tags-20260214T144212.json](../labs/_snapshot/auto/S3A-2A-3A/duplicate_delivery/smoke-duplicate-delivery-20260214T224157/_exports/jaeger-traces-tags-20260214T144212.json)

- P3 / `projection_version`
  - run_dir: [docs/labs/_snapshot/auto/S3A-2A-3A/projection_version/smoke-projection-version-20260214T224229/](../labs/_snapshot/auto/S3A-2A-3A/projection_version/smoke-projection-version-20260214T224229/)
  - result: [docs/labs/_snapshot/auto/S3A-2A-3A/projection_version/smoke-projection-version-20260214T224229/_result.json](../labs/_snapshot/auto/S3A-2A-3A/projection_version/smoke-projection-version-20260214T224229/_result.json)
  - traces: [docs/labs/_snapshot/auto/S3A-2A-3A/projection_version/smoke-projection-version-20260214T224229/_exports/jaeger-traces-tags-20260214T144302.json](../labs/_snapshot/auto/S3A-2A-3A/projection_version/smoke-projection-version-20260214T224229/_exports/jaeger-traces-tags-20260214T144302.json)

**stable**:

- 分层（P0–P3）已在此文档固化，并完成 A–H 全覆盖的 smoke 证据包示例（见本节“证据包示例”）。
- 每个 scenario 都具备最小交付件：`run + verify + export + clean`，且证据包目录可回放/可交接。

**archived**:

6) 把按钮搬进 GitHub Actions（workflow_dispatch / matrix）

**draft**:

- 目标：把“演练按钮”放到 GitHub Actions，形成可审计的回归入口：一键触发（run）→ 一键验收（verify）→ 一键取证（export）→ 一键清理（clean）。
- 最小输入（workflow_dispatch inputs）：
  - `scenario`：`es_429_inject` / `es_write_block_4xx` / `es_down_connect` / `collector_down` / `db_lock` ...
  - `env`：`.env.test` 或 `test`（以 harness 支持为准）
  - `duration`：例如 `120`
  - `since`：例如 `10m`（verify/export 的窗口）
  - `keep_last`：例如 `20`（clean 用）

- Job 的最小职责（与 harness 对齐）：
  - `run`：`python backend/scripts/cli.py labs run <scenario> --env <env> --duration <duration>`
  - `verify`：`python backend/scripts/cli.py labs verify <scenario> --env <env> --since <since>`
  - `export`：`python backend/scripts/cli.py labs export <scenario> --env <env> --since <since>`
  - `clean`（可选）：`python backend/scripts/cli.py labs clean <scenario> --keep-last <keep_last>`
  - Artifact：把 `docs/labs/_snapshot/auto/<lab_id>/<scenario>/<run_id>/` 整体打包上传（不再靠截图）。

- CI 环境依赖的两条路线：
  - 路线 1（优先）：CI 内全起（更可控）
    - 用 `docker compose up -d` 起 DB/ES/Jaeger(Collector)/Prometheus（按需）
    - 优点：可复验；缺点：启动慢、资源占用高
  - 路线 2：CI 只跑 harness（更轻）
    - 依赖外部常驻环境；优点：快；缺点：环境漂移会影响稳定性

- Inputs → 统一契约（建议）：
  - Actions 只负责把 inputs 映射成环境变量（尤其 `FAULT_*`），harness 内部负责映射到底层注入开关；避免 workflow 了解底层细项参数名。

- Job Summary（验收即交付结论）：
  - 从 `_result.json` 读取 `pass/why/checks[]`，写入 `GITHUB_STEP_SUMMARY`。
  - Summary 里至少包含：scenario、PASS/FAIL、why、关键断言 observed vs expected、artifact 链接。

- 逐步落地：
  - 先单场景按钮（P0 两个最稳）：`es_429_inject`、`es_write_block_4xx`
  - 单场景稳定后，再做 `matrix` 作为“回归按钮”（一次跑多个场景）。

**stable**:

- 已落地 workflow：`.github/workflows/failure-drills.yml`
  - `workflow_dispatch` 输入：`scenario/env_file/duration/lookback/keep_last`
  - CI 启动 infra：`docker compose -f docker-compose.infra.yml up -d` + `docker compose -f docker-compose.devtest-db.yml up -d`
  - 执行顺序固定：`run → verify → export → clean`
  - 证据包上传：上传 `docs/labs/_snapshot/auto/` 作为 artifact
- Job Summary 的 `_result.json → GITHUB_STEP_SUMMARY` 解析仍保留在 draft（当前优先保证 artifact 可回放）。

**archived**:

7) 上按钮门槛：同一场景连续 5 次一致（最小稳定性基准）

**draft**:

- 目标：保证“按钮”不是一次性脚本，而是可复验的工程产物。
- 门槛定义（建议）：同一 `scenario` + 同一 `env`，完整跑通 `run → verify → export` 连续 5 次，结果一致。
  - “一致”优先指：`verify` 能稳定给出 PASS/FAIL 且 `_result.json` 的 `why/checks[]` 可解释。
  - 若因 scrape 时机/噪声导致 metrics delta 不稳定，应调整 run 阶段顺序或把关键断言降级为 logs 断言，而不是把门槛放宽为“能跑完就算”。
- 证据要求：每次 run 都必须产出完整证据包；必要时在 `_notes.md` 记录异常与修复要点，避免“只在操作者脑子里”。

**stable**:

- 已完成“端到端可复验”的最小门槛：A–H 全场景均至少完成一次完整链路 smoke（run→verify→export→clean），并在第 5 节给出证据包示例。
- 连续 5 次一致（抗 flaky）门槛保留为验收标准：当需要把某个 scenario 标记为“回归按钮”时，再对该场景执行 5x 稳定性验证并记录结果。

**archived**: