# ADR-149 Plan164C Caret Pipeline Hardening

## Status

Status: Accepted
Date: 2025-12-04
Authors: Block Editor Working Group (Plan164C)

## Context

1. **Pointer intents仍然退化为首字母。** List/Todo/Paragraph shell 在 pointer 阶段没有计算真实 offset，只传 `edge:'start'` / `offset:0`，导致用户点击任意字符时 caret 仍落在行首。
2. **BlockEditorCore 仍混有 DOM helper。** 即便完成 Plan163C，核心组件内部依旧夹杂 placeCaret、副作用 hooks 与 selection 监听，闭包顺序小改就会重新触发 TDZ/ReferenceError。
3. **多处模块继续调用 `window.getSelection()`。** caretDomUtils 以外的代码（列表壳层、测试 helper）仍能直接写 selection，Plan163C 的“唯一 owner”约束缺乏强制守卫。
4. **Observability 完全缺位。** 没有 QuickLog 管线去记录 BlockEditorCaretIntent，QA 无法判断 pointer intent 是否携带 offset、是否被 keyboard 回抢，也无法追踪 fallback 事件。

## Decision

1. **抽离 caret DOM 工具。** `frontend/src/modules/book-editor/model/caretDomUtils.ts` 负责 selection 读取、`getOffsetFromPoint`, `placeCaretAtNodeOffset` 等纯函数；任何 DOM selection 读写都必须经由该模块。
2. **以 hook 统一消费 intent。** `useBlockCaretController` 订阅 focusIntentStore、selectionchange，并向 BlockEditorCore 暴露 `focusFromPoint/restoreEdgeFocus/publishSelectionSnapshot`。组件体仅创建 refs + 调 controller，杜绝 TDZ。
3. **Inline shell 只负责 intent。** List/Todo/Paragraph pointer handler 使用 `getOffsetFromPoint` 计算 offset，并通过 `announceFocusIntent({kind:'pointer', blockId, offset, source})` 上报；shell 自身不再接触 DOM selection。
4. **遥测强制上线。** `selectionStore.announceFocusIntent` 统一调用 `reportBlockEditorCaretIntent`，通过 `shared/telemetry/quickLogClient` → `/api/quicklog` 上报 `{trigger, blockId, offset, source}`，便于监控 pointer/keyboard 竞争和 fallback。
5. **Lint + RULES 守卫。** 新建 ESLint 规则 `wordloom-custom/caret-selection-owner`，仅允许 caretDomUtils 与 useBlockCaretController 调用 `window.getSelection()`；DDD/Hexagonal/Visual/BLOCK 键盘规则同步 Plan164C 条目并标记 Adopted。

## Consequences

* **Positive:** Pointer intent 始终携带真实 offset，点击任意字符不再落在首字母，列表/段落/待办间跳转连贯。
* **Positive:** BlockEditorCore 体积保持但职责单一，placeCaret 副作用集中在 controller，可预测性更强，TDZ/闭包顺序问题消失。
* **Positive:** QuickLog 具备 `BlockEditorCaretIntent` 事件，可在 dashboard 上建立 pointer fallback 告警并回溯 source 分布。
* **Positive:** Lint + RULES 杜绝重新引入 `window.getSelection()` 写点，任何违规在 CI 即被拒绝。
* **Negative:** 仓库中所有实验性脚本若直接访问 selection 需迁移到 caretDomUtils/controller，否则无法通过 lint。
* **Negative:** QuickLog 事件目前先流入 `/api/quicklog` 控制台，下游 dashboard 仍需搭建数据管线方能完成 D5 最终验收。

## Implementation Notes

* `frontend/src/modules/book-editor/model/caretDomUtils.ts`：集中 selection 读写、offset 计算与 `PLAN164C_POINTER_FALLBACK` 记录入口。
* `frontend/src/modules/book-editor/model/useBlockCaretController.ts`：封装 intent 订阅、selectionchange、快照广播，BlockEditorCore 仅依赖公开 API。
* `frontend/src/modules/book-editor/model/selectionStore.ts`：`announceFocusIntent` 接入 `reportBlockEditorCaretIntent`，所有调用者需提供 `source`。
* `frontend/src/modules/book-editor/shared/telemetry/quickLogClient.ts` & `.../blockEditorTelemetry.ts`：封装 `sendBeacon`/`fetch` fallback 与标准化事件 payload。
* `frontend/src/app/api/quicklog/route.ts`：Next API route，暂时记录 payload，为后续 dashboard 搭建提供入口。
* `frontend/eslint-rules/caret-selection-owner.js`：CI 守卫，仅白名单 caretDomUtils 与 useBlockCaretController。
* 文档：`assets/docs/DDD_RULES.yaml`、`HEXAGONAL_RULES.yaml`、`VISUAL_RULES.yaml`、`BLOCK_KEYBOARD_RULES.yaml` 更新 Plan164C 条目与状态。

## References

* QuickLog: `Plan_164A_BlockCursorTri-StabilityIssues.md`, `Plan_164B_Assessment.md`, `Plan_164C_CaretFullLanding.md`
* Rules: `POLICY-BLOCK-PLAN164C-CARET-PIPELINE`, `block_editor_plan164c_caret_pipeline`, `block_editor_plan164c_pointer_precision`, `pointer_precision_guards`
* ESLint: `frontend/eslint-rules/caret-selection-owner.js`
* Telemetry: `shared/telemetry/quickLogClient.ts`, `blockEditorTelemetry.ts`, `/api/quicklog/route.ts`
