一、先把「Wordloom 的 TODO Block」想清楚
你现在有三个相关东西：


Block 编辑页里的 TODO 类型


和段落、Callout、Divider 一样，是一种 Block。


需要做到“写起来像文本，点一下就是勾选”。




Overview 页里的「TODO」Tab


文案已经有：Promoted from Blocks。


这个 Tab 应该只列出「被提升为书本级 TODO，且尚未完成」的条目。




Maturity / 结构任务


有任务：清空关键 TODO、TODO 卫生 等。


本质上是根据「Promoted TODO 的数量 + 完成情况」给分。




所以，TODO Block 的职责可以拆成两层：
1. Block 层：只是「一条可勾选的句子」
最小特性：


有文字内容 text


是否完成 isDone:boolean


是否提升为书本级 TODO isPromoted:boolean


仍然是 Book 里的 Block，拥有顺序、位置等通用信息


你暂时不需要：子任务、负责人、项目、复杂提醒。那是以后 Orbit/Task 模块的事。
2. Book 视图层：从这些 Block 中挑出「重要 TODO」
规则建议：


只有 isPromoted = true 的 TODO Block 才出现在 Overview 的 TODO Tab
（避免所有零碎小条目把 Tab 挤爆）


Tab 里只显示 !isDone 的条目


当「Promoted & 未完成」数量为 0 时：


Maturity 的「TODO 卫生」打满分


结构任务「清空关键 TODO」自动完成




这种设计好处：


数据只有一份：所有信息都在 Block 里


TODO Tab / Maturity 都只是 不同的查询视图（filter + map）


以后要做「跨 Book 任务视图」「日历」也可以基于这些 Block 再聚合



二、交互设计（给你心里有数）
1. 在 Block 编辑页里


插入方式：


通过当前的「插入块菜单」选择「TODO 列表」


（以后可选）输入 - [ ] 自动转换为 TODO Block




显示样式：


左边一个 checkbox


右边是文本（支持换行但视觉上还是单条）


勾选后整行浅灰 + 文字中间线




操作：


点击 checkbox → isDone 布尔值反转，立即保存


文本编辑和普通段落差不多


右上角或 hover toolbar 上有一个“小火箭/小旗子”图标：
「提升为书本 TODO」/「取消提升」




被提升后：


在 Block 上有一个轻量标记（例如小蓝点或标签 TODO），提醒用户这条会出现在 Overview




2. 在 Overview 的 TODO Tab 里


标题：TODO / 结构 TODO


说明行：Promoted from Blocks


列表内容：


每条显示：


来自哪个 Block（文本前几十个字）


可选：出自哪个段落/章节（以后有层级再说）


一个 checkbox（勾选=完成）




点击勾选：


更新对应 Block 的 isDone = true


这条从列表中消失






空状态：


文案类似：暂无结构 TODO，继续保持！


同时对应的 Maturity 项可以给满分。





三、Maturity / Chronicle 的连接（逻辑层面）
建议你现在就把规则定死，方便 Copilot 写代码：


计分字段（已经有了，只是明确一下来源）


todoOpenCount: 当前该 Book 中 isPromoted = true && isDone = false 的数量


todoClosedCount: isPromoted = true && isDone = true




评分规则示例（你可以微调，但大体可以这样）


当 todoOpenCount = 0：


结构项「TODO 卫生」+10


结构任务「清空关键 TODO」标记为完成




当 todoOpenCount > 0：


「TODO 卫生」按数量扣分或不给分


结构任务「清空关键 TODO」未完成






Chronicle 事件（以后用得上）
每次以下事件发生时，记录一条 Chronicle 事件：


某 TODO Block 被 isPromoted = true


某 TODO Block 从 isPromoted = true → false


某 TODO Block 勾选完成（isDone 从 false → true）


这对以后做「时间线」很有用，但现在先只暴露接口即可。



四、给 Copilot 的完整实现计划（英文，可以直接粘）
下面是可以丢给 Copilot 的说明：
I want to implement the **TODO block type** and connect it with the Book Maturity "TODO" tab.

Tech stack:
- Next.js + React + TypeScript
- We already have a generic Block model and a Book Maturity module.
- The Maturity page already has a "TODO" tab with the text "Promoted from Blocks", but the actual TODO block type is not implemented yet.

# 1. Domain model

We already have a base Block entity (e.g. in the database and in the TypeScript layer).
Extend the block domain so that there is a dedicated `TodoBlock` type:

- `type: "todo"`
- Shared block fields: id, bookId, position/order, createdAt, updatedAt, etc.
- Todo-specific fields:
  - `text: string`
  - `isDone: boolean`
  - `isPromoted: boolean`   // whether this todo should show up on the Book-level TODO tab

Implementation suggestion:

- In the DB, keep using the same `blocks` table.
- Add a `type` column if we don't have it yet, and a JSONB `props` or similar column where todo-specific fields live.
- In TypeScript, define:

```ts
type BlockType = "paragraph" | "heading" | "callout" | "divider" | "todo" | ...;

interface BaseBlock {
  id: string;
  bookId: string;
  type: BlockType;
  order: number;
  // ...
}

interface TodoBlockProps {
  text: string;
  isDone: boolean;
  isPromoted: boolean;
}

type TodoBlock = BaseBlock & {
  type: "todo";
  props: TodoBlockProps;
};



Update the block repository / API DTOs so that TODO blocks are correctly serialized / deserialized.


2. Block editor: TODO block component
Add a React component that renders and edits a TodoBlock.
Requirements:


Visually: checkbox on the left + text input on the right (similar to Notion's todo).


Interactions:


Clicking the checkbox toggles isDone and sends an update to the backend.


Editing the text updates props.text.




Promotion:


In the block's hover toolbar or context menu, add a small icon/button like "Promote to Book TODO".


Clicking it toggles isPromoted (true/false).


When isPromoted = true, show a small subtle indicator on the block (e.g. a tiny label "TODO" or an icon) so the user knows this todo is part of the Book-level TODO list.




Implementation notes:


Reuse the existing block-editing infra (same save API, same optimistic update pattern).


For now, keep TODO blocks flat (no subtasks, no nested children).


3. Book-level TODO tab
The Maturity page already has a TODO tab with a placeholder.
Implement it as a real view:


Query: all TODO blocks for this book where isPromoted = true && isDone = false.


This can be a dedicated endpoint like GET /api/books/{bookId}/todos or a filtered blocks query.




UI:


Show a title "TODO" and a subtitle "Promoted from Blocks".


Render a list of items:


A checkbox (bound to isDone).


The todo text (first line).




When the user toggles the checkbox here:


Update the underlying TodoBlock (isDone).


Remove the item from the list as soon as it becomes isDone = true.






Empty state:


If there are no promoted & open todos, show a friendly empty message:


e.g. "暂无结构 TODO，继续保持！"


This state will be used by the Maturity scoring (see below).




4. Maturity integration
We need some derived fields for the Maturity engine:


todoOpenCount: number of blocks where type = "todo" && isPromoted = true && isDone = false for this book.


todoClosedCount: number of blocks where type = "todo" && isPromoted = true && isDone = true.


Later we can use these counts to:


mark the "清空关键 TODO" structure task as completed when todoOpenCount === 0,


grant a full score for the "TODO 卫生" maturity component when todoOpenCount === 0,


and/or reduce the score when there are many open TODOs.


For now, please:


Expose these counts from the backend (part of the maturity snapshot DTO), even if the scoring logic is simple.


Make sure the values are updated whenever a TODO block is edited or toggled.


5. Optional: editor convenience (v1.5, not required now)
If it's easy, add a small improvement:


When the user types "- [ ] " at the beginning of a paragraph and presses space or enter, convert that block into a TodoBlock with isDone = false and isPromoted = false.


This is optional. The primary insertion method remains the "Insert block" menu with the "TODO 列表" entry.

Please implement:


The TodoBlock domain data structure + persistence.


The React TODO block editor component (checkbox + text + promote toggle).


The Book Maturity TODO tab that lists promoted & open todos and allows completing them.


The derived counts todoOpenCount and todoClosedCount in the maturity snapshot DTO so that the scoring engine can use them later.



---

这样你就有一整套「从 Block → TODO Tab → Maturity」的闭环设计了。
等 TODO Block 落地之后，你的「结构任务 / TODO 卫生」这些内容也会变得更有抓手，不再只是描述性的文案。
::contentReference[oaicite:0]{index=0}
