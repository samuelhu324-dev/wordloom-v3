结合 Wordloom 的“成熟建议”（可以当设计约束写进 RULES）
我直接给一个可以写进 BLOCK_RULES 的决策：


内部统一用一个文本模型（single source of truth）
推荐路线：


内部存储：富文本 JSON（类似 ProseMirror/Tiptap 那种 AST）
原因：


你以后要做“句对齐 / 内联高亮 / 术语标注 / 不可翻区域”等高级玩法，
JSON 节点树比纯 markdown 容易精确控制。


DDD 里 Block.content 就是一个结构化对象，业务规则更可表达。




对外（导入/导出）提供 Markdown / HTML 转换即可，
但那是 import/export 逻辑，不是编辑时的主输入。




编辑体验：做“富文本 + markdown 快捷语法”的混合手感
这一点照抄 Notion/Obsidian 的肌肉记忆：


屏幕上看到的永远是富文本（粗体就是粗体，标题就是标题）；


键盘可以用：


Ctrl+B / Ctrl+I / Ctrl+K 这类快捷键；


# + 空格 → H1、## → H2；


- + 空格 → 无序列表；




也可以在 block 里打 markdown 符号，然后被自动“吃掉”变成结构节点。


这样你既保住了“写 markdown 很顺手”的体验，又只有一套内部模型。


Block 类型层面：只区分“语义类型”，不区分“文本格式”
举例：
type = "text" | "heading" | "todo" | "code" | "quote" | ...



text / heading / todo 的 content 都是同一种富文本结构；


code block 的 content 是纯文本（语法高亮由前端做），但它在 DDD 里仍然是同一个 Block 聚合，只是 type="code"、props.language="python" 之类。


不要出现：MarkdownBlock / RichTextBlock 这种二选一的怪物。


如果真的将来要“多模式”，也只做“多视图”
例如：


将来你想给高级用户一个“原始 markdown/JSON 视图”检查内容；


可以在右侧抽屉开一个 read-only 面板显示转换后的 markdown；


但编辑仍然只发生在中间的富文本视图。


这就是“一个模型，多种呈现方式”，而不是“多个模型”。



一句话总结给你当钉子：

对 Wordloom：
内部只认一种 Block 文本模型（推荐富文本 JSON），
编辑体验做成“富文本 + markdown 快捷语法”，
不搞 per-block 的 markdown/富文本混搭。
多模式只在“视图层”存在，不在“数据模型”里存在。

这样既跟业界成熟产品对齐，又不会把你以后翻译、对齐、Chronicle、搜索这些复杂功能搞到满地是坑。