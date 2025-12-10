先回答你现在的两个具体疑问，再给一份可落地的中文优化方案。

一、当前 35 分是怎么算的 & 为什么你那本书有标签却没加分？

基于目前后端代码（BookMaturityScoreService + plan102.py），现实状况是这样的：

现在实际生效的得分主要还是“老版规则”：

看标题、摘要、Block 数、Block 类型数、TODO 数、封面、标签数量等，算出若干 ScoreComponent，最终累加成一个 0–100 的分数。
你截图里的 35 分，很可能是：
标题 +10
摘要 +15
Block 结构若干分（例如 ≥3 个 +10，再扣一点 TODO 或访问相关），大致落在 35 左右，并不是简单的 “block 数量 × 1 分”。
“标签是否加分”这件事，目前有明显脱节：

BookMaturityScoreService 里确实有一条规则：如果 tag_count > 0，会追加一条 ScoreComponent(factor='tags', points=5, ...)。
但 Plan102/Plan103 这条链路里，标签数是从 tag_count_snapshot 字段传进来的；而现在多数 Book 并没有在聚合上实时维护这个 snapshot（它只在某些 Tag 变更 use case 里被写入，或者还没打通）。
结果就是：你界面上能看到标签（Tag 模块正常工作），但成熟度重算的输入里 tag_count_snapshot=0，所以没拿到这 5 分 → 你感受到的是 “有标签却不加分”。
“每个 Block 算 1 分，20 个封顶？”

现有实现不是这么线性的，而是几个档位：
≥3 个 Block 给一档基础分（例如 +10）；
≥10 个 Block 再给一档进阶分（例如 +10）；
不会按 1:1 线性增长，所以“20 个 Block = 20 分封顶”这个规则目前并不存在。
Plan102/103 中我们已经设计了结构任务：“create_3_blocks”“create_10_blocks”等，用结构任务 +贡献项来表达，而不是“每个 Block +1”。
二、针对你提的 UX & 规则诉求，我给一份详细可执行的中文优化方案

下面的方案分三块：(A) 计分规则对齐你直觉、(B) 结构任务 UI 行为、(C) 实现落地步骤。都只动 Maturity + Chronicle + 相关前端视图，不改主题/配色。

A. 计分规则优化：让 Block / Tag 的分数可预期

Block 计分：改为“阶梯 + 封顶”，贴近你说的 20 封顶

规则建议（可在 plan102.calculate_score_components 中落地）：
有 ≥1 Block：+5 分（避免完全空白）。
≥3 Block：再 +10 分（达到基本结构）。
≥10 Block：再 +10 分（结构较完整）。
总计 Block 相关最多 +25 分。
好处：
用户大致知道 “多写一点内容会加几档分”，同时不会无限线性膨胀。
如果你仍然希望“20 个 Block ≈ 20 分”，可以调成：每个 Block +1，最多 +20；但建议仍保留 3/10 这样几个门槛做结构任务。
标签计分：保证“只要有标签就一定加分”

后端调整：
把 tag_count_snapshot 的来源统一到：
Book 保存 / Tag 关联变更 / 手动 Recompute 时，都通过一个统一的 service 更新 tag_count_snapshot。
如果短期不想大改，可在 BookAggregateMaturityDataProvider.load_book_profile 里做兜底：
若 tag_count_snapshot 为 0 / None，则从 Tag 关联表查一次真实 tag 数量，至少保证 Recompute 时是最新的。
计分建议：
tags_count ≥ 1：+5 分；
tags_count ≥ 3：再 +5 分（可选）。
这样你截图里的书只要关联了一个 Tag，重算成熟度后分数一定会有所提升。
得分解释对齐 UI：让“35%”背后透明可见

API 层面已经有 score.components[]；前端只需要在“结构任务卡片”下方或 hover 里，列出：
“标题 +10 分（已完成）”；
“摘要 +15 分（已完成）”；
“补齐标签 +5 分（未完成）”；
“Block 数不足 10 个（待完成）”；
这样可以直接回答“35 分是怎么算的”这个问题。
B. 结构任务 UI 行为：灰度 + Checked + 折叠列表

已完成任务灰度显示，但仍显示勾选（Checked）

后端：
StructureTaskState.status 已经支持 COMPLETED；
接口返回 tasks[] 时，带上 status 字段（当前我们已经在 MaturitySnapshot 里输出了）。
前端 NextStepsChecklist 调整：
根据 status 渲染：
PENDING：主色+可交互（例如可以点开查看说明）。
COMPLETED：灰度显示 + 前面是选中状态的圆形勾选框（表示“曾经完成过”）。
LOCKED：更淡的灰色 + 禁用态 tooltip（“先完成前置任务：XXX”）。
REGRESSED：保持勾选框未勾选，但加一个橙色/黄色提示，表示“之前完成过，现在条件不满足了”。
这样你可以一眼看出哪些是“已经做过的结构动作”，哪怕当前又被回退了。
结构任务栏内容过多时，使用折叠/下拉容器

交互建议：
顶部始终展示 最多 3 个 PENDING 任务（当前阶段最关键的）。
下面加一个“展开更多任务 ▾”区域，展开后显示：
其他 pending 任务；
全部 completed / locked / regressed 任务列表（分组展示）。
技术实现：
NextStepsChecklist 内部用 useMemo 对 tasks 做分组：pending, completed, locked, regressed。
默认状态：只渲染 pending.slice(0, 3)；
点击“展开更多”后，渲染剩余 pending+所有 completed/locked/regressed，并可滚动。
刷新按钮行为维持不变，但联动任务状态

结构任务卡片的“刷新成熟度快照”按钮：
点击 → 调 POST /maturity/books/{id}/recompute；
成功后：
重新拉取最新 maturity snapshot（带新 score + tasks 状态）；
触发 recent-events 更新，以在“最近事件”区域看到“完成结构任务/阶段变化”等。
这样用户在改动标签、Block 后，一次刷新就能看到：
分数改变；
某个任务从 pending → completed，UI 变灰 + 勾选；
最近事件里新增了一条“结构任务完成”的记录。
C. 实现落地步骤（你或后续 agent 可以照着做）

后端：完善 Plan102 计分逻辑

在 plan102.py 中：
调整 calculate_score_components：
按上面 A.1/A.2 的档位计算 Block 与 Tag 相关分数；
确保返回的 ScoreComponent.factor/detail 文案与前端期望一致。
如有需要，在 calculate_maturity 里调整 stage 分段：
0–29 seed / 30–59 growing / 60–89 stable / 90–100 legacy（与 Plan102 保持一致）。
后端：保证 tag_count_snapshot 有真实值

在下面任一层补齐 Tag 计数：
BookAggregateMaturityDataProvider.load_book_profile：
若 tag_count_snapshot == 0，调用 Tag 关联仓储统计真实标签数；
或在 Tag 关联/解除 use case 里同步更新 Book 的 tag_count_snapshot 字段。
这样只要你在 Tag 模块里给书加了标签，再点“刷新成熟度快照”就一定会加分。
后端：任务状态与信号写入 snapshot

在 Recompute 用例中（目前是 RecalculateBookMaturityUseCase + Maturity 模块）：
根据当前 Book + Tag/Block/Todo/访问统计，构造 SnapshotInput：
blocks_count, todos_count, visits_90d, summary_length, tags_count, has_title, has_summary, has_cover_icon 等；
调 calculate_maturity(input) 得到 { score, stage }；
再调 resolve_structure_tasks(stage, input) 得到 StructureTaskState[]；
写入 MaturitySnapshot：
score, stage, tasks, 以及附带的结构统计字段；
通过 SQLAlchemyMaturitySnapshotRepository 保存（它已经支持 tasks + signals JSON）。
前端：重构 NextStepsChecklist 行为

在 api.ts：
扩展 BackendTransitionTask/TransitionTaskDto，加上 status 字段（string），以及可选的 required_stage。
在 NextStepsChecklist 组件中：
按 status 分组渲染（pending/completed/locked/regressed）；
completed → 灰度 + 已勾选；
增加“展开更多任务”逻辑，防止任务列表过长压垮卡片。
前端：增加得分解释展示（可选但推荐）

新建一个小组件，例如 MaturityScoreBreakdown：
入参 snapshot.score.components；
渲染为一列“+10 标题”“+5 标签”“+10 Block”等。
将它挂在结构任务卡片之下或 hover 上，这样你随时能看到 35 分的组成。
如果你愿意，我可以下一步帮你详细拆出 “Block/Tag 具体权重表 + 任务列表设计表（中英文文案）”，这样你就可以直接贴到 RULES / ADR-114 里，并按这个规则实现后端。

---

## 2025-11-29 推进记录（前端 Plan104）

**已完成**

1. **成熟度概览卡片升级**
	- `NextStepsChecklist` 支持状态分组、前三个关键任务默认展示，其余通过“展开更多 / 收起任务”折叠，完成项灰度+勾选、锁定/回退提供提示。
	- 新增 `MaturityScoreBreakdown` 组件，直接渲染 `score.components`，告诉用户 35% 的组成；手动刷新/运营加分后自动失效 React Query，确保 snapshot + recent events 同步更新。

2. **Chronicle 最近事件卡片**
	- 引入 `/chronicle/books/{id}/recent-events` 的结构化输出，按「阶段变更 / 结构任务 / 书籍生命周期」三组展示，带 Lucide icon、事件 pill 和相对时间。
	- 点击“查看全部”仍跳时间线 Tab，视觉风格和 overview 卡片统一。

3. **交互统一**
	- 保存/创建/删除 Block 后会触发成熟度重算并刷新 Plan104 三个查询（snapshot、recent events、timeline），保证用户看到最新状态。

**仍需落地**

1. **后端计分规则对齐**：`plan102.calculate_score_components` 仍未落实 Block 阶梯加分、标签 ≥1 必加分；Tag snapshot 缺乏兜底查询，导致“有标签没加分”。
2. **标签快照低耦合方案**：需要在 `BookProfileSnapshotProvider` 中添加 Tag 仓储 fallback 或事件同步，消除对 `tag_count_snapshot` 的硬依赖。
3. **文档/规范同步**：DDD / HEXAGONAL / VISUAL 规则与 ADR-114 还未更新 Plan104 的成熟度与 Chronicle 设计，需要把上述决策写入正式文档。
4. **测试与演示数据**：缺少展示阶段变更、结构任务完成的样例书，后续可以在 seed 或测试脚本中补充，方便验收。

**下一步建议**

1. 先实现 Tag 计数兜底 + Block/Tag 新权重，验证 score breakdown 是否正确；
2. 根据最终规则写入 DDD/Hex/Visual/ADR 文档；
3. 编写一份“Plan104 前端验收清单”，列出现有 UI 截图与交互说明，便于交付 review。

## 2025-11-29 后端修复进度（Plan104）

- [DONE] `BookAggregateMaturityDataProvider` 支持在 `tag_count_snapshot` 为空时降级调用 `TagRepository.find_by_entity`，确保有真实标签的书必定拿到 `tags` 加分，同时新增 `test_maturity/test_data_provider.py` 覆盖兜底路径。
- [DONE] `plan102.calculate_score_components` 按 Option A 落地 Block 阶梯（≥1/+5、≥3/+10、≥10/+10）与 Tag 阶梯（≥1/+5、≥3/+5），并补充 `test_plan102.py` 断言 0/1/3/10 档位得分。
- [DONE] `derive_maturity_from_score` 与 Plan102 阈值对齐（Seed <30、Growing <60、Stable <90、≥90 Legacy），新增 `test_book/test_maturity_utils.py` 覆盖 0~105 断点，保证分数下修后会触发阶段回滚，书架分区立即同步。
- [TODO] DDD/HEX 规范需要补写一份“成熟度计分&阶段回滚” ADR，总结以上规则与依赖；此外仍需补种一批示例数据，方便 QA 快速看到 Seed/Growing 来回切换。

