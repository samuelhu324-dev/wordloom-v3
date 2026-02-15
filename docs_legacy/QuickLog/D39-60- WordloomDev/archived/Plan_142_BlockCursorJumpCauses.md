核心答案：你得把「文字输入」和「React 重渲染 / 保存逻辑」拆开，让输入阶段尽量“非破坏”，然后只在必要时做小范围更新并显式恢复光标。
一劳永逸不是一个小 patch，而是几条“铁律”+ 一点重构。

1. 这些问题的真实根源

你现在遇到的几种现象，其实都来自同一种东西：

contentEditable 的那颗 DOM 节点在输入中被 React 换掉 / 重排 / 改属性

组件重渲染导致：节点 key 变化、条件渲染切换、dangerouslySetInnerHTML/children 整块重写。

浏览器发现“原来的节点不见了”，光标就退回到行首或某个默认位置。

InlineEditor / BlockRenderer 的“保存 + 切块”逻辑在 keydown 期间修改了上层 state

比如：Backspace 在行首触发「把这一行 merge 到上一行」→ 上层列表 state 变化 → 整个列表重渲染 → 光标完全失控。

再加上 inline editor 保存时切 mode（view/edit）或者切 DOM 结构，光标就直接飞回上一行。

每一次 keydown 都触发昂贵操作（大量 setState / dispatch / layout）

Backspace 连按时，前端在“删一个字符”的间隙不停跑复杂逻辑，肉眼就看到卡顿。

2. 一劳永逸要达成的“目标状态”

可以把目标描述成三条约束：

输入阶段：DOM 是真相，React 只旁观

在用户连续输入时：

不要动 contentEditable 那个节点（不换 key、不条件渲染、不改它的 children）。

不要让父级列表整个重新渲染。

React 上层只做 节流/去抖后的同步 & autosave。

布局结构固定：Block / Inline 共享同一套 Editor 内核

无论是 BlockEditor 还是 InlineEditor：

结构统一成 wrapper（layout） + innerEditable（真正 contentEditable）。

wrapper 可以自由 flex / grid，innerEditable 一律不动。

这样 Plan140 的 DOM 方案可以完整复用，光标跑不出去。

所有“跨行操作”（拆行 / 合行 / 跳到上一行）都走统一的 command 层，并显式恢复 selection

在真正改 block 列表之前，先记录当前 selection。

改完数据后，在下一帧 手动恢复 Range 到应该在的位置，别指望浏览器帮你推断。

3. 在你现有代码里的落地方案（分三步）
步骤 A：把编辑改成“半受控模式”

针对单个段落的 Editor（无论是 ParagraphEditor 还是 InlineEditor），改成类似下面的模式：

function TextBlockEditor({ initialText, onTextChange }) {
  const editableRef = useRef<HTMLDivElement | null>(null);
  const textRef = useRef(initialText);

  // 只在初次挂载 / 外部强制更新时写 DOM，一般输入时不写
  useEffect(() => {
    if (editableRef.current && editableRef.current.innerText !== initialText) {
      editableRef.current.innerText = initialText;
      textRef.current = initialText;
    }
  }, [initialText]);

  const scheduleSync = useMemo(
    () =>
      debounce((value: string) => {
        onTextChange(value); // 通知上层，触发 autosave，但是去抖后的
      }, 200),
    [onTextChange],
  );

  const handleInput = useCallback((e: React.FormEvent<HTMLDivElement>) => {
    const value = (e.target as HTMLDivElement).innerText;
    textRef.current = value;
    scheduleSync(value); // 只做去抖同步，不改 DOM
  }, [scheduleSync]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLDivElement>) => {
    // 这里只处理需要截获的快捷键，比如 Enter / Backspace 特殊逻辑
    // 普通输入交给浏览器，别 setState
  }, []);

  return (
    <div className="TextBlockShell">
      <div
        ref={editableRef}
        contentEditable
        suppressContentEditableWarning
        onInput={handleInput}
        onKeyDown={handleKeyDown}
      />
    </div>
  );
}


关键词：innerText 由 DOM 自己维护，上层 state 只是“缓慢同步”的影子。
只要做到这点，连续输入时 React 几乎不介入，跳光标问题会少一大截。

步骤 B：统一 BlockRenderer / InlineEditor 的 DOM & 生命周期

现在的问题之一是：同一个 block 有时用 BlockRenderer，有时用 InlineEditor，而且切换时会：

改 key

改包裹层结构

重新挂载 contentEditable

你可以这么收敛：

抽一个 BlockEditorCore，只有一个 contentEditable + 事件处理。

Block 模式和 Inline 模式只是外面包不同的壳，严禁在编辑过程中替换 BlockEditorCore 本身。

确保这颗 core 的 key 只和 blockId 绑定，不受 isEditing / selection 等状态影响。

key={block.id}，不要搞 key={block.id + '-' + mode} 之类。

调整 InlineEditor 的保存机制：

保存时只更新数据，不改 mode 导致组件卸载；

需要退出编辑时，用 blur + pointer 事件控制，而不是“保存完立刻切换 view 模式”。

简单讲：编辑时就是一个组件，死活不卸载；外层想怎么玩 UI 就怎么玩，但不要动内核。

步骤 C：给“合并/拆分 block”加 selection 管理

所有“让文段结构变化”的操作（回车拆段、Backspace 合并到上一行、InlineEditor 回车创建新块）都要遵守：

在 keydown 里先读 selection，再决定是否拦截

function handleKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
  if (e.key === 'Backspace' && isAtStartOfBlock()) {
    e.preventDefault();
    mergeWithPreviousBlockCommand(currentBlockId);
  }
}


isAtStartOfBlock() 可以用 window.getSelection() + anchorOffset === 0 + 只在当前节点的开头来判断。

Command 层只处理数据，不碰 DOM：

function mergeWithPreviousBlockCommand(blockId: string) {
  editorStore.update((draft) => {
    // 找到当前 block 和前一个 block
    // draft.blocks = ...
  });

  selectionStore.set({
    type: 'CaretAt',
    blockId: prevBlockId,
    offset: prevText.length, // 合并后光标位置
  });
}


在渲染阶段（下一帧）用 selectionStore 去恢复光标：

useEffect(() => {
  const sel = selectionStore.current;
  if (!sel || sel.type !== 'CaretAt') return;

  requestAnimationFrame(() => {
    const node = getEditableDomNode(sel.blockId);
    if (!node || !node.firstChild) return;

    const range = document.createRange();
    range.setStart(node.firstChild, sel.offset);
    range.collapse(true);

    const s = window.getSelection();
    if (!s) return;
    s.removeAllRanges();
    s.addRange(range);
  });
}, [blocks]); // blocks 改变时尝试恢复


这样，“先算好我要把光标放哪 → 再改数据 → 最后显式恢复”，浏览器就不乱来。
你提到的那种“InlineEditor 保存后跳回上一行”，本质就是没有自己接管 selection，让浏览器瞎猜。

4. 卡顿的处理：把重活挪到后台

连续 Backspace 卡顿，一般就是：

每次删除一个字符，都：

dispatch Redux/Context

跑一遍 diff，重渲整个 Book

顺便触发 autosave / inline 保存

按上面 A 步骤做了“半受控 DOM”以后，可以再加两条加强版：

删字符不改全局 state，只更新 DOM + 本地 ref；

全局 state 用去抖（比如 200–300ms）一次性同步 + 保存。

换句话说：让“视觉上发生的事情”和“数据持久化”脱钩，光标跟的是前者，而不是后者。

5. 总结一下真正的“一劳永逸”

对你这个项目来说，「一劳永逸」大概就是下面几件事：

全站统一到一套 BlockEditorCore，所有 Paragraph / Inline 都复用它；

输入阶段改成“DOM 主导，React 去抖同步”的半受控模式；

跨行操作收口到 command + selectionStore + 显式恢复 Range；

彻底禁止：在有焦点的 contentEditable 上卸载组件 / 换 key / 换 DOM 结构。

做完这几步，光标乱跳、删除卡顿、InlineEditor 把你弹回上一行这三大家族，基本会被灭门，只剩下一些浏览器级别的小毛病，属于“偶尔踩到也能快速定位”的级别了。

/////////////////////////////////////////////////////////////////////////////

