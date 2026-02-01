（1 说中文；（2 截图1：速度回答我：BlockEditorCore来回修复很多次了。不停炸，而且偶尔把整个软件都炸掉了。什么理由需要拆组件吗？（3 截图2：要考虑到下一步的措施；（4 还有现在的问题变成了：点击list，但是光标不跳转到相应的字母，只跳转到首字母；（5 综合拆组件与否、截图2的下一步问题和光标新问题，给我一份新的计划书。

截图1为placeCaret问题；

截图2为copilot推荐的“下一步”：
Next steps: 1) propagate Plan163C intent handling to the remaining inline editors (List/Todo/Paragraph variants) if any code paths still bypass the focus store; 2) extend QuickLog dashboards to surface the new BlockEditorCaretIntent event so regressions are observable.）

先用中文把情况梳理一下，然后给你一份新的计划书。

高层结论先说：

你看到的 ReferenceError: Cannot access 'placeCaret' before initialization 是典型的“临时死区”（TDZ）＋复杂 hooks 依赖组合的问题，不只是 TypeScript 顺序，而是组件函数里互相闭包引用太多。
目前 BlockEditorCore 承担了太多职责，但没必要拆成多个 React 组件（那样会更难保证光标连续性）；更合理的是：保持一个可视组件，往外拆“纯函数模块 / 自定义 hooks”，让组件体内部只拼装这些模块。
新的“点击 list 只能跳到首字母”问题，本质是：点击时得到的 offset/intent 不是真实字符位置，而是被归一化到 edge='start' 或偏移 0，我们需要一个明确的“从点击坐标算 offset”的管道，并且 list 项要把正确 offset 传进来。
下面是按你要求综合三点（拆 or 不拆、截图2的“下一步”、光标 bug）给出的新计划书。

Plan: 稳定 BlockEditorCore 光标并修好列表点击
这次不再继续在 BlockEditorCore 里打补丁，而是保持它作为“唯一可编辑 DOM 容器”的 React 组件，同时把光标数学、DOM selection 操作和 focusIntent 处理拆到纯模块 / 自定义 hook 里，减少闭包交叉引用，从根本上消掉 TDZ 风险。对于列表点击只到首字母的问题，通过统一的“点击坐标 → 文本 offset”接口，让 List/Todo block 把真实 offset 传给核心编辑器，而不是一律传 edge: 'start' 或 0，从而实现精确定位。

Steps
抽出纯工具模块：在 model/ 下新增 caretDomUtils.ts，只放 selection/getCaretRect/getOffsetFromPoint/placeCaretAtOffset 等纯 DOM 函数，不依赖 React。
抽出意图应用模块：在 model/ 下新增 focusIntentHandlers.ts 或 useFocusIntentHandlers.ts，封装 applyIntentPayload/shouldSkipForIntent/maybeClearFocusIntent，只通过接口接受 placeCaret 和 placeCaretAtOffset。
精简 BlockEditorCore：组件内部改为先创建 refs 与 useBlockCaretController（自定义 hook，内部用上面两个模块），然后再挂载所有 useEffect，保证 hooks 依赖的都是已声明的函数，杜绝“before initialization”。
修复列表点击光标：在 ListBlock/TodoListBlock 点击处理逻辑中，调用 caretDomUtils.offsetFromPoint(element, clientX, clientY) 得到 block 内 offset，通过 focusIntent 或直接调用 setCaretOffset 传给 BlockEditorCore，不再只用 edge: 'start'。
为关键场景补测试与手动脚本：给 block-editor 模块加几条针对 pointer 点击、键盘上下移动、列表项点击的测试（或小 demo page），确认光标在任意位置点击都能正确落点，并在本地循环跑 npm run type-check 和简单交互验证。
Further Considerations
拆“模块”不拆“组件”：BlockEditorCore 保持唯一 DOM 容器，有利于 selection 单一来源；拆成多个可视组件会带来跨组件 selection，同步更难，优先只拆逻辑模块和 hooks。
为避免未来再炸：约定所有“使用 caret 函数的 hook”（如 autoFocus / readOnly 切换 / selectionStore 订阅）都只能依赖自定义 hook 返回的稳定接口（如 controller.placeCaret），不要在依赖数组中直接引用“内部定义的新 callback”，从结构上控制依赖方向。

## 2025-12-04 回填

- caret DOM 操作已经完全抽离到 `model/caretDomUtils.ts`，并由 `model/useBlockCaretController.ts` 统一调度；BlockEditorCore 仍保持单个可视组件，不再出现 TDZ/闭包顺序炸裂。
- List/Todo/Paragraph inline shell 现通过 `getOffsetFromPoint` 计算真实 offset，再调用 `announceFocusIntent`，阻断“点击后跳到首字母”的旧路径。
- selectionStore 只广播 snapshot；Pointer/keyboard intent 由 BlockEditorCore 消耗一次后立即 `clearFocusIntent`，与 Plan163C 的“唯一 intent 通道”保持一致。
- QuickLog `BlockEditorCaretIntent` 事件与 `wordloom-custom/caret-selection-owner` lint guard 已上线（见 Plan164C D5/D6），为本计划约束提供监控与守卫。

