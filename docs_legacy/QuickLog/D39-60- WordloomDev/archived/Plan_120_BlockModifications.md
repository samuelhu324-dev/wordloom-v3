Block Editor 布局 & 交互精简规范（给 Copilot 看）
1. 布局目标

整体感觉像流式文档，而不是一堆输入框 / 卡片。

Block 仍然是独立单元（方便拖拽 / 统计），但视觉上尽量「隐身」。

一级标题不要被大面积空白顶起来，正文块之间的距离适中。

容器结构示意：

// 外层是一个“纸张”容器，里面是 block 列表
<BookBlocksPanel>
  <BlockList>
    {blocks.map(block => (
      <BlockItem key={block.id} block={block} />
    ))}
  </BlockList>
</BookBlocksPanel>

2. Block 间距 & 标题排版（CSS 要求）
2.1 基础间距（所有 Block 通用）
.block-list {
  padding: 24px 40px; /* 外层纸张边距，可按实际 UI 调整 */
}

/* 每个 block 的基础间距 */
.block-item {
  margin-top: 6px;
  margin-bottom: 6px;
}

/* 第一条 block 不要额外顶距 */
.block-list > .block-item:first-child {
  margin-top: 0;
}

2.2 文本类型对应样式

假设有三个 class：

.block-heading-1

.block-heading-2

.block-heading-3

.block-paragraph

可以这样定义：

/* 正文段落 */
.block-paragraph {
  font-size: 14px;
  line-height: 1.7;
  font-weight: 400;
}

/* 一级标题：作为章节标题使用 */
.block-heading-1 {
  font-size: 20px;
  line-height: 1.5;
  font-weight: 600;
  margin-top: 12px;
  margin-bottom: 4px;
}

/* 二级标题：比 H1 略小 */
.block-heading-2 {
  font-size: 18px;
  line-height: 1.5;
  font-weight: 600;
  margin-top: 10px;
  margin-bottom: 4px;
}

/* 三级标题：接近正文，只是稍粗一些 */
.block-heading-3 {
  font-size: 15px;
  line-height: 1.6;
  font-weight: 600;
  margin-top: 8px;
  margin-bottom: 2px;
}

/* 第一条 block 为 heading 时，取消顶部额外 margin */
.block-list > .block-item:first-child .block-heading-1,
.block-list > .block-item:first-child .block-heading-2,
.block-list > .block-item:first-child .block-heading-3 {
  margin-top: 0;
}

2.3 边界线 / 背景的使用规则

默认状态：不显示任何横线、边框；只靠 margin 形成段落间距。

hover / focus 状态才出现轻微边界提示：

/* hover 时，给当前 block 轻微背景 */
.block-item:hover {
  background-color: rgba(15, 23, 42, 0.015); /* 非常浅的灰蓝，可替换 */
}

/* 编辑中（focus）时，可以再稍微强化一点边界 */
.block-item--editing {
  background-color: rgba(15, 23, 42, 0.03);
  border-radius: 4px;
}

/* 可选：在 editing 时显示一条底部细线 */
.block-item--editing::after {
  content: "";
  display: block;
  border-bottom: 1px solid #E5E7EB;
  margin-top: 4px;
}


重要：不要像现在一样给每个 Block 常驻一条横线；
线只作为“当前块”的辅助视觉，而不是整个列表的分隔符。

3. 插入 Block 的交互（核心行为）

所有插入/变换行为最后都落在现有 UseCase 上：
createBlock, updateBlock, reorderBlock 等，接口保持不变。

3.1 Enter = 在下一行创建新段落 Block

规则：

在一个 Block 的文本末尾按下 Enter：

若当前是 paragraph，在其下方创建新的 paragraph block；

若当前是 heading（H1/H2/H3），在其下方创建新的 paragraph block（标准文档行为）。

伪代码：

function handleEnterAtEnd(block: BlockDto) {
  const newBlock: CreateBlockInput = {
    bookId,
    kind: "paragraph",
    content: { text: "" },
    beforeBlockId: getNextBlockId(block.id),
  };

  createBlock(newBlock);
  focusBlock(newBlock.id);
}


前端编辑器要负责判断「光标是否在行尾」，UseCase 不关心键盘事件。

3.2 Slash 菜单：/ 打开 Block 类型选择

规则：

在 Block 文本开头输入 / 时：

打开一个菜单（浮层），列出可用 Block 类型；

用户选择后，当前 Block 转换成对应类型（不创建新 block）。

示例菜单项：

文本：

段落（paragraph）

一级标题（heading level=1）

二级标题（heading level=2）

三级标题（heading level=3）

列表：

项目符号列表（list_bullet）

编号列表（list_numbered）

待办列表（list_todo）

其他：

引用（quote）

提示框 Callout（callout）

分割线（divider）

转换伪代码：

function transformBlockFromSlashCommand(block: BlockDto, command: SlashCommand) {
  switch (command) {
    case "heading1":
      updateBlock({
        blockId: block.id,
        kind: "heading",
        content: { level: 1, text: extractPlainText(block) },
      });
      break;
    case "heading2":
      updateBlock({
        blockId: block.id,
        kind: "heading",
        content: { level: 2, text: extractPlainText(block) },
      });
      break;
    case "paragraph":
      updateBlock({
        blockId: block.id,
        kind: "paragraph",
        content: { text: extractPlainText(block) },
      });
      break;
    // … 其他类型
  }
}

3.3 行间 + 插入按钮（hover 出现）

规则：

鼠标移到两个 Block 中间的空白区域时，显示一个小圆形 + 按钮；

点击 +：

打开与 Slash 菜单类似的插入菜单；

选择类型后，在这两个 Block 之间创建新 Block。

伪代码：

function BetweenBlocksInsert({ previousBlockId, nextBlockId }) {
  const [visible, setVisible] = useState(false);

  return (
    <div
      className="between-blocks-area"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {visible && (
        <button
          className="between-blocks-plus"
          onClick={() => openInsertMenu({ previousBlockId, nextBlockId })}
        >
          +
        </button>
      )}
    </div>
  );
}


插入逻辑：

function insertBlockBetween(kind: BlockKind, previousId: string | null, nextId: string | null) {
  createBlock({
    bookId,
    kind,
    content: getDefaultContent(kind),
    // 如果后端用 beforeBlockId：传 nextId；
    // 如果用 afterBlockId：传 previousId；
  });
}

3.4 Markdown 风格快捷语法

在当前 Block 行首识别下列模式：

# + 空格 → 当前 block → heading level 1

## + 空格 → heading level 2

### + 空格 → heading level 3

> + 空格 → quote

- + 空格 或 * + 空格 → list_bullet

处理流程：

用户输入 # 或 ## 等；

检测「行首 + 紧随空格」；

删除这段前缀；

调用 updateBlock 变更 kind + content。

伪代码：

function handleMarkdownShortcut(block: BlockDto, textBeforeCaret: string) {
  if (textBeforeCaret === "# ") {
    transformToHeading(block, 1);
  } else if (textBeforeCaret === "## ") {
    transformToHeading(block, 2);
  } else if (textBeforeCaret === "### ") {
    transformToHeading(block, 3);
  } else if (textBeforeCaret === "> ") {
    transformToQuote(block);
  } else if (textBeforeCaret === "- " || textBeforeCaret === "* ") {
    transformToBulletList(block);
  }
}

4. BlockItem 组件状态管理（结构建议）
interface BlockItemProps {
  block: BlockDto;
  isEditing: boolean;
}

export function BlockItem({ block, isEditing }: BlockItemProps) {
  const classNames = [
    "block-item",
    isEditing ? "block-item--editing" : "",
  ].join(" ");

  return (
    <div className={classNames} data-block-id={block.id}>
      <BlockGutter block={block} />
      <BlockEditorContent block={block} />
      <BetweenBlocksInsert /* 上面说的 + 区域 */ />
    </div>
  );
}


BlockEditorContent 根据 block.kind 和 content.level 使用前面定义的 CSS class：

function BlockEditorContent({ block }: { block: BlockDto }) {
  const { kind, content } = block;

  if (kind === "heading") {
    const level = content.level ?? 1;
    const cls =
      level === 1
        ? "block-heading-1"
        : level === 2
        ? "block-heading-2"
        : "block-heading-3";

    return (
      <RichTextEditor
        className={cls}
        value={content.text}
        // 这里挂 Enter / Slash / Markdown Shortcut 的处理
      />
    );
  }

  // 默认 paragraph
  return (
    <RichTextEditor
      className="block-paragraph"
      value={content.text}
      // 同样挂 Enter / Slash / Shortcut 逻辑
    />
  );
}

5. 约束总结（给未来自己看的小条款）

不允许每个 Block 都有常驻横线 / 边框；横线只在 hover / editing 状态出现。

标题与正文之间的距离要 小于 标题与上一块内容的距离，使标题看起来是“带着下面那段”的。

插入 Block 的主路径是：Enter → 下一段；/ 菜单和行间 + 是增强，不是唯一入口。

所有这些行为只在前端实现，最终都通过统一的 UseCase 调用更新 kind 和 content。

你把这份直接丢给 Copilot，它大概就知道：

「哦，Block Editor 的视觉要收敛，线要淡，标题要贴着正文，插入逻辑用 Enter + / + 行间 +，底层接口我不能乱动。」

然后你再根据实际效果微调数字就行，比如 margin-top/bottom 从 6px 改成 4px 之类的。