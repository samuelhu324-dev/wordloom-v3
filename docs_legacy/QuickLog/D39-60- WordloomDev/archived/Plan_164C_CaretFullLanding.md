# Plan 164C — BlockEditor 光标最终落地

> 结合 Plan 164A《Block Cursor Tri-Stability Issues》与 Plan 164B《Assessment》，输出可执行的最终交付清单，范围只涵盖 UI 适配层（BlockEditorCore、List/Todo inline shell、focusIntent/selection store 以及 QuickLog 监控）。

## 0. 约束复述
- **单一 caret owner**：BlockEditorCore + useBlockCaretController 是唯一能调用 `window.getSelection()` 的模块，其余组件只能发布 focus intent。
- **Intent-first**：所有 caret 移动（键盘、鼠标、命令、初始聚焦）都必须走 FocusIntentStore → caret controller 流程。
- **精确 pointer offset**：List/Todo/Paragraph 的点击事件必须根据点击坐标计算真实 offset，禁止把 pointer intent 简化成 `edge: 'start'` 或 `offset: 0`。
- **UI-only 边界**：Hexagonal/Domain 不感知 selection/caret，Undo/Autosave/Command 只通过 intent 描述“我需要的光标位置”。

## 1. 问题切分
1. **结构性炸裂**：BlockEditorCore 中 hooks 相互闭包引用（TDZ），selection 监听、focus intent 和 DOM helper 全部混在同一个文件里。
2. **多源 caret**：旧的 selectionStore API 仍可写 DOM，List/Todo 组件还有残存的 `window.getSelection()` 调用，导致 intent 与直接 setSelection 打架。
3. **Pointer 精度缺失**：列表点击只落在首字母，说明 pointer intent 没有携带真实 offset。
4. **观测盲区**：QuickLog 没有记录 BlockEditorCaretIntent，遇到回归只能靠手工复现。

## 2. 交付物
| 序号 | 交付物 | 内容要点 |
| --- | --- | --- |
| D1 | `model/caretDomUtils.ts` | 纯 DOM helper：selection 获取、rect/offset 计算、`offsetFromPoint`、`placeCaretAtNodeOffset`。不得依赖 React/store。|
| D2 | `model/useBlockCaretController.ts` | 自定义 hook，集中处理 intent 订阅与 DOM 操作，向外暴露 `placeCaret`, `setCaretOffset`, `focusFromPoint`, `publishSelectionSnapshot` 等稳定接口。|
| D3 | BlockEditorCore 精简 | 组件体只创建 refs、调用 controller、注册 UI 事件，不再直接实现 DOM 操作；所有 hooks 都依赖 controller 的稳定方法。|
| D4 | List/Todo/Paragraph inline shell 改造 | 点击 / 光标跳转全部转成 pointer intent；新增 `getOffsetFromPoint` 使用；删除任何直接 setSelection 的旧代码。|
| D5 | QuickLog & Dashboard 扩展 | 新增 `BlockEditorCaretIntent` 事件：`kind, blockId, offset, source`，并在 QuickLog/Dashboard 上加告警视图。|
| D6 | RULES & lint guard | 四大规则库添加“caret owner / intent-only / pointer offset”硬约束；ESLint 自定义规则禁止除 caretDomUtils / caret controller 以外的模块调用 `window.getSelection()`。|

## 3. 执行步骤
1. **模块拆分（D1 + D2）**
   - 先把所有 DOM selection 逻辑迁移到 `caretDomUtils.ts`。
   - 在 caret controller 内封装 focus intent 订阅、readOnly/autoFocus/selectionchange 副作用。
   - 对外只暴露 TS interface（`BlockCaretController`）。
2. **BlockEditorCore 重排（D3）**
   - 组件顶部只保留 refs/state；所有 hooks 依赖 controller。
   - 删除文件内残留的 placeCaret/getCaretRect 重复定义。
   - 保证 `useEffect` 统一返回清理函数，杜绝 TDZ。
3. **Inline editors 接入（D4）**
   - Paragraph/List/Todo 的 onMouseDown/onClick 计算 offset 并发布 pointer intent。
   - 上/下键、退出列表等键盘流程全部交给 intent 管道。
   - 移除 `selectionStore.requestSelectionEdge` 等旧 API。
4. **遥测与 QA（D5）**
   - 增加 QuickLog 事件及 Dashboard 小组件，监控 pointer→keyboard 连发、offset=0 异常等。
   - 完成 Paragraph→List→Paragraph / Todo→Paragraph / autoFocus / readOnly 切换等手工脚本。
5. **规约 & 守卫（D6）**
   - 更新 DDD/HEX/VISUAL/BLOCK 键盘规则，记录单一 owner + pointer 精度。
   - 加 ESLint 规则 `wordloom-custom/caret-selection-owner`（预留 TODO），CI 拒绝多处 DOM selection 写入。

## 4. 完成标准
- 任意点击列表/待办/段落，caret 落在点击字符上；上下键、Enter、Slash 菜单操作均不再出现“回弹”。
- `npm run type-check` 无 BlockEditorCore TDZ/副作用错误。
- QuickLog 可看到 BlockEditorCaretIntent；Dashboard 有提醒。
- 规则库中新增的 Plan164 条目获得评审签字。

## 5. 里程碑
| 日程 | 里程碑 | 说明 |
| --- | --- | --- |
| Day 0 | 模块拆分完成 | caretDomUtils + useBlockCaretController merge。|
| Day 1 | Inline editors 接入 | Pointer 精度验证 + e2e 手动脚本。|
| Day 2 | QuickLog & RULES 更新 | 监控上线、规则落表、lint guard 提交。|
| Day 3 | 回归测试 | 重点跑 Paragraph/List/Todo + Slash/Undo/Autosave 场景。|

> 如需进一步扩展（表格/Panel 等块），必须复用本计划的 intent-only 管道，禁止重新实现 caret owner。

## 2025-12-04 状态回填

| 序号 | 状态 | 说明 |
| --- | --- | --- |
| D1 | ✅ 已完成 | `frontend/src/modules/book-editor/model/caretDomUtils.ts` 提供 selection 读取、offset 计算与 `placeCaretAtNodeOffset`，所有 DOM 操作集中到该模块。|
| D2 | ✅ 已完成 | `useBlockCaretController` 统一消费 focus intent、selectionchange，并向 BlockEditorCore 暴露 `focusFromPoint/restoreEdgeFocus/publishSelectionSnapshot`。|
| D3 | ✅ 已完成 | BlockEditorCore 仅作为可视容器：创建 refs → 调 controller，所有副作用都依赖 controller 方法，TDZ 问题消失。|
| D4 | ✅ 已完成 | List/Todo/Paragraph inline shell 在 pointer 阶段调用 `getOffsetFromPoint` 并附带 `source`，pointer intent 不再退化为 `edge:'start'`。|
| D5 | ✅ QuickLog 上线（Dashboard 待接） | `selectionStore.announceFocusIntent` 通过 `shared/telemetry/quickLogClient` 发送 `BlockEditorCaretIntent`，Next API `/api/quicklog` 打印事件；待下游 dashboard 接入流数据。|
| D6 | ✅ 已完成 | 新增 ESLint 规则 `wordloom-custom/caret-selection-owner`；`DDD_RULES`、`HEXAGONAL_RULES`、`VISUAL_RULES`、`BLOCK_KEYBOARD_RULES` 已同步 Plan164C 条目并标记 Adopted。|

待办：Watch QuickLog dashboard 一旦连上真实流水立即验证事件密度，并将 `PLAN164C_POINTER_FALLBACK` 告警门槛写进监控脚本。
