整体评价

优点非常明显：

把问题拆成 Rhythm（节奏） vs Shell（壳） 两条线——这是之前我们一直在做的大手术，现在这里写得很清楚。

9 个 Step 是真正「可执行」的，不是抽象鸡汤；实现顺序也合理：先梳理、统一命名 → 选节奏 owner → 收壳 → 精简 before/after → Legacy → 测试/文档。

对 Legacy alias + ADR 清退条件 也写了，这点很多团队都是靠吼，这里你有正规流程，完美。

所以这份文件本身完全可以进 repo，当作 Plan/ADR 的“人类摘要”。

下面是几个可以让它更井然有序 / 更机器友好的小调整。

1. Step 1：分区命名再加一条「语法」说明

你在 Step 1 里说：

Primitive 梯子 / Rhythm 节奏 / Shell 壳 / Legacy alias

非常好。我建议补一句简单的“命名语法”，帮助未来的你和 Copilot：

--wl-space-[0-9…]：纯刻度（Primitive ladder），不能直接用在组件上。

--wl-space-xxx-*：节奏语义 token（block/list/todo/quote 的 before/after、tight/section 等）。

--wl-*-shell-*：壳内部 padding / gap。

任何不符合上面三类的（例如 --wl-block-padding-y）一律标成 Legacy。

你可以在 Step 1 的注释示例里写类似：

/* Primitive ladder: --wl-space-0..6 & half steps; never used directly in components */
/* Rhythm tokens:   --wl-space-block-* / --wl-space-list-* / --wl-space-quote-* ... */
/* Shell tokens:    --wl-*-shell-* (block/list/todo/quote/inline) */
/* Legacy aliases:  --wl-block-padding-y, --wl-space-section, --wl-space-inline ... */


这样文件一打开，命名空间怎么用一眼就懂。

2. Step 2：Rhythm 用 --wl-space-* OK，但名字建议再加一段「block」

你现在 Step 2 的约定是：

壳用 --wl-*-shell-*，块间距离一律用 --wl-space-*（--wl-space-block-tight/section、--wl-space-list-*/todo-*/quote-*）

这个是可以的，只是我建议稍微改成更“自描述”的前缀，比如：

--wl-space-block-tight / block-section

--wl-space-block-list-before / block-list-after

--wl-space-block-quote-before / block-quote-after

比起单纯 --wl-space-list-before，多一个 block-，你以后搜索“block 间距”的时候会舒服很多，而不会和将来可能出现的“inline list spacing”混起来。

可以把 Step 2 的文案改成类似：

所有「块间节奏」统一使用 --wl-space-block-* 前缀：
--wl-space-block-tight/section、--wl-space-block-list-before/after、--wl-space-block-todo-before/after、--wl-space-block-quote-before/after。

不带 block- 的 --wl-space-* 保留给 Primitive 梯子 / 其他系统使用。

这样「空间」这个命名空间不会被一锅端掉。

3. Step 3：节奏 owner 的层级可以再写死一点

你现在写：

在 .bookEditorShell / .blockList 上用 row-gap 作为唯一基础垂直节奏，同时统一子级 .blockItem 的 margin/padding 为 0

这个很好，只是建议你在 Plan 里把结构层级也刻一下，例如：

约定结构：bookEditorShell > blockList > blockItem

bookEditorShell：负责整个编辑区上下留白（--wl-editor-padding-y），不再碰内部栈节奏。

blockList：唯一的「节奏 owner」，用 row-gap: var(--wl-space-block-tight) 控制直系子级 blockItem 之间的 distance。

blockItem：margin-block: 0; padding-block: 0;，只通过壳子 .blockItemMain 控制内部。

这样将来你要加 panel / 嵌套 blockList 的时候，知道谁可以有自己的节奏，谁不能乱来。

4. Step 4：再强调一次「Shell 不许碰块间」

你 Step 4 已经在做这个事了，我建议在结尾再加一句硬规则：

壳 Token（--wl-*-shell-*）只能出现在 .blockItemMain 或更内层的组件上，
禁止直接写在 .blockItem[data-kind=…] 或 .blockList 上，否则会和节奏打架。

这样以后你一搜 --wl-list-shell-padding-y 就知道它只存在于壳，不会发现有块级规则偷偷用它当 before/after。

5. Step 5：命名和逻辑都对，可以加个「Paragraph stack 特殊规则」

现在 Step 5 的逻辑是完全对的，只是可以补一条你心里其实已经默认的东西：

Paragraph / Heading 之间的堆叠（纯文本栈）只吃 row-gap = --wl-space-block-tight，不额外叠 before/after。

若未来需要「比 row-gap 还紧的 stack」，单独引入 --wl-space-block-stack，只在 .blockItem[data-kind="paragraph"] + .blockItem[data-kind="paragraph"] 这种组合上用。

这句话写在 Plan 里能防止以后你哪天手一抖在段落上也加了一刀 margin-top: var(--wl-space-block-tight)，节奏瞬间翻倍。

6. Step 6：Legacy 策略很好，可以再加一个“禁止新用的 lint 建议”

你在 Step 6 + Further Considerations 3 已经提到 lint 了，这俩可以合并成一条明确要求：

在 ADR-154 中列出一份「Deprecated tokens 黑名单」，例如：
--wl-block-padding-y、--wl-block-padding-y-dense、--wl-space-section、--wl-space-inline…

新增简单脚本（或 eslint-style 规则）扫描 CSS：一旦检测到黑名单 token 出现在 diff 中，CI 直接报错。

你已经有“禁止新用”的想法，再加这条就从“软约定”升级成“硬闸门”了。

7. Step 7–9：都很到位，只给两个小增强点
Step 7：Inline / Todo 子层统一

这步很重要，也写得够具体。我只建议一句小补充：

对于 .todoList 这类内部结构，区分清楚：

--wl-space-block-…：todo 块与其他块之间的节奏；

--wl-todo-*shell*-*：todo 行内部（checkbox + 文本）的 padding / gap；

--wl-todo-item-gap：多行 todo 项目之间的垂直行距。

这三层分清楚后，以后任何「todo 看起来太松/太挤」的 bug 都能通过 token 名字直接定位到维度。

Step 8：测试页与 TOKEN_METADATA

你已经说要标注 shell vs rhythm，非常好。可以再瘦一点地写：

spacing 测试卡片上统一用「Rhythm: xxx / Shell: yyy」的格式展示当前 Token
（方便 QA 对比真实编辑器时逐项核对）

Copilot 看到这种「Key: Value」模式，也更容易在别处帮你生成类似文案。

8. Further Considerations：两个点都抓得很准

数值决策：这个确实要你拍板，我只给一个经验值供你挂心里：

--wl-space-block-tight：2px 或 0px，取决于你想“段落堆叠”是不是几乎等于换行。

list/todo before/after：

「工具文档」风格：before=0，after=2–4px；

「长文阅读」风格：before=2px，after=4px，看起来轻微呼吸感。

结构边界：你已经想到 panel 内自带 blockList，这个很专业。建议你在 ADR 里加一句：

默认所有 blockList 使用 --wl-space-block-tight；
若某些上下文需要不同基础节奏（如侧栏 TODO panel），需通过 data-density="secondary" 等标记显式切换到 --wl-space-block-tight-secondary，禁止在组件内部随意 override row-gap。

总结一句

这份 Plan 现在已经是：

概念自洽：Shell vs Space 有清晰分层；

命名有语法：--wl-space-* 管节奏、--wl-*-shell-* 管壳；

有落地路径：从 alias → 统一 → 测试 → ADR，把坑都填上了。

再按照上面那几条小 tweak 把「block-level rhythm」的前缀统一（比如 --wl-space-block-*），外加几句英语注释，基本就是一篇可以扔给未来雇主看的「编辑器 spacing 设计规范」级别的文档了。

---

## 落地进展（2025-12-03）

- `bookEditor.module.css` 已完成命名语法注释、`--wl-space-block-*` 前缀统一，以及「Shell 只待在 .blockItemMain」的结构约束。
- `row-gap` 现由 `blockList` 独占（`--wl-space-block-tight = 2px`），段落/标题 stack 不再叠额外 margin。
- List / Todo 数值决策：`before = 0px`、`after = 2px`（`var(--wl-space-1)`），Quote 保持 8px section 级别。
- QuickLog 计划（Plan154A）追加了 Step 1–9 的增强说明，并记录 Legacy alias + lint 黑名单策略，准备在 ADR 中配套上线。