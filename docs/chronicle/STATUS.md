# Chronicle STATUS

> 只写三类：scope / exit criteria / links。
> 
> 约定：ROADMAP 的 Now/Next 必须指向本文件的某个锚点；本文件只在 “Current work” 区块反向引用 ROADMAP 的一条当前工作（避免复制粘贴发散）。

## Current work (from ROADMAP)
- docs/ROADMAP.md（Now/Next 里带有 `[Chronicle] ... → docs/chronicle/STATUS.md#...` 的条目）

---

<a id="v1"></a>
## v1 — 止血（Envelope + 可追责串联）

**Scope**
- envelope 字段自动注入：schema_version/provenance/source/actor_kind/correlation_id/http
- 业务不阻塞：chronicle 写失败不影响主链路（关键事实事件另议补偿）

**Exit criteria**
- 新写入事件 payload 顶层具备 envelope（允许 correlation_id 在非 HTTP 场景缺失）
- 可以按 correlation_id 聚合同一次请求扇出的事件

**Links**
- docs/architecture/modules/chronicle-projection.md

---

<a id="v2"></a>
## v2 — 疗伤（Facts + Event Catalog）

**Scope**
- 关键 facts 覆盖：book/block/tag/todo/view/open 等
- Event Catalog：UI 文案/卡片 → facts 映射

**Exit criteria**
- 主路径用户动作都能被 facts 解释（不依赖单一“maturity_recomputed”解释事件）
- Event Catalog 中列出的核心卡片都有稳定 facts 支撑

**Links**
- docs/architecture/modules/chronicle-projection.md

---

<a id="phase-c"></a>
<a id="v3"></a>
## v3 — 产品化（Phase C：升列 + 索引 + 双写）

**Scope**
- envelope 升列：schema_version/provenance/source/actor_kind/correlation_id
- server_default（不加 NOT NULL；避免历史数据伪精确回填）
- 新写入双写：列优先，payload 兼容

**Exit criteria**
- 新写入数据：列字段基本齐全（允许 correlation_id 缺失的 worker 场景）
- 关键查询（按 book/time、按 correlation_id）走索引且排序稳定

**Links**
- docs/logs/others/others-047-source-of-truth-projection-chronicle-7.md

---

<a id="v4"></a>
## v4 — 防爆（高频事件治理 + TTL/归档）

**Scope**
- 高频低价值事件（visit logs / editor 过程事件）：去重/采样/合并/TTL
- 定期 prune job（访问类/噪声类）与可选冷归档

**Exit criteria**
- 在造流/压测下 chronicle_events 写入量可控（有明确的上限策略）
- visit logs 不再线性膨胀（TTL 或抽稀生效）
- 有观测口径：事件量、Top event_type、payload 体积分布、空值率趋势

**Links**
- docs/logs/others/others-047-source-of-truth-projection-chronicle-7.md

---

<a id="timeline-order"></a>
## Topic: Timeline 排序与分页稳定性

**Policy**
- DB 查询必须稳定排序：`ORDER BY occurred_at DESC, created_at DESC, id DESC`

**Why**
- occurred_at 精度/相同值会导致“看起来乱”与分页抖动；需要 tie-breaker。

---

<a id="payload-index-control"></a>
## Topic: payload/index control（观测与处置策略）

**Policy**
- payload 只放“解释事件所需的最小证据”，避免大字段（全文/巨大 before/after）。
- 索引是写入成本：高频事件表上只保留 Timeline 必需索引，避免对 payload 花式 key 建索引。

**Operational**
- 针对单 book 的统计：事件分布、payload keys 频率、payload 体积分位数。

---

<a id="runbook"></a>
## Topic: Projection runbook（Labs-005）

**Policy**
- runbook 必须能用现有脚本复现：API 写 → outbox → worker → entries。

---

<a id="adr"></a>
## Topic: ADR（决策沉淀）

**Rule**
- 凡是未来会问“当初为什么这么做”的内容，都要从 logs 提炼为 ADR（1 页）。

---

<a id="observability"></a>
## Topic: Observability（覆盖率/空值率/吞吐）

- 列字段空值率（按 source/actor_kind 分布）
- Top event_type（按 book/时间窗）
- payload bytes（p50/p95/max）

---

<a id="partitioning"></a>
## Topic: Partitioning（按需）

- 仅当 TTL/抽稀仍扛不住写入量，再考虑按月分区/按类型分区。

---

<a id="catalog"></a>
## Topic: Event Catalog

- UI timeline 默认聚焦 A 象限（低频高价值 facts）；visit/debug 作为可选开关。

---

<a id="backfill"></a>
## Topic: Backfill

- 只回填“可证明事实”，不做伪精确回填；迁移阶段优先 nullable + server_default。
