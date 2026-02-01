## 2025-12-10 回填

- **Outcome:** ParagraphEditor 现在在 `-/*/1./1)`、`- [ ]`、`>` 等 pattern 只剩标记和空白时就会通过 `markdownShortcuts.applyPattern` 触发 `commands.transformBlockKind`，不再依赖“整段必须完全空”的旧守卫，彻底解决 “No para block restoration” 的未决事项。
- **Code refs:** `frontend/src/modules/book-editor/ui/ParagraphEditor.tsx`、`model/markdownShortcuts.ts`、`ui/BlockItem.tsx` 同步收敛 entrypoint，并让 Markdown shortcut 只在空 paragraph 投递 `onMarkdownShortcut`，避免再创建/删除临时段落。
- **Tests:** `pnpm vitest frontend/src/modules/book-editor/model/__tests__/markdownShortcuts.test.ts` + `ui/__tests__/ListBlock.test.tsx`/`TodoListBlock.test.tsx` 均已覆盖 “pattern-only” 检测与壳层 handled 流程；回归验证 `- + Space`、`1.`、`- [ ]`、`>` 用例再也不会留下额外段落。

先给你结论：

现在这份 BLOCK_RULES.yaml 已经覆盖了截图里说的需求，不需要再加一套规则结构。

问题出在 实现还在用旧的“非空段落才算 markdown shortcut” 检测逻辑，没有真正按 markdown_shortcuts.minus_space 这条 flow 去写。

下一步就是：把 ParagraphEditor 里的 “- + Space 检测 + 调命令” 改成严格照 BLOCK_RULES 执行，然后以后所有 markdown shortcut 都按这套约束来加。

1. 现在 BLOCK_RULES 已经怎么说的？

在 BLOCK_RULES.yaml 里，其实已经有一条完整规范：

ui_integration:
  markdown_shortcuts:
    minus_space:
      pattern: "'-' + Space"
      flow:
        - "确认 block.kind = paragraph 且文本除 pattern 外为空"
        - "清空当前段落文本"
        - "调用 transformBlockKind(paragraph -> bulleted_list)"


以及 keyboard 映射：

keyboard_mapping:
  minus_space:
    combo: ["-", "Space"]
    context: "空 paragraph"
    command: "transformBlockKind(paragraph -> bulleted_list)"


所以文档层面已经非常清楚了：

只有在 paragraph 且除 - 之外是空 的时候才触发；

触发时要先把当前段文本清空；

通过 commands.transformBlockKind 把这个 block 改成 bulleted_list，不允许其它骚操作。

你现在遇到的问题，其实是 ParagraphEditor 还在用老一版检测条件：

“段落必须已经有非空文本，detectMarkdownShortcut 才返回 … ”

导致 在“空段里输入 - 再按 Space” 的时刻，检测直接返回 null，从来没走到命令层。

2. 这次要改的“操作方案”（给 Copilot 的指令）

你可以把下面这段丢给 Copilot 当“执行规范”，只让它在 ParagraphEditor 那一层动手：

2.1 集中处理 - + Space 快捷键

文件：ParagraphEditor.tsx（或者你现在集中处理 keydown 的地方）

在 handleKeyDown 里，找 Space 的分支，改成类似：

if (event.key === ' ' && !event.shiftKey && !event.altKey && !event.metaKey) {
  if (applyMinusSpaceMarkdownShortcut()) {
    event.preventDefault();
    return;
  }
  // 其他 Space 行为...
}


新增一个 helper，严格按 BLOCK_RULES flow 实现：

const applyMinusSpaceMarkdownShortcut = React.useCallback(() => {
  const handle = coreRef.current;
  if (!handle) return false;

  // 只在 paragraph 上启用
  if (block.kind !== 'paragraph') return false;

  // 当前文本 & 光标位置
  const text = handle.getText() ?? '';
  const caretOffset = handle.getCaretOffset();
  if (caretOffset == null) return false;

  const before = text.slice(0, caretOffset);
  const after = text.slice(caretOffset);

  // 模式：段落内容必须是 "-"，或者 "-" 后只有空白
  const isMinus = before.trimEnd() === '-' && after.trim().length === 0;
  if (!isMinus) return false;

  // 1. 清空当前段文本（BLOCK_RULES 要求）
  handle.setText('');         // 或通过 onChange / props.updateText('')

  // 2. 调命令层：transformBlockKind(paragraph -> bulleted_list)
  commands.transformBlockKind({
    blockId: block.id,
    targetKind: 'bulleted_list',
  });

  return true;
}, [coreRef, commands, block.id, block.kind]);


关键点就是不再要求“段落非空”，而是检查 “- 在前，剩下都是空白”。

2.2 避免绕过命令层 / selection

同时顺手让 Copilot 做两件清扫：

删除/禁止任何在 ParagraphEditor 里直接调用 transformBlockKind 的代码，全部改成走 commands.transformBlockKind；这点在 BLOCK_RULES 也有写到：

ui_integration:
  slash_menu:
    must_call: "commands.transformBlockKind"
    ...


确保 markdown shortcut 分支完全不碰 window.getSelection() / setSelectionRange，只改文本 + 调命令；caret 由你现有的 caret pipeline 接手。

3. BLOCK_RULES 要不要再改？

严格说：

结构上不需要再加新 section。
markdown_shortcuts.minus_space + keyboard_mapping.minus_space 已经足够描述行为了。

如果你想让将来回顾更一目了然，可以考虑在 minus_space.flow 里多加一行注释，但完全属于“锦上添花”：

markdown_shortcuts:
  minus_space:
    pattern: "'-' + Space"
    flow:
      - "仅在空 paragraph 上启用（允许只包含 '-' 与空白）"
      - "确认 block.kind = paragraph 且文本除 pattern 外为空"
      - "清空当前段落文本"
      - "调用 transformBlockKind(paragraph -> bulleted_list)"


核心是：不要再新造规则文件；让现有 BLOCK_RULES 作为真相源，代码只是追上它。

4. 小自查 checklist（你改完可以自己点点看）

改完让 Copilot跑一轮后，你可以用这个超短核对表：

空 paragraph 输入 - 然后 Space：

文本先被清空；

当前块的 kind 变成 bulleted_list；

caret 仍然在同一行，只是变成 list 第一条（没有跳到别的块）。

在“非空段落”（例如 A-）按 Space：

不触发 transform；

行为和普通输入空格一样。

搜索代码仓：

不再有 ParagraphEditor 直接调用 transformBlockKind 的地方；

没有为了 markdown shortcut 去直接改 selectionStore 或 window.getSelection() 的地方。

做到这三条，你这条 bug 就算从“行为”和“规则”两头都真正关死了。接下来再加 * + Space、> + Space 只要 copy 这套 flow 改 target kind 即可，不会再变成新雷区。