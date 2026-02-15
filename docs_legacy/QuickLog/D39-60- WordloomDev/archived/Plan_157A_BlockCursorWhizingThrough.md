这次这两张图才是“真正的飞移”没错 😂
简单说：不是浏览器抽风，是你代码在 两次 设置光标位置——先放到行首，再纠正到你点的那个字，于是出现扫视感。

Copilot 这版分析其实已经抓到要害了，我帮你把它收成一套可以长期不反弹的规则 + 落地写法。

1. 先把问题翻译成人话

现在的链路大概是这样：

你在只读的列表 / 段落里，用鼠标点到某个字母中间。

React / BlockEditorCore 这层会做很多事：

有 pendingFocusIndex / focusPosition / autoFocus 之类逻辑；

某些 effect 里会调用 setSelection / placeCaret('start')；

ListEditor 里还有 requestAnimationFrame 之后再去改一次 selection。

结果就是：

第一次：浏览器按点击位置放好 caret；

第二次：你的代码“统一处理焦点”，把 caret 先拖到行首，

第三次：another 逻辑再根据 focusPosition 把 caret 拉回你点的那个字。

肉眼看到的就是：光标从第一个字飞扫到目标字。

换句话说：
现在 selection 有 多个老板 —— 浏览器 + BlockEditorCore + ListEditor…
大家轮流“改一下”，于是出现「两次定位」的闪烁。

2. 核心原则：谁有权利动 caret？

你和 Copilot现在已经非常接近正确答案了：

只在「程序性跳转」时动 selection；
用户用鼠标点的时候，一律相信浏览器自己的 selection。

更细一点拆成两条 invariant：

只在这两种情况主动设 caret：

从别的 block 跳过来（键盘上下、Enter 新建 block 等）；

编辑器第一次 mount 的 autoFocus（例如编辑器刚打开时光标落在第一个 block 开头）。

在「鼠标点击进入某个 block」的路径里，不再调用任何 setSelection / placeCaret / focusPosition。

只做一件事：把“正在编辑的 block id”切到对应 block，

selection 的位置完全交给浏览器。

3. 落地做法：加一个“焦点意图” + 把 setSelection 收口
3.1 在 BlockEditorCore 维护一个「focusIntent」

伪代码示意：

type FocusIntent = 'pointer' | 'keyboard' | 'auto';

const focusIntentRef = useRef<FocusIntent | null>(null);


鼠标路径（包括 list 行、普通段落）：

function handleBlockMouseDown(blockId: string, event: React.MouseEvent) {
  focusIntentRef.current = 'pointer';
  // 让浏览器先根据点击自己算 selection
  startEdit(blockId); // 触发进入编辑模式
}


用 onMouseDownCapture 比 onClick 更稳一点，
能保证 flag 在 React 的 onFocus/onClick 之前就设好。

键盘路径：

function handleArrowOrEnter(/* ... */) {
  focusIntentRef.current = 'keyboard';
  startEdit(nextBlockId);
}

function mountFirstEditor() {
  focusIntentRef.current = 'auto';
  startEdit(firstBlockId);
}

3.2 在 唯一 的 caret 管理处检查 intent

现在你的 selection 设置逻辑散落在好几层：
BlockEditorCore / ListEditor / ParagraphEditor 甚至 onStartEdit helper。
目标是把“真正调用 setSelection(...) 的地方收口到一个 helper：

function applyProgrammaticCaret(editableEl: HTMLElement) {
  const intent = focusIntentRef.current;

  if (intent === 'pointer') {
    // 用户点进来的，不碰 selection
    return;
  }

  const sel = window.getSelection();
  sel?.removeAllRanges();

  if (intent === 'keyboard') {
    placeCaret(editableEl, 'start'); // 或者根据 focusPosition
  } else if (intent === 'auto') {
    placeCaret(editableEl, 'start'); // 第一次 autoFocus
  }

  // 用完就清空，避免污染下一次
  focusIntentRef.current = null;
}


在 ParagraphEditor / ListItemEditor mount 的地方，用 useLayoutEffect 调这个 helper：

useLayoutEffect(() => {
  if (!editableRef.current) return;

  editableRef.current.focus({ preventScroll: true });
  applyProgrammaticCaret(editableRef.current);
}, [/* isEditing, blockId 等依赖 */]);


这样：

鼠标点击进入：

focusIntent = 'pointer'；

浏览器先把 caret 放对；

applyProgrammaticCaret 看见是 pointer → 直接 return，不再 override；

没有“扫一遍”的过程。

键盘 / autoFocus：

focusIntent = 'keyboard' | 'auto'；

浏览器 selection 一开始可能在别的地方；

applyProgrammaticCaret 负责统一把 caret 迁到目标 block 的 start/end。

3.3 清理子组件里的“偷偷动 caret”

你截图里 Copilot 提到的这几处，都要配合上面规则一起收拾：

ListEditor / TodoListEditor 中的 pendingFocusIndex + requestAnimationFrame：

继续保留也行，但只允许它决定「哪一行获得 focus」；

真正改 selection 的动作交给 BlockEditorCore 的 applyProgrammaticCaret。
-或者在它内部也加判断：如果 focusIntentRef.current === 'pointer' 就直接退出，不再 setSelection()。

ParagraphEditor 中透传的 focusPosition：

仅在「键盘跳转 / 新建 block」时传；

对于鼠标触发的 onStartEdit，直接不传 focusPosition，让浏览器 selection 保留。

onStartEdit 里的 helper：

如果它现在有类似 ensureCaretAtStart() 这种操作，要么：

挪进 BlockEditorCore.applyProgrammaticCaret，统一处理；

要么加判断「只有当 intent !== 'pointer' 时才执行」。

一句话：所有 setSelection(...) 都要经过「你是 pointer 还是 keyboard」这道关。

4. 为了防止以后又反弹，可以写进规则文档

在你的 ADR / VISUAL_RULES 里可以加一条「Caret Ownership」：

Selection 的唯一 owner 是 BlockEditorCore。

只允许在以下情况主动设置 caret：

键盘在 block 之间跳转；

编辑器首次 autoFocus。

若用户通过鼠标点击进入某 block，任何层级（Core / ListEditor / ParagraphEditor）不得在该流程中调用 setSelection 或「把光标挪到行首/行尾」的 helper，selection 位置完全由浏览器原生决定。

把这段注释放在负责 caret 的 helper 文件顶部，再配合上刚才的 focusIntent 设计，Copilot 以后就会自觉绕开 pointer 流程，不会再给你塞新的 setSelection 进去。

5. 小结

你现在看到的“从第一个字扫到目标字”的现象，本质是双重 selection：浏览器一次 + 代码一次。

要彻底解决且不反弹，就要：

给焦点加一个「intent」：pointer / keyboard / auto；

把所有 setSelection 收到一个公共 helper 里；

在 helper 里：pointer 路径直接 return，键盘/auto 路径才真正去摆 caret。

再加一条规则写进 ADR：
「鼠标点击进入 block 不允许程序再干预 selection」，
后面你和 Copilot 调整代码时就有了稳定的护栏。

---

### 2025-12-03 收尾

- `selectionStore` + BlockEditorCore 已实现 focus intent store，pointer intent 直接放行浏览器 selection，其它 intent 统一过 `announce/clearFocusIntent` 管理。
- Nested editors（List/Todo）不再直接 setSelection，统一走 intent + ParagraphEditor/BlockEditorCore 入口。
- DDD_RULES / HEXAGONAL_RULES / VISUAL_RULES 已补充 Plan157A 的 caret ownership / intent 政策，方便后续评审。
- ADR-144（`assets/docs/ADR/ADR-144-plan157a-cursor-intent-store.md`）登记背景、决策、Guardrail，与 QuickLog 互相引用。
- 手动验证：普通段落、List、Todo 的 pointer 点击稳定；Enter/Backspace/Command flows 也能被 keyboard/command intent 正确接管。

Plan157A ✅