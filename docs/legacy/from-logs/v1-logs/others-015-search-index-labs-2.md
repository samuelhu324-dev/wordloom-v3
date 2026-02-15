可以，咱们把它做成一个**“不改业务语义，只改投影方式”**的小闭环：把你现在这份 同步写 DB 的 search_index handlers（直接 await db.execute(stmt)）改成 写 Outbox → worker 再投影到“Elastic(模拟)”。

你现在这份 handler 文件就是“世界 A：同步投影到 DB 表”的实现。

search_index_handlers


下一步我们做“世界 B：Outbox + worker（Elastic 模拟）”。

目标：你最后会得到什么（验收点）

业务写入（block/tag create/update/delete）仍然发同样的域事件（不改 domain/usecase）

handler 不再更新 search_index 表，而是只写 outbox_events（同一 DB 事务里）

一个 outbox_worker（可手动跑、可测试）读取 outbox，把事件投影到：

Elastic 模拟版（最简单：用一张 elastic_index_mock 表 / 或内存 dict）

worker 具备你已经做过的三件事：

幂等（event_id / unique）

防倒退（event_version / occurred_at）

可重试（失败不丢，下一次还能继续）

Step 0：先把“边界”画对（你会少走很多弯路）

现在的 search_index_handlers.py 做的是：消费域事件 → 写入 search_index 表。

search_index_handlers

改造后它应该做的是：

消费域事件 → 写入 outbox_events（记录“我要更新索引”这件事）
真正“更新索引”交给 worker（异步/可重试/最终一致）。

Step 1：新增 Outbox 表（DB 内）

建一张最小 outbox 表（字段别贪多，能闭环就行）：

id（UUID / event_id，唯一，幂等关键）

topic（例如 "search_index"）

event_type（BlockUpdated / TagRenamed…）

payload（JSON：entity_type/entity_id/text/snippet/event_version/occurred_at…）

status（pending/processing/done/failed）

available_at（用于延迟重试 backoff，可选）

created_at

要点：它和业务数据在同一个数据库事务提交。这样“业务成功但消息丢了”的概率被打到很低。

Step 2：把现有 handler 改成“只写 outbox”

以 on_tag_renamed 为例，你现在在 handler 里直接 upsert SearchIndexModel，并用：

where=SearchIndexModel.event_version <= excluded.event_version


来做防倒退。

search_index_handlers

改造后 handler 不再碰 SearchIndexModel，而是写一条 outbox：

payload 里包含你投影需要的最小信息：

{
  "entity_type": "tag",
  "entity_id": "...",
  "text": "new_name",
  "snippet": "new_name",
  "event_version": 1700000000123456,
  "occurred_at": "..."
}


防倒退逻辑不要丢：只是从“DB upsert where”挪到“worker 写 Elastic 时判断”。

Step 3：做一个 Elastic “模拟版”投影目标（你先别上真 ES）

你说“无改业务逻辑地换成 Elastic + worker 模拟版”，最稳的是：

方案 A（最快落地，便于 SQL/测试）：用一张表模拟 ES

建表 elastic_index_mock：

(entity_type, entity_id) unique

text

snippet

event_version

updated_at

worker 对它做 upsert，并带 anti-regression 条件（同你现在 search_index 的思路一致）：

ON CONFLICT DO UPDATE ... WHERE elastic.event_version <= excluded.event_version

这一步你已经在 search_index 上练过了，迁移成本接近 0。

方案 B（更“像 ES”，但不利于复现）：用内存 dict

适合写单测，但不利于你用 psql 看数据、跑 explain。

我建议先 A，闭环最快。

Step 4：写 outbox worker（核心）

worker 做三件事：

拉取 pending 的 outbox（可按 batch）

对每条消息投影到 elastic_mock（或未来 Elastic）

标记 outbox 为 done；失败则记录错误并保留 pending/failed 以便重试

幂等怎么做？

outbox 的 event_id 唯一：同一条消息重复跑，插入会冲突 → 你可以直接 skip 或更新状态

或者建一张 processed_events(event_id)：消费前先查/插入（同事务）

防倒退怎么做？

你已经有 event_version = occurred_at 微秒（你 _event_version() 就是干这个的）。

search_index_handlers


worker 写 elastic_mock 时加条件：旧的 version 不允许覆盖新的。

重试怎么做？

失败就别删 outbox：

status=failed

available_at = now + backoff
下次 worker 再拉 available_at <= now 的继续。

Step 5：你怎么验证“真的像生产”

你现在已经会用 pytest + 实验脚本了，所以验收我给你三个很硬的测试（你跑过就真的懂了）：

业务提交成功 → outbox 有记录 → worker 跑完 → elastic_mock 有记录

worker 故意失败一次 → outbox 还在 → 第二次重跑成功（可恢复/可重试）

乱序事件（先 v2 再 v1）→ elastic_mock 最终仍是 v2（防倒退）

这三个就是“生产搜索投影系统”的骨架。

Step 6：把“搜索”切到 elastic_mock（可选，但很爽）

你现在查询走 search_index 表。下一步只要把查询 repo 换成：

FROM elastic_index_mock WHERE ...

你就完成了“读模型替换”：业务照常写，搜索读从 search_index 换到 elastic_mock。

未来你上真 Elastic 时，等价于再换一个 adapter。

你现在立刻能动手的最小改造顺序（不炸 repo 版）

加 outbox_events 表 + alembic

handler 改：await db.execute(insert outbox)（不碰 SearchIndexModel）

加 elastic_index_mock 表

写 worker：pending → upsert elastic_mock（带 event_version 防倒退）→ done

写 3 个 pytest（上面那三条）