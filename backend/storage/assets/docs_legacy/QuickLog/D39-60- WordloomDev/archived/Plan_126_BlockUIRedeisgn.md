这个担心很合理，现在的交互有点像：

“每条句子右上角都有一排小路灯，虽然是 hover 才亮，但一亮就是一条街。”

要解决「臃肿 + 老要把鼠标移动到右边」这两个问题，可以从三方面下手：

频率拆分：什么是高频行为，什么是低频行为

位置拆分：什么必须用鼠标，什么优先键盘

显示拆分：什么时候一排三个图标都要出现，什么时候只要一个甚至 0 个

我给你一个可落地的方案，可以直接整理成规则丢给 Copilot。

1. 先认清三种操作的“频率等级”

新建 block：极高频（几乎每段都会用）

删除 block：中频（写错 / 清理时用）

查看历史：低频（调试 / 看成熟度时才点）

既然频率差这么多，就不要用同一种 UI 去承载它们。

2. 高频：新建/删除尽量键盘优先，鼠标只是辅助手段

你现在已经有：

Enter → 在当前 block 下方创建新 block

（可以加）Backspace：在空 block 上按一次 → 删除本 block，光标跳到上一条

只要这两条完成度够高，其实：

绝大多数时候压根用不到右上角的 + 和 🗑；

右上角的按钮更多是「给习惯点鼠标的人一个出口」，而不是主路径。

所以可以写成规则：

- Primary creation path: Enter creates a new block below, not the "+" icon.
- Primary deletion path: Backspace on an empty block deletes it.
- "+" and delete icons are secondary affordances, not required for fast editing.


这样你心里也有数：鼠标那三个图标只是 B 方案，不是 A 方案。

3. 减少“每条都有三颗图标”：拆成「激活块」vs「路过块」
设计建议

只有当前激活块（光标在里面的那条）才展示完整的 3 个图标

其他只是鼠标路过的 block：

要么啥都不显示；

要么最多显示一个非常淡的 + 或「⋯」菜单。

这样整页不会扩散出一堆小按钮，永远只有一条正在编辑的块“有控制台”。

具体实现思路

假设你有 activeBlockId：

function BlockItem({ block, activeBlockId }: Props) {
  const isActive = block.id === activeBlockId;

  return (
    <div className="block-item">
      <BlockEditorContent ... />

      <div className="block-item-actions">
        {isActive ? (
          <>
            <button onClick={insertBelow}>+</button>
            <button onClick={showHistory}>🕒</button>
            <button className="btn-danger" onClick={deleteBlock}>🗑</button>
          </>
        ) : (
          <button onClick={insertBelow}>+</button>  // 非激活块只露一个 +
        )}
      </div>
    </div>
  );
}


再配合一个很低对比度的样式（之前说的那套灰色、透明边框），视觉噪音会小很多。

4. 把「三按钮横排」缩成一个“⋯”菜单（真正低频）

尤其是历史这个按钮，其实可以塞进菜单里：

当前 block 右边只露出一个灰色的「⋯」

点一下弹出一个小菜单：

Insert block below

View history

Delete block

结构：

<div className="block-item-actions">
  {isActive && (
    <Popover trigger={<button>⋯</button>}>
      <Menu>
        <MenuItem onClick={insertBelow}>Insert block below</MenuItem>
        <MenuItem onClick={showHistory}>View history</MenuItem>
        <MenuItem danger onClick={deleteBlock}>Delete</MenuItem>
      </Menu>
    </Popover>
  )}
</div>


这样 始终最多只有一个小点点出现，只有你点开它才会看到三条操作，页面瞬间干净很多。

5. 减少“鼠标要跑很远”的问题：靠近文本而不是靠右边缘

现在图标在最右侧，你每次从文本跑到右边，Fitts’ Law 在哭。

两个优化方向：

把操作按钮挪到左侧（Notion/Linear 的老套路）：

block 最左边来一列小把手 / ⋯ 菜单，当鼠标靠近左边的时候出现；

你从文字到左边的距离通常比到右边短。

或者：靠近第一行文字右侧，而不是拉到整行尽头：

用 inline-block 或绝对定位在文字附近，鼠标移动的距离会少很多。

你可以先简单点：先不改位置，只把「只有激活块显示⋯」+「菜单收起三个按钮」做了，后面再考虑换到左边。

6. 小结：一套组合拳把“烦躁感”打掉

给你压成几条规则，方便你贴到 VISUAL_RULES / Copilot 里：

- Enter creates a new block; Backspace on empty block deletes it. These are the primary flows.
- Only the active (focused) block may show full block actions; non-active blocks must show at most one subtle icon (e.g. "+" or "⋯") on hover.
- Prefer a single "⋯" menu for low-frequency actions (history, delete) instead of three always-visible icons.
- Block actions should be low-contrast gray, with transparent background, and must not draw attention during normal reading.
- Action triggers should be positioned close to the text (or on the left gutter) to minimize pointer travel.


做完这些之后：

你不会再看到“每一行右边挂着三颗彩色小球”；

真正在写东西时，基本只用键盘完成增删，鼠标偶尔点一下 ⋯ 就够了；

页面恢复成「一篇文章 + 少量隐身工具」，而不是一堆明显的 UI 控件。

////////////////////////////////////////////////////////////////////////////////

对，你这个直觉非常对：
如果插入 todo / heading 还得把鼠标划到最右边点图标，那说明交互设计是失败的。

右上角那些按钮，本来就只该是“备用方案”，真正高频的插入方式应该是——光标在哪，手就在那儿解决问题，尽量少动鼠标。

我给你一套“主线路 = 键盘 + 贴着光标的小菜单”的方案，你可以直接当规则喂给 Copilot。

一句话版原则

插入 / 切换 block 类型（heading / todo / quote…）的主通道：

/ slash 菜单

Markdown 前缀（# 、- [ ] 等）
-（可选）快捷键 Ctrl+1/2/3 切 H1/H2/H3

右边 / 右上角的 + / ⋯ 只是“鼠标党备用方案”，不是首选。

1. 当前这行直接变成 heading/todo —— 用 Slash 菜单 + Markdown 前缀
1）Slash 菜单（Notion 同款）

规则：

在 block 开头 输入 /，弹出一个跟着光标走的小菜单：

Heading 1

Heading 2

Heading 3

Todo

Bullet list

Quote

…

用户用键盘上下选，Enter 确认；

编辑器把当前 block 的 kind 改掉，而不是插入新 block。

伪逻辑：

// 当检测到 "/" 且在行首：
openSlashMenuAtCaret({
  onSelect(kind) {
    transformBlock(blockId, kind); // updateBlock: kind + content
  }
});


效果：
光标就在文中，不需要去点任何按钮，就能把“这一段”变成 heading/todo/quote。

2）Markdown 快捷前缀

给经常敲字的人更快的路径：

# + 空格 → 当前 block 变成 H1

## → H2

### → H3

- [ ] / [] / - [x] → 当前 block 变成 Todo

> → Quote

流程：

用户在行首敲 # 或 - [ ]

编辑器检测到 pattern 后：

删除这一小段前缀

updateBlock 把 kind 和对应字段改掉

伪代码：

function handleMarkdownShortcut(block, textBeforeCaret) {
  if (textBeforeCaret === "# ") transformToHeading(block, 1);
  if (textBeforeCaret === "## ") transformToHeading(block, 2);
  if (textBeforeCaret === "### ") transformToHeading(block, 3);
  if (textBeforeCaret === "- [ ] ") transformToTodo(block);
  if (textBeforeCaret === "> ") transformToQuote(block);
}


这样就变成：

“我只要把脑子里的 # 标题 打出来，它就自然变成标题，不用找按钮。”

2. 想在下面插一个 todo/heading —— Enter + Slash / Markdown

插在下面实际上就是两步串起来：

Enter → 新建一个普通 paragraph block；

马上在新 block 里用 / 或 Markdown 前缀切换类型。

典型操作流：

光标在某段末尾

Enter（新 block）

输入 /todo → 选 Todo
或一上来就 - [ ] → 直接变成 Todo block

所以日常写东西几乎可以全键盘：

…这一段结束了<Enter>
/todo<Enter>
写 todo 内容…


你根本不需要去右上角的 +。

3. 很怕记不住这些？给懒人再加一个“贴着文本的小工具条”

如果你想再多一点“可见的、但不烦”的 UI，可以加一个紧挨着文本、只在激活块出现的小工具条，而不是右上角三颗球：

当前 block 有光标时，在文字上方/左侧浮出一个 mini toolbar：

H1 / H2 / H3

todo

quote

图标都是灰色、线稿，鼠标移上去才稍微变清晰。

结构示例：

function ActiveBlockToolbar({ block }) {
  if (!block.isActive) return null;

  return (
    <div className="active-block-toolbar">
      <button onClick={() => transformToHeading(block, 1)}>H1</button>
      <button onClick={() => transformToHeading(block, 2)}>H2</button>
      <button onClick={() => transformToHeading(block, 3)}>H3</button>
      <button onClick={() => transformToTodo(block)}>☑</button>
      <button onClick={() => transformToQuote(block)}>❝❞</button>
    </div>
  );
}


CSS 思路：

.active-block-toolbar {
  position: absolute;
  left: 0;             /* 或 text 左侧一点 */
  top: -24px;          /* 浮在这一行的上方 */
  display: flex;
  gap: 4px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.12s ease;
}

.block-item--editing:hover .active-block-toolbar {
  opacity: 1;
  pointer-events: auto;
}


这样：

鼠标党不用跑到最右边，只要稍微往上挪一下就能改类型；

键盘党继续用 / 和 Markdown；

toolbar 只在当前激活块出现，不会满屏都是。

4. 把这些写死成规则，避免又退回“到处点按钮”

给你压一段可以直接塞进 VISUAL_RULES / SPEC 里的文字：

- Block 类型切换和插入的主流程应为键盘驱动：
  - "/" at the start of a block opens a slash-menu to change block kind (heading, todo, list, quote, etc.).
  - Markdown-like prefixes ("# ", "## ", "- [ ] ", "> ") convert the current block to the corresponding kind.
  - Enter creates a new paragraph block; users can immediately use "/" or prefixes to choose its type.
- Mouse-based controls (right-side "+", context menu, etc.) are secondary affordances only.
- Optionally, when a block is active, show a small inline toolbar near the text (H1/H2/H3/Todo/Quote) instead of making users travel to the far right.


所以答案其实是：

todos / headings 这种东西，主路径应该一直在“光标附近”，而不是右上角图标。

真·高频插入方式：

Enter → /todo / # 标题 / - [ ]

或激活块上方的小 toolbar

右边那一列图标，就把它当成「可视化备用工具」，而不是主武器。