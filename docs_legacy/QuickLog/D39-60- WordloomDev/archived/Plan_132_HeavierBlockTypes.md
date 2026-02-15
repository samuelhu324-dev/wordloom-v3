现在这块已经干净顺手了 👍 下一步就是：在不破坏这份干净感的前提下，把「Todo / Callout / 引用 / 窗格图」这些重一点的块插进去。
我先说整体思路，再给你一套“键盘入口 + 鼠标入口”的方案，你可以直接丢给 Copilot 实现。

0. 总体原则：少造新块，多“变形”
先定一个玩法，否则会很乱：


默认新建的永远是 paragraph block（你现在就是这样）；


Todo / Callout / 引用 / 窗格图：


优先用「把当前空段落 变形 成某种块」


而不是一直插“额外一行空块”。




比如：


光标在一条空段落 → /todo → 这条段落直接变成 Todo；


光标在一条空段落 → /callout → 这条段落直接变成 Callout 壳 + 内部文本编辑。


这样：


视觉上还能保持你现在这种“连续流文档”；


不会堆一堆空白行；


代码层面只要一个 changeBlockKind(blockId, newKind) 命令。



1. 键盘入口：Slash 菜单（主要入口）
定位：重度键盘用户 + 保持界面干净。
触发规则可以做成 Notion 那一套简化版：
触发时机


光标在一个 block 的开头，且这个 block 的 text 目前为空；


用户输入 / 时打开“插入/变形菜单”。


function onKeyDown(e: KeyboardEvent<HTMLDivElement>) {
  if (e.key === "/" && isCaretAtBlockStart() && isBlockEmpty()) {
    e.preventDefault();
    openSlashMenu({ blockId, anchorRect: getCaretRect() });
  }
}

菜单内容示例


Todo：/todo


Callout：/callout


引用：/quote


窗格图：/panel 或 /figure


表现上就是一个小的浮层列表：
Todo        [ ] 任务清单
Callout     重点提示
Quote       引用
Panel       窗格图 / 图文块

选择后的行为


对文本块类（todo / callout / quote）：


不新建 block，直接 changeBlockKind(blockId, newKind)


保留当前文本（如果用户 already 打了几个字，就一起迁过去）




对独立块类（panel / 图片图块）：


当前 paragraph 仍然存在；


在当前 block 下面 插入一个新的 panel block（或者允许“替换当前段落”作为可选选项）。





2. 鼠标入口：行左侧的「+」按钮（轻量版）
你之前那条“横线 + 中间一个加号”的方法太占空间，现在可以换成更隐蔽的版本：
规则


当鼠标 hover 在某个 block 上时，在这行左边显示一个小小的 +（和一个拖拽把手也可以）；


点击 + 打开和 Slash 菜单同一套数据源的小弹层；


光标不在的时候，这个 + 是完全隐藏的。


<div className="block-root" onMouseEnter={() => setHover(true)} ...>
  {hover && (
    <button className="block-add-btn" onClick={openMenu} />
  )}
  <InlineEditor ... />
</div>

CSS 大概是：
.block-root {
  position: relative;
}
.block-add-btn {
  position: absolute;
  left: -24px;
  top: 4px;
  opacity: 0.4;
}
.block-root:not(:hover) .block-add-btn {
  display: none;
}

行为逻辑：


如果当前块是空 paragraph → 视为“变形”当前块；


如果当前块有内容 → 在下面插入一个新 block，并根据选项设置 kind。


好处：


鼠标用户不用记 /；


界面平时是干净的，没有工具栏，只有 hover 时才略微出现一个 +。



3. 各种块的 UI & 数据模型建议
你已经有 paragraph 了，其他三个推荐这样做：
3.1 TodoBlock
数据：
type BlockKind = "paragraph" | "todo" | "callout" | "quote" | "panel";

interface TodoBlock extends BaseBlock {
  kind: "todo";
  done: boolean;
}

渲染：
<TodoShell>
  <Checkbox checked={block.done} onChange={toggle} />
  <InlineEditor ... />
</TodoShell>



Checkbox 点击时只改 done，不影响 block 文本；


仍然是同一个 InlineEditor 负责文本内容。


3.2 CalloutBlock
数据：
interface CalloutBlock extends BaseBlock {
  kind: "callout";
  tone: "info" | "warning" | "success"; // 先支持一种也行
}

UI：


左侧一条色线 + 浅色背景：


内部还是 InlineEditor。


<div className={`callout callout-${block.tone}`}>
  <Icon ... />
  <InlineEditor ... />
</div>

3.3 QuoteBlock
最简单：
<div className="quote-block">
  <InlineEditor ... />
</div>

CSS：左边灰线，字体稍微斜一点、颜色淡一点即可。
3.4 PanelBlock（窗格图）
这个可以当「重型块」：
数据：
interface PanelBlock extends BaseBlock {
  kind: "panel";
  layout: "one-column" | "two-column";
  // imageUrl / caption / etc.
}

UI：


直接渲染成一个卡片，可以是：


左图右文，或


上图下说明文字的容器；




内部可以包含一个 InlineEditor 做说明文字。


插入方式：


通常不要在空 paragraph 里“变形”，


而是在当前块下方插一个 panel，然后把光标聚焦到 panel 的说明文字区域。



4. 命令层：给 Copilot 的指令模型
为了不让逻辑散在各处，可以在前端也模拟一层“命令”：
type BlockCommand =
  | { type: "changeKind"; blockId: string; newKind: BlockKind }
  | { type: "insertAfter"; afterId: string; kind: BlockKind }
  | { type: "toggleTodoDone"; blockId: string }
  | { type: "updateText"; blockId: string; text: string };

InlineEditor / SlashMenu / “+” 按钮都只需要 dispatch 这些 command，
真正修改 state 的地方只有一个 reducer / hook。
给 Copilot 可以这么说：



Add a changeBlockKind(blockId, newKind) helper that updates the kind (and initializes block-specific fields like done or tone).


Implement a slash-menu that is triggered when the user types "/" at the start of an empty paragraph block; choosing an item either transforms the current block (for todo/callout/quote) or inserts a new block below (for panel).


Implement a small "+" button shown on hover at the left side of each block; clicking it opens the same menu as slash.


Todo/callout/quote re-use the same InlineEditor component; only their outer shell changes.


Panel block is rendered as a dedicated component with its own layout; inserted as a separate block below the current one.




5. 视觉上的小建议


Slash 菜单尽量窄一点，贴着光标位置，不要占整行；


+ 按钮颜色尽量淡（#d0d0d0），hover 时稍微变深，不要红不蓝显眼；


引用 / Callout / Panel，要保证编辑态和只读态 DOM 差异尽量小，延续你现在“不抖”的特性。



总结下你可以当 checklist 用的：


当前空段落 / → Slash 菜单 → 变形 block；


Hover 在 block 左侧出现 + → 点开即是同一个菜单；


Todo/Callout/Quote 共享 InlineEditor，只换壳；


Panel 单独组件，从 Slash / + 插在当前 block 下方。


做到这几条，你的界面还能保持现在这种“干净一片白”，
但功能上已经是一个小 Notion 了。
