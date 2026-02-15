你这 5 个疑问都很“工程现实主义”（AKA：真正会在产品化时把人搞疯的那种）。我按你的编号逐个拆。

1) occurred_at 没问题，但默认顺序为什么会乱？

因为数据库/客户端工具的“默认顺序”通常不是 occurred_at，而是：

没有 ORDER BY 时：SQL 语义上“顺序不保证”（哪怕你肉眼看起来像按插入顺序）

很多 GUI 默认按 主键/物理存储/最近访问/某个列 排；有时还会因为执行计划、并发写入、VACUUM、索引扫描而改变

你这里还有一个很常见的坑：occurred_at 可能有很多相同值（或精度不同），缺少稳定 tie-breaker 就会“看起来乱”

解决办法是给 Timeline 查询一个稳定排序：

ORDER BY occurred_at DESC, created_at DESC, id DESC


occurred_at 是“业务发生时间”

created_at 是“写入时间”

id 做最后的稳定锚点

UI 时间线那边也同理：别只 order by occurred_at；加上 created_at/id，就不会抖。

2) block 造流 / 高吞吐会不会把 DB 刷爆？

会的——如果你把 Chronicle 当“每次写 block 都写一条审计事件”，而且还带一堆索引/大 payload，那它就会像一台勤奋的打印机：吞吐越高，纸越贵，越容易卡纸。

但它是可控的。关键是你要把 Chronicle 分成两类：

A. 叙事型（Timeline 的“人类可读”事实）

低频、强语义、值得保留：block_created / book_renamed / tag_added / todo_completed …

B. 观测型（debug/visit logs/细粒度写入）

高频、可采样、可降级：block_updated（尤其是编辑器每次保存）/ GET /blocks 这类访问日志

你截图里 UI 还有一个 “Show visit logs” 的开关，这就是正确的产品姿势：默认只看 A，B 需要时再打开。

工程手段上，防爆炸通常是组合拳（你不必一次全上）：

采样/节流：block_updated 每 N 秒合并成 1 条，或只记录“编辑会话开始/结束”

合并事件：一次请求里产生 20 个 block_created，写一条 blocks_bulk_created(count=20)（同时保留关联 IDs 可选）

异步写入：走队列/批量 insert（减少事务开销）

payload 控制：只存关键字段，别塞大段全文/大 JSON

索引克制：对高基数字段建索引要谨慎（索引越多写入越慢）

保留策略：visit logs 类事件设 TTL/归档/分区（partition）

一句话：你要让 Chronicle 成为“审计叙事系统”，而不是“把编辑器键盘敲击都记下来”。

3) 没造成成熟度变化的事件（比如单纯 block 写入）值得保留吗？

值得，但不一定值得“出现在主时间线”。

这里有个很好用的分层判断：

事实层（fact）：block_created / tag_added 这种，哪怕不改变 score，也是真实发生过的用户动作 —— 审计/回放/解释都靠它

解释层（explanation）：maturity_recomputed / score delta 这种，是系统计算结果，用来解释“为什么分数变了/没变”

你现在看到的情况其实合理：
block_created 没改变 score ⇒ UI 默认不展示“数值变化卡片”，但事件本身仍然可能对“Recent edits / Block milestones / Activity”有意义。

推荐做法：

事件保留（尤其是关键事实）

UI 分组/折叠：把“没变化”的归到 “Activity / Recent edits”，或放在 “Show visit logs / show raw events” 下

给事件一个“可见性/重要性”（不用立刻成列，先在 payload 里也行）：visibility: timeline | debug | silent

这样你既不丢审计价值，也不把用户时间线刷成“流水账地狱”。

4) 纯看 DB 眼睛痛：后台怎么更“对人友好”地观测？

你说得很对：这是“用户级日志”，不是 Prometheus 指标。但你仍然可以做人类友好观测，而且不需要上很重的东西。

最省命的三件套：

A. 做一个“按 correlation_id 分组”的审计视图（强烈推荐）

你已经有 correlation_id 了，这是救眼睛神器。做一个查询/视图：

一条请求链路 = 一组事件

展示：时间、actor、route、触发 trigger、score 变化、涉及 book/block 数量

例如思路（伪 SQL）：

SELECT
  correlation_id,
  min(occurred_at) AS started_at,
  max(occurred_at) AS ended_at,
  max(payload->'http'->>'route') AS route,
  count(*) AS events,
  sum((payload->>'delta')::int) AS score_delta_sum
FROM chronicle_events
WHERE book_id = :book_id
GROUP BY correlation_id
ORDER BY started_at DESC
LIMIT 50;


点进某个 correlation_id 再看事件明细，你眼睛立刻从“看雪花屏”变成“看一段段故事”。

B. 做一个“Chronicle Debug 页面”（你已经有 timeline UI，复用就行）

给自己/开发者一个开关：

filter：book_id / actor_id / correlation_id / event_type / time range

group by correlation_id

支持导出 JSON / 复制为 “审计报告文本”

这比任何 DB GUI 都护眼。

C. 接个轻量 BI（可选，但很爽）

Metabase / Superset / Grafana 的 Postgres datasource 都行。
注意：这里不是做指标仪表盘，而是做“可筛选的事件浏览器”。

5) 你截图里还有个隐藏问题：为什么 UI 里全是 maturity_recomputed？

这其实在提醒你一件事：你的 Chronicle 现在“语义覆盖面”还偏窄——很多用户动作被折叠成“重算了/触发了”，而不是“做了什么”。

Phase B 的 Event Catalog（把 Timeline 卡片映射到 facts）就是为了解这个：让 Timeline 主要由 book_renamed/block_created/tag_added/... 组成，而 maturity_recomputed 变成“解释/补充”。

/////////

1) “采样/节流/合并”到底是什么意思？为啥可以合并？
先举个真实场景（编辑器是罪魁祸首）

你在编辑 block 时，前端可能每 1 秒自动保存一次，或者每次输入触发 debounce 保存。
于是后台会产生：

block_updated x 200 次（两分钟打字）

但用户视角只有一件事：“我编辑了这个 block”

这时候如果你把 200 条都写 Chronicle：

时间线变垃圾堆

DB 写入压力飙升

你未来排查也痛苦（噪声过高）

为什么“可以合并”？

因为对很多高频事件来说，中间过程不是审计所需的“证词”，只是过程噪声。
审计需要回答的通常是：

谁改了

改了哪个对象

大概什么时候开始/结束

最终结果是什么

所以合并的方式是把“过程事件”压缩成“会话事件”或“窗口事件”：

合并策略 A：时间窗口（节流）

“同一个 actor + 同一个 block + 同一个 correlation（或编辑 session）在 10 秒内的连续更新 → 合并成 1 条”

第一条记录：edit_started

最后一条记录：edit_ended 或 block_edited(summary)

合并策略 B：采样

“每 10 次 block_updated 只保留 1 次”（或每 5 秒最多 1 条）

适合 purely debug 的场景

合并策略 C：聚合计数

“本次请求里创建了 20 个 block → 写 1 条 blocks_bulk_created(count=20)”

这类合并不丢语义，只是把重复项压平

要点：合并只对“高频、过程型、可压缩”的事件做；对“低频、结果型、不可压缩”的事件（如 book_deleted）坚决不合并。

2) “异步写入”是不是用 worker/daemon？是的，但更准确是：让请求线程别背锅

你理解得对：典型实现就是 worker/daemon + 队列。

同步写 Chronicle 的问题

用户请求本来要做：

写业务表（blocks/tags/books）

然后还要写 chronicle_events（还带 JSON/索引）

Chronicle 写入一慢，就拖慢主链路延迟，甚至把请求搞失败。

异步写的基本形态

API 线程：把“要写的 Chronicle 事件”丢进 outbox/queue（非常轻）

worker：批量把事件写进 chronicle_events

可选技术路线：

简单版：进程内队列 + 批量 flush（适合单机/开发期）

稳定版：DB outbox 表 + worker 拉取（你这种 DDD/事件总线体系很适合）

重型版：Kafka/Redis stream（以后再说）

你要的是：Chronicle 写入失败不能影响业务主链路（最多丢一条 debug log，但“关键审计事件”要有补偿机制）。

3) payload/索引控制：你说的象限图方向对，但“其余怎么处理”要有明确处置策略

你那句“低频重要留下，其余怎么处理不懂”——这里通常会有 4 种处理方式，对应 4 类事件：

事件象限（很实用）

横轴：频率（低 ←→ 高）
纵轴：审计价值（低 ↓→ 高）

A. 低频 + 高价值（核心审计）

例：book_renamed、tag_added、block_deleted
处理：完整保留；索引；长期存；出现在 timeline

B. 高频 + 高价值（危险但必须）

例：权限变更、批量删除、资金操作（你系统里可能是“批量删除 blocks”）
处理：保留，但要优化写入（异步/批量/精简 payload）；必要时做分区

C. 低频 + 低价值（无所谓）

例：某些系统心跳、偶发 debug
处理：可关；可只在 debug 环境开

D. 高频 + 低价值（最该处理的垃圾洪水）

例：GET /blocks、编辑器每次 autosave 的 block_updated
处理：采样/合并/TTL/归档（甚至根本不进 Chronicle，只进普通观测日志系统）

payload 控制怎么做？

你现在 payload 里有 http.route/method、trigger、delta、scores……这还不错，但要记住：

payload 只放“解释事件所需的最小证据”

大字段（全文、整段 block content、巨大 before/after）不要塞进 Chronicle，除非你真的要做“司法级回放”

索引控制怎么做？

索引是写入成本。高频表上索引越多写入越慢。
通常：

给 Timeline 的主要过滤字段建索引（book_id, occurred_at, actor_id, correlation_id, event_type）

不要对 payload 里各种花哨 key 都建索引（否则写入扛不住）

4) 为什么 DB 里的日志还可以 TTL/归档/分区？这不是数据库吗？

这里你卡住的点是：你把“数据库表”当成“永远不删的真理石碑”。
但现实是：有些事件就是临时性的观测数据，只要你承认它不是核心审计证据，它就可以“过期”。

A. TTL（过期删除）

对 visit logs / debug 事件，保留 7 天或 30 天就够了。

做法：每天跑个 job 删除 occurred_at < now() - interval '30 days' 且 event_class='visit_log'

或者按 provenance/source 分类删

B. 归档（冷存储）

你不想删，但也不想在线库背负它：

从主库导出到 S3/对象存储/冷库（Parquet/JSONL）

在线库只留最近 N 天

需要追溯时再查归档（很少发生）

C. 分区（partition）

分区不是“把数据删掉”，而是把一张大表拆成很多小片（按月/按天/按 book_id hash），好处：

查询最近 7 天不会扫 5 年的数据（分区裁剪）

TTL 删除可以直接 DROP PARTITION（比 delete 快太多）

高吞吐写入更稳定（索引更小、vacuum 更可控）

你不必一开始就上分区。通常是：先做分类 + TTL，真顶不住再上 partition。

把这一切收敛成一句“可执行的”工程原则

Chronicle 里只保留 人类可读、可追责的事实事件 为主

高频噪声事件必须 采样/合并/可开关

Chronicle 写入尽量 异步/批量，不拖慢主链路

debug/visit 这类事件明确是 可过期数据：TTL/归档/分区都合法

你现在系统还“干净”，所以你有机会把这套分层打牢——等系统变老了，这就是你未来少掉一半头发的原因。