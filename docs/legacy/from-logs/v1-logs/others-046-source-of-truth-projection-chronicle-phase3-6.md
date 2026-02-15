Phase C（产品化）：要做什么、按什么顺序做
Phase C 的目标是：把 Phase A/B 已验证有价值的“信封字段”从 payload 提升为表列 + 索引，让查询/排障/分页稳定、快、可控；同时保留 payload 作为语义扩展区。

下面是建议的落地清单（按执行顺序）：

1) 设计：确定要提升的列（最小集合）
推荐先提升这些（与你现在的 envelope 对齐）：

schema_version（int）
provenance（text：live|backfill）
source（text：api|worker|cron|migration|unknown）
actor_kind（text：user|system|unknown）
correlation_id（text/uuid）
说明：actor_id 如果你表里已经有列就不动；如果还没有，也建议一并提升（但你 Phase A 里强调“默认从认证上下文自动填”，通常意味着表里本来就有 actor 相关字段）。

2) DB Migration：加列（nullable）+ 默认值策略
第一步不要上来就 NOT NULL，先可空，避免老数据/历史回填挡住迁移。

-- 仅示例：表名/类型按你的实际 DB 调整
ALTER TABLE chronicle_events
  ADD COLUMN correlation_id TEXT NULL,
  ADD COLUMN source TEXT NULL,
  ADD COLUMN actor_kind TEXT NULL,
  ADD COLUMN provenance TEXT NULL,
  ADD COLUMN schema_version INT NULL;

然后做一个“温和 backfill”（从 payload 顶层搬运）：

UPDATE chronicle_events
SET
  correlation_id = COALESCE(correlation_id, payload->>'correlation_id'),
  source         = COALESCE(source,         payload->>'source'),
  actor_kind     = COALESCE(actor_kind,     payload->>'actor_kind'),
  provenance     = COALESCE(provenance,     payload->>'provenance'),
  schema_version = COALESCE(schema_version, (payload->>'schema_version')::int)
WHERE
  correlation_id IS NULL
  OR source IS NULL
  OR actor_kind IS NULL
  OR provenance IS NULL
  OR schema_version IS NULL;

有些库 payload 不是 JSONB 或字段名不同，需要你按实际改。

3) 索引：让最常用的查询路径“稳且快”
优先建你确定会用的索引（别贪多）：

按请求链路聚合排障：correlation_id
按实体时间线：通常是 (book_id, created_at desc)（如果表里有 book_id 与 created_at）
按 actor 审计：(actor_id, created_at desc)（如果 actor_id 在列上）

CREATE INDEX IF NOT EXISTS idx_chronicle_events_correlation_id
  ON chronicle_events (correlation_id);

-- 视你表结构：book_id/created_at 若存在才建
CREATE INDEX IF NOT EXISTS idx_chronicle_events_book_id_created_at
  ON chronicle_events (book_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chronicle_events_actor_id_created_at
  ON chronicle_events (actor_id, created_at DESC);

4) 应用层改造：Recorder “双写”列 + payload（短期兼容）
把你现在“自动注入 payload 顶层”的逻辑保留，但同时把值写到新列：

写入时：列字段从同一个上下文计算（不要从 payload 反读）
读取/查询时：优先用列（更快更稳）；payload 仅做补充展示
这一步一般是：

ChronicleRecorderService.record_event(...)：新增参数/内部赋值到 ORM model columns
查询 API / projection worker：聚合/过滤改用列（如按 correlation_id、source）

5) 收口：加约束（可选，但建议最终做）
当你确认：

新写入 100% 已双写列
老数据 backfill 完成到可接受比例
再逐步加约束/默认值（分两次，避免锁表风险）：

SET DEFAULT
SET NOT NULL（谨慎：体量大就要分批/在线迁移策略）
6) 观测与回滚策略（必须有）
观测：新列空值比例（例如 correlation_id/source）
回滚：应用仍能从 payload 读（短期保留兼容），DB 迁移可不回滚只前滚
我需要你确认 3 个信息，才能给你“精确到文件/迁移脚本”的 Phase C patch
你的 DB 是 Postgres / MySQL / SQLite 哪个？chronicle_events.payload 是 JSONB/JSON/TEXT 哪种？
chronicle_events 当前有哪些列（至少：id/event_type/created_at/actor_id/book_id/block_id 是否存在）？
你们 migrations 用什么（Alembic / Prisma / Drizzle / Knex / 纯 SQL）？
把 chronicle_events 的建表/ORM 定义贴一下，我就能把 Phase C 拆成 2～3 个安全迁移（含索引、backfill、双写代码改动）给你。

1) 历史数据会直接让 migration 失败（或让你被迫做不可信的回填）

你现在已经遇到 actor_id 空、request 链缺失这种情况。
如果你对 actor_kind/source/schema_version/correlation_id 之类加 NOT NULL：

表里只要存在一行 NULL，ALTER TABLE ... SET NOT NULL 就会失败（除非你先全量回填）。

为了过 migration，你可能会被迫“瞎填默认值”，结果审计系统最怕的“伪精确”就来了（比如把未知都填成 system）。

所以常见策略是：先加列 + server_default（让新写入不再产生 NULL），跑一段时间确认没有漏网之鱼，再对“确实应该永远有”的字段加 NOT NULL。

2) 你还没证明“所有写入路径都覆盖到了”，NOT NULL 会把边缘路径炸出来

Chronicle 这种东西最阴的点是：写事件的不止一条路：

API request（有 request_context）

worker/cron（可能没有 request_id）

backfill/migration 脚本（可能直接 insert）

未来的补偿任务 / 重放 rebuild

单测里构造的 event（常常偷懒漏字段）

你以为补齐了，但只要漏掉一个角落，NOT NULL 就会在生产上把那条路径的写入变成 500 或任务失败。
这是好事（暴露问题），但时机不对就是事故：你可能只是想上线一个“可索引 correlation_id”，结果后台队列全挂。

所以要先“观测一段时间”：看新数据里 NULL 是否已经趋近于 0，再收紧。

3) 有些字段在语义上就是“允许为空”的（强行 NOT NULL 会逼你造假）

比如：

correlation_id：HTTP 请求链路通常有，但系统任务/纯异步也可能没有（除非你强制每个 job 也生成 correlation）

request_id：worker 根本没 request

actor_id：系统/未知/历史缺失都可能没有（除非你用 SYSTEM/UNKNOWN 统一填充，但那也需要你先定清楚规则）

provenance：你可能早期没写，后面才引入

如果这些字段你还没定下“缺失时怎么表示”（unknown vs system vs null），直接 NOT NULL 会把你逼进“乱填 default”——然后审计就开始说谎。

一句话总结你截图里那句建议的真实含义

先“让新数据不再产生 NULL”（server_default + 代码写入统一），并跑一段时间确认写入路径稳定；
再对“语义上必须存在、且已验证不会缺”的字段加 NOT NULL。
NOT NULL 最好作为最后一道闸门，而不是第一道。

这就像你做自动化测试：先让系统能观测、能报警、能定位，再上“强约束”。直接强约束，相当于你在还没画清楚电路图时就把保险丝换成超敏——啪，整栋楼黑了。

如果你后面要继续做 Phase C 的“缺口清单”，我会把字段分三档（永远必填 / 通常必填但允许例外 / 应该允许为空），然后按档位决定何时 NOT NULL、何时只做 default + 索引。这样收口会非常顺滑。