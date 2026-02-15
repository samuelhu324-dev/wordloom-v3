# Log-S3A/2A/2B：migration/daemon-ready worker migration

---

**id**: `S3A-2A-2B`
**kind**: `log`               # log | lab | runbook | adr | note
**title**: `migration/daemon-ready worker migration`
**status**: `stable`          # draft | stable | archived
**scope**: `S3A`
**tags**: `EVOLOTION, Docs, Observability, lab, sub/2`
**links**: ``
  **issue**: `#40, #45`
  **pr**: ``
  **adr**: ``
  **runbook**: ``
**created**: `2026-02-13`
**updated**: `2026-02-13`

---

## Background

在 scripts 治理落地后（分区 + 统一入口 + legacy 围栏），仍有一个“不可拖延的关键点”：
`search_outbox_worker` 这类**线上会真的跑、且你会真的救火用**的入口，不应该长期处于“只能去 legacy/ 考古”的状态。

这份 log 的目标是：在不炸旧链接/旧 runbook/旧肌肉记忆的前提下，把 outbox worker 的运行入口迁移到“新体系的稳定入口”，并给出一个可持续的 cutover 策略。

本 log 结构遵循 [log-S0B-2A-scripts-snapshots-management.md](log-S0B-2A-scripts-snapshots-management.md) 的模板：每个议题保留 `draft/stable/archived` 三段，先落 draft，stable 与 archived 预留。

## What/How to do

0) Inventory（Search + Chronicle 两套“全家桶”入口清单）

**draft**:

- Search outbox（SearchIndex → Elasticsearch）：
  - Worker（长期运行）：
    - WSL2 推荐：`./backend/scripts/ops/run_worker.sh .env.dev` / `.env.test`
    - 稳定 Python 入口：`python backend/scripts/search_outbox_worker.py`（内部转发 legacy 实现）
  - Rebuild（SoT → search_index，可选 emit outbox）：`python backend/scripts/rebuild_search_index.py --truncate --emit-outbox`
  - Replay failed（failed → pending，带审计字段）：`python backend/scripts/search_outbox_replay_failed.py --by <who> --reason <why> --limit 100 --dry-run`
  - Labs：
    - 插入 pending 事件（供演练制造 supply）：`python backend/scripts/labs/labs_009_insert_search_outbox_pending.py`
    - 导出 Jaeger（证据）：`python backend/scripts/cli.py labs export-jaeger --service wordloom-search-outbox-worker --lookback 24h`

- Chronicle outbox（ChronicleEvents → ChronicleEntries）：
  - Worker（长期运行）：`python backend/scripts/chronicle_outbox_worker.py`
  - Rebuild（DB→DB，可选 emit outbox 验证 worker）：`python backend/scripts/rebuild_chronicle_entries.py --truncate --emit-outbox`
  - Replay failed：`python backend/scripts/chronicle_outbox_replay_failed.py --by <who> --reason <why> --limit 100 --dry-run`

**stable**:

- 已落地稳定入口（不再要求你去 `legacy/` 打开文件）：
  - `backend/scripts/ops/run_api.sh`、`backend/scripts/ops/run_worker.sh` 为稳定 shim（Procfile 继续引用稳定路径）。
  - `backend/scripts/*.py` 中关键 worker/replay/rebuild 入口已补齐稳定 shim。
  - Labs-009 相关 exporter/inserter 也补齐稳定 shim；实验类命令优先走 `backend/scripts/cli.py`。

**archived**:

1) Define what counts as “critical worker entrypoints”

**draft**:

- “critical entrypoint”的判定标准：
  - 实际会长期运行（daemon/worker），且失败时需要快速处置。
  - 被 Procfile / 一键启动脚本引用（属于开发/测试/演练闭环的必经路径）。
  - 被文档/Runbook/Issue 高频引用（路径一旦断，会造成排障/回归成本飙升）。
- 对应策略：critical entrypoint 必须在 `backend/scripts/` 根下有稳定入口（或 `backend/scripts/cli.py` 子命令），legacy 只作为实现复用或兼容层。

**stable**:

- 关键入口已按“稳定路径优先”的规则落地：
  - Search：`backend/scripts/ops/run_worker.sh` + `backend/scripts/ops/search_outbox_worker.py`
  - Chronicle：`backend/scripts/chronicle_outbox_worker.py`
  - Replay/Rebuild：`backend/scripts/(search_outbox_replay_failed|chronicle_outbox_replay_failed|rebuild_search_index|rebuild_chronicle_entries).py`

**archived**:

2) Migration model: “new engine + old handle (shim)”

**draft**:

- 不建议“硬搬家把旧入口弄死”。更稳妥的迁移模型是：
  - 新体系提供稳定入口（CLI / 顶层脚本 / run_*.sh）。
  - legacy 保留旧文件名/旧路径，但逐步退化为 shim（只做转发 + 弃用提示，不再承载新增逻辑）。
- shim 的目标：
  - 旧文档/旧 Issue 链接仍能打开、仍能跑。
  - 团队的“正确入口”逐步收敛到 CLI 或 stable 脚本路径。

**stable**:

- 已采用 shim 模式：legacy 实现保留在 `backend/scripts/legacy/`，稳定入口脚本在 `backend/scripts/` 转发执行。
- 对外推荐入口收敛为：`Procfile.*` + `run_*.sh`（运行）与 `cli.py`（实验/证据）。

**archived**:

3) Where to place the outbox worker in the taxonomy

**draft**:

- 建议的职责落点：
  - 对外稳定入口：`backend/scripts/ops/run_worker.sh`（WSL2 一键启动/Procfile 使用）
  - 运行实现（Python）：`backend/scripts/search_outbox_worker.py`（稳定路径；必要时内部可转发 legacy）
  - 演练/注入/证据导出：继续放在 `backend/scripts/labs/` 或 `backend/scripts/cli.py labs ...`
- CLI 的定位：
  - 对“实验/导出/证据收集”这类任务，优先收敛到 `backend/scripts/cli.py`（命令空间稳定）。
  - 对“长期运行 worker”这类任务，CLI 可以补充子命令，但不强制替代 Procfile + run_*.sh。

**stable**:

- Worker 运行链路保持在“稳定入口层”：
  - WSL2：`run_worker.sh`（便于 Procfile/honcho 一键启动）
  - Python：`backend/scripts/search_outbox_worker.py` 与 `backend/scripts/chronicle_outbox_worker.py`
- 演练/注入/证据导出继续在 `backend/scripts/labs/` 与 `backend/scripts/cli.py labs ...` 下演进。

**archived**:

4) Cutover rules (from now on)

**draft**:

- 从本 log 起，新增的 outbox worker 相关 runbook/实验脚本：
  - 不再引用 legacy 路径作为“官方入口”。
  - 统一引用稳定入口（`run_worker.sh` / `search_outbox_worker.py` / `cli.py`）。
- legacy 文档允许保留历史叙述，但如果包含“可执行命令”，应补充一条“当前推荐入口”。

**stable**:

- 新增 runbook/lab 不再引用 `backend/scripts/legacy/...` 作为主入口；统一引用稳定 shim 或 CLI。

**archived**:

5) Optimize ENVIRONMENTS + command-line startup docs (old docs refresh)

**draft**:

- 目标：减少“环境混淆 + 命令失效 + 路径搬家炸链”。
- 优化点（最小集合）：
  - `Procfile.dev/test` 引用的 `backend/scripts/ops/run_api.sh` 与 `backend/scripts/ops/run_worker.sh` 必须是稳定可用路径。
  - `docs/ENVIRONMENTS.md` 应指向当前的事实来源与入口文档（例如 `docs/QUICK_COMMANDS.md` 与 `docs/ONE_COMMAND_START_WSL2.md`），避免继续引用已迁移的 legacy 文档。
  - `docs/QUICK_COMMANDS.md` 中涉及 worker 的“直跑命令”，应与稳定入口一致（并明确：实验类命令优先走 CLI）。

**stable**:

- `docs/ENVIRONMENTS.md` 已更新为指向当前的命令事实来源，并在 dev/test worker 启动处明确推荐 `run_worker.sh`。
- `docs/QUICK_COMMANDS.md` 已对齐“稳定入口优先”的写法，避免搬家后命令失效。

**archived**:

