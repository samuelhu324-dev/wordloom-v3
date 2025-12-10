好，这个问题的关键就是：把「+ 插入按钮」这条路完全关掉，让 / 成为唯一的“打开插入菜单”的入口，而且只有在“当前行是空的”的时候才截获 /，其它情况就正常打字。

你要跟 Copilot 说的，其实就是三件事：

设计规则（行为说明）

在哪一层实现（ParagraphEditor.tsx 的 keydown）

大致的检测逻辑（isCaretInEmptySegment）

我先给你一段可以直接贴给 Copilot 的英文说明，然后再补充一点解释。

给 Copilot 的说明（可以整段丢给它）

Goal

Remove the old hover “+” insert button completely.

Use / as the only entry point to open the block/insert menu.

/ should only trigger the menu when the caret is on an empty line / empty segment.
In all other cases / should behave as a normal character and be inserted into the text.

Where to implement

Implement this in ParagraphEditor.tsx (or whatever file handles per-block keydown).

We already have access to coreRef / handle.getCaretOffset() / handle.getText().

Detection rule

Replace the old isCaretPrecededByContent() helper with a new helper isCaretInEmptySegment().

Definition of “empty segment”:

Take the current block text from handle.getText().

Get the caret offset using handle.getCaretOffset().

Look at the substring from the last line break (last \n or \r\n before the caret) up to the caret.

Remove zero-width markers and whitespace and trim.

If that substring is empty, we consider the caret in an empty segment → / is allowed to open the menu.

If handle.getText() is empty and caretOffset is 0, this also counts as empty.

Suggested implementation

const isCaretInEmptySegment = React.useCallback(() => {
  const handle = coreRef.current;
  if (!handle) return !hasText; // fallback, keep old hasText flag

  const caretOffset = handle.getCaretOffset();
  if (caretOffset == null) return !hasText;

  const textContent = handle.getText() ?? '';
  const before = textContent
    .slice(0, caretOffset)
    .replace(ZERO_WIDTH_PATTERN, '');

  const lastBreak = Math.max(before.lastIndexOf('\n'), before.lastIndexOf('\r'));
  const currentSegment = before.slice(lastBreak + 1).trim();

  return currentSegment.length === 0;
}, [hasText]);


Then update handleKeyDown:

function handleKeyDown(event: React.KeyboardEvent) {
  // ... existing logic ...

  if (event.key === '/' && !event.shiftKey && isCaretInEmptySegment()) {
    event.preventDefault();
    // open block / insert menu here instead of inserting '/'
    openInsertMenuAtCurrentBlock(); // or call existing helper
    return;
  }

  // fall through: normal typing, '/' is inserted as a character
}


Constraints

Do NOT re-introduce any hover “+” insert handle. The only ways to insert new blocks are:

Enter to split the current paragraph and create a new paragraph block;

the “继续写 / 写点什么…” entry at the end of the book;

the / command menu when isCaretInEmptySegment() is true.

The / key must never block normal typing when there is already non-whitespace content on the current line (e.g. typing URLs like http:// must keep working).

给你自己的一点补充说明

为什么要「segment」而不是「整段空」？
这样你在同一个 block 里写了几行东西之后，

AAA
BBB
|


在第三行刚换行还没打字的时候按 /，依然能弹菜单；
但如果光标在 AAA| 中间，就当普通 / 打字，完全不会挡你。

hasText 还能留着吗？
可以把它当作 fallback：

coreRef.current 或 caret 拿不到的时候，就退回到“整段有没有内容”的粗略判断，

不会出 bug，只是某些边缘情况菜单不弹而已。

openInsertMenuAtCurrentBlock() 具体叫什么无所谓
关键是：

它以前可能是 hover “+” 用的 callback；

现在直接复用，触发入口换成 /。

你可以把上面那段英文直接喂给 Copilot，然后在 ParagraphEditor.tsx 里让它帮你替换原来的 isCaretPrecededByContent 和 handleKeyDown 条件。
这样，视觉上没有 +，交互上 / 只在“这一行是空的”的时候接管，既干净又符合你刚刚定的设计规则。

---

### 2025-12-04 实施

- `frontend/src/modules/book-editor/ui/ParagraphEditor.tsx` 替换成 `isCaretInEmptySegment()` 判定，Slash 只在当前行空白时截获，URL 等场景仍可输入 `/` 字符。
- Slash Menu 入口与 Plan158A 的无悬浮 “+” 策略对齐：顶层插入途径仅保留 Enter 拆分、尾部 CTA、Slash 命令。
- BlockEditorCore + BlockItem 支持 readOnly → 编辑态的键盘触发；首个 `/` 直接重放到 ParagraphEditor，空行判定后立即弹出菜单，不用再按第二次。
- 下一步：在 RULES 中补 Plan159A 章节、补 ParagraphEditor 快捷键单测，覆盖空行/非空行两种路径。