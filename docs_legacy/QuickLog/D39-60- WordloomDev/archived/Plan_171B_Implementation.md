Plan: 为 Shift+Enter 软换行补 BLOCK_RULES 规则
简要结论：
需要在 BLOCK_RULES.yaml 里补充一小段关于“软换行语义 + 判空 + 键盘映射”的规则，用来锁死：Shift+Enter 只改行内文本、不走 block 命令层；然后按这个约束去改 ParagraphEditor/命令层/判空/测试。

Steps
在 BLOCK_RULES.yaml 的 domain_contracts 里新增一个软换行子项，定义 \n 的语义和判空规则。
在 BLOCK_RULES.yaml 的 keyboard_mapping 区域增加一条 Shift+Enter 映射，明确“只插入软换行，不触发 deleteGuard / list_family_exit / keyboardDecider”。
（可选加强版）在 ui_integration 下加一个 inline_soft_break 小节，写清入口是 ParagraphEditor.onKeyDown，必须在顶部拦截并调用 inline 命令。
基于上述规则，列出实现触点：ParagraphEditor / 列表&todo编辑器 / 文本命令（insertSoftBreak）/ 判空 helpers / 渲染层 / 测试文件，供实现时逐项勾选。
建议写回 BLOCK_RULES 的规则片段（中文）
1）domain_contracts：新增 soft_break_semantics

  soft_break_semantics:
    summary: "Shift+Enter 软换行只影响行内文本，不改变 Block 结构"
    rules:
      - "软换行在内容层使用 '\\n' 或等价 soft-break API 表示，同一 Block 内允许出现多行文本。"
      - "isEmpty / deleteGuard 判空时，文本仅包含空白字符（含空格、Tab、'\\n'）仍视为“空”，不得因为软换行改变退出语义。"
      - "列表/待办 family 中，软换行不得单独触发 block 级退出或 deleteBlockWithGuard，只能在当前 item 内换行。"

放在 domain_contracts 最后一个子项之后即可：

2）keyboard_mapping：新增 soft_break_shift_enter

  soft_break_shift_enter:
    combo: ["Shift+Enter"]
    context: "Inline 编辑状态下的 paragraph / list-item / todo-item"
    command: "仅在当前 Block 文本中插入软换行（'\\n'），不创建/删除 Block，也不触发 list_family_exit 或 deleteBlockWithGuard。"

紧挨着 backspace_empty_block 附近放一条，方便 review 时对比“软 vs 硬”：

3）ui_integration（可选，但推荐）：inline_soft_break 入口说明

  inline_soft_break:
    entrypoint: "ParagraphEditor.onKeyDown / InlineEditor"
    behavior:
      - "Shift+Enter 必须在 onKeyDown 顶部拦截并处理后 return，不再透传到 keyboardDecider 或 block 级命令。"
      - "实现层通过 paragraphCommands.insertSoftBreak（或等价 inline 命令）仅更新当前文本与 caret offset，不调用 create_block / delete_block_with_guard / transform_block_kind。"

在 ui_integration 最后追加一个轻量小节，锁死入口和“不碰命令层”的红线：

实施层执行方案（给实现 agent 的导航清单）
编辑器 & 命令入口

ParagraphEditor / 统一 inline 编辑组件

在 onKeyDown 顶部加 if (e.key === 'Enter' && e.shiftKey) 分支：preventDefault() → 调用 paragraphCommands.insertSoftBreak() → return。
确认普通 Enter 仍走原有 handleInlineEditorKeyDown / keyboardDecider，不受影响。
列表 / Todo 行编辑组件（ListItemEditor / TodoItemEditor 或对应 inline shell）

复用 ParagraphEditor 的 onKeyDown 或复刻同样的 Shift+Enter 分支，保证：
软换行只在当前 item 文本中插 \n；
不新建/删除 item；
不让事件继续冒泡到 list_family_exit / block 级删除。
文本命令层（如 paragraphCommands / blockCommands 内的文本操作模块）

新增 insertSoftBreak：读取当前文本 + caret offset，插入 '\n'，写回文本，并把 caret 移动到 offset+1。
只更新当前 block 文本，不调用 createBlock、deleteBlockWithGuard、transformBlockKind 等命令。
渲染 & 判空

文本渲染组件（段落、列表项、todo 文本显示处，例如 .textBlockContent 或行内 <div contentEditable>）

若已使用 white-space: pre-wrap（当前看你已在 bookEditor.module.css 里这么做），确认列表/todo 文本同样生效；否则在对应 class 上补上。
目标：文本中的 \n 在 UI 中显示为同一 bullet/checkbox 下的多行。
判空 helpers / deleteGuard 前置判定

搜索所有用于 list/todo 退出、backspace 删除空 block 的 isEmpty / isTextEmpty / allItemsEmpty 函数，将逻辑调整为：
例：const normalized = text.replace(/\s+/g, ''); const isEmpty = normalized.length === 0;
保证“只包含空格、Tab、\n 的情况”仍然被视为空，从而不会因为软换行堵住 list/todo 的退出通路。
决策器 & 测试

keyboardDecider

不需要改 Enter/Backspace 分支，但可以在注释中说明：Shift+Enter 在编辑器层被拦截，不会传到此处。
验证它的 allItemsEmpty / isEmpty 输入已经按上面的软换行判空规则处理。
Vitest 测试（已有 ListBlock / TodoListBlock / keyboardDecider 测试）

增补用例（可以分散在对应测试文件中）：
段落软换行：初始 "abc|def"，Shift+Enter 后 "abc\n|def"，block 数不变。
列表项软换行：item "item|1" → "item\n|1"，仍是一个 item，不触发 keyboardDecider 的 block 级决策。
空列表 + 连续 Shift+Enter：唯一空 item，多次 Shift+Enter 只插入 \n，不触发 list_family_exit 或 deleteBlockWithGuard。