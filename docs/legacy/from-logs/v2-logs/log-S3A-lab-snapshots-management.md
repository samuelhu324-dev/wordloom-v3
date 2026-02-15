# Log-S3A: Lab 快照（snapshots）资产治理与清理策略

Status: draft
links:
- docs/architecture/runbook/labs/_snapshots/
- docs/architecture/runbook/labs/labs-007-observability-tracing-api-outbox-worker.md

## Background
快照目录（例如 `docs/architecture/runbook/labs/_snapshots/`）很容易在调试/试验迭代中堆成“垃圾山”。
但如果把快照全删，会失去可回放的基线，后续规则/worker 行为变化只能靠“感觉”回归。

## What/How to do

### 1) 给快照分层（决定什么该长期保留）
draft:
- 将快照当作“测试资产”管理，而不是临时产物。
- 把现有快照按用途分成三类：
	- Golden fixtures（长期保留，少而精）：证明“同一批输入事件 → 输出稳定（排序/过滤/汇总一致）”，需要进 git。
	- Diff snapshots（短期保留）：用于 v1/v2/v3 对照；结论固化后可归档或删除。
	- Ad-hoc dumps（默认不保留）：随手 dump 的 json/csv/log；用完即删或放入 `tmp/` 并 gitignore。
adopted:

- 2026-02-08（以 labs-007 为例）已完成一次分层清理：保留“可复现 + 可验收”的最小证据集在 `_snapshots/`，其余迭代产物移入归档目录。
- Golden fixtures（长期保留，当前 labs-007 最小集合）：exp1 保留 `labs-007-{api,worker,request,response,jaeger-*}-20260208T12*.{jsonl,json}`；exp2（PASS）保留 `labs-007-exp2-{validate,jaeger-trace-*,jaeger-traces-operation-*}-20260208T090524Z.*`。


### 2) 设定保留上限（垃圾山止血规则）
draft:
- 每个实验/每条 labs 只保留最小集合：
	- 1 份输入（fixtures）
	- 1 份输出（golden）
	- 1 份对照（可选，diff）
- 其余全部：删除或压缩归档（zip），避免目录持续膨胀。
- 为避免散落，按“实验号/日期/用途”固定结构（示例）：
	- `docs/.../labs-007/fixtures/`
	- `docs/.../labs-007/golden/`
	- `docs/.../labs-007/tmp/`（gitignore）
adopted:

- 2026-02-08（labs-007）：`docs/architecture/runbook/labs/_snapshots/` 仅保留 12 个关键文件；其余 80+ 个 `labs-007*` 迭代快照已移动到 `docs/architecture/runbook/labs/_snapshots/_archive/labs-007-20260208/`。


### 3) 定义“可以大清理”的 DoD（什么时候能放心删一大批）
draft:
- 当且仅当结论已经被制度化为：
	- 可重复的脚本（rebuild / replay / export / validate）
	- 可验证的断言（条数/排序/summary/过滤字段等）
	- 并写入 ADR/issue 的 DoD 或 runbook 验收步骤
- 满足以上三条后，历史 diff/ad-hoc 快照可以批量清理，因为价值已被脚本与断言替代。
adopted:

- 2026-02-08（labs-007）：已用可重复脚本 `backend/scripts/_labs_007_exp2_export_validate_jaeger.py` 固化实验2验收，并产出 `overall=PASS` 报告；因此历史 exp2 的失败验证快照、重复导出列表归档/清理是安全的（保留一套 PASS 证据集即可）。


### 4) 执行一次清理（把“当前目录”变成“可维护资产”）
draft:
- 选定一个实验（例如 labs-007），挑出能代表验收点的“最小快照集合”（输入/输出/对照）。
- 将其余同类重复文件移入归档（zip）或删除；把临时 dump 迁入 `tmp/` 并加入 gitignore。
- 在对应 labs 文档中记录“本实验的 Golden fixtures 是哪些文件、如何复现/如何校验”。
adopted:

- 2026-02-08（labs-007）：已完成一次清理动作——把非关键 `labs-007*` 快照移入 `_archive/labs-007-20260208/`，并在 `_snapshots/` 保留 exp1 的一套端到端证据 + exp2 的一套 PASS 证据。