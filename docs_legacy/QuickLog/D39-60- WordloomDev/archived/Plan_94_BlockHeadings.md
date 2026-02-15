一、两种主流模型
模型 A：标题是独立 block 类型

Notion / Craft / Logseq / Obsidian（块模式）基本都是这样干的：

数据里有：

paragraph 段落块

heading 标题块 + level = 1 | 2 | 3

UI 上可以看到：

插入菜单里有「Heading 1 / Heading 2 / Heading 3」

或者通过快捷键 / 命令把当前段落变成标题

用户体验上常见的手势：

Markdown 快捷写法：

在一行开头输入 # 后按一下空格 → 当前 block 变成 H1

## + 空格 → H2

### + 空格 → H3

编辑器会：

识别开头的 # 数量

删除这些符号

把该块的 type 从 paragraph 改为 heading，设置 level

菜单 / 工具栏转换：

在段落上点小菜单：段落 → 一级标题 / 二级标题 等

本质就是改 block 的 type / level，内容不变

也就是说：标题和普通段落在数据结构里确实是不同类型的块，只是编辑体验看起来更像“换了个样式”。

模型 B：标题只是“段落的样式”

像 Google Docs / Word 这类传统文档，会把「标题一」当作一个段落的样式，而不是独立块类型：

段落只有一个类型：paragraph

但有 style = normal | heading1 | heading2 | ...

这种对 Wordloom 来说没什么优势，反而让后端处理结构化内容（大纲、TOC、书章节）更麻烦，所以我会推荐你走 模型 A：标题 = 独立块。

二、结合你现在的编辑器怎么落地？

你现在的 UI 是「无 block 感的多段编辑」：

每个 block 背后是一个实体（有 id / created_at / updated_at）

前端用类似 <textarea> 或 contenteditable 让它看起来像普通一段话

上面有一个「+ 插入块」菜单（段落 / Todo 列表 / Callout / 分割线 / 更多块类型…）

在这个前提下，我建议这样设计：

1. 数据模型层

你的 blocks 表可以这样扩展（伪代码）：

type BlockKind =
  | 'paragraph'
  | 'heading'
  | 'todo_list'
  | 'callout'
  | 'divider'
  // 将来还有 media / quote / code 等

type Block = {
  id: string;
  bookId: string;
  kind: BlockKind;
  headingLevel?: 1 | 2 | 3; // 只有 kind === 'heading' 时有值
  text: string;
  // 其他字段：排序、状态、时间戳...
}


也就是：标题本身就是 kind = 'heading' 的块，具体是 H1/H2/H3 由 headingLevel 决定。

2. UX 方案：不把标题塞进「插入菜单」

为了保持你现在这个干净的菜单（段落 / Todo / Callout / 分割线），标题可以采用 快捷转换 而不是必须“插入标题块”。

方案一：Markdown 风格自动升级（强烈推荐）

在「块编辑」模式下，对当前块监听输入：

如果光标在行首，用户输入 #、##、###，再按一次空格：

阻止这次空格的默认行为

数一下前面有几个 # → level = 1/2/3

删除这些 # 和空格

把当前块从 paragraph 改成 heading，设置 headingLevel = level

伪代码（前端逻辑）：

function handleKeyDown(e: KeyboardEvent, block: Block) {
  if (e.key === ' ' && caretAtLineStart(block)) {
    const text = getCurrentLineText(block);
    const match = text.match(/^#{1,3}$/); // 只允许 1~3 个井号
    if (match) {
      e.preventDefault();
      const level = match[0].length as 1 | 2 | 3;

      // 清空这一行里的 # （也可以只删掉前缀）
      replaceCurrentLineText(block, '');

      // 更新 block 类型
      updateBlock(block.id, {
        kind: 'heading',
        headingLevel: level,
      });
    }
  }
}


这样用户感觉就是：
“像写 markdown 一样打 #，结果这段话自动变标题”。

方案二：小工具条切换

再加一个“小浮动工具条”：

选中某个块（或者在块左侧 hover 出来）时，出现一个小菜单：

「正文 / 一级标题 / 二级标题 / 三级标题」

选中不同项 → 调用 updateBlock 改 kind 和 headingLevel

这对不喜欢 # 的用户更友好，你可以放到 v1.1/1.2 做增强。

3. 渲染层怎么区分？

在“非编辑态”渲染时非常简单：

function BlockView({ block }: { block: Block }) {
  if (block.kind === 'heading') {
    if (block.headingLevel === 1) {
      return <h1 className="wl-heading wl-heading-1">{block.text}</h1>;
    }
    if (block.headingLevel === 2) {
      return <h2 className="wl-heading wl-heading-2">{block.text}</h2>;
    }
    return <h3 className="wl-heading wl-heading-3">{block.text}</h3>;
  }

  if (block.kind === 'todo_list') {
    // ...
  }

  if (block.kind === 'callout') {
    // ...
  }

  // 默认 paragraph
  return <p className="wl-paragraph">{block.text}</p>;
}


样式规则（可以写进 VISUAL_RULES.yaml）大致是：

H1：比正文大 2–3 级，带上下 margin、大一点的行高

H2：比正文大 1.5–2 级

H3：略大于正文或加粗

重点是：数据上是干净的块列表，UI 上长得像“Word 段落 +标题”，完全符合你“无 block 感”的目标。

三、你需要考虑的几个小细节（顺便给你踩坑）

是否允许一个标题块里有多行？

一般编辑器允许（你现在是 textarea 模式的话，天然就是多行）

逻辑上没问题，只要行首识别 # 的地方只看第一行就好。

回车时怎么分块？

现在你是：一块 = 一个 textarea，按 Enter 就是该块内部换行

如果未来想升级为「回车 = 创建新块」，那就会是另外一套编辑模型（更接近 Notion），可以之后再聊；暂时不需要纠结。

大纲 / 目录 / Chronicle

标题是独立块以后，你将来要做：

Book 内目录（根据 H1/H2/H3 自动生成）

Chronicle 里记录「标题结构变更」

从 DDD 的角度也更舒服：标题是有语义的结构节点，不只是字体变大。

四、一句话总结给你

是的，标题一般就是独立的 block 类型，在数据里有自己的 kind 和 headingLevel。

成熟编辑器大多走的路是：

用户先得到一个普通段落 block；

输入 # + 空格 或通过小菜单，把这个 block“升级”为 heading；

UI 看起来像 Word 的标题样式，但数据是干净的块列表。

你现在这套「无 block 感 + 插入菜单」已经很接近 Notion 的底层逻辑了，再加上 # 快捷转换，就可以自然地把标题体系接上，而不用在 UI 上多塞一个「插入标题」选项，保持清爽。