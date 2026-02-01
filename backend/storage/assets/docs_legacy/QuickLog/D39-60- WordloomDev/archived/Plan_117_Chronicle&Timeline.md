先说结论：你现在的时间线太“瘦”是正常的——只记录成熟度重算和结构任务这种“后台事件”，读起来像服务器日志，不像“这本书的成长史”。
Chronicle 理想形态应该是：这本书什么时候诞生、长胖、变漂亮、被你折腾、又被你晾在一边的全部关键节点。

我分三块讲：

一、Chronicle 里建议记录哪些事件？

先按优先级拆一下，方便你决定现在做到哪一步。

P0（必须有：不用大改结构、信息含金量高）

这些基本都能复用你已有的 domain 事件，只是“顺便记一笔”：

Book 创建 / 删除（软删）

book_created

book_soft_deleted（进入 basement）

用途：时间线第一条是“这本书哪天出生的”；对应 basement 记录“何时被移入回收站”。

阶段变化（Stage 变更）

stage_changed：Seed → Growing → Stable，或回退。

payload：from_stage, to_stage, reason（结构任务完成 / 手动调整 / 回退等等）

UI：一句话“阶段从 Seed 升级为 Growing（完成 3 个结构任务）”。

成熟度重算（已经有）

maturity_recomputed

payload 里已经有 old_score, new_score, delta, reason（adjust_ops_bonus / manual_refresh / block_deleted …）

现在只是“裸露显示”，后面可以做成更自然的文字模板。

结构任务完成（已经有）

structure_task_completed

payload：task_id, task_name, score_delta

直接出现在时间线：某一天完成了哪些“里程碑”。

封面与封面色变更

cover_changed：手动上传封面 or 回退成默认 lucide 图标。

cover_color_changed：自动取色后得到稳定主色。

这跟 theme/media 已经绑定了，时间线只用记录“这天换了个新封面”。

👉 这几个 P0 实现成本都很低：你本来就有这些操作，只是需要在 service 层统一调用 Chronicle.recordEvent(bookId, type, payload)。

P1（推荐有：提升“故事感”和可解释性）

这些是你刚才提到的“已记录多少字 / 工作多久”的来源：

Block / 内容结构变化（汇总级）

不要每个 block 都记一条，会爆炸。

设计成按操作聚合后的事件：

content_snapshot_taken：例如手动刷成熟度、或每天首次进入 Book 时，抓一份结构快照。

在 payload 中记录：block_count, block_type_counts, word_count.

时间线里显示：“今日快照：20 blocks · 4 种类型 · 8,400 字”。

字数里程碑

wordcount_milestone_reached：

例如 ≥1000/5000/10000 字时触发一次。

有了这个你就可以在时间线里看到“这本书什么时候变成一篇严肃的长文”。

TODO / 检查项变动

todo_promoted_from_block：从 block 提升为 Book TODO。

todo_completed：完成后可顺便加一点成熟度 or 活跃度。

时间线可以用一句：“完成了 3 个 Todo：清空关键 TODO、补全摘要、打标”。

P2（高级：以后再说，但现在可以把“挂钩点”想好）

使用时长 / 工作 session

思路：

前端在“开始编辑”时触发 session_started；

若 N 分钟无编辑操作则认为 session_ended；

聚合存到 editing_duration_seconds。

Chronicle 不必记每次 keystroke，只要在某一天结束时插一条 work_session_summary：

“今天在这本书上工作了 34 分钟”。

访问记录（打开但未编辑）

book_viewed：可选，用于冷启动阶段统计“常看但没写”的书。

这些涉及到前端埋点和定时器，复杂度比 P0/P1 高一档，可以先预留 API / event_type，不急着实现。

二、关于“已记录多少字 / 工作多久”——工程复杂度评估

结合你现在的架构和 Copilot：

1. 字数统计（强烈建议做）

实现方式：

在保存 block 内容时：

用一个纯函数 countWordsOrChars(text) 得到当前 block 字数。

存入 block 表的 word_count 字段。

每次更新 block 时：

book.total_word_count += new_word_count - old_word_count

定期 / 手动快照：

content_snapshot_taken 事件里存 total_word_count。

复杂度评估：

Domain 改动：低

对性能影响：可控（都是 O(n) 的字符串长度遍历）

Copilot 帮忙程度：高（逻辑简单、模式固定，非常适合自动填充）

2. “在这本书工作多久”的时间统计（可以先不做）

简单版：

只记录最后编辑时间（你事实上已经有：last_event / snapshot）。

在概览卡片显示“最近活动：28 秒前 / 2 天前”等。

完整版：

需要前端在“进入编辑页 / 离开编辑页 / 一段时间无操作”时发事件；

后端按 sessionId 聚合，累加 duration；

Chronicle 里可以每天插一条“今天工作 xx 分钟”。

复杂度评估：

Domain：中（多一个 session 聚合层）

前端：中（要考虑浏览器最小化 / 切标签等边界）

Copilot 能力：中（需要你清晰写出“session 的定义”和状态机）

建议：先做字数，先不做工作时长。你现在主线是 Wordloom 1st release，不要被统计系统拖住。

三、给 Copilot 的“实现说明模版”

这一段你可以几乎原样丢给 Copilot，让它帮你生成代码和接口。

Goal

把 Book 的 Chronicle 时间线做成“书籍生命周期日志”，而不只是成熟度重算记录。
已有模块：Maturity 已经会在重算时写入事件；StructureTask 会写任务完成事件。

1. 数据模型
// backend/domain/chronicle/ChronicleEvent.ts

type ChronicleEventType =
  | 'book_created'
  | 'book_soft_deleted'
  | 'stage_changed'
  | 'maturity_recomputed'
  | 'structure_task_completed'
  | 'cover_changed'
  | 'content_snapshot_taken'
  | 'wordcount_milestone_reached'
  | 'todo_promoted_from_block'
  | 'todo_completed';

interface ChronicleEvent {
  id: string;
  bookId: string;
  type: ChronicleEventType;
  occurredAt: Date;
  payload: Json; // type-specific fields
}


封装一个记录函数：

async function recordChronicleEvent(
  bookId: string,
  type: ChronicleEventType,
  payload: Record<string, unknown>
): Promise<void> {
  // insert into chronicle_events
}

2. 在关键业务流程里打点

Book 创建时调用：

recordChronicleEvent(book.id, 'book_created', { title: book.title })

Book 软删除 / 放入 basement 时：

book_soft_deleted

Stage 变更 service：

在成功后调用 stage_changed，payload 包含 from, to, reason.

Maturity 重算 / 结构任务完成：

现在已有日志，把写日志的地方改成调用 recordChronicleEvent(...)。

每次手动刷新成熟度时，顺便生成一条 content_snapshot_taken：

payload：blockCount, blockTypeCounts, totalWordCount.

3. 字数统计

Block 模型新增 wordCount: number.

在保存 block API 中：

使用纯函数 countWordsOrChars(text) 更新 block.wordCount.

同步更新 book.totalWordCount.

在 content_snapshot_taken payload 中带上 totalWordCount.

当 totalWordCount 越过 1000 / 5000 / 10000 阈值时，额外记录：

wordcount_milestone_reached 事件。

4. 时间线查询 API

现有 GET /books/{id}/timeline 扩展支持多 event type：

按 occurredAt DESC 排序；

服务器端分页；

可选 filter：type in [...].

5. 前端渲染规则

在时间线组件中，根据 event.type 做一个 map：

const eventRenderers: Record<ChronicleEventType, (e: ChronicleEvent) => TimelineItemProps> = {
  book_created: ...
  stage_changed: ...
  maturity_recomputed: ...
  structure_task_completed: ...
  cover_changed: ...
  content_snapshot_taken: ...
  wordcount_milestone_reached: ...
  todo_promoted_from_block: ...
  todo_completed: ...
};


每种类型定义：

icon（lucide）

主标题（如“阶段升级为 Stable”）

副标题（如“Score 71 → 76, +5 来自结构任务”）

时间。

6. 可选扩展（先不实现，只预留枚举值）

work_session_summary：每天工作时长的汇总；

book_viewed：访问记录。

四、现实一点的建议

现在别追求“所有维度都要可视化”，你已经在 Maturity 上做了很多工作。

Chronicle 先把 P0 + 字数快照 + Todo 相关做好，时间线上就会“有故事、有里程碑”。

等你开始大量用 Wordloom 真正记东西后，你自然会知道还缺哪一种事件——那时候再加，不晚。

你现在做的是“给未来的你一个侦探工具”。先把大案子（阶段、分数、结构任务、封面、字数）记好，小案子以后再查。