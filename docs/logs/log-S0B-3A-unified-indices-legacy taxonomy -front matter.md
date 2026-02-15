# Log-S4B/3A：tools/unified indices & legacy taxonomy & front matter

---

**id**: `S0B-3A`
**kind**: `log`               # log | lab | runbook | adr | note 
**title**: `tools/unified indices & legacy taxonomy & front matter`
**status**: `draft`          # draft | stable | archived
**scope**: `S0B`               
**tags**: `Docs, EVOLUTION, sub/1`
**links**: ``
  **issue**: `44`
  **pr**: ``
  **adr**: ``
  **runbook**: ``
**created**: `2026-02-12`
**updated**: `2026-02-12`

---

## Background

当前文档的 S 编号体系如果同时绑定：时间顺序、能力域/模块、以及交付批次，就会导致“改一次目录/能力域，就要全库大改”的高耦合问题。
本次调整的核心是把这些维度解耦：
时间顺序交给 Git Project/Issue 流水线管理；交付批次与内容用稳定的工作流编号表达；状态、范围、关联链接等便于机械维护的信息统一放到 front matter。
这样可以允许目录与内容持续演进（搬家不炸链），同时让命名规则可跨 log/lab/issues/runbook/adr 复用。

## What/How to do

1) Unified indices（统一工作流编号与索引入口）

**draft**:

- 目标：用统一的编号/命名规则表达“交付批次 + 内容主题”，但不再与时间顺序、特定模块目录强绑定。
- 命名规范（建议）：
  - 工作流编号：`S<No><Char>-<No><Char>`（或仅 `S<No><Char>` / `S<No>` 视场景裁剪）
  - 文件/条目命名：`<prefix>-S4B-3A-<slug>`，其中 `<prefix>` 可是 `log/lab/runbook/adr/issue` 等。
- 首层索引维护：
  - `S<No>` 这一层（例如 S0/S1/S2/S3/S4）由一个稳定入口维护（INDEX），不要求与目录结构一一对应。
  - INDEX 的职责是“稳定导航 + 语义解释”，不是时间线；时间线放在 Git Project。
- 例子与复用：
  - `xxx-S4B-3A-unified-indices-legacy-taxonomy-front-matter` 可用于 log/lab/git issues（用来表达：这是 S4B 下 3A 这个交付批次/主题）。
  - `S4B`（顶层）+ `<Char>`（例如 3A）可以用于 adr/runbook 这类“相对稳定资产”的聚合总结：代表在多个子 issues 之上收敛的稳定结论。

**stable**:

**archived**:

2) Legacy taxonomy（legacy 内容保留与“垃圾分类”）

**draft**:

- 原则：legacy 内容不轻易丢弃；优先“归类 + 指路 + 冻结”，而不是立刻“迁移/重写”。
- 第一阶段（指路与归类）：
  - 在 Git/Issue/文档中引用 legacy 时，统一使用显式标记，避免与新体系混淆：例如 `Legacy Refs: <path-or-link>`。
  - 按现有模块/领域做“垃圾分类”（不是价值判断，是便于检索）：例如 chronicle/search/outbox/observability/docs 等。
- 第二阶段（按需迁移）：
  - 后续如果某段 legacy 仍被频繁调用：按新系统规则迁移进去（并在 legacy 原位置留下 stub 指向）。
  - 如果只是“可能有用”：先不动，避免把精力消耗在低回报的搬运上。

**stable**:

**archived**:

3) Front matter（机械可管理的文档头部元数据）

**draft**:

- 目标：把状态/范围/标签/关联链接/创建更新时间等“便于机械维护”的字段统一放在 front matter，降低口头约定与人工对齐成本。
- 字段约定（参照本 log 与 ADR 模板 `docs/adr/-adr-.md`）：
  - `id`：使用统一工作流编号（例如 `S4B-3A`）
  - `kind`：`log | lab | runbook | adr | note`
  - `title`：人类可读标题（不承担版本/目录语义）
  - `status`：`draft | stable | archived`
  - `scope`：顶层范围（例如 `S4B`）
  - `tags`：可检索标签（建议低基数）
  - `links`：与 issue/pr/adr/runbook 的互链（便于从任一入口回到上下文）
  - `created/updated`：用于机械排序与审计
- ADR/runbook 这类稳定资产建议额外字段：`decision_date` / `context_issue` / `supersedes` / `superseded_by` / `applies_to` 等（不要塞进文件名）。

**stable**:

**archived**:

4) Cutover & Stub（从 S4B-3A 开始启用新文件管理体系）

**draft**:

- 从 `S4B-3A` 起，新增内容按新体系执行：
  - 命名使用统一编号（见 1）
  - 元数据写入 front matter（见 3）
  - legacy 只做归类/指路，不做大规模搬运（见 2）
- 与 legacy 的分界：
  - legacy 内容默认冻结为“参考资料”，继续存在但不主动扩写。
  - 新内容必须可被 INDEX/links 定位；必要时用 stub 保持旧引用不失效。

**stable**:

**archived**: