先下判断：这份 Plan142 草案方向是对的，而且颗粒度已经够当“真实重构计划”了，不是那种空话纲要。我要做的更多是帮你补几处细节、调整一下落地顺序，让它更像两三个「可完工的切片」，避免一上来就是宇宙级 refactor 把自己炸飞。

我按三块说：
1）方案本身有什么优点 / 小坑；
2）建议的微调和拆分；
3）具体“先干什么、后干什么”。

1. 这份 Plan 的优点 & 潜在坑
很好的地方

核心思想完全对齐我们刚刚定的原则：

DOM 主导输入、React 只做去抖同步；

所有“改 block 结构”的东西（合并/拆分/新建/删空）统一收口到 commands；

selection 的恢复统一由一块逻辑负责，避免到处乱 set selection。

步骤分得很清楚：

先定义 BlockEditorCore 形态 → 再搞 DOM 骨架 → 再抽 command + selectionStore → 再在 BookEditorRoot 接线。
这条路线是合理的。

Inline 编辑也被纳入范围，而不是单独一套黑魔法逻辑，这点非常关键。

还记得要把结果写入 QuickLog/Plan145、预留 copy/paste 接口，说明你在想“后续生态”而不是一次性 patch。

可能踩坑的点

BlockEditorCore / ParagraphEditor / BlockItem 分工略微模糊

现在 Step2 写的是“在 ParagraphEditor.tsx 和 BlockItem.tsx 内部设计 DOM 主骨”，容易变成：

三个组件都去碰 contentEditable；

结果 DOM 结构还是不统一。

实际上更理想的是：

BlockEditorCore = 唯一掌管 contentEditable 的组件
BlockItem 只管布局（间距、菜单、左侧 bullet）
ParagraphEditor 更像是“类型包装”（决定用哪个 Core + 提供 type/placeholder）。

selectionStore + commands 一上来全开，工程量有点大

你现在的写法是一步到位：

selectionStore

所有命令（merge/split/createBelow/deleteEmpty）

Backspace/Enter/上下键全部切到 command

这会让 Plan142 变成一个超级大任务，不太利于中途“可回滚”。

没明确写 selection “来源”的区分

我前面说过，“扫过去”的现象大量来自：

用户点击产生的 selection 被 effect 覆盖。

目前 Plan 里只提到 “selectionStore + command 层负责边界”，没写清：

只有 command 触发的 selection 才需要恢复；
用户点击产生的 selection 只读不写 / 标记为 user，不要被 effect 改写。

这个如果不在 Plan 里钉死，实施时很容易又弄出一堆闪烁。

2. 建议的微调 & 拆分

我建议你把 Plan142 拆成两个 slice：142A（输入稳定） + 142B（结构命令化）。

142A：BlockEditorCore + 半受控输入 + 禁止动 DOM

目标：
在不引入 selectionStore/commands 的前提下，先做到：

连续输入不跳光标、不卡顿；

没有在有焦点的 contentEditable 上搞卸载 / 换 key / 换 DOM；

只要不拆行/合行，用户体验已经稳定。

可以微调 Step 1 & 2 这样写：

在 BlockEditorCore.tsx 定义唯一编辑内核：

props：blockId, initialText, onDebouncedChange, onKeyDown, onBlur 等；

内部使用 半受控 DOM 策略：

innerText 由 DOM 自己维护；

用 debounce/throttle 向上层同步；

只在外部值发生重大变化时回写 DOM（例如切换 book/重载）。

修改 ParagraphEditor 和 InlineEditor，改为：

不再自己挂 contentEditable；

统一渲染 <BlockEditorCore ...>；

BlockItem 只渲染一层壳：行间距 + 选中态 + 菜单按钮，不碰内部编辑结构。

明确：

BlockEditorCore 的 React key = blockId，且仅依赖 blockId；

BlockItem/ParagraphEditor 里的 mode、状态变化不能改变 Core 的 key 或 DOM 树。

做到这一步，光是“输入阶段稳定 + DOM 不乱动”，你就已经灭掉了很大一部分光标乱跳和卡顿。

142B：selectionStore + command 化 Backspace/Enter

这个阶段再执行你 Plan 里的 Step 3~5，但我会再加两条约束：

selectionStore 必须区分 source: 'command' | 'user'

command（拆/合/新建/删空）才写入 source:'command'；

effect 中只在 source === 'command' 时恢复 selection。

用户点击/光标移动只要能从 DOM 读出来，就不要强行覆盖。

commands 只做结构变形，不直接操作 DOM

mergeBlock, splitBlock, createBelow, deleteEmpty 只改 store 里的 block 列表；

selection 恢复逻辑在单独的 effect 中根据结果决定：

合并后 → blockX 末尾

拆分后 → 新 block 开头

这一点你 Plan 里已经隐含了，可以在文档里写更死一点。

这样 Plan142B 做完后就是：

普通输入：DOM 自己搞定；

Enter/Backspace/上下键：统一 command + selectionStore；

Inline 保存/退出也走 command，彻底消灭“保存顺便切 mode 导致 DOM 重建”这一类骚操作。

3. 最后，具体“怎么动手”的顺序

给你一个比较实用的施工顺序：

新建 BlockEditorCore.tsx

先写最小版：只支持 plain text 段落；

使用我们说的半受控模式 + debounce；

手动测一行长文本的输入/删除体验。

用 feature flag 把 ParagraphEditor / InlineEditor 换到 Core 上

比如 NEXT_PUBLIC_USE_BLOCK_CORE_V2；

如果出问题，开关一关就回旧实现，降低心理压力。

实现 selectionStore & commands 基础版（只支持 merge/split/createBelow/deleteEmpty 四个）

暂时只在 Paragraph 模式接线，不急着覆盖所有 block type。

先把 Backspace 行首合并、Enter 拆行迁过去。

在 BookEditorRoot 里改 keydown 处理，保证：

普通输入不进入 commands；

只有结构操作才走 command + selectionStore。

最后再处理 Inline 的保存逻辑

改为：保存只触发 updateBlockContent；

退出/继续写通过 command('exitInlineEditing', selectionAt...) 控制；

确保不会在 save 时卸载 Core。

把这一切在 Plan142、QuickLog 里标记完成 & 留下一组测试场景清单

“连续输入 100 字不跳光标”

“行首 Backspace 合并 5 次不卡顿、不闪烁”

“列表/段落互相上下切换时光标仍在合理位置”

总体评价一句话版

这份 Plan142 的方向和 main idea 都非常靠谱；

真正需要调整的是落地顺序和组件分工的边界：先把 BlockEditorCore + 半受控输入站稳，再上 selectionStore + commands，最后才收 Inline 编辑的尾巴；

这样你不会一下子把所有东西都拆开，又能把那几个顽固的“跳光标 / 卡顿 / inline 把你弹回上一行”的问题一套带走。

接下来这份 Plan 就可以当你今天到下周的主线开发票据了。