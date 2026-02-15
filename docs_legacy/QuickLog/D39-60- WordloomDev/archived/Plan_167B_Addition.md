## 2025-12-10 回填

- **Outcome:** Plan167B 追加的“统一 markdown 入口 + deleteGuard 专属触点 + 自检 checklist”已在主干执行完毕：Space 分支仅负责检测 pattern，真正的 transform 委托命令层，guard 只会响应 block 壳层的 requestDelete，确保列表/待办在编辑途中不会再莫名降级。
- **Code refs:** `ParagraphEditor.tsx` 的 Space 处理、`model/markdownShortcuts.ts`、`ui/BlockItem.tsx::handleMarkdownShortcut`、`useBlockCommands.deleteBlockWithGuard` 均已贴上注释并引用 BLOCK_RULES 校验；另在 `scripts/qa/BEHAVIOR_AUDIT.md` 加入三条手测清单。
- **Tests:** `pnpm vitest markdownShortcuts` + `ListBlock/TodoListBlock` suites + Playwright 手溜路径（Slash→List、List→Paragraph）全部通过，Checklist 也纳入 code review 模板。

1. 快捷键完全失效的原因
从你现在的现象看：

- + Space 没反应
但 Slash 菜单可以插入 bullet list
说明命令层/BlockKind/transform 是 通的，问题卡在：

某些 ParagraphEditor 根本没挂 onMarkdownShortcut

Block shell（BlockItem）里的 paragraph 已经传了 handler，
但特殊块内部（例如 TodoListBlock、ListBlock、Callout 内部用到的 ParagraphEditor）很可能没有继续把这个 handler 透传下去。
结果：在这些上下文里按 - + Space，只是普通输入，检测函数根本没被调用。
Space 分支的检测前置条件还在挡路

当前实现里 Space 处理大概类似：
先要求 caret 在行尾（isCaretAtEdge('end') 等）
再看整段是否“pattern + 空白”
但在 IME / 选区状态轻微不同（比如前面还有不可见字符、selectionStore 未同步）时，这些前置会直接短路返回，连 markdown 检测都不跑。
这就导致：你以为自己是“空段 + - + Space”，但在逻辑层眼里条件不成立，所以 shortcut 不生效。
总结：命令层没问题，Slash 正常说明 transformBlockKind OK；Markdown shortcut 是“UI 没发请求 + Space 分支条件过严”导致的。

2. 特殊块一打字就降级为 paragraph 的原因
这个现象基本只能来自：

误用 deleteBlockWithGuard 作为“清空/回退”的通用手段

根据 BLOCK_RULES，deleteBlockWithGuard 的职责是：
真正“删除块”时保证至少留一个 paragraph
对特殊块优先做“降级为 paragraph”而不是直接删掉
如果特殊块内部（list/todo/quote/callout 等）的某些逻辑，在“内容被清空/行内删除”的时候也去调用了这个命令：
guard 会认为“这是在删一个特殊块”，于是按 delete_fallbacks 把它降级成 paragraph。
这就是你看到的：“菜单插入的 list 一旦打字/退格，很快就变普通块”。
老的“空块自动还原 paragraph”策略残留在某个 handler 里

很早以前为了解决“空列表恢复成段落”的需求，可能写过类似逻辑：
if (isSpecialBlock && isEmptyAfterEdit) transformToParagraph()
这段如果还挂在特殊块的 onChange / onBlur / onExit 上，就会在你编辑时频繁触发“还原段落”，看起来就像“打几个字就被外星人重置”。
总结：不是 Domain/命令层在乱降级，而是 UI 层在错误场景下调用了 delete guard / 旧还原逻辑，guard 只是忠实执行了“特殊块 → paragraph”的规则。

3. 一劳永逸封死这一类问题的方案（落到代码/规则上）
结合你现有的 BLOCK_RULES + Plan165/166/167，我建议：

收紧 delete guard 的入口：只允许「块壳层删除」使用

代码策略：
搜索全仓所有 deleteBlockWithGuard 调用点：
只保留 Block shell（BlockItem 或等价组件）对 Backspace/Delete/菜单删除的调用。
特殊块内部（List/Todo/Callout 等）一律禁止直接调用这个命令，只能：
自己删行/删 item
或通过“显式按钮”调用 transformToParagraph（如果你真的要一个“转成段落”功能）。
任何“onChange / onKeyDown / onInput” 中出现 deleteBlockWithGuard 的，全部改掉。
规则补充：
在 BLOCK_RULES.yaml.command_layer.deletion 里加一条：
deleteBlockWithGuard.may_only_be_called_from_block_shell = true
并写明：inner editors (list items, todo rows, callout body) MUST NOT call delete guard.
统一 Markdown shortcut 的入口，并给 ParagraphEditor 一个清晰契约

代码策略：
把 markdown 检测抽成一个纯函数（你已经有雏形）：
输入：textBeforeCaret, textAfterCaret, key
输出：{ kind, shouldClear } | null
ParagraphEditor 在 Space 分支：
不再依赖“段落必须完全为空”或内部 selection 状态，只要：
caret 在行尾（用 textAfterCaret 判空来兜底）
textBeforeCaret（去掉尾空格）匹配 - 等 pattern
就认定为命中。
命中后：
setText('') + onChange('')
调用上层的 onMarkdownShortcut({ kind, cleared: true })
确保所有需要支持快捷键的 ParagraphEditor 实例，都透传同一个 onMarkdownShortcut：
顶层 BlockItem（段落）
列表首行 / todo item 首行 / 其他你希望支持 markdown 的上下文
不希望支持的，就不要传 handler，而不是传一个空实现。
规则补充：
在 BLOCK_RULES 的 ui_integration.markdown_shortcuts 下写清三步：
检测仅由 ParagraphEditor 完成；
命中时必须先清空文本，再调用命令层；
仅当 cleared === true 时，shell 可以跳过“空段落”检查。
加一层“行为自检”——简单的 e2e / 集成测试

至少加三个用例（可以先写在 Vitest + jsdom，后面搬到 Playwright）：

空段 paragraph 中输入 -，再按 Space：
预期：当前 block.kind 变为 bulleted_list（或你的枚举值），doc 中内容为空。
插入一个 todo/list block，在其中输入文字然后 Backspace 直至清空：
预期：仍然是 todo/list block，只是内部 item/text 为空；不会自动变成 paragraph。
在 list 最后一项后敲 Enter：
预期：按设计是新增列表项或退格成段落，但不得在你只打字的途中就发生降级。
把这三条写进 BEHAVIOR_AUDIT.md / Plan167A 的“整体验证”部分，每次你重构 editor，只要跑一遍就能快速发现回归。

4. 现状总结
Plan167A 把 老编辑器入口 基本清干净了，但你现在遇到的问题已经全部发生在 新 editor 栈内部：
Markdown shortcut 的 Space 分支和 handler 透传不完整；
一些特殊块内部仍然错误调用了 delete guard 或旧的“空块降级”逻辑。
命令层的规则（BLOCK_RULES）总体是对的，需要做的是：
把 delete guard 调用点彻查一轮，收缩到 block 壳层；
把 ParagraphEditor 的 markdown 合约（检测条件 + 清空顺序 + handler 透传）落实成统一代码路径；
用 2–3 条自动化测试把这几个关键行为钉死。
如果你愿意，下一步我可以按这三条原则，列出一个“搜索与修改清单”（精确到函数名/文件路径），你可以在 VS Code 里一条一条确认改。

/////////////////////////////////////////////////////////////

Plan: 彻查并修复快捷键 & 特殊块问题
下面是给“实现方”的精确改造清单，你可以直接照着逐条执行 / 对照代码。

Steps 一：Markdown 快捷键链路
统一检测逻辑到 markdownShortcuts.ts

文件：markdownShortcuts.ts
检查/补充：
用它作为唯一入口：detectMarkdownShortcut(text, caretOffset)、isCaretInEmptySegment(text, caretOffset)，不要在别处再手写正则和 ZERO_WIDTH 处理。
在这里写清契约注释：
输入假设：caret 在当前“marker 段”的末尾，textAfterCaret 只允许空白。
输出：匹配 - / 1. / - [ ] / > 时返回对应 BlockKind，否则 null。
保留“after 为空”这层判断（如果 caret 后还有非空字符就返回 null），避免中间插入触发。
精简 ParagraphEditor 的 Space 处理

文件：ParagraphEditor.tsx
重点符号：handleKeyDown、isCaretInEmptySegmentLocal、detectMarkdownShortcutLocal
修改要点：
Slash 菜单逻辑保持：event.key === '/' 时用 isCaretInEmptySegmentLocal() 决定是否触发。
Space 分支改成只做三件事：
if (event.key === ' ' && !event.shiftKey && onMarkdownShortcut)：
先判断 markdown shortcut 是否启用。
从 coreRef.current 读：
const text = handle.getText() ?? ''
const caretOffset = handle.getCaretOffset()；如果为 null 直接 return;。
调 detectMarkdownShortcut(text, caretOffset)：
返回非空则：event.preventDefault(); coreRef.current.setText(''); onChange(''); onMarkdownShortcut({ kind, cleared: true });
返回空则不做任何事，继续走 handleInlineEditorKeyDown。
删除/避免在这里再次手工对 before/after 做正则切片，让 detectMarkdownShortcut 负责。
明确“哪些块允许触发 markdown shortcut”

文件：BlockItem.tsx
确认当前实现（接近已有逻辑）：
常量：MARKDOWN_SHORTCUT_SOURCE_KINDS = new Set<BlockKind>(['paragraph', 'heading']);
在 editor 上挂：
onMarkdownShortcut={MARKDOWN_SHORTCUT_SOURCE_KINDS.has(block.kind) ? handleMarkdownShortcut : undefined}
在 handleMarkdownShortcut 中：
保持现有 guard：if (!MARKDOWN_SHORTCUT_SOURCE_KINDS.has(block.kind)) return;
对 options.cleared !== true 的情况保留 isDraftEmpty() 检查，防止“在有正文的段落里刷新成 list”。
结果：只有最外层 paragraph / heading 的 block 会真的把 -+Space 转成 list / quote，其他 block（包括 list 内的行）即使用了 ParagraphEditor 也不会触发。
Steps 二：特殊块内部编辑，禁止隐式降级
ListBlock：行内只改 items，不动 block 类型

文件：ListBlock.tsx（请在项目中打开确认具体名称，通常是这个）
逐项检查：
每一行的删除逻辑应该是类似：
onDeleteEmpty={() => removeItem(item)}
removeItem 内部只更新 content.items，绝不调用 useBlockCommands / deleteBlockWithGuard / transformBlock。
当列表只剩 1 行时：
清空这一行文本 -> 列表仍然是 bulleted_list / numbered_list，只是 items 里有一条空字符串；不要在这里把整个 block 变回 paragraph。
行内的 ParagraphEditor：
不要给它传 onMarkdownShortcut（保持 undefined），这样 list 中输入 - + Space 只会改这一行文本，不会变 block。
TodoListBlock：对 todo item 做同样的约束

文件：TodoListBlock.tsx
关键点：
removeItem / ensureAtLeastOneItem：
确保这俩只操作 content.items，不触碰 block kind、不调用 useBlockCommands。
当删到只剩一行，再把这一行清空时：
用 ensureAtLeastOneItem 创建一个“空 item”，不是删掉整个 todo_list block。
内部的 ParagraphEditor：
和上面一样，不传 onMarkdownShortcut；只负责编辑 item.text。
任何关于“把 todo 降为 paragraph”的需求，只能在 block shell 外通过 blockCommands.transformBlock 显式触发（例如 toolbar 里有个“转成普通段落”按钮）。
Quote / Callout / Panel：确认没有调用命令层

文件：
QuoteBlock.tsx
CalloutBlock.tsx
PanelBlock.tsx
检查点：
编辑器组件（QuoteEditor / CalloutEditor / PanelEditor）里：
只接受 content + onChange + onExitEdit，内部不调用 useBlockCommands / deleteBlockWithGuard / transformBlock。
删除/关闭行为只通过 UI 上的“完成”/“取消”来结束编辑，不去改 block kind。
若发现任何“内容为空就 transformToParagraph”之类逻辑，全部删掉，集中到 blockCommands 的 guard 内处理。
Steps 三：约束 deleteBlockWithGuard 的调用点
审计所有 deleteBlockWithGuard 调用

全局搜索：deleteBlockWithGuard(
预期：只在 BlockItem.tsx 之类的 block 壳组件中出现。
如果在以下位置发现调用，必须移除：
ListBlock / TodoListBlock / QuoteBlock / CalloutBlock / PanelBlock 内部
任何 ParagraphEditor 宿主的 onChange / onKeyDown / onExitEdit 里
替代策略：
行内/内容层只改 content，不改 block 列表。
真正要“删整块”的地方，都走 Block shell 层的 toolbar/menu/Backspace 逻辑。
明确 guard 的职责并在代码中写死

文件：blockCommands.ts
函数：deleteBlockWithGuard
调整/注释：
在函数上方加注释（中文/英文都可）：
“只允许由块级容器（例如 BlockItem）在‘删除整个块’时调用。禁止在列表行 / todo 行 / 富文本内部调用。”
逻辑层面保持现有语义：
单个 base block：清空内容但不删 block；
单个 special block：可选择降级到 paragraph（downgradeBlockToParagraph），或在 allowDowngrade=false 时 no-op；
多块时，根据 computeFallback 决定新的 focus。
若你希望更强约束：
可以从 useBlockCommands 导出的对象里只暴露：
createBlock, deleteBlock, transformBlock
另写一个 useBlockDeleteGuard() 专门在 BlockItem 内部用。
这样别的地方从 TS 层就拿不到 deleteBlockWithGuard。
在 BlockItem 中核对“只有壳层触发 guard”

文件：BlockItem.tsx
函数：requestDelete / handleDeleteEmptyBlock
检查：
requestDelete(...) 内部是：
const result = await deleteBlockWithGuard({ blockId: block.id, intent: origin });
且只由：
toolbar 菜单
整块 Backspace（handleDeleteEmptyBlock）
其它“删块” UI 入口
调用。
不要把 requestDelete 下沉传给子编辑器作为“行级删除”。
Steps 四：测试与人工验证
补单元测试（Vitest）
测 markdown：
文件：markdownShortcuts.test.ts
覆盖：
detectMarkdownShortcut('- ', 2) -> 'bulleted_list'
detectMarkdownShortcut('1.', 2) -> 'numbered_list'
detectMarkdownShortcut('- [ ]', 5) -> 'todo_list'
detectMarkdownShortcut('>', 1) -> 'quote'
caret 不在末尾 / 后面还有字时 → null。
测 guard：
新文件：frontend/src/modules/book-editor/model/__tests__/blockCommands.deleteGuard.test.ts
用假数据喂 blocks，直接调用 deleteBlockWithGuard：
单段落有内容 → status cleared，kind 不变；
单 todo/list → status downgraded 或 noop，但不无声删除；
多块场景 → 删除/降级后 focus 落到 fallback。
设计一个最小 UI 手测 checklist（你本地按顺序试一遍）
新建空书本，在 Blocks Tab：
输入 - 再按 Space → 当前块变为 bullet list；再用 Undo/Redo 验证稳定。
同一段落中间：输入 Hello - world 光标在 “-” 后按 Space → 不应触发 list，仍是 paragraph。
在 list item 内输入 - + Space → 只改变该行文本，不产生新 block。
新建 todo 块，输入 2 条待办，勾选/取消，再退格删空第二条：
只删掉第二条 item，整个块仍是 todo_list。
把 todo 只剩一条 item，再把它删空：
仍然是 todo_list，只是内部是一个空行。
在完全空的 list / todo 块上，移动光标到块最开始，按 Backspace：
按你的 UX 方案，要么：降级为 paragraph；要么：保持 special block 不动，但绝不会在“打字过程中”偷偷降级。
如果你愿意，下一步我可以针对其中某一块（比如“只保留 BlockItem 调 guard”）和你一起对照实际代码逐行走一遍，帮你确认没有遗漏调用点。

