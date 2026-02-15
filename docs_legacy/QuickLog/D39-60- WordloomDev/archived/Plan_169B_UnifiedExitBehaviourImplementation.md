## 2025-12-10 回填

- **Outcome:** Unified Exit 行为全面上线：list/todo 壳层消费 keyboardDecider 的 list_family/todo 决策，handled flag 阻止后续重复提交，deleteGuard 只降级一次并自然回退到 paragraph，Plan169B 进入“已交付”状态。
- **Code refs:** `keyboardDecider.ts`、`ui/ListBlock.tsx`、`ui/TodoListBlock.tsx`、`ui/BlockItem.tsx`、`model/useBlockCommands.ts` 共用同一个 `KeyboardActionResult` 协议；`assets/docs/BLOCK_RULES.yaml` / `HEXAGONAL_RULES.yaml` / `DDD_RULES.yaml` 也同步补上壳层职责。
- **Tests:** `pnpm vitest ListBlock TodoListBlock keyboardDecider` 畅通 + Playwright “退格空 todo/list 仅生成一个段落”脚本通过，且 EverydayLog 已记录验证截图。

Plan: 统一 TODO/LIST 退出规则 & 文档更新
基于 Plan169A，要让 todo_list 和普通 list 使用同一套“退出大原则”，并同步更新代码与 BLOCK_RULES.yaml 的约定。

Steps
调整 keyboardDecider 的 TODO 决策

文件：keyboardDecider.ts
明确 TodoKeyboardContext 字段：保留 isItemEmpty, isFirstItem, allItemsEmpty，若需要可新增 isLastItem，与 list 对齐。
在 KeyboardAction 中增加 todo-exit（类似 list-exit），和现有的 todo-insert-item / todo-remove-item 并列。
改写 decideTodoAction(intent, ctx)：
intent === 'enter'：
!ctx.isItemEmpty → todo-insert-item（有内容就断行，继续扩展 todo 列表）；
ctx.allItemsEmpty → todo-exit（整块全空时，最后一个空项 Enter 视为退出意图）；
!ctx.allItemsEmpty && ctx.isItemEmpty && /* 尾项 */ → todo-insert-item（和 list 一样，尾空但整体仍有内容时继续插 item）；
其他空项 → todo-remove-item（中间空行删掉）。
intent === 'backspace'：
!ctx.isItemEmpty → 'noop'（只让编辑器自己删字符）；
ctx.allItemsEmpty 或 ctx.isFirstItem && ctx.isItemEmpty → todo-exit（整块空或首空行 Backspace 触发退出）；
其他空项 → todo-remove-item。
统一 TodoListBlock 的键盘上下文 & 退出逻辑

文件：TodoListBlock.tsx
在 TodoListEditor 中完善 KeyboardContextInput：
为每个 item 计算：isItemEmpty（用与 list 相同的 normalizeForEmptyCheck 思路）、isFirstItem、isLastItem、allItemsEmpty。
getKeyboardContext(intent) 返回 { kind: 'todo-item', isItemEmpty, isFirstItem, isLastItem, allItemsEmpty }。
引入类似 ListEditor 的“整块空退出护栏”：
添加 const pendingAllEmptyExitRef = React.useRef(false)；
当 allItemsEmpty 从 false→true 时重置为 false，防止旧状态残留。
在 onKeyboardDecision 中分支处理：
对 decision === 'todo-insert-item'：插入新 item（调用现有的 insertItemAfter），返回 true。
对 decision === 'todo-remove-item'：
若当前有多个 item：删除该项并把焦点移到相邻项，返回 true；
若只有一个 item：不要再“强行补一条空项”，而是让后面 todo-exit 负责退出（保持与 list 的分层：行删 vs 块退）。
对 decision === 'todo-exit'：
若 allItemsEmpty && !pendingAllEmptyExitRef.current（第一次触发）：
若想保持“需要双击”护栏，则先在列表里插入第二条空 item 或简单保持一条，设置 pendingAllEmptyExitRef.current = true，返回 true；
若不需要双击护栏，也可以直接走下一分支。
否则（第二次或不需要双击）：
清空 pendingAllEmptyExitRef.current；
调用 onExitEdit()；
调用外层提供的 onDeleteEmptyBlock?.()（或若存在 onCreateSiblingBlock，与 List 一样：先创建新 paragraph sibling 再删掉 todo block）。
保证返回 true，让 ParagraphEditor 不再触发自身 onDeleteEmptyBlock。
调整 Todo 行级删除逻辑与 decider 的优先级

仍在 TodoListBlock.tsx：
确保：
ParagraphEditor 的 onDeleteEmptyBlock 只在 decider 未处理 Backspace 时作为 fallback；
当 onKeyboardDecision 返回 true（处理了 todo-remove-item/todo-exit），就不会再触发 onDeleteEmptyBlock，避免“先删行再补行”覆盖退出语义。
若当前实现 removeItem 在 items.length <= 1 时会主动补回一个空项，需要拆分：
removeItem 专注于“行删除 + 调整焦点”，允许列表临时变成 0 条；
“至少一条可见 todo”这一 UX 需求，让外层 block shell 或命令层通过 deleteBlockWithGuard/ensureAtLeastOneBlock 处理，而不是行级逻辑强行补。
覆盖 TODO 键盘行为的测试用例

新建或扩展测试文件：frontend/src/modules/book-editor/ui/__tests__/TodoListBlock.test.tsx（风格参考 ListBlock.test.tsx）
使用 mock ParagraphEditor 捕获 props：onKeyboardDecision、getKeyboardContext。
重点用例：
多条 todo，中间空项 Backspace 删行
初始 items：['a', '', 'b']；在 index=1 调用 onKeyboardDecision({ intent:'backspace', decision:'todo-remove-item' })；
断言：onChange 最终 items 为 ['a', 'b']。
整块 todo 全空时，最后一项 Enter/Backspace 触发退出（含护栏）
单条空 todo：
第一次调用 onKeyboardDecision({ intent:'enter', decision:'todo-exit' })：
不应调用 onExitEdit / onDeleteEmptyBlock；
若实现了双击护栏，可断言 items 被扩展为两条空项。
用新内容重渲染后，在最后一条上再次调用 todo-exit：
断言 onExitEdit、onDeleteEmptyBlock（和可选 onCreateSiblingBlock）被调用一次。
同样的场景测试 intent:'backspace'。
单条非空 todo Backspace 不直接删块
items：['hello']；
模拟 decider：decideKeyboardAction('backspace', { isItemEmpty:false, ... }) 应返回 'noop'；
UI 层测试：onKeyboardDecision({ intent:'backspace', decision:'noop' }) 不触发 onDeleteEmptyBlock / onExitEdit。
keyboardDecider 的 todo 测试补充

文件：keyboardDecider.test.ts
在 makeTodoCtx 中加入 isLastItem 默认值，配合新的规则。
新增/调整用例：
enter：
非空 → todo-insert-item；
全空 + 最后一项 → todo-exit；
尾空但 allItemsEmpty=false → todo-insert-item；
中间空项 → todo-remove-item。
backspace：
非空 → noop；
全空 + 首项 → todo-exit；
多条、空中间项 → todo-remove-item。
Further Considerations
BLOCK_RULES.yaml 更新建议

在 command_layer.delete_guard.forbidden 后增加说明：
「list_row_backspace / todo_row_backspace 代表列表家族内部行级退格，由内嵌编辑器和 block shell 处理，不得调用 deleteBlockWithGuard。」
在 delete_fallbacks 或单独 note 中补充：
「当 bulleted_list / numbered_list / todo_list 整块判定为空、并由 keyboardDecider 给出 *-exit 决策时，block shell 应通过 deleteBlockWithGuard 删除该 block；guard 将按本表降级为 paragraph，确保 base_paragraph_guard。」
在 validation_checklist 新增一条：
「检查 list/todo 行级 Backspace/Enter 是否仅在壳层删除/插入行，只有在整块空且由 keyboardDecider 判定 *-exit 时，才通过命令层触发 deleteGuard/transform。」
Todo 与 List 的差异需要在代码注释或文档标注

文档中可点明：
判空只看文本，不看 checkbox 状态；
Todo 视觉上通常至少留一条空待办，但这个“至少一条”的策略由 Block shell + 命令层负责，不由行级 Backspace 决定。