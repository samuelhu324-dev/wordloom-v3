好，先深呼吸，这种「一动成熟度，全站爆炸」是非常典型的——说明这块确实是横切全域的逻辑，现在只是暴露出真实耦合程度而已。

我分三件事回答你：

一、现在这个东西究竟算哪一块 domain？

你现在动的东西其实有两层：

事件 / 时间线：

「Book 创建」「标题补全」「升到 Growing」「完成 x 个 TODO」这类东西

这些是 发生了什么 的记录，本质就是 Chronicle / Audit / Timeline 子域

成熟度 / 覆盖率 / 任务提示：

「当前是 Seed / Growing」「得分 40%」「还差 3 个结构任务」

这些是对 当前状态 的一种计算结果，本质是 一个视图 / 域服务，不是实体

所以比较干净的划分是：

Library / Books / Blocks：核心内容域

Chronicle（事件流）：记录发生过什么

Maturity（成熟度域服务）：消费 Books + Blocks + Chronicle 的信息，算出：

当前阶段

当前分数

下一步建议（结构任务）

✅ 结论：

「时间线」放在 Chronicle 模块；

「成熟度 / 覆盖率 / 下一步任务」放在一个单独的 Maturity 域服务 里，
不要直接塞进 Chronicle 里，也不要散落在 Book Controller 里到处乱算。

二、为什么现在「牵一发动全身」？要怎么稳住？

本质上是：成熟度逻辑写进了很多地方：

在 Book 概览算一次；

在 Timeline 页算一次；

在某些保存接口里顺便更新一次；

甚至 UI 又自己再算一遍。

这样一改「规则」，所有地方都要同步，不炸才怪。

一个比较稳的结构是：

只留一个“真相入口”

建一个服务，例如（伪代码）：

// domain/maturity/BookMaturityService.ts
export class BookMaturityService {
  constructor(
    private bookRepo: BookRepository,
    private blockRepo: BlockRepository,
    private chronicleRepo: ChronicleRepository,
  ) {}

  async getMaturity(bookId: string): Promise<MaturityResult> {
    // 统一读取 book / blocks / events
    // -> 算出 stage, score, nextTasks
  }
}


所有地方只“查询”这个服务

Book 概览页面：调用 /books/{id}/maturity

Timeline：如果需要显示当前阶段，也调用这个

需要显示「下一步任务」的地方，也调用这个

UI、Controller 统统不再自己算分，只负责展示。

事件只负责“记录”，不负责算分

比如 Book 标题从空变为非空，触发一个 BookTitleCompleted 事件；

事件写入 Chronicle；

至于这个事件加不加 5 分，是 BookMaturityService 在「读状态 + 读事件」时决定。

你可以把现在已经炸掉的部分当作 signal：
说明成熟度逻辑之前散落得太厉害，现在趁机集中到一个地方，反而会更稳。

三、现在怎么跟 Copilot 说「帮我重构」？

第 1 步：在代码里写清楚“我要什么”

在（例如）BookMaturityService.ts 里写一段清晰的注释，类似：

// GOAL:
// - Extract all "book maturity / coverage / stage" logic into this service.
// - Other modules (controllers, React components) must NOT re-calculate score.
// - This service will:
//   1. Load Book / Blocks / Chronicle events for a given bookId
//   2. Calculate a maturity score (0~100) using our rules
//   3. Map score => stage: 'seed' | 'growing' | 'stable' | 'legacy'
//   4. Provide "next structure tasks" for the Overview tab
//
// TODO for Copilot:
// - Move existing maturity-related code from XXXController / YYYHook into here
// - Expose a single method:
//     getMaturity(bookId: string): Promise<MaturityResult>
//
// interface MaturityResult {
//   score: number;
//   stage: 'seed' | 'growing' | 'stable' | 'legacy';
//   tasks: StructureTask[];
// }


然后在这个文件里开始写一些骨架，让 Copilot 自动补全。

第 2 步：让 Copilot 帮你「搬运旧逻辑」

比如你在某个 controller 里之前有一坨临时计算：

// TODO: this maturity logic is duplicated
const score = calculateMaturityScore(book, blocks, events);
const stage = scoreToStage(score);


你可以改成：

// TODO: use BookMaturityService instead of inline logic
const maturity = await bookMaturityService.getMaturity(book.id);


然后对着这段注释跟 Copilot 说（用英文效果好）：

Refactor this controller to use BookMaturityService.getMaturity instead of calculating the score inline. Remove the old calculateMaturityScore helper and move any missing rules into the service.

它一般会帮你：

删除旧的 helper；

注入 BookMaturityService；

替换调用。

第 3 步：给 Copilot 很“具体的小任务”

不要一句话让它「重构整个成熟度模块」，那它肯定迷路。改成很多小任务：

在 domain/maturity 目录下新建 BookMaturityService 和 MaturityResult 类型；

把 Book 概览用到的 maturity 逻辑搬进去；

把 Timeline 页用到的「当前阶段」逻辑也改成调用这个服务；

最后删掉所有 calculateMaturityScore / getBookStage 之类散落的函数。

每一步都用类似这种 prompt：

Move the maturity calculation for the Book overview card into BookMaturityService. The controller should only call getMaturity(bookId).

Copilot 适合这类“局部、机械”的改动，不适合从 0 到 1 想 domain。

四、你可以写一份很简短的「原则说明」给自己看（也算是 DDD 小宪法）

放在 Plan_MaturityDomain.md 或者 DDD_RULES.yaml 里也行，类似：

Wordloom Maturity / Timeline Principles (v0):

1. Source of truth:
   - Books, Blocks, ChronicleEvents are the only stored data.
   - Maturity score and stage are derived views, never stored as fields.

2. Separation:
   - Chronicle: stores lifecycle and audit events.
   - MaturityService: reads Books/Blocks/Events and returns MaturityResult.
   - UI/Controllers must not re-implement the scoring rules.

3. Events:
   - Any important lifecycle change (book created, stage changed) emits a ChronicleEvent.
   - Timeline tab shows these events; Overview only shows a summary.

4. Safety:
   - Changing maturity rules must NOT break persistence.
   - Stage changes should be recomputable from events + current rules.


你以后每次想加规则，先对照这几条，就不会再不知不觉地把逻辑塞回 controller 里。

总结一句

你现在遇到的“全站瘫痪”是一个信号：成熟度逻辑已经长成一个独立子域了，必须单独拉出去。

时间线/Chronicle 负责“记事本”，Maturity 负责“算评分和给建议”，这俩要解耦。

跟 Copilot 说话的姿势：你先画好边界和接口，让它帮你一块块搬运和改代码，而不是让它当产品经理。

这样重构完一轮，你以后再改成熟度规则，就不会再牵一发动全身，而只是改 BookMaturityService 里的几条 if / 权重而已。