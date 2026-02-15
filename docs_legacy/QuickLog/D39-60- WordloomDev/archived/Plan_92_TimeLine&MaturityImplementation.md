先把要点捋清，然后直接给你一份“可以立刻作为实现蓝本”的中文计划，不改代码，只写计划层级。

## Plan92: Book 成熟度 & 时间线落地实施

> 目标：在 2025-12 之前完成成熟度得分体系、分区迁移、时间线审计的端到端实现，并同步 RULES / ADR 文档。

### 1. 分区迁移核心约束（沿用 Plan72）

| 区域 | 自动分数段 | 备注 |
| --- | --- | --- |
| Seed | score < 30 | 必须满足基础 45 分后才允许手动升出该区 |
| Growing | 30 ≤ score < 70 | 默认由 score 推导，可被手动覆盖 |
| Stable | score ≥ 70 | 进入 Stable 需通过 TODO 守门；score < 70 时自动跌回 |
| Legacy | N/A | 由 `legacy_flag` / 专用用例触发，不计入 COVERAGE 分母 |

- 分区 = `Book.maturity` 的实时值（不是历史 score）。
- 任何成熟度变化（自动或手动）必须触发两件事：
  1. 书架视图卡片从旧分区移除并插入新分区；
  2. 时间线写入 `stage_changed` 事件，Overview Tab 展示最近一次变更。

### 2. 后端 / Domain / UseCase

1. **字段补全**：`maturity_score`, `maturity`, `legacy_flag`, `last_visited_at`, `visit_count_90d`, `manual_maturity_override`。
2. **评分策略**（来自 Plan72）
	- 标题/描述/Tag/Lucide/Block 类型/Block 数/TODO 等加减分；固定 45 分基础项 + 55 分弹性项。
	- `recalc_score(book)` 负责重算并返回 `(score, reasons[])`。
3. **状态机策略**
	- `derive_maturity(score)`：只输出 seed/growing/stable。
	- `legacy_flag === true` 时强制 `maturity='legacy'`，不再受 score 影响。
4. **RecalculateBookMaturityUseCase**
	- 触发：Block 结构、Tag、CoverIcon、TODO 状态变化后。
	- 流程：重算 score → 推导候选 maturity → 若未被 `manual_maturity_override` 锁定则更新 → 如有变化写 `stage_changed`。
5. **UpdateBookMaturityUseCase**（手动）
	- 入参：`{ book_id, target_maturity, override_reason?, force? }`。
	- 校验：Stable 需 score≥70 且 TODO=0；Legacy 需 Stable 且满足“180 天未编辑 + 90 天无人访问 + 未 pinned”。
	- 行为：更新 maturity / legacy_flag，记录 override 状态，写时间线事件，并返回最新 score/maturity。
6. **Timeline 事件**
	- `BookEvent.kind`: `created`, `stage_changed`, `status_changed`, `moved`, `tags_changed`, `pinned`, `unpinned`, `legacy_flag_changed`, `visited`。
	- 接口：`BookTimelineQueryService.list_book_events(book_id, { include_visits?: boolean, limit?, cursor? })`。

### 3. 前端实现路线

1. **数据同步**
	- `ListBooks` / `GetBook` DTO 必须包含 `maturity`, `maturity_score`, `legacy_flag`, `manual_override`。
	- `buildBookMaturitySnapshot` 仅以 `maturity` 作为分组 key；`legacy` 不进入进度条分母。
2. **书架视图交互**
	- 每个分区 header 增加提示：“来源：当前 maturity = {section}”。
	- 卡片 hover tooltip 展示 score 明细 + 手动 override 标记（小闪电图标）。
	- React Query 成功回调：
	  - 若 `UpdateBookMaturity` 返回新的 `maturity`，立即更新 cache 让卡片“瞬时搬家”；
	  - 仍触发 `invalidateQueries(['books', bookshelfId])` 以获取服务端真值。
3. **Book Workspace Timeline Tab**
	- 默认 `include_visits=false`；勾选“显示访问日志”后重拉。
	- Timeline item renderer 需要包含 `stage_changed` 的 from/to 文案；手动 override 需额外标记。
	- Overview Tab 展示最近 3 条生命周期事件（调用同一 hook 但 limit=3）。

### 4. 文档与审计要求

1. **DDD_RULES.yaml**：补写 `POLICY-BOOK-MATURITY-SCORE`、`POLICY-BOOK-MATURITY-STATE-MACHINE`、`POLICY-BOOK-LEGACY-FLAG`。
2. **HEXAGONAL_RULES.yaml**：补充 DTO 字段、`RecalculateBookMaturityUseCase`、`UpdateBookMaturityUseCase`、`BookTimelineQueryService` 的契约。
3. **VISUAL_RULES.yaml**：更新 `book_maturity_view_v2`、`book_edit_dialog_v3`、`book_workspace_tabs_visual_rules`，描述分区来源、卡片 tooltip、Timeline 视觉。
4. **ADR-111**：新增 “Partition Migration & Timeline Coupling” 小节，记录“成熟度变化 = 分区迁移 + 时间线事件”的决定。

### 5. 执行顺序（落地 Checklist）

1. 更新 RULES/ADR 文档，使架构共识同步；
2. 后端：实现 score service + Recalculate/Update UseCase + Timeline 事件写入；
3. 前端：
	- 调整 DTO & hooks；
	- 优化 `BookMainWidget`、`BookWorkspaceTimeline`；
	- 增加 override 标记与 tooltip；
4. 编写测试：
	- Domain 层 score 计算 + 状态机单测；
	- API 集成测试（成熟度变化导致查询结果分区移动、时间线出现事件）；
	- 前端单元/端到端测试（Playwright）覆盖“点击标记 Stable → 卡片移动 + Timeline 更新”。

> 下一步：按以上 checklist 同步 RULES/ADR 文件，然后进入后端与前端的实际开发。
三、前端书架视图 / 工作区计划


