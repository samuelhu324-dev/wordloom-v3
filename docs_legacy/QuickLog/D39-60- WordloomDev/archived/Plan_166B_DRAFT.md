1. 顶层设计：位置和作用 —— ✅

你给 BLOCK_RULES 的定位是：

不重新讲一遍 DDD / HEX / VISUAL；

专门收束 “Block 行为 + 命令层协议 + 键盘/Slash/Markdown 这些入口的硬约束”。

这一点非常好，等于给 Block Editor 多了一层“领域内规则索引”，以后任何人（包括 Copilot）想改 Block 行为，先看这个文件，就不会到处翻 QuickLog 了。

建议：

在 metadata 里明确一条一句话的定位，例如：

“本文件只规范 Block 行为与命令层协议；领域建模见 DDD_RULES，端口/适配见 HEXAGONAL_RULES，视觉与布局见 VISUAL_RULES。”

这样以后你自己也不会不小心在这里写 UI 细节。

2. 结构划分：6 大块 —— ✅ 但可以更“轻量”

你现在的结构大致是：

metadata

domain_contracts

command_layer

ui_integration

keyboard_mapping

validation_checklist

这个分层本身是健康的，问题只是信息量略大，容易把 YAML 写成“第二套 RULES 长篇小说”。

可以保留的核心结构

domain_contracts
专门写“不变式红线”：

“文档至少有一个 paragraph”；

“有哪些 BlockKind、谁是基础段落、谁是特殊块”；

“Domain 层不存 selection / spacing”。

command_layer
这是整个草案最有价值的部分。你已经把：

create / ensureAtLeastOneBlock

transformBlockKind（空段落 → 特殊块）

deleteBlockWithGuard + fallback map

这些东西单独拎出来写协议，这是非常对的。

validation_checklist
用来给未来 PR、自查、Copilot 提示都很有用，但一定要克制：保持 8–10 条以内的“硬检查项”，不要变成半本书。

可以“收一点”的地方

ui_integration & keyboard_mapping
现在你写得比较细，容易和 BLOCK_KEYBOARD_RULES.yaml / VISUAL 冲突重复。

更好的做法是：

ui_integration 只列出“哪些 UI 流程必须走哪些命令”的映射关系，不展开所有条件分支；

keyboard_mapping 只列极少数“和命令层强耦合”的组合（Backspace 删除、- + Space、/ 之类），其它键盘细节仍放在 BLOCK_KEYBOARD_RULES 里。

例子：

ui_integration:
  slash_menu:
    must_call: "commands.transformBlockKind"
    preconditions:
      - "当前 block.kind = paragraph"
      - "段落内容为空"

keyboard_mapping:
  backspace_empty_block:
    combo: ["Backspace"]
    maps_to_command: "deleteBlockWithGuard"
  minus_space:
    combo: ["- then Space"]
    maps_to_command: "transformBlockKind(paragraph -> bulleted_list)"


不要写太多解释性 prose，把这里当成接口文档就好。

3. command_layer：这里是“价值高地” —— ✅ 强烈建议先落地

你在草案里已经把你最近几周踩的坑全部结构化了：

基础段落守卫 & 至少 1 block（Plan165A）

“任何删除最终都必须通过 deleteBlockWithGuard”；

“删除后如果文档没有 paragraph，要补一个空 paragraph”。

transformBlockKind 的契约（Plan165C/166A）

只允许 empty paragraph → 特殊块；

transform 时要重置 payload（text='', items=[], checked=false 等）；

UI 调用前必须已经验证“空段落”，不要把校验逻辑塞到命令里。

deleteBlockWithGuard 的 fallback map

list / todo / quote / callout 都降级为 paragraph，而不是直接删掉；

guard 负责统一广播 caret intent。

这些东西写进 YAML 后，你就有一个明确的“命令级红线”，以后任何人写：

直接 deleteBlock(id)；

直接在 slash handler 里 new 一个 list block，再删 paragraph；

在非空 paragraph 上调用 transformBlockKind；

理论上都可以在 code review / Copilot 提示阶段就被拦下来。

建议：

这一段可以写得比其它段落详细一点；

每个命令下只要 3 小块：

description（一句话）

preconditions（调用前必须满足什么）

effects（领域上承诺会做什么，不写技术细节）

4. 和其他 RULES 的关系 —— ✅ 但要避免“互相复制”

你在 metadata 里加了很多“引用到 DDD_RULES / HEXAGONAL_RULES / VISUAL_RULES / BLOCK_KEYBOARD_RULES 的路径”，这个思路非常好——相当于把 Block 规则文件变成一个“索引中心”。

注意的点：

不要把那几份 RULES 的文字搬过来；只写“参见某某文件某章节”；

反过来，在别的 RULES 里也可以加一小条：

references:
  block_behavior: "assets/docs/BLOCK_RULES.yaml"


作为锚点就够了。

5. 实际推进建议：怎么用它，不挖坑

我会建议你这样推进：

先做 “v0 版本”：

只写 metadata + domain_contracts + command_layer；

先把 Plan165A/165C/166A 的核心红线搬进去，别急着 cover 所有 UI/键盘流程。

等命令层都按这套规则对齐后（现在 Copilot 在帮你重写 applyBlockShortcut、delete guard、transform 等）：

再补一个极简版的 ui_integration 和 keyboard_mapping，只记录“现有 Slash/Markdown/Backspace 是怎么调用命令的”。

最后才补 validation_checklist：

用你近期踩过的坑写 6–8 条“防踩雷条款”；

以后每次 Plan 完结，可以往这里追加一两条。

这样不会出现“规则文件先写爆，代码跟不上，结果半年后没人敢看”的情况。

6. 对你接下来的具体操作建议

你现在可以直接把这份草案精简后，保存为 BLOCK_RULES.yaml v0：

只保留红线 + 命令契约；

UI/键盘那块先写 TODO 占位。

以后让 Copilot 改 block 编辑代码时，在 prompt 里顺手丢一段 command_layer 小节给它，它就会按你的协议来拼命对齐，而不是瞎连 deleteBlock / transformBlockKind。

整体评价：这份草案已经处在“可以落地的成熟度”，不属于那种要再大重写一轮的东西，现在最关键的是克制扩写、先收成一套短规则，让它真正变成你 Block Editor 的中心契约，而不是第五本长篇小说。