2) 你该怎么处理 failed：三件套（看 / 修 / 重放）
A. 看：给 failed 一个“可查询列表”

至少要能按这些维度查：

projection（search/chronicle/…）

error_reason / error_class（429 / 5xx / mapping_error / payload_invalid …）

attempts、last_error、processed_at、created_at

（可选）library_id 或 scope key（方便定位影响面）

这一步你已经有 SQL 能查了，只是建议做成一个简单运维入口：哪怕是 CLI 命令都行。

B. 修：确定性错误要先“修因”，否则重放没意义

举例：

mapping_error / parse_error：修 ES mapping 或修你的文档结构/字段类型，然后才重放

payload_invalid：修 SoT 里的脏数据（或修事件生成逻辑），必要时补一个“数据迁移/修复脚本”

业务逻辑 bug：修代码，发版本

这类错误的关键是：不要让它继续占 worker 的处理能力（所以才要 failed）。

C. 重放：给一个安全的“replay”按钮（把 failed 变回 pending）

你有两种主流做法：

做法 1：原表重放（最省事）

对某一批 failed，执行类似：

status: failed → pending

attempts: 视情况清零或保留（我一般建议保留，但允许手动清零）

next_retry_at: now()

清掉 owner / lease_until / processing_started_at

error 保留在 last_error 或 error_history（至少别丢）

然后 worker 会重新 claim。

✅ 优点：实现快
⚠️ 风险：如果没修因，会反复 failed；所以要配合“分类 + 人工确认”

做法 2：DLQ（dead letter queue）/ dead_letter_outbox（更生产）

当事件判定失败，把记录搬到 dead_letter 表（保留 payload + 错误 + attempts + 发生时间）：

主 outbox 更干净

DLQ 专门做运维：查询、标注、重放、归档

✅ 优点：运维体验好，主队列不被污染
⚠️ 成本：多一张表 + 搬运逻辑 + 重放逻辑

你现在阶段：先做“原表重放”完全够用。等第二个 projection 上线（比如 chronicle）再做 DLQ，收益立刻翻倍。

3) “人工干涉”具体怎么长得像个系统？

你可以给自己定一个最低可用的运维闭环（MVP）：

错误分类器（你已经做 v2 的核心了）：把失败分成 retry / failed + reason

failed 列表（SQL/脚本即可）：按 reason 聚合计数 + 列表

replay 命令：

replay by ids

replay by reason + 时间窗口

replay by projection

安全阀：replay 前检查“修因是否完成”（至少是你人脑确认：mapping 修了没？版本发了没？）

做到这四点，你的 daemon 就从“能跑”升级成“能运维”。

4) 哪些 failed 可以“自动处理”，哪些必须人看一眼？

一个实用规则（不装神弄鬼）：

必须人看：400 mapping/parse、payload 校验失败、你自定义的 business error

可以半自动：5xx/timeout（如果 ES 恢复了，可以批量 replay），429（如果你确认只是过载，限流后可以 replay）

甚至你可以做一个“自动化策略”：

failed_reason 是 transient（5xx/timeout）并且“系统已恢复”→ 允许自动把 failed 转 pending（但要限速）

deterministic 的 failed 永远不自动 replay（除非人工点）

5) 你问得很关键：重放会不会造成重复写 ES？

这就是你一直在做的那个词：幂等（idempotent）。

你现在的 search 投影如果用 deterministic id（比如 event_id / doc_id 固定），那么：

同一事件重复 upsert → 最终结果一致

这让 “replay” 变得安全

这也是为什么生产系统敢给你“重放按钮”。

结论（你可以直接写进 runbook）

failed 是“自动化停机点”，不代表永远失败

处理 failed 的正确姿势：分类 → 修因 → replay

你现在最合适的落地：先做“原表重放 + 运维脚本/接口”，等第二个投影再上 DLQ

下面是你接下来会自然扩展出来的方向：把 failed 做成可搜索、可重放、可审计的运维入口，这就是真正的 “daemon 化”。

（继续往前你会发现：系统不是写出来的，是“跑得久、修得快、改得稳”长出来的。）