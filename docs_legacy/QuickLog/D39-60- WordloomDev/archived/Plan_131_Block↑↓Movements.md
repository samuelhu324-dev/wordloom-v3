现在这块看起来已经很像“正经编辑器”了，舒服多了👌
来一个个拆你现在的三个问题。

1. ↑ 只能在本 block 里移动，不能跳上一块

这是现在 contentEditable 的默认行为：
浏览器只知道“行内”怎么动，不知道你有 block 概念。

业界常见做法（Notion / Google Docs）：

在块的第一行按 ↑，跳到上一块的末尾

在块的最后一行按 ↓，跳到下一块的开头

你可以做个“够用版”的拦截逻辑：

思路

只在这两种情况下接管：

caret 在当前块最开头，按 ↑

caret 在当前块最末尾，按 ↓

其他情况，交给浏览器默认行为在当前块内部上下移动。

伪代码（放在 InlineEditor 的 onKeyDown 里）
function handleKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
  const sel = window.getSelection();
  if (!sel || !sel.focusNode) return;

  const isCollapsed = sel.isCollapsed;

  // 只处理未按住 Shift 的情况
  if (!isCollapsed || e.shiftKey) return;

  // 检查是否在当前 block 的开头或末尾
  const caretOffset = sel.focusOffset;
  const textLength = getPlainTextLengthOfBlock(e.currentTarget);

  if (e.key === "ArrowUp" && caretOffset === 0) {
    e.preventDefault();
    focusPreviousBlock(blockId, { atEnd: true }); // 你自己封装这个
    return;
  }

  if (e.key === "ArrowDown" && caretOffset === textLength) {
    e.preventDefault();
    focusNextBlock(blockId, { atStart: true });
    return;
  }

  // 否则让浏览器自己处理
}


简化版的 trade-off：

不精确区分“是不是第一行 / 最后一行”，

只要 caret 在整体文本开头/结尾就跳块。

在你的场景里已经很自然：大部分块不会长到十几行。

2. block 间距 vs Shift+Enter 段内换行：要不要统一？

这点上，绝大部分现代编辑器都选择“不统一”：

块之间的间距比较大：

段落之间看起来明显分开，

用户能一眼看出来“这里是新的逻辑单元 / 新块”。

同块内的换行（Shift+Enter）只用行高：

行与行之间间距比较小，

视觉上感觉是“同一段里的紧凑换行”。

你现在截图里已经能看出这个效果了：
第二个 block 里的 AAA↵AAA 看起来就是“同一段两行”，下面那个大一点的是“新块”。

建议：

保持这两个差异，这是在帮用户区分：

“这是一个 block 里的多行内容”

“这是两个独立的 block”。

如果设计成一模一样的间距：

用户会很难分辨：这是一个段的软换行，还是新 block；

也不符合 Notion / Docs / Word 的读感。

3. 具体一点的设计建议（给你几个可以直接改 CSS 的数字）
3.1 正文行高 & 段内换行

正文字号假设是 14–16px；

行高可以设成 1.5 左右：

.block-paragraph {
  font-size: 14px;      /* 或 15/16，看你整体 */
  line-height: 1.5;
}


Shift+Enter 的行间距就等于这行高，不用额外设置。

3.2 block 间距（段落与段落）

给每个 block 一个 margin-bottom，比行高略大一点：

.block-root {
  margin-bottom: 0.75rem; /* 大约 12px，如果字体 16px */
}


这样效果大概是：

同块内：行与行相差 1 行高度；

块与块之间：差 1.2–1.5 行高度，明显“松”一点。

如果你想更精细一点：

段落：margin-bottom: 0.75rem

Todo 列表：margin-bottom: 0.5rem（列表更紧凑）

Callout：上下多一点，比如 1rem，显得是“特殊说明块”。

3.3 第一块 / 最后一块的 padding

你现在那块大白卡片已经挺好看了。可以再加两条小规则：

卡片内部：padding-top 和 padding-bottom 固定，比如 24px；

第一块上面不要再额外 margin-top，最后一块下面保持统一的 margin-bottom。

这样从上到下，看起来就是：

白卡片（固定内边距） + 块与块之间规则的竖向节奏。

3.4 轻微的“当前块”提示（可选）

你现在 block 已经不抖了，可以考虑加一个非常轻的 active 状态：

当前选中的 block 左侧加一条 2px 的淡色线；

或者 block 背景 alpha 很低的一点点高亮；

例：

.block-root--active {
  background: rgba(0,0,0,0.02);
  /* 或者 */
  border-left: 2px solid #d0defa;
}


不要太重，只是让眼睛知道“焦点在哪一块”。

小结一下

↑ / ↓ 的跨块移动

在“文本开头/结尾 + 没按 Shift”时接管键盘，

↑ 聚焦上一块末尾，↓ 聚焦下一块开头；

其他情况让浏览器自己在块内部动。

块间距 vs 段内间距

保持不同是对的：行高 < block margin；

这样 Shift+Enter 看起来是“同一段里换行”，

普通 Enter = new block，看起来更松一点。

设计上

正文：14–16px，行高 1.5 左右；

block 间距：0.75rem 起步；

todo 紧一点、callout 松一点；

可以加一个很轻的 active block 提示。

你现在已经从“能用”进化到“有编辑器味道”了，接下来就是这些小细节慢慢打磨，会非常有成就感的那种阶段。