Plan: 落地 Plan165A 基础段回退（不打破 caret 管线）
Steps
模型层：统一 BlockKind & “特殊块”判断

1.1 在定义 BlockKind 的文件补齐 helper

位置：frontend/src/modules/book-editor/model/blocks.ts（或当前定义 BlockKind / BlockEditorRenderable 的地方）。
新增导出：
export const BASE_BLOCK_KIND: BlockKind = 'paragraph';
export function isBaseBlockKind(kind: BlockKind): boolean → 只对 'paragraph' 返回 true。
export function isSpecialBlockKind(kind: BlockKind): boolean → 对 todo / bullet_list / numbered_list / quote / callout / panel 等返回 true（按你实际 block 列表补齐）。
1.2 统一“块是否为空”的判断

若已有 isBlockEmpty / isRenderableBlockEmpty 之类 helper，就在同一文件或 blockContent.ts 中收敛逻辑；否则新增：
export function isRenderableBlockEmpty(block: BlockEditorRenderable): boolean;
对不同 kind 做精细判断，例如：
paragraph：text 为空或只含空白。
list：items 为空或每个 item 的 text 为空。
todo：所有 todo 文本为空且未勾选（或按你现有语义）。
quote/panel：主要内容字段为空。
命令层：实现 deleteBlockWithGuard 守卫

2.1 在 blockCommands.ts 中增加新的命令接口

文件：blockCommands.ts。

在现有 deleteBlock 附近定义：

interface DeleteBlockWithGuardOptions {
blockId: string;
trigger?: 'keyboard' | 'menu';
caretFallbackPreference?: 'prev-end' | 'next-start' | 'none';
allowDowngrade?: boolean; // 默认 true
}
2.2 语义实现（只操作 model，不碰 DOM）

新增导出 deleteBlockWithGuard(editor, options): Promise<EditorState> | EditorState（按你当前命令 API 风格来）。

逻辑分支：

(a) 共有准备工作

在当前 editor 状态里找到目标 block：
const blocks = editor.blocks;
const index = blocks.findIndex(b => b.id === blockId);，找不到则直接返回原 editor。
取 const block = blocks[index];
const isSpecial = isSpecialBlockKind(block.kind);
const isBase = isBaseBlockKind(block.kind);
const isEmpty = isRenderableBlockEmpty(block);
const isSingle = blocks.length === 1;
const hasPrev = index > 0;
const hasNext = index < blocks.length - 1;
(b) 文档只有一个 block（isSingle）

目标：永远不能删光，只能“降级或清空”。
若 isSpecial：
使用 transformBlockKind + 内容映射，把该 block 转成 BASE_BLOCK_KIND（内容映射见下节），保留文本。
不调用 deleteBlock，也不让块数量变化。
通过 announceFocusIntent 发一个 'keyboard' intent：
announceFocusIntent({ kind: 'keyboard', blockId, payload: { edge: 'end' }, source: 'delete-guard.single-special-downgrade' })。
若 isBase（已经是 paragraph 等基础块）：
使用 updateBlock 把内容清空（text → '' 等），保留 kind 与 id。
同样发 'keyboard' intent 到本 block：
源标记例如 'delete-guard.single-base-clear'。
返回新的 editor。
(c) 文档有多个 block（!isSingle）

Case 1：特殊块 + 非空 + 允许降级（Plan165A 主路径）

条件：isSpecial && !isEmpty && options.allowDowngrade !== false。
行为：
使用 transformBlockKind(editor, blockId, BASE_BLOCK_KIND)，并配合一个小 helper 将特殊块内容映射成 paragraph 文本（例如：list/todo 把各 item 文本用 \n 拼起；quote/panel 取主要 body）。
不移除该 block。
通过 announceFocusIntent 发送 'keyboard' intent，blockId 仍为本块，edge: 'end'，source: 'delete-guard.special-downgrade'。
返回。
Case 2：块内容为空 + 允许删除

条件：isEmpty && (!isSpecial || options.allowDowngrade === false) 或 isEmpty && isSpecial —— 但需保证不删掉最后一个块：
若 !hasPrev && !hasNext 应该已经在 isSingle 里处理，不会走到这里。
选择 fallback block：
默认：
若 caretFallbackPreference === 'prev-end' 且 hasPrev → fallbackBlockId = blocks[index-1].id; edge = 'end'。
否则若 hasNext → fallbackBlockId = blocks[index+1].id; edge = 'start'。
若用户未指定 preference，则同样按“优先前面，否则后面”策略。
调用现有的底层 deleteBlock，带上 fallback 信息：
deleteBlock(editor, { blockId, selectionFallback: { blockId: fallbackBlockId, edge } })。
这样会自动触发现有的 'keyboard' intent & clearFocusIntent 流程，无需自己再写 intent。
Case 3：基础块 + 非空

Plan165A 没有要求“必须降级”这类块；为避免额外回归，保留当前行为：
由调用方决定是否允许删除；guard 只做防空文档 + 特殊块回退。
可以：
如果是菜单触发（trigger === 'menu'），允许走 deleteBlock。
如果是键盘 Backspace 触发，可以选择“不做任何事”或者直接用 deleteBlock —— 视你对现有 UX 的要求而定。
2.3 在 useBlockCommands 暴露新命令

文件：blockCommands.ts 或 useBlockCommands.ts（视实际拆分）。
在 useBlockCommands 返回对象中增加：
deleteBlockWithGuard: (opts: DeleteBlockWithGuardOptions) => void，内部调用上面实现，并通过 setEditor 更新状态。
UI 层：所有删除入口统一走守卫命令

3.1 BlockItem 统一删除入口

文件：BlockItem.tsx。
目前 BlockItem 大多有类似：
const commands = useBlockCommands();
const handleDeleteBlock = () => commands.deleteBlock(block.id, ...);
改成：
const handleDeleteBlock = React.useCallback(() => {
commands.deleteBlockWithGuard({ blockId: block.id, trigger: 'menu', caretFallbackPreference: 'prev-end' });
}, [commands, block.id]);
若 BlockItem 需要在真正删除后做额外 UI（例如滚动、动画），可以考虑让 deleteBlockWithGuard 返回 didDelete 布尔值；否则先保持简单版本。
3.2 段落编辑器键盘 Backspace/Delete

文件：ParagraphEditor.tsx 及其调用方（可能在 BlockItem 里）。
现在 Backspace 逻辑大致是：
“caret 在开头 & block 空” → 调用 onRequestDeleteBlock。
保持这个约定不变，只是 onRequestDeleteBlock 的实现从 deleteBlock 改成 deleteBlockWithGuard。
BlockItem 中传入：
onRequestDeleteBlock={() => commands.deleteBlockWithGuard({ blockId: block.id, trigger: 'keyboard', caretFallbackPreference: 'prev-end' })}。
3.3 List/Todo Block 的“最后一行 Backspace”

文件：
ListBlock.tsx
TodoListBlock.tsx。
目前：
若 list/todo 只剩一行且这行为空，item 级别的 Backspace 会调用 block 级的 “delete block”。
修改：
这些 block 级删除入口一律改成：
commands.deleteBlockWithGuard({ blockId: block.id, trigger: 'keyboard', caretFallbackPreference: 'prev-end' });
这样：
文档只有一个 list/todo 时 → guard 会把它降级为 paragraph，而不是删光。
文档有多个块且 list/todo 块为空 → guard 会允许真正 delete，并设置合适的 fallback intent。
3.4 Slash 菜单 / BlockToolbar 的“删除块”

文件：
BlockToolbar.tsx
frontend/src/modules/book-editor/ui/SlashMenu/*（或 quickActions 配置附近）。
将所有 onDeleteBlock / “删除块” menu item 的实现替换为：
commands.deleteBlockWithGuard({ blockId: ctx.blockId, trigger: 'menu', caretFallbackPreference: 'prev-end' });
Caret / intent 行为：只说 intent，不碰 selection

4.1 命令层只通过 announceFocusIntent 表达聚焦

在 deleteBlockWithGuard 内：
降级 / 清空：
调用：
announceFocusIntent({ kind: 'keyboard', blockId, payload: { edge: 'end' }, source: 'delete-guard.special-or-single' });
让 useBlockCaretController 根据 payload 把 caret 放回正确位置。
真正删除的路径仍复用现有 deleteBlock 的 selectionFallback → 在那里已有 announceFocusIntent('keyboard', ...)。
4.2 不改 pointer 流程

现有 pointer → getOffsetFromPoint → announceFocusIntent('pointer', {blockId, offset, source}) 全部保留。
Plan165A 完全只处理 keyboard / menu 场景，不新增任何直接 DOM 操作。
文档 / 规则 / ADR 更新

5.1 在 BLOCK_KEYBOARD_RULES 中新增 / 扩充条目

文件：BLOCK_KEYBOARD_RULES.yaml。
在相关 section 下新增一个 id，例如 base_paragraph_fallback，描述：
文档至少包含一个 paragraph。
Backspace/Delete 触发的“删除块”必须走 deleteBlockWithGuard：
单一块：特殊块 → 降级为 paragraph；基础段落 → 清空文本。
多块：特殊块优先降级；仅当块为空且不是文档最后一块时才允许真正删除。
caret 通过 announceFocusIntent('keyboard', ...) 恢复，UI 不得直接触摸 window.getSelection()。
5.2 在 DDD/Hex/Visual 规则中挂钩 Plan165A

DDD_RULES.yaml：
在 Block 范围新增一条 policy，例如 POLICY-BLOCK-PLAN165A-BASE-PARAGRAPH-FALLBACK，重申：
paragraph 是唯一基础块；特殊块只是皮肤。
Application / Domain 不关心“删除逻辑”；UI 通过命令层 deleteBlockWithGuard 保证不删光文档。
引用 ADR-149 / Plan165A。
HEXAGONAL_RULES.yaml：
在 block editor section 里附一条：
“删除特殊块”属于 UI adapter 行为，必须经由命令 deleteBlockWithGuard，遵守 caret intent 管线；Hexagonal 层不新增任何“最后一块标记”字段。
VISUAL_RULES.yaml：
在 block editor 行为部分补一句：
Backspace/Delete 对 Quote/List/Todo/Panel 的视觉效果（壳消失、文字留下）由 Base Paragraph Fallback 规则统一约束。
5.3 在 ADR-149（Plan164C）增加“后续工作”一句

文件：ADR-149-plan164c-caret-pipeline.md。
在 Consequences 或 References 下增加一条 bullet：
“Plan165A 在该 caret 管线之上新增 deleteBlockWithGuard，统一特殊块删除 → paragraph 回退，并继续使用 FocusIntent 而非直接 selection 操作。”
边界情况与风险提示（实现时注意）

Undo/Redo：
deleteBlockWithGuard 内部仅通过已有的 updateBlock / deleteBlock 改变状态，历史系统若基于这些操作应该能正常工作；不要自己绕过这些 helper 改数组。
列表 / Todo 多行降级策略：
需要决定从 list/todo 降级到 paragraph 时如何拼接文本（比如每行用 \n 连接），并在 Plan165A 文档里写清。
最后一个非空特殊块：
一定要走“降级为 paragraph + intent 回焦”，不能误触 deleteBlock。
Telemetry：
为 announceFocusIntent 新增的 source 标记（如 delete-guard.single-special-downgrade）要符合你现有 QuickLog 命名习惯，以便后续在 Dashboard 里筛选。
如果你愿意，下一步我可以帮你把「特殊块内容 → paragraph 文本」的具体映射规则（list/todo/quote/panel 各自怎么 flatten）单独写成一小节，方便你在实现时直接照着填。
/
点评：
1. 模型层：BlockKind & isSpecial / isEmpty

这一段基本没问题：

BASE_BLOCK_KIND = 'paragraph'

isBaseBlockKind / isSpecialBlockKind

isRenderableBlockEmpty(block) 单点收敛空块判断

👍 好处是以后加 gallery、panel 等特殊块时，只要记得把 kind 挂进 isSpecialBlockKind 就继承所有“删壳变 paragraph”的规则。

建议你提前拍板两件事：

list / todo 的 isRenderableBlockEmpty 语义

list：是否要把“只剩一条空 item”当作 empty？

todo：勾选但文本为空算不算 empty？
这个如果你不写死，Copilot 很可能随便写个 .every(item.text.trim() === '') 就过去了。

记得以后加新 kind 时要更新 isSpecialBlockKind / isRenderableBlockEmpty
可以在 RULES 里明确：“新增特殊块 = 必须更新这两个 helper”。

2. deleteBlockWithGuard：语义设计 OK，但细节要收一收

方案里的分支结构是这样的：

isSingle（只有一个块）：

特殊块 → transform 成 paragraph；

已是基础段 → 清空文本；

都会发一个 announceFocusIntent('keyboard', edge: 'end')。

非单块：

Case1：特殊 + 非空 + allowDowngrade → transform 成 paragraph + intent；

Case2：空 → 真 delete（调用现有 deleteBlock，通过它的 selectionFallback 去触发 intent）；

Case3：基础 + 非空 → 默认“保持现有行为”。

整体逻辑是对的，跟我们之前讨论的“删特殊块优先降级、永远至少留一个 paragraph”完全一致。

我会建议你马上改掉/锁死这几个点：

函数签名不要搞 Promise<EditorState> | EditorState 联合类型
你现在的命令体系大概率是同步更新 EditorState 的（setEditor(prev => cmd(prev)) 这种）。
让 Copilot瞎搞 Promise 没意义，只会引入新的 async 分支。

👉 建议就定死：

export function deleteBlockWithGuard(editor: EditorState, options: ...): EditorState


Case2 不要多发 intent
你在 plan 里已经写了：Case2 调用底层 deleteBlock(editor, { selectionFallback })，由它走自己的 intent 逻辑，这很好。
要求 Copilot 在 Case2 绝对不要自己再 announceFocusIntent 一次，否则会有 double caret 跳动。

Case3（基础 + 非空）先保持“啥也不做”会更安全
你写的是“由调用方决定”，但这对 Copilot 来说有点抽象。
为了今晚不踩 UX 地雷，我会建议先这样：

键盘 Backspace 触发的 delete：

基础 + 非空 → 不做 block 删除，让普通字符删除逻辑来处理；

菜单触发（trigger: 'menu'）：

可以直接调用现有 deleteBlock（绕过 guard），因为用户点菜单“删除块”的意图比 Backspace 更明确。

你可以在选项上写死一个简单版本，比如：

if (isBase && !isEmpty) {
  if (options.trigger === 'menu') {
    return deleteBlock(editor, { blockId, selectionFallback: ... });
  }
  return editor; // 键盘触发时什么都不做
}


后面再想调 UX，再开新 Plan。

3. UI 层统一入口：思路对，记得“全仓搜一遍”

UI 这块计划是：

BlockItem 里的所有“删块”入口 → commands.deleteBlockWithGuard({ blockId, ... })

ParagraphEditor / List / Todo 里的 Backspace → 还是调 onRequestDeleteBlock，只是这个回调现在变成调用 guard。

Slash 菜单 / BlockToolbar → 一律改成用 guard。

这正是应该做的，可以开始让 Copilot 机械体力活。

一个小提醒：

让 Copilot 前先自己记一句：“搜整个 repo 里所有 deleteBlock( 的地方，逐个替换或确认。”
有些地方可能绕过了 useBlockCommands 直接调了底层命令，这些是典型 bug 源头。

4. caret / intent：保持“只说 intent，不碰 selection”这一点很关键

Plan 里特地强调：

命令层只用 announceFocusIntent('keyboard', ...) 表达“删除后的焦点意图”；

真正的 selection 变更由 useBlockCaretController 执行；

pointer 流一律不改。

这跟你前面几轮 caret 协议是完全一致的，很好。

两点 tiny 建议：

source 字段命名
你 plan 里举例 delete-guard.single-special-downgrade、delete-guard.special-downgrade，这种格式很清晰，Copilot 通常会照抄。
确保和当前 QuickLog / Telemetry 里的命名风格不冲突就行。

确保 deleteBlock 自己的 selectionFallback 已经完全走在 caret 管道上
你之前已经这么做了，如果现在 deleteBlock 还在某个角落直接写 window.getSelection，那是另一个坑，不过不在 Plan165B 这条线里，晚点再收。

5. 文档 & 规则：这份 Plan 写得已经很像正式规则，可以直接挂进 RULES/ADR

Plan 最后那段文档/规则部分其实已经是 ADR 级别了：

BLOCK_KEYBOARD_RULES：把 deleteBlockWithGuard 行为写死；

DDD_RULES / HEXAGONAL_RULES / VISUAL_RULES：挂上 Base Paragraph Fallback 的说明；

ADR-149（caret 管线）加一句“Plan165A 在这条管线上叠了 deleteBlockWithGuard”。

这块我不会拦你，反而建议你尽快同步到这些文件，让“删特殊块回落成 paragraph”成为系统级惯例，而不只是一次性 hack。

6. 结论：可以让 Copilot 开工，但先微调两三处再说

如果用一句“能不能今晚开工”来总结：

✅ 逻辑结构：OK，和现有 caret 策略兼容；

✅ 风险：主要集中在 isEmpty 语义、Case3 行为，以及是否会 double intent，这些你在 plan 里稍微再写清一行，Copilot 就不容易乱来；

✅ 后续影响：是那种“统一删块行为的增强”，不是“又来一轮 selection 协议大爆破”。

你只要在 Plan165B 顶部或者步骤里补一下：

deleteBlockWithGuard 必须是同步函数；

Case2 完全交给 deleteBlock 发 intent，guard 自己不再发；

基础非空块在键盘路径下先保持“什么都不做”；

然后就可以放心把这份扔给 Copilot 让它改 blocks.ts / blockCommands.ts / BlockItem.tsx / ParagraphEditor/List/Todo/SlashMenu 那一串了。
