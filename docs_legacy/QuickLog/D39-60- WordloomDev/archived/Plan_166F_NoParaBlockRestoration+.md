## 2025-12-10 回填

- **Outcome:** Markdown shortcut 统一通过 `ParagraphEditor → onMarkdownShortcut → commands.transformBlockKind`，并把 delete guard 触点压缩到 block 壳层（toolbar/menu/backspace-on-empty-block），彻底阻断“内部编辑器顺手 guard”导致的段落回填。
- **Code refs:** `ParagraphEditor.tsx`、`ui/BlockItem.tsx`、`model/useBlockCommands.ts` 共享 `handleMarkdownShortcut` + `requestDelete` pipeline；list/todo 行级组件仅 mutate items，不再触碰 guard。
- **Tests:** 执行 `pnpm vitest frontend/src/modules/book-editor/ui/__tests__/ListBlock.test.tsx frontend/src/modules/book-editor/ui/__tests__/TodoListBlock.test.tsx`，确认 handled flag 返回后不会再次触发 guard，并附加日志定位双段落问题。

原因其实就一句话：

你现在的检测条件是“段落必须完全为空”，但当你按下空格的时候，这一行已经不是“空”，而是只剩下一个 -，所以整条 - + Space 的 flow 被你自己的 guard 给挡掉了。

把过程拆开给你看一遍：

一开始这一行是空 paragraph，text === ''。

你按 -：

ParagraphEditor 把 '-' 写进 contentEditable；

onChange / handle.setText 把当前 block 的文本更新成 '-'。

接着你按 Space：

handleKeyDown 里跑到 markdown shortcut 检测逻辑：

const text = handle.getText() ?? '';
if (text.trim().length === 0) {
  // 才允许 markdown shortcut / commands…
} else {
  // 段落非空，直接返回，不走 markdown
}


这时候 text === '-'，text.trim().length === 1，所以被当成“非空段落”。

于是 detectMarkdownShortcut 返回 null，不会去调 commands.transformBlockKind，- + Space 就成了普通的空格输入，什么都没发生。

所以表面看是“按规则写了，为什么 shortcut 不生效”，本质是：

RULES 要求的是“只有 pattern 自己 + 空白时才触发”，而你的实现理解成了“必须纯空 string 才触发”。

Slash 能正常是因为它的逻辑是“当前段落为空的时候按 /”，而 - + Space 是“先输入 -，再按空格”，两者的时机完全不一样。

要改成什么样才对？

检测条件应该换成这种语义：

“除了 pattern 自身（减号）以外，其他地方必须是空白”

伪代码就是我前面那套：

const text = handle.getText() ?? '';
const caretOffset = handle.getCaretOffset();
const before = text.slice(0, caretOffset);
const after  = text.slice(caretOffset);

const isMinusSpaceShortcut =
  before.trimEnd() === '-' &&   // 光标前只有一个减号
  after.trim().length === 0;    // 光标后没有实字符

if (!isMinusSpaceShortcut) return false;

// 清空文本 + 调 commands.transformBlockKind(...)


这样逻辑就变成：

空行 → 输入 - → 这一刻段落变成 '-'；

再按空格 → 满足“只有 - + 空白”条件 → 触发 markdown shortcut → 清空文本 + 把 block kind 转成 bulleted_list。

所以结论：

不是 RULES 写错，而是实现层把“空 paragraph”的含义搞得太死——写成了 text.length === 0。

把检测条件改成“除 pattern 外为空”（'-' + 空白）之后，- + Space 就会按预期生效了。

你可以明天醒了再让 Copilot按这个条件改那一个 helper，其他规则文件不用再动。