## 2025-12-10 回填

- **Outcome:** Plan168B 的“Enter 专属日志 + list 专属处理器”现已 merge，List/Todo 行级 editor 通过 handleKeyboardDecision 自己吞下 exit，BlockItem 只关心结果，自然杜绝“退出→再提交”导致的两段文本。
- **Code refs:** `ui/ListBlock.tsx`、`ui/TodoListBlock.tsx` 暴露 `handleKeyboardDecision`，`ParagraphEditor.tsx` 的 Enter 分支完全依赖 decider 输出；`keyboardDecider.ts` 也新增 isLastItem/isOnlyItem 判定避免误判。
- **Tests & QA:** `pnpm vitest ListBlock TodoListBlock` + 手动“空 list 连续 Enter / 中间空行 Enter/Backspace”脚本均通过；`devtools/logKeyboardDecisions` 输出佐证 Enter 只执行一次。

你现在的状态是：

普通 Enter：已经修好了 ✅

场景：list 里最后一项是空的，连续按 Enter

结果：list 被炸成 两个 paragraph block（“爆破裂成两 para”）

这个现象基本只说明一件事：

这一次 Enter 被处理了两次——先按“退出列表”的规则跑了一遍，又按“普通段落的规则”再跑了一遍。

下面给你一个非常具体的排查 + 修法，按步骤做就好。

1. 先确认这次 Enter 走了哪几条路径

在你现在的 keyboard pipeline 里，应该有类似这样的结构（伪代码）：

function handleInlineEditorKeyDown(e) {
  if (e.key !== 'Enter') return;

  const decision = decideEnterAction(ctx); // 你之前搞的决策器

  switch (decision) {
    case 'CREATE_BLOCK_BELOW':
      handleCreateBelow();
      break;
    case 'SPLIT_BLOCK':
      handleSplit();
      break;
    case 'EXIT_LIST_TO_PARAGRAPH':
      exitListToParagraph();
      break;
    // ...
    default:
      onSubmit();   // 或者某个 fallback
  }
}


先在这里加一行日志：

console.log('[ENTER]', {
  blockId,
  blockType,
  decision,
  isEmpty,
  isLastItem,
});


然后实际操作一遍 “非空 list item → Enter → 再 Enter”，看第二次 Enter 的 log：

理想情况：只打一行，decision: 'EXIT_LIST_TO_PARAGRAPH'

现在很可能是：

要么打了两次 log（说明 Enter 被监听两次）

要么打一次 log，但执行路径除了 EXIT_LIST_TO_PARAGRAPH 还“掉进了 default”，又走了一次 CREATE_BLOCK_BELOW / onSubmit

2. 修“执行两次”的核心：在 list 分支里 return 掉

先给你一个推荐的 switch 写法（重点是 return）：

function handleInlineEditorKeyDown(e) {
  if (e.key !== 'Enter') return;

  const decision = decideEnterAction(ctx);

  switch (decision) {
    case 'CREATE_NEXT_LIST_ITEM':
      e.preventDefault();
      commands.createNextListItem();
      return;  // ✅ 这一层就终止

    case 'EXIT_LIST_TO_PARAGRAPH':
      e.preventDefault();
      commands.exitListToParagraph();
      return;  // ✅ 不再落入任何 fallback

    case 'CREATE_BLOCK_BELOW':
      e.preventDefault();
      commands.createBlockBelow();
      return;

    case 'SPLIT_BLOCK':
      e.preventDefault();
      commands.splitBlock();
      return;

    default:
      // 真正的兜底逻辑
      return;
  }
}


常见坑就是：
在 EXIT_LIST_TO_PARAGRAPH 里你虽然调用了 exitListToParagraph()，
但后面没有 return，函数继续往下走，又执行了一个 onSubmit() / handleCreateBelow()：
于是：

第一步：退出列表 → 把当前 block 转成 paragraph（或在下面新建一个 para）

第二步：generic Enter 逻辑再建一个 para
→ 肉眼看到“两个 para”，以为列表爆炸。

所以第一刀就是：

所有 list 专用的 decision 分支，记得 return，不能再落到通用 Enter 逻辑里。

3. 确认“空 list item”那一格的决策正确

再看一下你 decideEnterAction(ctx) 里关于 list 的部分，建议是类似这样：

if (ctx.blockType === 'listItem') {
  if (!ctx.isEmpty) {
    // 有内容：创建下一个 list item
    return 'CREATE_NEXT_LIST_ITEM';
  }

  // 以下都是 isEmpty === true 的情况
  if (!ctx.isLastItem) {
    // 中间空项：删当前 item，光标到下一项
    return 'DELETE_THIS_LIST_ITEM';
  }

  // 空 + 最后一项：退出列表
  return 'EXIT_LIST_TO_PARAGRAPH';
}


你现在的“爆裂成两 para”，常见两种原因：

isLastItem 算错：

列表还有第二项，你以为是最后一项，就走了 EXIT 分支；

EXIT 逻辑上再调用了“在下方建一个 paragraph”，

下次再 Enter，又走 paragraph 的通用 CREATE_BLOCK_BELOW，

列表此时已经不在了，看起来像被拆成一堆 para。

isEmpty 判定漏掉了软换行 / 空格：

第二个 item 视觉上“空”，但内部 text 实际上是 '\n' 或 ' '，

isEmpty false → 决策器以为“有内容”，走了 CREATE_NEXT_LIST_ITEM，

结果列表继续延长，然后又被 fallback 的 paragraph 逻辑接管，结构乱套。

你可以把 isEmpty 改成更严格一点的：

const normalizedText = text.replace(/\s+/g, '');
const isEmpty = normalizedText.length === 0;


确保软换行 / 空格都被视为“空”，
尤其是在你已经加了 Shift+Enter 软换行之后，这个很关键。

4. exitListToParagraph 只做“一件事”

最后一个容易踩的坑：exit 函数自己里面又在 createBelow

exitListToParagraph() 里建议只做：

如果整个列表只剩这一项：

把 block 类型改成 paragraph（原地变身）；

如果列表有多项且你在最后一项：

删除这项；

在列表下面新建一个 paragraph block，光标移过去。

不要在里面又顺手调用你通用的 createBlockBelow()，
否则你即使在 switch 里 return 了，也可能在函数内部再建一次 para。

伪代码参考：

function exitListToParagraph(ctx) {
  const { isOnlyItem, blockId } = ctx;

  if (isOnlyItem) {
    // 一个 list item 的列表，直接把这个 block 变成 paragraph
    commands.changeBlockType(blockId, 'paragraph');
    return;
  }

  // 多个 item：删掉最后一项，在列表下方建 para
  commands.deleteListItem(blockId);
  commands.insertParagraphBelowList();
}

5. 快速验证 checklist

修完之后，用这几个步骤手动测一遍：

输入：- a，Enter

期待：列表 item(1) = "a"，item(2) = 空

在 item(2) 上按 Enter

期待：列表整体结束，列表下面出现一个空 paragraph

编辑器里 block 结构应该是：[listBlock(items=['a']), paragraph('')]

再在那个 paragraph 上继续 Enter

期待：按你通用规则走（创建下一个 paragraph / whatever），但列表不再发生任何变化

如果还是有“两段 para”那种怪象，让你刚才加的 [ENTER] log 说话——
看是哪里多跑了一次逻辑，基本就能直接对上上面的几个点。

总之，现在这个 bug 已经不是“神秘的玄学”，
它几乎肯定就是 “list 情况下没彻底从通用 Enter 流程里退出来” + isEmpty/isLastItem 判定边缘值 两个组合拳。

按上面这几刀挨个戳一遍，一般能把“空 list 连续 Enter 爆裂成 para”这条线彻底抹干净，后面再加其它 block 类型也会舒服很多。