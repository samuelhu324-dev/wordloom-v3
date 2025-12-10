已思考 35s

整体评价：
这份 Block 页 i18n 收口方案范围、顺序、颗粒度都挺合理，可以直接作为「一次性扫干净 Block 页文案」的执行蓝本，只是可以再补几处“防踩坑”的小约束。

一、逐条点评 Steps
Step 1：梳理 block 页面结构

梳理 block 页面结构…列出所有提示/按钮/空态/对话框及相应组件。

👍 很关键的一步，我建议你把结果变成一个小清单文件，而不是只在脑子里记：

维度建议：

Surface：overview / editor / timeline / autosave/toast / dialog

State：normal / empty / loading / error / disabled

每一行：位置 + 组件名(可选) + 当前文案 + 计划的 i18n key

这个清单后面正好可以贴进 QuickLog / ADR-179A 的附录，用来证明“已经全覆盖”。

Step 2：扩展 en-US / zh-CN 字典 & 命名空间选择

新增 bookBlocks.（或复用 books..blocks）覆盖 tabs、editor 工具栏、状态提示、toasts、aria。

这里是方案里最值得先拍板的一点。

我个人推荐：挂在 books 命名空间下，而不是单独拉一个顶层 bookBlocks*：

Option A：独立命名空间 bookBlocks.*

✅ 优点：一眼就知道是 “Block 页”。

❌ 缺点：和 books.*、bookshelves.* 比较割裂；以后如果 Book 页也要做 i18n，很容易一堆顶层命名空间横着铺开。

Option B：嵌套在 books.* 下（推荐）

比如：

books.blocks.tabs.*

books.blocks.editor.toolbar.*

books.blocks.editor.insertMenu.*

books.blocks.timeline.*

books.blocks.autosaveBanner.*

好处：

Domain 视角上，“Blocks 页”是 Book 的子视图；挂在 books 下语义更自然。

字典结构可以和路由结构对应：/books/[id]/blocks → books.blocks.*，以后很好维护。

不管选哪种，都给自己一条硬规则：

key 中不要出现具体组件名/技术名（比如 BlockTimelineCard），只描述语义位置：timeline.entryTitle, toolbar.bold.tooltip 这类。

Step 3：顶层注入 useI18n

给 Block 页面顶层…注入 useI18n()，以 t() 替换所有硬编码字符串和 aria/tooltip。

这一步没问题，但有两个常见坑要提前防一下：

确保顶层是 Client Component

如果 admin Block 页当前还是 server component，要么：

在最外层加 'use client'，

要么做一个 BlockPageShell 之类的 client 包壳，再把 i18n 和 tabs/toolbar/timeline 都放进去。

aria + tooltip 一定记得一起改

建议 key 格式统一一点：

books.blocks.editor.toolbar.bold.label

books.blocks.editor.toolbar.bold.ariaLabel

books.blocks.editor.toolbar.bold.tooltip

这样后面如果你要做无障碍检查，很容易系统性排查。

Step 4：BlockEditor 子组件 i18n 化

命令描述、快捷键提示、确认弹窗走字典；必要时抽公用 helper 处理动态插值。

这块是“容易碎、但很关键”的一层，我有两个增强建议：

命令 / 快捷键描述尽量“单一真相”

不要一边是 command config 写 "Bold"，另一边 tooltip 自己再写 "Bold (Ctrl+B)"。

更理想做法是：

做一个 Command 列表（比如 BLOCK_COMMANDS），里面存 command id、默认 keybinding、i18n key 前缀；

toolbar / 菜单 / 快捷键提示都从这份配置渲染，避免后期 drift。

确认弹窗 / 错误提示注意插值模式

比如："确定要删除 {count} 个 block 吗？"

尽量让 helper 接受 t 或 lang，而不是自己在 helper 里写死中文/英文格式。

插值 key 可以统一习惯：{count}, {blockType}, {title} 等，避免到处各写一套。

Step 5：格式化 helper 接受 lang

更新格式化 helper（autosave 时间、block 计数、history 描述）以接受 lang，并在渲染层调用。

方向是对的，只是实现上可以再“干净一点”：

不要从下往上传 lang 字符串（那样 props 会越传越乱）
建议两种方案选一个：

传 t 进 helper，而不是传 lang

function formatAutosaveTime(date: Date, t: TFunction) {
  const relative = formatRelativeTime(date, t); // 内部用 t('books.blocks.autosave.xMinutesAgo', { count })
  return t('books.blocks.autosave.banner', { relative });
}


传 locale 给“纯格式化函数”，文案还是在字典里

比如用 Intl.DateTimeFormat / dayjs 的多语言包：

helper 只负责“算时间 + 格式化成 human 值”

把 "x 分钟前自动保存" 这句放回字典里。

两者都比“helper 里自己拼中文/英文句子”要稳得多。

Step 6：QA + QuickLog / ADR

运行本地页面切换语言进行 QA，记录缺失 key，补齐后截屏/记录结果。

除了你写的流程，我建议 QA 时有一个简单 checklist（肉眼点一圈）：

切换语言时：

✅ Tab 名 / 面包屑

✅ Editor toolbar / 插入菜单

✅ Block 列表空态

✅ Autosave banner / 保存结果 toast

✅ History timeline（动作 + 时间 + 人）

✅ 错误条 / error dialog

✅ 浏览器标题（如果有动态 title）

✅ aria-label / tooltip 没有残留英文

另外，可以加一个极简自动化：

写一个小单测比对 key 结构：

assertSameShape(en.books.blocks, zh.books.blocks)

确保两个语言至少 key 是对齐的，不会一个多一个少。

二、Further Considerations 两个问题
1）命名空间：bookBlocks.* vs books.editor.*

是否新建 bookBlocks.* 命名空间还是扩展现有 books.*？

我推荐的折中命名：

books.blocks.* 作为 Block 页的统一个 namespace：

books.blocks.tabs.*

books.blocks.overview.*

books.blocks.editor.*

books.blocks.timeline.*

books.blocks.autosave.*

editor 的更细粒度可以：

books.blocks.editor.toolbar.*

books.blocks.editor.insertMenu.*

books.blocks.editor.emptyState.*

这样既不再新拉一个顶层 bookBlocks，又保持“路由=命名空间”的清晰关系。

如果你以后 Book detail 页也要拆 i18n，可以对应用：

books.detail.*

books.settings.*

books.blocks.*

结构感会很完整。

2）BlockEditor 插入菜单 / 快捷键的 dev-only 文案

BlockEditor 插入菜单/快捷键描述需区分 dev-only 文案吗？若需要可准备 debug.* key。

这里我的建议是：

真正用户可见的东西 → 一律正规 key + 全量中英。

纯 dev-only（例如 debug overlay 里的文案、内部标号）：

可以放在单独的 debug.* 或 dev.* 命名空间，例如：

debug.blockEditor.commandId

debug.blockEditor.selectionRange

但只要“有机会出现在生产环境界面上”，还是建议翻译一份，哪怕：

zh-CN 里就写同样的英文，加个前缀 [debug] 保持一致。

日志 / console.error 这种，保持英文即可，不必进 i18n。

三、我会怎么微调这份方案

在你现有的基础上，我只会加三件小事：

Step 0：锁一份“现状截图”

语言切换前的混杂样子截图 1–2 张，给自己一个 before/after，对 demo 很有用。

Step 2 明确命名空间约定（比如就拍板用 books.blocks.*）

加一个“字典完整性单测”

保证以后新加 key 不会只写一边语言。

除此以外，这份 Plan 已经足够可执行、粒度也对得上你现有前端结构，可以直接喂给 Copilot / 自己开分支落地。

等你把 Block 页收口完，整个 admin 区的 i18n 基本就接近“体系化”了，接下来再搞别的页面就会轻松很多。

# Plan179A · Block Page 文案清单（2025-12-07）

> 维度：Surface × State. 目标是覆盖 `/admin/books/[id]` Block 页（概览、块编辑、时间线、Autosave/Toast/Dialog）所有可见文案，为 `books.blocks.*` 命名空间建立映射。

| Surface | 组件 / 定位 | 现有文案示例 | 建议 key (`books.blocks.*`) |
| --- | --- | --- | --- |
| Breadcrumb | `page.tsx` `Breadcrumb` items | `书库列表` / `暂无简介。` | `nav.libraries` / `overview.summary.empty` |
| Hero CTA | `page.tsx` header 按钮 | `AUTO SAVE` / `加载中...` | `hero.autoSave.label` / `hero.autoSave.loading` |
| Tabs | `TAB_DEFS` | `概览` / `块编辑` / `时间线` | `tabs.overview` / `tabs.blocks` / `tabs.timeline` |
| Overview Eyebrow | Metrics summary | `Maturity` / `SCORE` / `最近活动` | `overview.maturity.title` / `overview.score.label` / `overview.activity.label` |
| Stage badges | `MATURITY_META` + `overviewStats` | `Seed` / `内容结构已成型，适合长期维护` | `overview.stage.seed` / `overview.stage.seed.description` |
| Score chips | `overviewStats` fallback | `暂无分值拆解` | `overview.score.empty` |
| Usage labels | Usage card | `blocks` / `events` | `overview.usage.blocks` / `overview.usage.events` |
| Activity meta | Activity card footnote | `snapshot {overviewStats.snapshotRelative}` | `overview.activity.snapshot` |
| Insights tabs | `insightViewDefs` | `评分构成` / `结构任务 {x}/{y}` / `TODO {n}` | `insights.tabs.score` / `insights.tabs.tasks` / `insights.tabs.todos` |
| Insights empty | Score & todo placeholders | `暂无可用的得分拆解。` / `暂无提升的 Todo...` | `insights.score.empty` / `insights.todos.empty` |
| Promoted todo meta | `todoPreviewItem` | `写点什么...` / `Block {id}` | `insights.todos.placeholder` / `insights.todos.blockLabel` |
| Toast: Todo update fail | `handleTogglePromotedTodo` | `更新 Todo 失败，请稍后重试` | `toast.todo.updateFailed` |
| Toast: autosave hint | `handleGlobalSave` | `编辑器会自动保存更改` | `toast.autosave.info` |
| Loading/error shell | `page.tsx` fallback | `加载中...` / `无法加载书籍` / `返回` | `shell.loading` / `shell.error.title` / `shell.error.back` |
| Prompt adjust bonus | `handleAdjustBonus` | `人工评估（-5～+5）：` / `请输入 -5～+5 的整数` / `已应用额外分数` | `dialogs.opsBonus.prompt` / `dialogs.opsBonus.invalidRange` / `toast.opsBonus.applied` |
| Metrics CTA | `handleAdjustBonus` error toasts | `应用失败，请稍后重试` | `toast.generic.retryLater` |
| Overview empty tokens | `overviewStats` placeholder `—` / `尚未生成成熟度快照` / `暂无事件` | `shared.emDash` / `overview.snapshot.none` / `overview.activity.none` |
| Block tab shell | `BookEditorRoot` states | `缺少 bookId...` / `加载块列表中…` / `加载块失败` | `editor.shell.missingBook` / `editor.shell.loading` / `editor.shell.error` |
| Block toolbar button | `BlockToolbar` | aria-label `添加块` | `editor.toolbar.addBlock.aria` |
| InlineCreateBar | CTA/Loading | `写点什么…` / `创建中…` | `editor.inlineCreate.placeholder` / `editor.inlineCreate.loading` |
| Empty state | `BlockList` empty view | `暂时没有内容` / `点击下方的输入条开始记录第一段内容` | `editor.empty.title` / `editor.empty.hint` |
| Save badge | `SaveStatusBadge` | `保存中…` / `保存失败` | `editor.save.saving` / `editor.save.error` |
| Quick insert groups | `quickInsertGroups.ts` | `常用 · Lists` / `结构 · Blocks` / `更多块` | `editor.quickMenu.groups.favorites` / `...structure` / `...more` |
| Quick insert metadata | `QuickInsertMenu` / `SlashMenu` | `覆盖当前` / `插入新块` | `editor.quickMenu.meta.transform` / `editor.quickMenu.meta.insert` |
| Quick insert actions | `model/quickActions.ts` | `Todo`, `Bullet List`, `Callout`, hints `重点提示` | `editor.commands.todo.label` / `.hint` 等 |
| Slash toggle | `SlashMenu` label wrappers | inherits QuickMenu group titles/hints | (沿用 `editor.quickMenu.*`) |
| BlockItem toasts | `showToast` usage | `更新 Todo 失败` / `创建块失败` / `删除块失败` / `变更块类型失败` 等 console | `editor.toast.todoUpdateFailed` / `editor.toast.createFailed` / ... |
| Delete guard logs | `requestDelete` | (console only) – 可留英文 | — |
| Markdown shortcuts | `BlockItem` log `[shortcut]` | Debug only | `debug.blockEditor.shortcut` (可选) |
| Todo preview label | `todoPreviewMeta` | `Block {id}` | `insights.todos.sourceBlock` |
| BlockList aria | List display `aria-label='有序列表'` / placeholders `暂无列表内容，点击编辑添加` | `editor.list.aria.ordered` / `editor.list.empty` |
| List markers | `ListDisplay` placeholder `LIST_PLACEHOLDER` | `editor.list.placeholder` |
| Paragraph placeholders | `ParagraphEditor` derived `'标题'` / `'写点什么…'` | `editor.paragraph.headingPlaceholder` / `editor.paragraph.defaultPlaceholder` |
| Todo list placeholder | `TodoListBlock` `TODO_PLACEHOLDER` | `editor.todo.placeholder` |
| Autosave banner | (待实现) hooking to `SaveStatusBadge` & global hotkey toast | `books.blocks.autosave.*` |
| Timeline header | `ChronicleTimelineList` title/subtitle defaults | `时间线` / `最近的书籍生命周期事件` | `timeline.title` / `timeline.subtitle` |
| Timeline toggle | `显示访问日志` | `timeline.toggle.visits` |
| Timeline loading/empty/error | `加载时间线…` / `无法加载时间线。` / `暂无事件…` | `timeline.state.loading` / `timeline.state.error` / `timeline.state.empty` |
| Timeline actions | `Button` label `重试` / infinite scroll `加载更多` (在文件后段) | `timeline.actions.retry` / `timeline.actions.loadMore` |
| Timeline event labels | `BASE_LABELS` map & stage change strings | e.g. `创建书籍`, `成熟度阶段晋级` | `timeline.events.bookCreated` 等 |
| Timeline summaries | `summarizePayload` texts (`从 {from} → {to}` etc) | 需拆 key + 插值 | `timeline.summary.bookMoved`, etc |
| Timeline actor | `操作者 {id}` | `timeline.actorLabel` |
| Toggle visits state copy | `showVisits` bool: copies string? only toggle label; need also `aria` | `timeline.toggle.aria` |
| Buttons/back link | Book error `返回` button | `shell.error.back` |

## 备注
- 所有 key 归入 `books.blocks.*`，若与书籍详情共享可用 `books.detail.*` 协调。
- Timeline 属于 Chronicle 模块，但在 Block 页嵌入，依旧挂在 `books.blocks.timeline.*`，Chronicle 模块可暴露 `useTimelineCopy(lang)` 复用。
- Autosave/Toast 顶层建议统一使用 `editor.toast.*`、`editor.banner.*` 子树，避免分散。
- 后续将添加 `assertSameShape(en.books.blocks, zh.books.blocks)` 的单测，防止 key 漏填。