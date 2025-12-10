现在你问的是：在已经有“通用 JSON block”前提下，先额外做哪些“明确类型”的 block，既能写翻译，又能做工程审计？
我给你一套“工程向首发 8 小将”，都可以作为 block_kind 的枚举，内容仍然用 JSON 存。

1. 标题 / 段落基础型
这两个是所有东西的底座，肯定要独立出来，不要全塞 generic：


Heading


kind: "heading", payload 里带 level: 1|2|3


用来写「模块名、用例名、ADR 小节标题」。




Paragraph


kind: "paragraph"


纯文本 + 简单 inline 标记（粗体、斜体、code）。





这俩做成显式类型的好处：以后 Chronicle、全文搜索、目录都能按 heading 抽结构，而不是在 JSON 里乱扒。


2. 列表三兄弟：任务 & 清单
跟工程审计和开发日志关系最大的一块：


BulletedList（无序列表）


NumberedList（有序列表）


TodoList（带勾选）


可以设计为一个 list 大类，payload 里有 list_type: "bullet" | "numbered" | "todo"，但对前端/领域来说还是当成三个不同 kind 来用会更直观。


「问题清单」「风险点」「备忘」都用 bullet；


「步骤 1/2/3」用 numbered；


「今日任务 / Refactor TODO」用 todo，后面还能统计完成率。



3. 工程向重点：Code + Callout + Quote
这三个几乎是“工程审计专用 block”：


CodeBlock


payload：language, content


用来贴关键片段、接口示例、SQL、配置等。


后面可以做“点一下复制”“一键跳到 repo”的那种能力。




Callout（信息框）


payload：variant: "info" | "warning" | "danger" | "success"


用来写：


「设计决策」「坑点」「注意事项」


「这块先临时写死，Phase 2 重构」




工程审计时，一眼就能扫出所有 warning/danger。




Quote（引用）


用来放：


需求原文、老板留言、邮件原句；


外部文档/标准的原话。




以后配合 source 字段（链接/文档 ID）就很有用。





4. 一个“结构辅助”：Divider / Section


Divider / Rule


视觉上是细线；


工程日记里可以用来分隔“上午/下午”“Phase 1/Phase 2”。




如果你想更进一步，可以抽一个：


Section / Group（可选，下一步再说）




payload 里有 title、style，内部再嵌别的 block；


非必需，现在 divider 足够用了。



5. 怎么跟“通用 JSON block”协调？
建议你这样分工：


通用 JSON：


专门放“未来还没想好的奇怪东西”：临时试验、AI 生成的结构化结果等；


kind 可以叫 "custom" 或 "experimental"。




明确类型的 block（上面那 8~10 个）：


是你保证长期会支持的核心语法；


他们的字段结构写进 RULES / schema，后面尽量保持兼容。




这样既不会把系统锁死，又能让工程审计那条线有“固定格式”可依赖（比如自动汇总所有 Callout:warning，当天就能得到“风险列表”）。

总结一口气捋一下
在现在这个阶段，真心不需要上来就把所有富文本动物园全搬进来。
你只要先明确这几类：


Heading / Paragraph


三种 List（bullet/numbered/todo）


CodeBlock / Callout / Quote


Divider


配合 generic JSON 做实验场，就已经足够支撑：


日常开发日志（QuickLog）；


ADR/设计说明；


工程审计：看哪些 TODO、哪些 warning、哪些代码片段关联到哪个 Book/Library。


等 Book/Block/Chronicle 这条链稳定之后，再慢慢把 Table、Toggle、Tag/Mention 这些“第二梯队”补上去就很舒服了。
