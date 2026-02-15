好，先把范围收紧：现在只管 Maturity 模块 + Chronicle/Timeline 模块，完全不碰 theme、配色这些东西。

你可以把下面这份当成“交给 Copilot 的设计说明书 v1”。我会尽量用「数据结构 + 事件类型 + 分数规则 + UI 行为」四块来讲清楚。

一、Domain 分工再确认

Maturity（成熟度）

负责：分数 score、阶段 stage、各类计数（blocks、events、visits90d…）、成熟度快照。

输出的是一个结构化的 BookMaturitySnapshot。

Chronicle / Timeline（事件时间线）

负责：记录“发生过什么事”，即 BookEvent 列表。

每个事件可以附带它对分数的影响（加分 / 扣分），但分数计算的真相只由 maturity 决定。

UI 上：

概览页最上面：Maturity 指标条（你现在那一排卡片：STAGE / SCORE / SNAPSHOT / BLOCKS / EVENTS…）

下方两个卡片：

最近事件：Chronicle 的缩略版（最近 5 条关键事件）。

结构任务：由 Maturity 规则推导出来的 checklist，“下一步该做什么”。

二、核心数据结构（后端可以照着建）
1. BookMaturitySnapshot
type MaturityStage = 'seed' | 'growing' | 'stable' | 'legacy';

interface BookMaturitySnapshot {
  bookId: string;

  score: number;          // 0–100
  stage: MaturityStage;   // 根据 score 算出来

  blocksCount: number;
  todosCount: number;     // 来自 todo 列表 block
  visits90d: number;
  lastVisitAt: Date | null;
  lastEventAt: Date | null;

  summaryLength: number;  // 摘要字数
  tagsCount: number;

  // 方便以后扩展的 flags（例如：是否有封面图、是否有 pinned TODO…）
  hasSummary: boolean;
  hasTitle: boolean;
  hasCoverIcon: boolean;

  snapshotAt: Date;       // 本次快照时间
}

2. BookEvent
type BookEventKind =
  | 'created'
  | 'title_updated'
  | 'summary_added'
  | 'summary_removed'
  | 'tag_added'
  | 'tag_removed'
  | 'block_added'
  | 'block_removed'
  | 'todo_promoted'
  | 'todo_completed'
  | 'visit'
  | 'maturity_recomputed'
  | 'maturity_stage_changed'
  | 'structure_task_completed'
  | 'structure_task_regressed';

interface BookEvent {
  id: string;
  bookId: string;
  kind: BookEventKind;
  occurredAt: Date;
  // 用 JSON 存 payload，前端可以按需解析
  payload: any;
}


Chronicle full timeline 就是某个 book 的 BookEvent[]。

“最近事件”卡只取其中一小部分。

三、分数与阶段规则（Maturity）
1. 阶段分界（示例）

你可以先用一套简单的：

0–29：Seed

30–59：Growing

60–89：Stable

90–100：Legacy

Go / TS 里就是：

function resolveStage(score: number): MaturityStage {
  if (score >= 90) return 'legacy';
  if (score >= 60) return 'stable';
  if (score >= 30) return 'growing';
  return 'seed';
}

2. 基础得分规则（只看结构，不看内容质量）

一套“结构分”示例（具体数字你可以慢慢调）：

标题：

有标题：+10

摘要：

有摘要（>= 40 字）：+15

Block：

blocksCount >= 3：+10

blocksCount >= 10：再 +10

TODO：

todosCount >= 1：+5

todosCount >= 5：再 +5

标签：

tagsCount >= 1：+5

访问：

visits90d >= 3：+5

visits90d >= 10：再 +5

Maturity 模块提供一个纯函数：

function calculateMaturity(snapshotInput: {
  blocksCount: number;
  todosCount: number;
  visits90d: number;
  summaryLength: number;
  tagsCount: number;
  hasTitle: boolean;
}): { score: number; stage: MaturityStage; contributions: Contribution[] }


contributions 是一个数组，记录每个规则贡献了几分，方便以后在 UI 上解释：

interface Contribution {
  key: string;       // e.g. 'title', 'summary', 'blocks_3_plus'
  points: number;
}


这样未来“结构任务完成 / 回退”只需要看这些 contribution。

四、「最近事件」设计
1. 哪些算“最近事件”

不是所有事件都要挤在“最近事件”里，否则很吵。可以筛选：

强事件（一定要露出）：

created

summary_added / summary_removed

maturity_stage_changed

structure_task_completed / structure_task_regressed

弱事件（只在 full timeline 里看）：

block_added / block_removed

tag_added / tag_removed

todo_promoted / todo_completed

visit

maturity_recomputed

前端接口示例：

GET /api/books/{id}/recent-events
// 服务端：从事件表里取最近 N 条“强事件”，按时间倒序。


展示形式：

标题：最近事件 Chronicle

每一条：时间 + 图标 + 短文案，例如：

2025-11-27 15:03 · ⭐ 成熟度升级为 Growing

2025-11-27 14:50 · 📝 新增摘要

2025-11-26 20:11 · ✅ 完成结构任务「添加首个 Todo 列表」

卡片右上角一个「查看全部」按钮 → 跳到 Timeline Tab。

五、「结构任务」设计（Next Steps）

核心思路：把 Maturity 规则拆成 checklist，用户一看就知道“下一步干啥才能升级”。

1. 任务模型
type StructureTaskId =
  | 'add_title'
  | 'add_summary'
  | 'create_3_blocks'
  | 'create_10_blocks'
  | 'create_first_todo_list'
  | 'add_tag'
  | 'reach_visits_3'
  | 'reach_visits_10';

interface StructureTask {
  id: StructureTaskId;
  title: string;          // 展示文案
  description?: string;   // 可选说明
  requiredStage: MaturityStage;   // 最低阶段要求（用于解锁进阶任务）
  points: number;         // 完成后可贡献的分数（与 Contribution key 对应）
}


后端有一份静态配置表（或 pure function 返回数组）：

const ALL_TASKS: StructureTask[] = [
  { id: 'add_title', title: '填写书名', requiredStage: 'seed', points: 10 },
  { id: 'add_summary', title: '写一段不少于 40 字的摘要', requiredStage: 'seed', points: 15 },
  { id: 'create_3_blocks', title: '新增至少 3 个块', requiredStage: 'seed', points: 10 },
  { id: 'create_first_todo_list', title: '创建第一个 Todo 列表', requiredStage: 'seed', points: 5 },
  { id: 'add_tag', title: '添加至少 1 个标签', requiredStage: 'seed', points: 5 },
  { id: 'create_10_blocks', title: '累计 10 个以上块', requiredStage: 'growing', points: 10 },
  { id: 'reach_visits_3', title: '最近 90 天访问不少于 3 次', requiredStage: 'growing', points: 5 },
  { id: 'reach_visits_10', title: '最近 90 天访问不少于 10 次', requiredStage: 'stable', points: 5 },
];

2. 任务状态计算

Maturity 模块提供一个函数：

interface StructureTaskState {
  task: StructureTask;
  status: 'locked' | 'pending' | 'completed' | 'regressed';
}

function resolveStructureTasks(
  snapshot: BookMaturitySnapshot
): StructureTaskState[] {
  // 1) 根据 snapshot.stage 过滤出已解锁任务（requiredStage <= stage）
  // 2) 根据 snapshot 的字段决定每个任务的 status:
  //    - 比如 snapshot.hasTitle => 'completed'
  //    - 没标题 => 'pending'
  // 3) 如果之前是 completed，现在条件消失（例如摘要被清空），状态变成 'regressed'
}


每次刷新 snapshot 时，都会重新算一遍 task 状态。

当 pending -> completed 发生变化时，后端写入一个事件：

BookEvent {
  kind: 'structure_task_completed',
  payload: { taskId: 'add_summary', points: 15 }
}


当 completed -> regressed 时，写入：

BookEvent {
  kind: 'structure_task_regressed',
  payload: { taskId: 'add_summary', points: -15 }
}


这就把「加分 / 回退」的信息清晰记在 Chronicle 里了。

3. 「结构任务」卡片 UI

卡片标题：结构任务

副标题：基于成熟度计分

内容：显示当前阶段下，最多 3 个未完成的任务，格式类似：

 填写书名（+10 分）

 写一段不少于 40 字的摘要（+15 分）

 新增至少 3 个块（+10 分）

已完成的任务可以折叠到“已完成 · 3 项”里，不占主画面空间。

当 snapshot.stage 升级，任务列表自动改变（requiredStage 更高的任务解锁）。

4. 「刷新成熟度」按钮放哪儿、怎么触发？

“达到必要分数后才能修改额外分数，这个按钮放什么地方？”

这里我建议把“按钮”设计成：手动触发完整重算 + 任务状态同步，而不是直接改分数。

按钮文字：刷新成熟度快照

位置：放在 “结构任务” 卡片右上角的小按钮，比「查看全部」略小一点。

行为：

调用后端 POST /api/books/{id}/recompute-maturity

后端：

重新统计 snapshotInput（blocksCount、todosCount、visits90d…）

重新 calculateMaturity

重新 resolveStructureTasks

如有 stage 变化 → 写 maturity_stage_changed 事件

如有 task 完成 / 回退 → 写 structure_task_completed / structure_task_regressed 事件

写一条 maturity_recomputed 事件，记录旧分数、新分数。

前端刷新 Overview 卡片和「最近事件」、「结构任务」。

这样逻辑是：

你平时改 block / 摘要 / TODO → 只是改数据，不立即暴力改分。

当你点“刷新成熟度快照”（或系统自动定期触发） → 一次性评估所有规则，统一结算分数和任务。

并且所有变化都有事件记录，Chronicle 完整可追溯。

六、已有 Book / 分数回退 的处理
1. 已有 Book 首次接入 Maturity

后端脚本或用户第一次打开 Book 时：

如果没有 snapshot，就调用 recompute-maturity：

生成一个初始 maturity_recomputed 事件（payload 标记 initial: true）。

不写任何 structure_task_completed 事件（因为是历史回填，避免一次性刷一长串任务完成）。

之后用户再点击“刷新成熟度”时，才开始正常写任务完成 / 回退事件。

2. 分数回退（摘要没了、block 减少）

因为任务状态是由 snapshot 推导的，所以：

摘要被清空 → 下一次 recompute-maturity：

hasSummary 从 true → false

对应 add_summary 任务从 completed → regressed

分数变低（少了 15 分）

Chronicle 里多两条事件：

maturity_recomputed（score: 70 → 55）

structure_task_regressed（taskId: 'add_summary', points: -15）

“最近事件”卡片就能看到：“摘要被清空 → 某个任务退回，分数下降”。

七、给 Copilot 的实现切片（你可以直接复制给它）

你可以把这些按功能拆成几个 Task 给 Copilot：

后端：实现 Maturity 纯函数

calculateMaturity(snapshotInput) -> { score, stage, contributions }

resolveStructureTasks(snapshot) -> StructureTaskState[]

写死一份 ALL_TASKS 配置。

后端：实现 Recompute API

POST /api/books/{id}/recompute-maturity

逻辑按上面“按钮行为”写。

同时写入 BookEvent。

后端：实现 Recent Events API

GET /api/books/{id}/recent-events

过滤 “强事件”，按时间倒序，限制 N 条。

前端：最近事件卡片组件

调 recent-events，列表展示。

右上角「查看全部」按钮跳到 Timeline Tab。

前端：结构任务卡片组件

概览页调 GET /api/books/{id}/maturity，拿 snapshot + taskStates。

展示未完成任务 + 已完成折叠。

右上角「刷新成熟度快照」按钮 → 调 recompute-maturity，然后刷新 Overview + 最近事件。

做到这一步，你的 Book 页面就形成了一个闭环：

Maturity：一目了然的分数和阶段。

Chronicle：完整的时间线。

最近事件：可以快速知道刚刚发生了啥。

结构任务：告诉用户“下一步该干啥才能升级”。

这四块都是纯 Domain（成熟度 + 审计），不依赖 theme，改 theme 的时候也不会把核心规则炸掉。