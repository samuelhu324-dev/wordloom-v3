# ADR-126: Plan117 Chronicle Timeline Storyline

- Status: Accepted (Dec 1, 2025)
- Deciders: Wordloom Core Team
- Context: ADR-093 (Chronicle recorder), ADR-104 (Book todo + timeline link), ADR-118 (Maturity resilient shell), ADR-125 (Plan116 shell parity)
- Related Artifacts: `assets/docs/VISUAL_RULES.yaml#chronicle_timeline_visual_rules`, `assets/docs/HEXAGONAL_RULES.yaml#chronicle_storyline_plan117_pipeline`, `assets/docs/DDD_RULES.yaml#POLICY-CHRONICLE-PLAN117-STORYLINE`, `frontend/src/features/chronicle/ui/ChronicleTimelineList.(tsx|module.css)`, `backend/api/app/modules/chronicle/services/chronicle_recorder_service.py`, `backend/api/app/modules/book/application/services/word_count_projection.py`

## Problem / 背景

1. **时间线缺少故事感。** 现有 Book Timeline 只呈现成熟度重算与结构任务少量事件，看起来像后台日志（参见 Screenshot#Plan117），无法回复“这本书经历了什么”。
2. **数据缺口。** Block/Book 聚合没有维持 word_count / total_word_count，导致无法产出“快照”“里程碑”类事件；封面/主题更新、Todo 升级等行为虽然存在，却没有统一记账。
3. **UI 难以扩展。** 时间线组件没有事件→模板映射，新增事件必须改动多处字号/颜色，难以保持和结构任务卡片一致的语义层级。

## Decision / 决策

1. **事件集合扩充。** 以 Plan117 的 P0/P1 清单为准，正式纳入以下 ChronicleEventType：
   - P0：`book_created`、`book_soft_deleted`、`stage_changed`、`book_maturity_recomputed`、`structure_task_completed`、`structure_task_regressed`、`cover_changed`、`cover_color_changed`。
   - P1：`content_snapshot_taken`、`wordcount_milestone_reached`、`todo_promoted_from_block`、`todo_completed`。
   - P2 占位：`work_session_summary`、`book_viewed`（暂不实现，仅列入 Enum 与 RULES 以避免将来 break）。
2. **统一记录助手。** `ChronicleRecorderService.record_event(book_id,type,payload)` 成为唯一入口；Book/Block/Maturity/StructureTask UseCase 完成后立即调用该助手，不允许 UI/脚本直接写表。
3. **字数与快照投影。** Block 模型新增 `word_count`，保存时由纯函数统计；Book 聚合维护 `total_word_count` 并在满足 1k/5k/10k 阈值时自动触发 `wordcount_milestone_reached`。每次手动刷新成熟度或每天首次进入 Book 时，写入 `content_snapshot_taken`，payload 包含 `{block_count, block_type_counts, total_word_count, trigger}`。
4. **Todo/封面事件可视化。** Block → Todo promotion/completion 继续复用 Chronicle todo 事件，现在纳入 Timeline 渲染；封面/主题变更在 Media/Theme adapter 层调用 recorder，展示“封面换新”文案。
5. **前端模板化渲染。** `ChronicleTimelineList` 使用 event→renderer map：每种类型定义 icon、标题、摘要模板，并复用 NextStepsChecklist 的 0.875rem/450 secondary 字体；新增 filter chips（内容快照、字数里程碑、封面、Todo）。

## Consequences / 影响

- **正面：** 时间线终于覆盖书籍生命周期关键节点（出生、升级、换封面、写作里程碑、清单），用户无需查后台就能回溯变化。
- **正面：** 字数/快照数据可复用于其他统计（如“本周写了多少字”），而且由 Block save pipeline 自动维护，不增加 UI 负担。
- **正面：** 文案模板 + 统一字重后，Timeline 与结构任务/成熟度卡片视觉一致，QA 只需对照 VISUAL_RULES 即可验收。
- **负面：** 保存 Block 内容的代价稍增（需统计字数并写入 Book total）；若一次更新多个 Block，需关注事务性能。
- **风险：** 事件数量激增可能导致时间线请求更重，需要分页/过滤控件默认收敛（Overview 仍展示 5 条）。

## Implementation Notes / 实施

1. **Backend**
   - Chronicle 模块：更新 `ChronicleEventType` Enum + Recorder + Query DTO，新增 payload schema 校验；RECENT_EVENT_TYPES 常量同步扩充。
   - Book/Block 服务：在 Block save hook 中调用 `count_words`，写回 block.word_count 与 book.total_word_count；编排 `content_snapshot_taken`、`wordcount_milestone_reached` 触发点。
   - StructureTask/BookUseCase：Stage/Task/Maturity/Theme 等入口成功后统一调用 `record_event`，payload 带上 from/to/score/delta/actor。
2. **Frontend**
   - `ChronicleTimelineList.(tsx|module.css)`：新增 eventRenderers map、Todo/封面/字数布局、filter chips；标题字形复用 NextStepsChecklist 规则。
   - Overview 卡片：`useRecentChronicleEvents` 默认 eventTypes=P0+wordcount，避免信息噪音。
3. **Docs & Tests**
   - 更新 VISUAL/DDD/HEXAGONAL RULES（见 Related Artifacts）。
   - Router/Service tests 覆盖新事件 payload；前端单测验证 renderer 输出与过滤逻辑。
