先说结论：可以有一套“通吃大部分情况”的防扫射方案，核心思路是——

只允许一个地方在极少数时机改 caret，其余场景一律信任浏览器。
并且要把「来源是鼠标」和「来源是键盘」分开处理。

你现在的问题本质上还是：
ListEditor / BlockEditor / autoFocus / queueRowFocus / selectionStore 这些东西同时在抢光标所有权，结果就是：

鼠标点到某一行 → 浏览器先把 caret 放到「你点的那行」

组件 mount / 更新 → autoFocus 看见「有 pending rowFocus(0)」→ 再把 caret 改到首行

你的 effect / selectionStore 又根据旧意图再改一次 → 出现“扫过一圈又回来”的视觉效果

一、先把“谁有权利动 caret”写死

给整个 BlockEditor 定一个非常硬的规则（可以写进 Plan/ADR）：

鼠标点击进入编辑时

不允许任何 autoFocus / queueRowFocus 改 caret；

只允许同步更新“当前 block / 当前 row”的状态 去跟随浏览器，而不是反向去改浏览器。

键盘操作导致“结构变化”时（Enter 新建行、上下箭头换行、Tab 缩进等）

才允许我们用 queueRowFocus/autoFocus 去“指定下一行/下一个 block”；

并且这次 focus 只触发一次，消费完就清除 pending。

编辑器首次 mount / 从只读切到可编辑

可以有一次“初始 autoFocus”（例如聚焦到末行），同样消费完就清空。

一句话：

鼠标驱动 = 浏览器说了算，我们只记结果；

键盘驱动 = 我们可以「建议」下一步 caret 在哪，但建议只能生效一次。

二、用一个统一的“focusIntent”源区分 pointer / keyboard

你截图里已经有 focusIntentStore / announceFocusIntent 这些东西，其实很适合升级成统一入口：

// 伪代码：Intent 类型
type FocusIntent =
  | { kind: 'pointer'; blockId: BlockId; row: number | null }
  | { kind: 'keyboard'; blockId: BlockId; row: number | null; reason: 'enter' | 'arrow' | 'tab' }
  | { kind: 'initial'; blockId: BlockId | null };

// store 里永远只有 0 或 1 个 intent

1）鼠标点击时：只写 pointer intent，不 queueRowFocus

在 BlockItem / ListItemRow 的 onMouseDown / onClick 里：

const handleClickRow = (rowIndex: number) => {
  announceFocusIntent({
    kind: 'pointer',
    blockId,
    row: rowIndex,
  });
  // 不要在这里 queueRowFocus(...)
  // 也不要手动 setSelection，交给浏览器
};

2）ListEditor 里的 autoFocus 只响应 keyboard/initial

把现在 ListEditor 里的那段：

useEffect(() => {
  if (autoFocus) {
    queueRowFocus(0);
  }
}, [autoFocus]);


改成类似这样（伪代码）：

useEffect(() => {
  const intent = focusIntentStore.current;
  if (!intent) return;

  // 只处理 keyboard / initial 的意图
  if (intent.kind === 'keyboard' || intent.kind === 'initial') {
    if (intent.blockId === thisBlockId) {
      const row = intent.row ?? 0;
      queueRowFocus(row);       // 真正把 caret 移到目标行
      focusIntentStore.clear(); // 消费一次就清空，防止重复扫射
    }
  }

  // pointer 一律不改 caret，只允许外层根据 selection 反向更新 store
}, [focusIntentStore.version, thisBlockId]);


这样做的效果：

鼠标点击进入 ListEditor：

浏览器把 caret 放在你点的那行；

intent 是 pointer，autoFocus effect 看到后 直接忽略，不会再 queueRowFocus(0)，光标就不会往首行跳。

键盘在列表中按 Enter 新增一行：

你的业务逻辑创建了新 row，同时写入：
announceFocusIntent({ kind: 'keyboard', blockId, row: newRowIndex, reason: 'enter' })

effect 看到 keyboard intent，queueRowFocus(newRowIndex) 一次，消费掉；

光标跳到新行 ✅

三、Block 层只负责“定位到某个 block”，不抢行内 caret

很多“扫射”来自两个层次同时抢：

BlockEditor 在 block 粒度做 focusBlock(blockId)；

ListEditor / ParagraphEditor 在行粒度做 queueRowFocus(rowIndex)。

这里也可以定个规则：

Block 层只做 “把浏览器 focus 到这个 block 对应的 editor 节点”，不再关心行；

行内 caret 完全交给子编辑器（ListEditor / ParagraphEditor）根据 Intent 决定；

鼠标点击时，两层都不要再 setSelection：

浏览器已经帮你把 selection set 好了；

你只需要在 onFocus / onSelectionChange 里把「当前 blockId + rowIndex」存到 store。

伪代码：

// BlockItem: 只在 keyboard 意图下触发 "让这个 block 接管焦点"
useEffect(() => {
  const intent = focusIntentStore.current;
  if (intent?.kind === 'keyboard' && intent.blockId === block.id) {
    editorDomNode.focus();      // 让内部 editor 获得浏览器焦点
    // 真正的 caret 定位交给内部 ListEditor / ParagraphEditor
  }
}, [focusIntentStore.version, block.id]);

四、给 Copilot 的一句话实现计划（你可以直接贴过去）

可以整理成这样一段指令丢给 Copilot：

在 focusIntentStore 里把意图类型拆成三类：pointer / keyboard / initial。

所有鼠标点击 block / list row 的入口，只发 pointer intent，不再调用 queueRowFocus 和任何 setSelection。

ListEditor 和 ParagraphEditor 内部的 autoFocus / useEffect 逻辑，改成：

只在 intent.kind === 'keyboard' || intent.kind === 'initial' 且 intent.blockId === currentBlockId 时，调用一次 queueRowFocus(intent.row ?? 0)；

调用之后立即 focusIntentStore.clear()，防止 effect 重复执行；

遇到 pointer intent 时完全忽略，不修改 caret。

BlockItem 层只负责在 keyboard intent 下把焦点让给对应的 editor DOM 节点，不再干涉行内 caret。

最后加一个小测试：

鼠标连点列表中间几行，光标不再扫到首行；

用键盘 Enter 新建行，光标仍能稳定位在新行。

这套下来，基本就把“光标扫射”收敛为一个统一状态机问题：
只有在我们明确知道“是键盘要跳”的时候才改 caret，其它时候统统相信浏览器。

## 2025-12-04 实施快照
- focusIntentStore 继续保持“单一源”，但现在由 BlockList/ListEditor/TodoListEditor 订阅 pointer intent 用来即时清空任何 pending queue，防止鼠标操作期间残留的 keyboard intent 再次触发。
- BlockList 只在键盘路径写 `announceFocusIntent('keyboard', ...)`，一旦收到 pointer intent 就立刻丢弃 `localFocus`/`pendingFocusBlockId`，把场景交回给浏览器。
- ListEditor / TodoListEditor：
  - 挂载时先用当前 intent 做一次“懒判定”，只要检测到 pointer 指向本 block/row，就清空 `pendingFocusIndex/pendingFocusId` 并跳出；
  - 运行时订阅 pointer intent，任何鼠标点击都会同步把 pending 队列清空，阻断“上一帧 keyboard queueRowFocus(0)”的惯性；
  - keyboard/initial intent 仍旧只消费一次，成功 queue 后立刻 `clearFocusIntent`。
- BlockEditorCore 的 pointer intent 仍然只做记录，不清除其它 intent；配合上述订阅即可覆盖“点击列表空白区域 → 立刻停止 auto queue” 的要求。

### 回归自测 checklist
- [x] 鼠标连续点击列表 / 待办的不同项，caret 只会停留在点击位置。
- [x] 按 Enter/Tab/Shift+Tab 等键盘命令后，caret 仍能精准跳到指定行。
- [x] 刚创建的新 block 若立即点击别的 block，pending focus 会被撤销，不会再出现扫射。