一、Plan158A 的问题：规则写在 ADR 里，代码没真的守

从你截图里的几点 + Plan_158A 文件本身来看，现在的状况是：

deleteBlock 直接干掉 block，不做兜底

useBlockCommands.deleteBlock 调的是一个“毁灭指令”，删完就完事，
没调用 ensureAtLeastOneBlock 之类的守门人。

一旦删掉最后一个 block，editor state 真的会掉到 blocks.length === 0，
正好违背 Plan158A 的“永远至少一个 block”的 invariant。

ADR 里承诺的 helper 只是“纸上函数”

ADR / Plan 里写了：
ensureAtLeastOneBlock(book)、appendEmptyParagraphAtEnd()、splitParagraphAtCaret() 等等，
但在代码里这些要么没实现，要么实现了但没有被调用。

命令层（blockCommands）也没有在 destructive action 后统一调用这些 helper。

UI 层也没兜底：BlockItem / BlockList 都是“真空可见”

BlockItem.tsx 的 onDeleteEmptyBlock 直接 deleteBlock，
没先判断“我是最后一个吗？”
所以在最后一个空段落上按 Backspace，会直接把 blocks array 削成 0。

BlockList.tsx 在 blocks.length === 0 时渲染的是“empty state + CTA”，
等用户点“写点什么”再添一个 safety paragraph，
但 Plan158A 的意思是：根本不要让界面看到 0 个 block 的状态，
0 只能是中间态，立刻被 helper 修回 1 个。

评价一句话

现在的状态是：Plan158A 已经“定了法”，但执行官还没上岗。

ADR 讲清楚了设计和 invariant；

但是命令层 / UI 层都还在用老习惯，
所以“基础块不得删除”的规则在 runtime 完全不成立。

建议的修补顺序（告诉 Copilot 可以这么干）

在 blockCommands 里真正实现 helper

function ensureAtLeastOneBlock(state: EditorState): EditorState {
  if (state.blocks.length > 0) return state;

  const id = createBlockId();
  const newBlock: ParagraphBlock = {
    id,
    kind: 'paragraph',
    text: '',
    // …其他默认字段
  };

  return {
    ...state,
    blocks: [newBlock],
    selection: { blockId: id, offset: 0 }, // 光标回到新段首
  };
}

function appendEmptyParagraphAtEnd(state: EditorState): EditorState {
  // 用于“写点什么…” CTA
}


把所有 destructive command 都包一层

例如：

const deleteBlock = (blockId: BlockId) =>
  setState(prev => ensureAtLeastOneBlock(deleteBlockInternal(prev, blockId)));


其它诸如 deleteSelection、clearBlocksInRange、deleteBookContent 之类也同理处理。

UI 层不再自己玩“空数组”游戏

BlockItem.onDeleteEmptyBlock：

如果有前/后兄弟，先把焦点移过去，然后调用 deleteBlock；

如果自己是唯一一个，仍然调用 deleteBlock，
但依赖 ensureAtLeastOneBlock 去重建新的空 paragraph，而不是掉到 0。

BlockList 不应该看到 blocks.length === 0 的长期状态；
真看到说明命令层漏掉了 helper——这就属于 bug，而不是“正常 empty UI”。

这样把 Plan158A 的 helper 和命令层真正接上线，你的“永远至少一块空 paragraph”规则才算真的生效。

---

### 2025-12-04 落地记录

- `frontend/src/modules/book-editor/ui/BlockItem.tsx`：在 `onDeleteEmptyBlock` 中判断当前是否为唯一 block，若是则直接拦截 Backspace，不再触发 delete command，只复位光标，符合“最后一块只能清空内容”的行为。
- `frontend/src/modules/book-editor/model/blockCommands.ts`：`deleteBlock` 现在在删除最后一块之前先通过 `createBlock` 创建新的空 paragraph，再删除旧块；若删除失败会回滚新建块，确保运行时 `blocks.length` 永远 ≥ 1，并且焦点落在新插入的空段首。
- 后续：在 DDD/Hexagonal/Visual RULES 补充 Plan158B 执行情况，并继续观察批量删除/undo 流程是否还会触发 Zero-block 闪现。

二、/ 菜单栏打不开的问题：大概率是“截获条件没生效”

你之前的设计是：

去掉 + 插入按钮；

用 / 打开插入菜单；

只有在“当前行/segment 是空的”时才截获 /，否则就当普通字符打出来。

Copilot 给的方案大致是：

实现 isCaretInEmptySegment()：

用 handle.getCaretOffset() + handle.getText()；

找到最近一个换行之后到 caret 的那一段文本；

去掉零宽字符、trim；

为空则返回 true。

在 handleKeyDown 里：

if (event.key === '/' && !event.shiftKey && isCaretInEmptySegment()) {
  event.preventDefault();
  openSlashMenu();
  return;
}


现在你说“/ 菜单栏完全没打开”，常见原因有几类，可以自查一下：

1. handleKeyDown 根本没跑到这段逻辑

在 ParagraphEditor 顶部是不是有类似：

if (readOnly) return;
if (event.defaultPrevented) return;


或者别的 handler 提前 return 了？

你可以先在 / 分支里 console.log('slash hit') 看看有没有触发。

如果 log 都不出来，问题在事件流或 keydown 绑定位置上。

2. isCaretInEmptySegment() 永远返回 false

典型坑：

当前行里其实有某些不可见字符（zero width）没被你的 ZERO_WIDTH_PATTERN 处理掉；

你依赖了 hasText，但它的语义是“整段有没有内容”，和“当前行是否为空”不完全一致；

caretOffset 拿到的是 null，触发了 fallback 分支，一直走 !hasText，而 hasText 已经是 true。

排查办法很简单：在 helper 里把 caretOffset、before、currentSegment 全部 console.log 一下，对着你屏幕上那个空行试一遍。

3. 条件写对了，但放的位置不对

handleKeyDown 里大概有很多分支，比如 Backspace 处理、Enter 处理、上下方向键处理。

如果 / 的分支写在很靠后的位置，前面某个分支已经 preventDefault + return，那 / 条件永远不会运行。

一般习惯是把全局快捷键（包括 / 菜单）放在最前面，至少要保证在任何“普通字符输入”逻辑之前拦截。

4. 输入法 / key 值的问题（小概率）

设计上你是期望“英文状态下按 /”，这时 event.key 确实是 '/'；

如果在中文输入法下，有时候 keydown 的 key 会是 'Process' 之类，这种情况你本来也很难可靠截获；

我个人建议：就约定 Slash 菜单只在英文输入状态下可用，否则体验会非常混乱，可以在帮助文档里写清楚。

三、该怎么把这两件事交给 Copilot 做？

你可以这样把需求压缩成两条丢过去：

Plan158A 落地

Implement the helper functions promised by ADR-145:
ensureAtLeastOneBlock, appendEmptyParagraphAtEnd, etc.

Refactor all destructive commands in blockCommands (deleteBlock, deleteSelection, etc.) so they always call ensureAtLeastOneBlock before returning.

Update BlockItem.onDeleteEmptyBlock to use these commands and never leave the editor with zero blocks; when the last block is deleted, a new empty paragraph should be auto-created and focused.

BlockList should no longer rely on “empty state + CTA” as the only way to recover from zero blocks; zero blocks should be treated as a transient state fixed inside commands, not as a stable UI.

Slash 菜单修好

In ParagraphEditor.tsx, make sure handleKeyDown intercepts / before other early-return branches.

Replace the old isCaretPrecededByContent check with the new isCaretInEmptySegment helper we discussed, and log its intermediate values to confirm that it returns true when the caret is on a visually empty line.

Only when event.key === '/' && !event.shiftKey && isCaretInEmptySegment() should we preventDefault() and open the insert menu; otherwise / must be inserted as a normal character.

一句压缩版结论：

现在的问题不是 Plan158A 写错了，而是规则只停在文档和注释里，没有全链路接到命令层和 UI；

/ 菜单打不开，多半是 keydown 没打到那一层或“当前行为空”的判定始终为假——一旦把这两个点查清，把 Copilot 往这两个方向推，它就能帮你把这一轮收口掉。