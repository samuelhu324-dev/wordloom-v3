好，下面这段你可以直接扔给 Copilot，当成前端 / 全栈实现规格。
（你可以放在 BLOCK_EDITOR_SPEC.md 之类的文件里。）

Wordloom 块编辑器 v1 收尾规格（给 Copilot 看）
1. 目标

实现一个 「无 Block 卡片感」的行内编辑器，但内部仍然是 DDD/Hex 定义的 Block 模型。

所有内容都由 Block 构成，每个 Block 有 kind 和 content。

页面看上去像一整片连续文本，不要到处是卡片边框。

支持一二三级标题（H1/H2/H3），并且可以在正文和标题之间来回切换。

2. 数据模型（必须遵守 DDD/HEX 约束）

前端操作的是 BlockDto，最终通过 UseCase 调用后端。不得修改 Domain/Hex 的合同。

// 例：前端使用的 BlockDto 结构（示意，字段名可按现有代码）
type BlockKind =
  | "paragraph"
  | "heading"
  | "list_bullet"
  | "list_numbered"
  | "list_todo"
  | "callout"
  | "quote"
  | "divider"
  | "image"; // 其他类型按现有 RULES

interface BlockDto {
  id: string;
  kind: BlockKind;
  content: any;           // 实际是 JSONB，前端可以用更具体的类型别名
  fractionalIndex: string;
}


其中与本次收尾相关的核心要求：

paragraph：

content 至少包含：{ text: string }

heading：

content 必须包含：{ level: 1 | 2 | 3; text: string }

level=1/2/3 分别对应 H1/H2/H3

所有 Block 的增删改排，都要通过既有 UseCase，例如：

// 新建 Block
createBlock({
  bookId,
  kind: "heading" | "paragraph" | ...,
  content,              // JSON
  beforeBlockId?: string,
});

// 更新 Block
updateBlock({
  blockId,
  kind,                 // 可以在 paragraph/heading 等之间切换
  content,
});


前端允许修改 kind 和 content，但不能改 UseCase/Repository 的接口设计。

3. 插入与类型切换交互
3.1 Insert 菜单（底部 + 行内）

Block 列表有两种 Insert 入口：

列表底部的 “+ 添加一段文字 / 插入内容” 按钮；

每个 Block 行尾或行间的悬浮 “+” 按钮（inline insert）。

Insert 菜单中至少包含这些选项（中文文案可以再调）：

文本：

段落 → kind="paragraph"，content={ text: "" }

一级标题 → kind="heading"，content={ level: 1, text: "" }

二级标题 → kind="heading"，content={ level: 2, text: "" }

三级标题 → kind="heading"，content={ level: 3, text: "" }

列表：

项目符号列表 → kind="list_bullet"

编号列表 → kind="list_numbered"

待办列表 → kind="list_todo"

标注：

引用 → kind="quote"

提示 Callout → kind="callout"

分割线 → kind="divider"

伪代码示例：

function onInsertBlockAfter(targetBlockId: string, kind: BlockKind, extra?: any) {
  const content = getDefaultContent(kind, extra); // 负责生成 {level,text} / {text}
  createBlock({
    bookId,
    kind,
    content,
    beforeBlockId: getNextBlockId(targetBlockId),
  });
}

3.2 Slash 菜单和行首 Markdown 语法

在「段落/标题」编辑时，支持以下转换逻辑：

Slash 命令（在当前块输入 / 打开菜单）：

/h1 或 /一级标题 → 当前块变为 heading level=1

/h2 或 /二级标题 → heading level=2

/h3 或 /三级标题 → heading level=3

/text 或 /paragraph → 切回 paragraph

Markdown 风格行首语法：

行首输入 # + 空格 → 该段变成 heading level=1

## + 空格 → heading level=2

### + 空格 → heading level=3

实现方式：

在编辑器组件（例如 BlockTextEditor）中监听输入。

当判定为上述模式时：

去掉行首标记（如 # / ## / ### ）。

调用 updateBlock({ blockId, kind:"heading", content:{ level:1/2/3, text } })。

或切回 paragraph。

3.3 左侧“文本类型 Chip”切换

为避免到处都是按钮，只在当前聚焦 block 左侧展示一个小 Chip，例如内容：

正文 / H1 / H2 / H3

交互需求：

点击 Chip 弹出一个小菜单：

正文（paragraph）

H1 标题（heading level=1）

H2 标题（heading level=2）

H3 标题（heading level=3）

选择之后，更新当前 Block：

function onChangeTextKind(block: BlockDto, target: "paragraph" | "h1" | "h2" | "h3") {
  if (target === "paragraph") {
    updateBlock({
      blockId: block.id,
      kind: "paragraph",
      content: { text: extractText(block) },
    });
  } else {
    const level = target === "h1" ? 1 : target === "h2" ? 2 : 3;
    updateBlock({
      blockId: block.id,
      kind: "heading",
      content: { level, text: extractText(block) },
    });
  }
}

3.4 键盘快捷键

在 Block 聚焦时支持：

Ctrl+Alt+1 → 当前 Block 变为 heading level=1

Ctrl+Alt+2 → heading level=2

Ctrl+Alt+3 → heading level=3

Ctrl+0 → paragraph

实现逻辑同上，只是触发源是 keydown。

4. 视觉表现（“无 Block 感”）

目标：页面整体看起来像一篇文档，不像一堆卡片。

要求：

不要给每个 Block 渲染明显的卡片边框和背景。

默认状态：只是一段文字；Block 之间仅有 4–8px 垂直间距。

仅在以下状态显示操作元素：

鼠标 hover 到某个 Block；

文本光标在该 Block 内聚焦。

此时才显示：

左侧拖拽 handle（如果有排序需求）；

左侧文本类型 Chip（正文/H1/H2/H3）；

行尾或行间的 + Insert 按钮；

其他操作 icon（更多菜单等）。

标题与正文的视觉差异依靠排版而非边框：

H1：

字号 > 段落字号；

字重加粗；

上下间距略大（例如上 16px，下 8px）。

H2：

比 H1 小一点，略粗，上下 8 / 4px。

H3：

接近正文，只稍微加粗；上下间距稍大于正文。

正文：

普通字号和行距，不需要额外装饰。

分割线 divider：

使用简单的一条横线，占整行宽度或中间半宽，不要复杂样式。

5. 技术实现提示（给 Copilot 的导向）

不要改动现有 Domain/UseCase/Repository 签名。所有新增逻辑放在：

Block 编辑器 React 组件；

前端 Adapter（DTO ↔ API）。

主要改动集中在：

Block 列表渲染组件（例如 BookBlocksView）；

单个 Block 渲染组件（例如 BlockItem、BlockTextEditor）；

Insert 菜单组件、Slash 菜单组件；

样式文件（CSS/Styled/Tailwind）。

Slash 命令 / Markdown 转换逻辑：

实现为前端纯函数，输入为当前文本和光标位置，输出为：

新的 kind；

新的 content；

是否需要阻止默认输入行为。

请确保：

所有 Block 的增删改排序仍然经过统一的 hook/useCase 调用；

新逻辑不破坏现有 Block 加载、保存、时间线等功能。

总结：
实现一个行内 Block 编辑器：视觉上“像文档”，内部保持 Block 语义，支持正文 ↔ H1/H2/H3 的切换（Insert 菜单、Slash 命令、Markdown 行首语法、左侧 Chip、快捷键），底层仍通过现有 UseCase 更新 kind 和 content.level/text。