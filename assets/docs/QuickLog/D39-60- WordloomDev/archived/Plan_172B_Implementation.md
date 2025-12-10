实施层执行方案（给实现 agent 的导航清单）
编辑器 & 命令入口

ParagraphEditor / 统一 inline 编辑组件

在 onKeyDown 顶部加 if (e.key === 'Enter' && e.shiftKey) 分支：preventDefault() → 调用 paragraphCommands.insertSoftBreak() → return。
确认普通 Enter 仍走原有 handleInlineEditorKeyDown / keyboardDecider，不受影响。
列表 / Todo 行编辑组件（ListItemEditor / TodoItemEditor 或对应 inline shell）

复用 ParagraphEditor 的 onKeyDown 或复刻同样的 Shift+Enter 分支，保证：
软换行只在当前 item 文本中插 \n；
不新建/删除 item；
不让事件继续冒泡到 list_family_exit / block 级删除。
文本命令层（如 paragraphCommands / blockCommands 内的文本操作模块）

新增 insertSoftBreak：读取当前文本 + caret offset，插入 '\n'，写回文本，并把 caret 移动到 offset+1。
只更新当前 block 文本，不调用 createBlock、deleteBlockWithGuard、transformBlockKind 等命令。
渲染 & 判空

文本渲染组件（段落、列表项、todo 文本显示处，例如 .textBlockContent 或行内 <div contentEditable>）

若已使用 white-space: pre-wrap（当前看你已在 bookEditor.module.css 里这么做），确认列表/todo 文本同样生效；否则在对应 class 上补上。
目标：文本中的 \n 在 UI 中显示为同一 bullet/checkbox 下的多行。
判空 helpers / deleteGuard 前置判定

搜索所有用于 list/todo 退出、backspace 删除空 block 的 isEmpty / isTextEmpty / allItemsEmpty 函数，将逻辑调整为：
例：const normalized = text.replace(/\s+/g, ''); const isEmpty = normalized.length === 0;
保证“只包含空格、Tab、\n 的情况”仍然被视为空，从而不会因为软换行堵住 list/todo 的退出通路。
决策器 & 测试

keyboardDecider

不需要改 Enter/Backspace 分支，但可以在注释中说明：Shift+Enter 在编辑器层被拦截，不会传到此处。
验证它的 allItemsEmpty / isEmpty 输入已经按上面的软换行判空规则处理。
Vitest 测试（已有 ListBlock / TodoListBlock / keyboardDecider 测试）

增补用例（可以分散在对应测试文件中）：
段落软换行：初始 "abc|def"，Shift+Enter 后 "abc\n|def"，block 数不变。
列表项软换行：item "item|1" → "item\n|1"，仍是一个 item，不触发 keyboardDecider 的 block 级决策。
空列表 + 连续 Shift+Enter：唯一空 item，多次 Shift+Enter 只插入 \n，不触发 list_family_exit 或 deleteBlockWithGuard。
如果你愿意下一步就开干，我可以按这份 BLOCK_RULES 方案，帮你具体点出在 book-editor 下面应该改哪些文件、哪些函数名，以便你直接让实现 agent「按图施工」。



# Plan 172B Block Soft Break Doc Sync — Implementation Log

Date: 2025-12-05
Owner: Block Editor Guild
Linked Plans: Plan_171A, Plan_171B, Plan_172A

## Completed Work

1. **VISUAL_RULES.yaml** — added `block_editor_plan171a_inline_soft_break` detailing keyboard interception, text semantics (`\n` storage + whitespace empty), and QA coverage.
2. **DDD_RULES.yaml** — introduced `POLICY-BLOCK-PLAN171A-INLINE-SOFT-BREAK` in a new `POLICIES_ADDED_DEC05` section, clarifying that Domain/UseCase never see `Shift+Enter` and that guards treat `\n`-only strings as empty.
3. **HEXAGONAL_RULES.yaml** — documented `block_editor_plan171a_inline_soft_break_contract`, covering handler responsibilities, normalization helpers, and regression requirements.
4. **ADR-151-plan171-inline-soft-break.md** — captured the context/decision/consequences for the inline-only soft-break design, with references to code/tests/rules.

## Validation

- Diff review confirms the three RULES files now cite Plan171A-specific guardrails and QA steps.
- ADR numbering follows the directory convention (`assets/docs/ADR/ADR-151-*.md`) and references the updated RULES files plus test suites.
- QuickLog Plan_172A acceptance criteria satisfied (docs exist, cross-links recorded, no additional schema changes needed).

## Follow-Up / QA Notes

- Future caret/keyboard plans should reference ADR-151 when proposing changes to `Shift+Enter` handling.
- If additional RULES (e.g., BLOCK_RULES) need mirroring, spin up Plan_172C rather than reopening this plan.
