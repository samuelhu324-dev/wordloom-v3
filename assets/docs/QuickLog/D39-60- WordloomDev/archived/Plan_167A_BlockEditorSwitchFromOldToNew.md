## 2025-12-10 回填

- **Outcome:** 所有块编辑入口（书籍工作区、Blocks 页、调试页）已统一挂到 `modules/book-editor` 壳层，旧版 BlockList/BlockRenderer/ParagraphEditor 被移入 `features/block/legacy/` 并通过 ESLint `no-restricted-imports` 禁止被再次引用；Plan167A 的“切换到新编辑器”正式完结。
- **Code refs:** `frontend/src/features/block/legacy/*` 仅保留历史参照；`ui/BookEditorShell.tsx`、`ui/BlockList.tsx`、`ui/BlockItem.tsx` 负责全部写路径，`BlockEditorRoot` 成为唯一入口，INSERT/DELETE/UNDO 逻辑再无双轨。
- **Tests:** `pnpm vitest frontend/src/modules/book-editor/ui/__tests__` 通过（ListBlock/TodoListBlock/BlockItem suites），确保新壳层在 Enter/Backspace/Slash/Toolbar 场景均与旧 UI 行为一致；手动对比书籍详情页确认所有键盘规则均遵循新栈。

Plan: 旧块编辑入口统一切到新编辑器
把现在依然使用 BlockList/BlockRenderer 的“老块编辑页”全部替换为 modules/book-editor 体系，让 markdown shortcut、delete guard 等行为只在新编辑器里实现和演进，从根上消除两套逻辑打架的问题。

Steps
找入口页面：在 src 全局搜索 BlockList 和 BlockRenderer，列出所有仍在使用旧编辑器的页面组件（例如某个 BlockListPage 或书籍详情页的 block 区域容器）。
引入新壳子：在这些页面中改为 import 新编辑器壳（modules/book-editor/ui 里的 Shell 组件，例如 BookEditorShell 或等价容器），并删除对旧组件 BlockList/BlockRenderer 的引用。
对齐数据层：把旧页面原来传给 BlockList 的 bookId、blocks、onUpdateBlock 等 props，梳理后按新编辑器壳需要的结构传入（initialBlocks、命令层 hooks、selection store 等），保证读写同一套后端 API。
关闭旧逻辑：在新壳子接入完成并验证无误后，将旧编辑器模块标记为 legacy（或直接移除导出）：包括 BlockList.tsx、BlockRenderer.tsx 及其内部的 ParagraphEditor/Slash/markdown/delete 逻辑，避免被其他新代码再次引用。
整体验证：在所有入口页面手动走一遍核心流程（新建段落、- + 空格 触发 bullet list、插入 todo/list/quote、在特殊块内部输入与退格），确认行为与 modules/book-editor 规范一致，不再出现“打字即降级”为 paragraph 的情况。

2025-12-05 更新
- `BlockList.tsx`、`BlockRenderer.tsx`、`insertMenuConfig.ts`、`insertTypes.ts` 与 `blockPlugins.ts` 已整体迁入 `frontend/src/features/block/legacy/`，并从 `features/block/ui` barrel 中移除导出，防止新代码误用旧编辑器。
- `legacy` 目录顶部都加了 “LEGACY” 注释，提醒阅读者这些实现仅作历史参照；若真要加载，必须显式 import legacy 路径，默认入口仅剩 modules/book-editor。
- 新入口（Book detail / Blocks workspace）确认继续通过 `BookEditorRoot` 工作；后续如发现残余引用，按本计划步骤逐个替换。
- 前端 ESLint 现已启用 `no-restricted-imports`，禁止引用 `@/features/block/legacy/*`；若有人想动 legacy 模块，必须显式关闭 lint 或走 override，以此保证所有新代码只触达 `modules/book-editor`。
- 新增 `modules/book-editor/model/markdownShortcuts.ts`，把段落编辑器里的 Markdown 转换逻辑抽成纯函数，并用 Vitest (`model/__tests__/markdownShortcuts.test.ts`) 覆盖 bullet/number/todo/quote 四种快捷键，防止回归。
- `model/keyboard.ts` 的 Enter 处理顺带修正：Shift+Enter 统一 `preventDefault` 并只触发软回车，空段落按 Enter 会调用 `onExitEdit`，对应老编辑器里“空段落直接退出”行为。
- 补充《BEHAVIOR_AUDIT.md》记录 Slash Menu 锚点、Markdown shortcut、删除守卫的人工验证步骤，后续可以按文档把这些场景搬到 Playwright。
- 在 `modules/book-editor/EDITOR_CONTRACT.md` 里写死壳组件的对外契约（必填 bookId、React Query 依赖、禁止再手写 selection store 等），方便后续页面直接查阅。
- 复查 `BlockItem` / `TodoListBlock`：确认 Markdown shortcut → `transformBlock` 仍依赖 `isRenderableBlockEmpty`，todo 行内编辑靠 selectionStore 撑住焦点迁移；暂未发现“特殊块打字变 paragraph” 的残留调用链，后续需要在 e2e 里补一条 todo-list 输入与退格用例来锁行为。
Further Considerations
分阶段迁移：可以先迁移一两个主要入口（例如书籍详情页），确认无回归后，再全局替换所有对旧编辑器的引用。
文档约束：在 BLOCK_RULES.yaml / QuickLog 里补一条“块编辑只能通过 modules/book-editor 入口使用”的约束，防止后续再新建基于旧组件的页面。

/////////////////////////////////////////////////////////////

先下个结论：这份迁移方案方向是对的，而且结构已经够“工程化”，可以真的拿去做一轮重构了。核心思想——所有块编辑入口统一走 modules/book-editor——正好顺手把 - + 空格 那类快捷键乱斗的问题从根上拔掉。

下面我分几块说：哪些地方已经很好、有哪些风险点、以及我会怎么微调这份计划，让你扔给 Copilot 也更“机械可执行”。

1. 方案本身的优点

你现在这版有几个亮点：

入口统一，逻辑单源头

从“全局搜 BlockList / BlockRenderer → 找入口页面 → 一律改成新壳子”

再加上最后“BLOCK_RULES 里写死：块编辑只能通过 modules/book-editor”
这两步组合起来，相当于在“入口层 + 文档层”都立了规矩：以后谁再新建老编辑器入口就是违规。

迁移路径清晰，步骤粒度对

你现在的步骤顺序很合理：
找入口 → 换壳子 → 对齐数据层 → 标记 legacy → 整体回归。
这一套非常适合你现在的 repo 状态，不会大爆炸。

显式关闭旧逻辑

特地写了“标记 legacy / 移除导出”

还点名：BlockList.tsx / BlockRenderer.tsx / ParagraphEditor / Slash / markdown / delete 逻辑
这个很关键，因为你现在遇到的那种“看起来改了，其实还有某个旧组件在偷偷接管输入”就是典型幽灵依赖问题。

有“分阶段迁移”的意识

先迁移一两个主页面（比如书籍详情），观察稳定性，再全局替换——
对你这种单人开发 + 要准备 demo 的状态来说，这个保守度刚刚好。

总的来说：思路简洁且抓到了关键点：消灭双轨编辑器。

2. 目前这版里容易踩坑的地方

我会重点提醒几类风险，基本都能提前在方案里补一句：

风险 A：新壳子和数据层的契约写得不够“死”

你现在写的是：

把旧页面原来传给 BlockList 的 bookId、blocks、onUpdateBlock 等 props，梳理后按新编辑器壳需要的结构传入（initialBlocks、命令层 hooks、selection store 等）

问题在于：新壳子到底需要哪些“必填参数”和“可选参数”？
如果这东西没写死，Copilot 很容易帮你接成“刚好能编译，但行为一团糟”。

可以补充成类似：

新壳子必须接收：

bookId

initialBlocks（和旧 blocks 的字段映射规则）

onBlocksChange / onCommit（写回 API 的统一出口）

不再允许：

页面直接调 “老的 block 更新 API”

页面自己管理 selection / focus 状态（必须交给 selection store）

也就是说：把“谁有权改 block 状态”写进这份计划里。

风险 B：feature parity（功能对齐）没被写清

你在“整体验证”里列了一些关键交互：

新建段落

- + 空格 触发 bullet list

插入 todo/list/quote

特殊块里输入与退格

建议再加两类你前面吐槽过的场景，不然容易漏：

多行选中 + Delete / Backspace 行为

比如从列表末尾退格，是否正确“合并为普通段落”，而不是整块全部被 paragraph 接管。

与占位符/空文档的交互

现在的 “写点什么...” placeholder 逻辑，确保在新壳子里也是同一套（不要出现某个入口进去是空白，另一个入口进去有 placeholder 这种割裂感）。

直接把这两个项目写入“整体验证 checklist”，以后你每次重构只要按 checklist 走一遍就安心很多。

风险 C：旧模块“标记 legacy”的策略还不够彻底

你写的是“标记 legacy（或直接移除导出）”。
对你现在这种会频繁 refactor 的 repo，我更推荐一套更暴力一点的手法：

建一个 legacy/ 目录，把旧编辑器文件整体挪进去

在每个 legacy 文件顶部加一个超醒目的注释：
// LEGACY EDITOR – DO NOT USE. Will be removed after vX.Y.Z

在 tsconfig 或 ESLint 里，加一条 rule：
如果在非 legacy 目录里 import legacy 模块 → 报错 / 抛 lint

这样可以彻底防止将来你半夜写代码时顺手 import { BlockList } from "..."; 结果又把旧逻辑招魂回来。

3. 建议追加到方案里的几个具体动作

这些属于“往这个 Plan 里再插几刀细节”，方便你丢给 Copilot 执行：

3.1 增加一个临时开关：老入口 → 新壳子 + feature flag

你可以在步骤 2–3 之间加一条：

在每个被迁移的页面临时保留一个 useNewEditor 开关（env / local config），允许在开发时快速切换新旧编辑器，用来 A/B 对比行为是否一致。

这样当你发现“新编辑器里出现奇怪 bug”时，还能临时切回旧版验证是不是新逻辑引入的问题，而不是 API / 数据造成的。

3.2 给 modules/book-editor 补一份“公共接口说明”

在这个 Plan 里增加一句：

在 modules/book-editor 目录下新增 README.md 或 EDITOR_CONTRACT.md，明确：

对外暴露的主壳组件有哪些（例如 BookEditorShell）

必填 props / 可选 props

对外暴露的 command hooks（如 useInsertBlock, useToggleMark）

禁止直接调用的内部模块（例如某些低层 ParagraphEditor）

这一条会极大降低后续“误用内部 API”的概率，也方便你未来拆子模块。

3.3 把“整体验证”升级为可复用测试用例

你现在写的是手动走流程；我会在计划里再补一句：

同步在 Playwright / Cypress / Vitest 中补一组最小 e2e / 集成测试，覆盖：

- + 空格 转换

todo / list / quote 插入

删除特殊块边界行为

从空文档开始输入第一段文字

哪怕先写 3–4 条也好，至少你以后重构不会每次都靠纯人肉回归。

4. 文档（BLOCK_RULES / QuickLog）层面的小补强

你已经提到要在 BLOCK_RULES / QuickLog 里补一条“块编辑只能通过 modules/book-editor 入口使用”，我建议稍微展开成一段规范，像：

所有与 Block 内容有关的 UI，只能通过 BookEditorShell / 其子壳接入

禁止在页面级组件中：

自己维护 block selection 状态

直接操作 block 列表（增删改）
这些只能通过 editor command 执行

若未来要增加新的特殊块类型：

必须先在 modules/book-editor 内实现、测试

再在外层暴露插入命令（而不是在外层直接造 JSX）

这段写进 YAML / DOC 之后，你就有了一个“别人如果违反，属于对系统规则的破坏”的标准，而不是“只是风格问题”。

5. 总结一句

这份迁移方案本身没啥大问题，方向完全正确：统一入口、杀掉双轨编辑器、把 markdown shortcut / delete guard 等所有复杂行为都锁进新编辑器体系，是解决现在那些“- 空格 失灵、段落莫名降级”的正确办法。

如果在这份 Plan 上再加一点点“契约说明 + legacy 防回流机制 + 测试清单”，你就可以放心把它当成一次正式的“Block 编辑器 v2 切换 ADR 实施计划”，而不是临时补丁。

等你把第一个入口（比如书籍详情页）切过去，很多之前那些玄学 bug 会直接消失，编辑器这条线的心智负担会下降不少。

