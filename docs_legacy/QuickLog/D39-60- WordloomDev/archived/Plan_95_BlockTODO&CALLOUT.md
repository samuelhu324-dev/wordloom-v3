好，这俩终于要从“挂名干部”转正了😄
我给你分两块说：Block TODO 和 Callout，每块都讲：

设计目标（为什么要有它）

数据结构（方便你对表和 TS 调整）

交互 / UI 规则（Copilot 好下手）

跟 Book 概览怎么挂钩（尤其是 TODO）

最后给你一段「可以直接丢给 Copilot 的实现任务说明」。

一、Block TODO 设计
1. 这个 TODO 块在 Wordloom 里干什么？

定位：“嵌在正文里的小任务组”，而不是一个全局任务系统。

写日志 /案例分析时：中间随手记几条「要做的事」

Book 概览页：只汇总那些你觉得重要、勾选了「提升 / Promote」的条目

不做复杂 GTD，只做：勾选 + 可选的「提升」

所以 v1 先做到：

一个 Todo List block 里有多条 item

每条 item：勾选完成 / 未完成

每条 item 可以标记 isPromoted，这样出现在 Book Overview 的 TODO 区域

不要日期、优先级这些复杂字段，留到 v1.5 以后

2. 数据结构（示意）

假设你原来有一个 blocks 表 / 实体：

type BlockKind = 'paragraph' | 'heading' | 'todo_list' | 'callout' | 'divider';


可以加一个子结构（存在 JSON 字段里）：

type TodoItem = {
  id: string;          // 局部唯一即可
  text: string;
  isDone: boolean;
  isPromoted: boolean; // true 时会出现在 Book Overview 的 TODO 区
};

type Block = {
  id: string;
  bookId: string;
  kind: BlockKind;
  text: string;        // 对 todo_list 可以不重要，或者用来保存第一行标题
  todoItems?: TodoItem[]; // kind === 'todo_list' 时有值
  // ... 其他通用字段
};


数据库可以：

blocks.todo_items JSONB

以后需要更复杂再拆子表。

3. 前端交互 / UI 规则（TODO 块）

插入方式

在「插入块」菜单里点击「Todo 列表」

在当前光标位置插入一个空的 todo_list 块，默认有 1 条空 item

展示样式（块内部）

每条 item 一行：

左侧：方形复选框（未完成：空白边框；已完成：填色 + 勾）

中间：可编辑文本区域（contenteditable span 或 input）

右侧（可选 hover 时出现一个小按钮）：

「↑ 提升」图标（例如 lucide: ArrowUpRight）来切换 isPromoted

isDone === true 时：

文本浅色 + 加删除线

isPromoted === true 时：

右侧小标记点亮（比如一个小星星 / 小箭头高亮）

键盘行为

在某一条 todo 文本末尾：

Enter：在下面插入一个新的 todo item

如果文本为空且按 Backspace：删除这一条；如果是最后一条，可以让整个 block 变回普通段落或保持一个空项（看你现在的编辑策略）

4. 跟 Book 概览联动（TODO / Checklist 区）

概念：Book Overview 里的 TODO 面板 = 当前 Book 所有 Blocks 里被提升的 TodoItem 列表。

查询逻辑（伪代码）：

// 后端 / 前端任一处都行
const promotedTodos = blocks
  .filter(b => b.kind === 'todo_list')
  .flatMap(b => b.todoItems ?? [])
  .filter(item => item.isPromoted && !item.isDone);


展示逻辑：

每条显示：

文本

所在 block 的简短定位（可选，比如「第 3 块」「某个小标题下」）

点击：

可以跳到对应 Book 的「块编辑」页，并把该块滚动到视图中。

二、Callout Block 设计
1. 这个 Callout 用来干嘛？

定位：“在正文里用来高亮一小段说明 / 提示 / 风险”。
对应你 Book 概览里“风险 / 备注”一类内容，可以让读者 / 将来的你一眼看到重点。

v1 先做简单版：

只是样式上突出的一段话

有几种变体：info / warning / success / idea

每种变体对应一个图标 + 一种背景色

只需要一个文本区域（不分标题和正文）

2. 数据结构（示意）
type CalloutVariant = 'info' | 'warning' | 'success' | 'idea';

type Block = {
  id: string;
  bookId: string;
  kind: BlockKind;
  text: string;            // callout 主内容
  calloutVariant?: CalloutVariant; // kind === 'callout' 时有值，默认 'info'
};


你也可以加一个 emoji / iconName 字段，但 v1 可以直接在前端用固定映射：

const CALLOUT_ICON_MAP = {
  info: 'Info',
  warning: 'AlertTriangle',
  success: 'CheckCircle2',
  idea: 'Lightbulb',
} as const;

3. 前端交互 / UI 规则（Callout）

插入方式

在「插入块」菜单里选择「Callout」

默认 variant = 'info'，文本为空

展示样式

结构建议：

<div className={`wl-callout wl-callout-${variant}`}>
  <div className="wl-callout-icon"><Icon /></div>
  <div className="wl-callout-body">
    {/* 单文本域，支持多行 */}
  </div>
</div>


CSS 规则（语义化一点）：

通用：

背景浅色 (rgba(… , 0.08~0.12))

左侧一条粗一点的彩色边（4px）

圆角 + 适度 padding

不同 variant：

info：蓝色系（配合你 Wordloom 主色）

warning：橙 / 红

success：绿色

idea：紫 / 黄色 都可以，看你整体主题

变体切换方式

为了保持“低噪音”，建议：

Callout 块右上角有一个很小的下拉按钮（只在 hover 时显示）

点击后弹出一个极简菜单：

标注类型
- 信息（info）
- 提示（warning）
- 成功 / 结论（success）
- 灵感 / idea（idea）


前端只要把 block.calloutVariant 更新即可。

三、可以直接丢给 Copilot 的任务说明（整理好的一段）

你可以把下面这段原样或者略微调整后贴给 Copilot：

Goal

Implement two new block types in the Wordloom block editor:

todo_list block – inline todo checklist

callout block – highlighted note box with variants

Both must integrate with the existing “block editor” and the Book Overview page.

1. Extend Block model

In the shared Block type / entity:

type BlockKind = 'paragraph' | 'heading' | 'todo_list' | 'callout' | 'divider';

type TodoItem = {
  id: string;
  text: string;
  isDone: boolean;
  isPromoted: boolean;
};

type CalloutVariant = 'info' | 'warning' | 'success' | 'idea';

type Block = {
  id: string;
  bookId: string;
  kind: BlockKind;
  text: string;
  todoItems?: TodoItem[];          // only for kind === 'todo_list'
  calloutVariant?: CalloutVariant; // only for kind === 'callout'
  // ... existing fields (order, timestamps, etc.)
};


Persist todoItems as a JSON column in the blocks table.

For calloutVariant, default to 'info' when kind = 'callout'.

2. TodoListBlock component

Create a React component TodoListBlock that:

Receives a Block with kind === 'todo_list' and its todoItems.

Renders each item as a row: [checkbox] [editable text] [optional promote icon].

Clicking the checkbox toggles isDone.

Clicking the promote icon toggles isPromoted.

Pressing Enter at the end of an item creates a new TodoItem below.

If an item is empty and user presses Backspace at its start, remove that item.

Styling:

Completed items: muted text + strikethrough.

Promoted items: small accent icon / chip to indicate promotion.

Update the central block renderer to route kind === 'todo_list' to this component.

Add an “Insert Todo list” entry to the block insert menu: create a new block with:

kind: 'todo_list';
todoItems: [{ id: uuid(), text: '', isDone: false, isPromoted: false }];

3. Book Overview – TODO / Checklist panel

In the Book Overview page:

Query all blocks for the current book where kind === 'todo_list'.

From these blocks, collect all todoItems where isPromoted === true && isDone === false.

Render them in the “Todo / Checklist” section as a flat list.

Each item should display:

its text

optionally a small link / button to jump to the originating block in the block editor.

4. CalloutBlock component

Create a CalloutBlock component that:

Receives a Block with kind === 'callout' and calloutVariant.

Renders a box with:

left colored border

light background

an icon on the left side depending on variant

the main editable text area on the right.

Use a simple icon map, e.g.:

const CALLOUT_ICON_MAP: Record<CalloutVariant, IconName> = {
  info: 'Info',
  warning: 'AlertTriangle',
  success: 'CheckCircle2',
  idea: 'Lightbulb',
};


On hover, show a small variant selector in the top-right corner of the block:

Clicking it opens a minimal menu:

“信息（info）”

“提醒 / 警告（warning）”

“结论 / 成果（success）”

“灵感 / Idea（idea）”

Choosing an option updates calloutVariant.

Add an “Insert Callout” entry to the block insert menu:

kind: 'callout';
calloutVariant: 'info';
text: '';


Update the central block renderer to route kind === 'callout' to CalloutBlock.

你可以先让 Copilot实现一个最小版本：

不纠结动画 / 微交互

先把数据打通 + 基本样式做出来

之后我们再一起挑毛病、微调视觉和交互。