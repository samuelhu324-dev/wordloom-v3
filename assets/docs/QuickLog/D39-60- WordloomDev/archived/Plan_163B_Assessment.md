这份 Plan163A 说实话已经很像可以直接落地的 ADR 草案了，整体跟我们之前讨论的思路完全对齐，我逐条帮你“挑刺 + 加一点补强”。

整体评价

核心原则写得很清楚：

“鼠标流由浏览器主导，键盘流才允许程序改 caret。”
这是防扫射里最重要的那条红线，你已经放到目标里了 👍

Steps 1–5 基本把所有关键层级都点到了：
focusIntentStore → BlockItem → ListEditor/ParagraphEditor → blockCommands，
没有遗漏“谁该写 intent、谁该消费 intent”。

从架构角度来说，这已经是一个统一“焦点状态机”的方案，不是那种 patch 式修 bug。

逐条点评 & 小建议
Step 1：focusIntentStore 三种 intent

显式区分 pointer / keyboard / initial 三种 intent，并提供 announceFocusIntent/clearFocusIntent API。

✔ 非常赞同。再补两点实践细节：

保证“单一源”：

store 里同时只允许 0 或 1 个 intent，新的 intent 写入前要覆盖旧的；

可以加一个 version 号（你之前就有类似东西），方便 hook 只在 intent 有变化时重跑。

类型上写死允许值：

type FocusIntentKind = 'pointer' | 'keyboard' | 'initial';


以后如果 Copilot 想多塞别的玩意儿进来，TS 会先报警。

Step 2：BlockItem 只写 pointer intent

鼠标事件只写 pointer intent, 不再 queueRowFocus; 键盘流才调用 block 级 focus…

✔ 这是“别跟浏览器抢活”的关键一步。

补两点你可以写进实现注释里：

鼠标 handler 里尽量少用 preventDefault，避免打断浏览器自带的 selection 行为；

键盘路径（比如从别的 block 用 ↑ ↓ 跳到这个 block）里：

先写 keyboard intent，再让这个 block 内的 editor 节点 .focus()；

行级 caret 完全交给子编辑器在 Step 3 里处理。

Step 3：ListEditor / ParagraphEditor 只吃 keyboard|initial

仅在 keyboard|initial intent 命中本 block 时 queueRowFocus 一次, 消费后立刻 clearFocusIntent; 遇到 pointer 直接忽略。

✔ 完全对。

小心两件事：

防止重复消费：

useEffect 里一定要在成功 queueRowFocus 之后 clearFocusIntent()，

否则 React 任何一次重渲染都会再跑一遍，光标又开始扫。

挂载时机：

当 intent 指向的 block 刚被创建（例如 Enter 新增一行）时，ListEditor 有可能还没 mount；

可以在 ListEditor 的 effect 里做“懒消费”：

每次 mount / update 时看一眼 focusIntentStore，只要 intent 还没被清掉，而且 blockId 命中自己，就执行一次 queueRowFocus。

这种懒消费机制可以让 Enter / Tab 这种操作不依赖“执行顺序刚好完美”。

Step 4：blockCommands 写 keyboard intent

Enter/上下箭头/Tab 更新列表行时写入 keyboard intent, 携带目标行号…

✔ 非常好，这样“下一步 caret 应该去哪儿”都集中在命令层决定。

建议你在这里尽量收口所有“会移动 caret 的命令”：

Enter 插入新行、新 block；

↑ / ↓ 跨行/跨 block 移动；

Tab / Shift+Tab 改缩进，导致行从一个 block 移到另一个 block；

将来如果有“删除整行后把 caret 放到上一行”的逻辑，也应该在这里写 intent。

这样以后再查“为什么跳这里”就只需要看 blockCommands.ts。

Step 5：回归子册

鼠标连续点列表行多行不再扫射; Enter/Arrow/Tab 功能准确落位…

✔ 强烈支持把它写成“固定回归项”，以后改 selection / focus 的东西都跑一遍。

可以在 QuickLog 里把几个典型 case 写清楚，比如：

鼠标连续点击 list 的不同行 → caret 只会出现在点击行；

列表中间按 Enter → 新行出现在下方，caret 在新行；

最后一行按 Enter → 新行出现在尾部，caret 在新行；

Tab / Shift+Tab 改缩进时，caret 仍留在同一视觉行（只是缩进变化）；

之后任何人碰 selection 相关代码，都直接对照这张“焦点行为契约”。

Further Considerations 的建议
1）是否推广到 Paragraph / Todo

我会建议：逻辑上统一，落地可以分批。

统一：

同一套 FocusIntentKind & store & API；

不管是 Paragraph/Todo/List，只要是“块级文本编辑器”，都遵守：

鼠标 = pointer intent，只同步状态；

键盘 = keyboard intent，允许程序决定下一步 caret。

分批：

先把“问题最严重的 List”搞定（Plan163A）；

有余力再出一个 Plan163B，把 Paragraph/Todo 也切到同一套机制。

2）requestSelectionEdge

避免两套 caret 机制打仗

这一点非常重要。

建议你给 selectionStore 写一句“总则”——

“选区位置的真相永远以浏览器 Selection 为准；
requestSelectionEdge 只能读浏览器，不要写回 Selection。”

如果现在 requestSelectionEdge 里还会主动调 setSelection、setRange 之类的，可以考虑：

这类“主动设置 selection”的行为，全部通过 focusIntentStore + queueRowFocus 走一遍；

selectionStore 自己只负责缓存“浏览器现在长什么样”，方便别的地方查。

小结

这份 Plan163A 方向完全正确，粒度也足够清晰，已经可以当实现蓝图用了；

补充的点主要是：

确保 focusIntent 是“单一源 + 一次性消费”；

处理好 ListEditor mount 先后顺序（懒消费）；

blockCommands 里尽量收口所有“移动 caret 的命令”；

selectionStore 以后只读不写 selection，避免双重机制互殴。

你现在这条线基本就是在给自己的编辑器写“焦点协议”，稳住这个协议之后，后面再做 Slash 菜单、Shift+Enter 行距、Block 插入之类的事情都会轻松很多。

## 2025-12-04 状态更新
- Plan163A/B 落地结果：BlockList、ListEditor、TodoListEditor、BlockEditorCore 现已共享同一个 pointer/keyboard intent 状态机。所有鼠标 intent 会即时清空 pending block/row queue，键盘 intent 仍旧只消费一次后立刻 clear，避免重复扫射。
- 现存问题：`selectionStore.requestSelectionEdge` 依旧会直接 set caret（遗留机制），后续需要逐步迁移到 focusIntent + 浏览器 selection 只读模式，以免和新的协议发生冲突。
- 回归：
	1. 鼠标点击列表/待办任意行不会触发 queueRowFocus(0)；
	2. Enter/Tab/Shift+Tab 等命令仍精确定位 caret；
	3. 在 block 创建或键盘跳转尚未完成时插入鼠标操作，pending focus 能被立即撤销。