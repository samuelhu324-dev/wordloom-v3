一、Plan128 里的关键骨架（按你这份文档的意图重述）

目标定位

Block 编辑器要变成一个有清晰边界的子系统：有统一入口、有内部分层、有插件点，而不是现在“到处塞点逻辑”。
所有改动都必须能在三份 RULES（DDD/HEXAGONAL/VISUAL）里找到依据或新增条目，避免“拍脑袋写 UI”。
分层骨架（从 Plan128 + 现有代码综合）

Adapter & Data 层（已存在，Plan128 只要求梳理）
frontend/src/features/block/api.ts / hooks.ts：负责 HTTP、DTO 正规化、BlockContent union。
职责：只讲“Block 列表 / 创建 / 更新 / 删除 / 重排”的端口，不知道编辑器 UI。
BlockEditor 模块层（Plan128 重点）
对外：BookBlocksEditor / BookEditorRoot 这种单一入口组件。
内部再切：BlockList（列表）、BlockItem（单块控制器）、*Display/*Editor（纯展示/编辑）、toolbar/inline menu（动作层）、keyboard（快捷键行为）、plugins（不同 kind 的渲染/编辑器注册）。
原则：只有极少数“控制器组件”（例如 BlockItem）可以碰 TanStack Query hooks，其余尽量纯函数/无副作用。
插件 / kind 扩展层
Plan77/83 已经定了：用 BlockKind → {Display, Editor, createDefaultContent} 的注册表。
Plan128 要求：后续 rich block、todo、callout 等，都走同一注册表，而不是在 switch 里胡加 case。
交互策略层
把 Enter/Backspace/Slash/Markdown 等键盘规则，收敛成可复用 helper（Plan126 已经部分落地，Plan128 是再系统化）。
Inline toolbar / 行间 + / 底部 CTA 等行为，不散落在 N 个组件里，而是走统一的“插入控制器”（BlockInsertController）。
二、与三份 RULES 的对齐检查（Plan128 视角）

HEXAGONAL_RULES.yaml
已有：block_editor_inline_decisions、block_renderer_plan77_adapter、block_renderer_plan83_adapter、block_insert_menu_plan85_adapter、block_editor_plan120_contract、block_editor_plan121_micro_editor_contract、block_editor_plan126_keyboard_contract。
Plan128 需要补充的点：
增加一个类似：block_editor_plan128_module_contract，强调：
BlockEditor 作为 UI 模块，只消费 features/block/api.ts 暴露的 UseCase 端口；
插件注册表位置（例如 frontend/src/features/block/ui/blockPlugins.ts）及职责；
“控制器组件有限集”（BlockList/BlockItem/BookEditorRoot）可以持有 hooks，其它 Editor/Display 组件必须是纯 UI。
VISUAL_RULES.yaml
已有：block_editor_plan77_v1、block_editor_plan120_refinement、block_editor_plan121_micro_editor、block_editor_plan126_keyboard_visuals、block_insert_menu_plan85 等。
Plan128 需要补充的点：
一条 block_editor_plan128_visual_scaffolding：
定义 BlockEditor 模块的视觉骨架：纸张容器、Block 间距、toolbar 显隐策略、插件扩展的统一视觉规范（icon 大小、对齐、hover 动画）。
说明“kind 新增时必须在注册表里填 Label/描述/Icon，不得随便在某个页面单独画一套 UI”。
DDD_RULES.yaml
已有：POLICY-BLOCK-PLAN77-*、PLAN80/82、PLAN83/85、POLICY-BLOCK-PLAN120-UI-ONLY、POLICY-BLOCK-PLAN121-MICRO-EDITOR、POLICY-BLOCK-EDITOR-PLAN126-UI-ONLY 等。
Plan128 需要补充的点：
一条 POLICY-BLOCK-PLAN128-EDITOR-MODULE：
再次强调：BlockEditor 的模块划分与聚合边界——Domain 只看见 Block/Book/Chronicle；任何“编辑器内部状态（选中 block、toolbar 展开、Slash 菜单查询）”都禁止进入 DTO / UseCase 参数。
明确禁令：不得因为新插件（table、code 等）向 Domain 申请“editor_schema”一类字段；插件配置必须完全停留在前端或配置文件。
三、建议的实施计划清单（中文，尽量工程化且可执行）

我按“先搭骨架，再补 RULES”的顺序列，方便你直接拿去驱动实现/PR：

BlockEditor 模块物理结构重组

在 ui 或单独 modules/book-editor/ 下，建立统一入口：
BookEditorRoot.tsx（或 BookBlocksEditor.tsx）；
子目录：list/, item/, editor/, display/, toolbar/, plugins/, keyboard/。
把现在分散在 BlockList.tsx/BlockRenderer.tsx 里的“列表逻辑、编辑逻辑、toolbar 逻辑”拆回对应子模块，但公共导出仍是 BookEditorRoot。
插件注册表（Block kind → 组件/默认内容）

新建 blockPlugins.ts：
定义接口：BlockPlugin = { kind, Display, Editor, createDefaultContent }。
先注册 paragraph / heading / 已有的 todo_list / callout / quote / divider / image / image_gallery。
BlockRenderer 改为“查表渲染”而不是大 switch，为 Plan83 后续扩展铺路。
控制器边界收紧（hooks 只待在少数组件）

规定只有以下组件可以使用 TanStack Query hooks：
BookEditorRoot：取 bookId、调用 useBlocks(bookId)。
BlockItem：调用 useUpdateBlock / useDeleteBlock 等，把结果状态（saving/saved/error）通过 props 传给纯 UI 层。
其他组件（ParagraphEditor、HeadingEditor、InlineCreateBar、Toolbar）只收 props，不直接关心网络/缓存。
键盘行为集中化（Enter/Backspace/Slash/Markdown）

把 ParagraphEditor 里目前散落的键盘逻辑整理到一个 keyboard.ts 或 useBlockEditorKeyboard：
输入法组合保护：event.isComposing 时尽量不干预。
Enter：
行尾 Enter → 调用 onInsertBlockAfter('paragraph')；
非行尾 Enter → 暂时当作软换行（或留 TODO）；不可交给浏览器默认 insertParagraph。
Shift+Enter → 明确记录为“软换行”; 未来改成 <br> 时只改 helper。
Backspace 空块时的 delete/merge 行为 → 只在 UI 中完成合并再调用 Delete/UpdateUseCase。
对应在 VISUAL_RULES / HEXAGONAL_RULES 标明“键盘行为完全属于 UI-only”。
列表/工具条交互统一

为 Block toolbar 建一个统一组件 BlockToolbar.tsx：
只接受 (onInsertBelow, onOpenTimeline, onDelete) 三个回调；
实现所有 hover/opacity/布局细节；
保证所有 kind 看到的是同一套控件，而不是各自写一遍。
Inline 插入（+）与底部 CTA 统一通过 BlockInsertController 接口：
输入：锚点 blockId + position(before/after/append) + kind；
输出：调用父层传入的 onAddBlock(kind, options)。
保存策略与状态提示标准化

在 BlockItem 里实现：
本地 content 状态 + lastSavedContent 对比；
300ms debounce 保存；Blur 强制 flush；
保存状态枚举：idle/saving/saved/error，UI 用统一的小徽章/文案表现。
更新 VISUAL_RULES：
补充一条：Block 编辑器的保存状态视觉规范（位置、颜色、文案），避免以后有人随意在块内部加 Loader。
三份 RULES 的 Plan128 对应更新

HEXAGONAL_RULES.yaml：
新增 block_editor_plan128_module_contract：
记录模块分层、插件注册表位置、控制器组件名单；
强调“BlockEditor 只消费 block UseCase 端口，不反向依赖 Domain/Infra”。
VISUAL_RULES.yaml：
新增 block_editor_plan128_visual_scaffolding：
描述纸张容器、块间距、toolbar/inline menu 的统一视觉和显示条件；
说明新增 block kind 时需要补的视觉信息（icon/颜色/描述）。
DDD_RULES.yaml：
新增 POLICY-BLOCK-PLAN128-EDITOR-MODULE：
申明 BlockEditor 作为 UI 模块的边界；
禁止 Domain 暴露“编辑器配置/模式/状态”字段；
对未来新 Plan（rich text、table、code）规定：必须先通过插件和 RULES 解决，必要时再提新的 ADR。
后续迭代挂钩（在 Plan128 中先打 TODO）

在 keyboard.ts 里预留：
软换行实现点；
Slash 菜单 anchor/caret 计算抽象（未来可以从当前 ParagraphEditor 的实现迁移过去）。
在 blockPlugins.ts 标注：
rich block（code/table）的占位 config，但明确“暂不实现 Editor，只展示 placeholder”，防止 UI 崩盘。
如果你愿意，我下一步可以直接在 ui 里帮你写好第 2–4 步的具体骨架（blockPlugins.ts + BookEditorRoot.tsx + 重构 BlockRenderer 的查表逻辑），并草拟三份 RULES 中 Plan128 的新增条目草稿，方便你 review 后填正式中文文案。