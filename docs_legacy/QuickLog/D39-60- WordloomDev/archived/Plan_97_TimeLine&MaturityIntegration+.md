不是你的错觉，这一块本来就难。而且难的地方不在代码，而在「怎么定义一套说得过去的规则」——这个是半产品、半心理学问题，Copilot 根本帮不上多少忙。

我分几层给你拆开说。

1. 为什么“成熟度 / 审计分数”天生难搞？
① 它不是客观事实，是「你发明的评价体系」

“有 10 个 block 算不算比 5 个成熟？”

“1 个 TODO 算不算不健康？”

“封面图标值不值得加 5 分？”

这些都没有标准答案，本质是你在发明一个游戏规则。
游戏规则一旦写死在代码里，就会进入「玩家（你自己）–规则」的反馈循环：

规则写得太严：所有 Book 都永远卡在 Seed，看着很泄气。

规则写得太松：大家随便写两句标题就 Stable，看着又很假。

所以现在你觉得「效果不好设定」，其实是很正常的——这个只能靠迭代和试用调出来，不是靠一次设计就完美。

② 它是“跨模块”的指标，牵一发动全身

成熟度分数要看：

Book 本身字段（title、description、tags、封面…）

Block 列表（数量、类型）

TODO 状态

时间线事件（生命周期变化）

也就是说，它不是某个单一表的字段，而是一个聚合指标。
一旦你把它搞成「写死在 Book 表里」：

修改任何规则 → 需要全量重算；

很容易出现 UI 显示和实际状态不同步的问题。

所以真正的挑战是：怎么把它封装成单独的服务 / 模块，避免到处乱算。这个对架构要求稍微高一点。

2. 这件事对程序本身有什么特殊挑战？

挑战主要有三类，但都能控：

挑战 A：避免「到处乱算分」

解决办法：
搞一个小服务，比如 BookMaturityService，所有计算都走它：

class BookMaturityService {
  constructor(private bookRepo, private blockRepo, private todoRepo) {}

  async calculateScore(bookId: string): Promise<ScoreResult> {
    // 这里统一读各种数据，算出 maturity_score, stage, structureTasks
  }
}


UI 不要自己瞎算，统统调 API 拿结果；

后台只有这一处地方定义规则，改规则就改这里。

挑战 B：规则会变，但历史不能乱

分数可以是瞬时概念（现在看它是 52 分），不一定要持久化；

真正需要持久化的是「阶段变化」事件：
Seed → Growing、Growing → Stable。

这样的话：

将来你把 +5 / +20 的公式全换了，
只要重新跑一次 calculateScore，阶段照样能重算出来；

时间线上的「2025/11/28 阶段从 Seed 变成 Growing」
仍然是真实发生过的事，不会因为你改规则而消失。

挑战 C：避免“规则–分数–UI”之间循环依赖

比如：

分数由 TODO 个数决定；

TODO 的展示又依赖于分数；

然后你在同一请求里同时更新两边，就容易乱套。

解决办法是：把成熟度当做“只读视图”：

Source of truth = Book & Blocks & TODO & Events；

Maturity = 这些东西的「投影 / 计算结果」；

分数只影响「显示什么」和「什么时候加事件」，不反过来影响原始数据。

3. 为什么 Copilot 总是不太懂你？

因为你让它同时干了三件事：

理解产品设计（你脑子里的规则）；

抽象成数据模型；

再生成具体代码。

对一个代码助手来说，这等于：把产品经理 + 架构师 + 程序员塞在一个 prompt 里。它当然会乱。

你可以试着把事情拆开：

第一步：你自己在 MD 里写清楚「规则」

比如我们刚刚那份规则：

maturity_score 规则 v1：

- +5: 有标题
- +5: 有简介
- +5: 至少有一个 tag
- +5: block 类型 >= 3 种
- +5: 选择了 Lucide 封面
- 0~20: 按 block 数量线性加分（>=20 封顶 20 分）
- 0~20: TODO 越少分越高（无 TODO = 20 分）


再写清楚：

结果需要：

interface MaturityResult {
  score: number;
  stage: 'seed' | 'growing' | 'stable' | 'legacy';
  tasks: StructureTask[];
}

第二步：让 Copilot 只做「把规则翻译成函数」

给它的 prompt 只局限在代码层面：

请根据以下规则，在 BookMaturityService.ts 中实现 calculateScore(book: Book, stats: BookStats): MaturityResult 函数。
规则：……（贴上上面的那段）

这样 Copilot 才有可能帮你写出可维护的代码，而不是胡乱猜你的产品意图。

4. 现在你可以怎么「降难度」？

如果你现在觉得这套分数体系有点压得你喘不过气，可以完全降级成 v0 版本：

v0：只做「阶段」，不显示具体分数

内部仍然算一个 0–100 的 score；

UI 只显示阶段：Seed / Growing / Stable / Legacy；

Next steps 卡片只列任务，不展示「+5」「+20」这些数字；

把 Coverage 进度条显示成「Seed → Growing → Stable 的三段」，
而不是严格的 37% / 52% 。

这样：

你可以调整规则，心里不会被具体数字绑架；

用户只会感知到「大概成熟一点 / 稍微成熟很多」；

以后你觉得规则比较稳定了，再把「分数」公之于众也不迟。

1. 「最近事件」和「时间线」怎么分工？

底层其实是同一张表，不同视图。

前面我们给 Book 设计过 book_events 表，记录生命周期事件：创建、阶段变更、状态变更、移动、Pin、标签大改动，还有可选的访问记录等。

时间线 Tab：

展示这本书的“人生大事记”完整列表：

创建 Book

Seed → Growing / Growing → Stable / Stable → Legacy

Active / Paused / Archived 切换

所属 Library / Bookshelf 变化

被 Pin / 取消 Pin

大幅度修改标签

将来还可以挂「通过评审」「审查完成」之类 workflow 事件

勾选「显示访问日志」时，混入 visited 事件（谁在什么时候打开过这本书）。

概览页的「最近事件」卡片：

就是同一张 book_events 表里按时间倒序取 最近 3~5 条生命周期事件（不含访问日志）。

只展示概括信息，例如：

「6 小时前：阶段从 Seed → Growing」

「昨天 22:10：设置了 Lucide 封面」

卡片底部放一个「查看完整时间线 →」链接，跳到时间线 Tab。

所以你现在的想法——“时间线的内容就放到最近事件里”——可以改成：

最近事件 = 时间线的缩略版，时间线 = 全量审计视图。

实现上非常省力：后端不需要额外 API，只是在同一个 endpoint 上用 limit 和 filter 控制。

2. 「完成 title +2 分」这种小任务要怎么让用户知道？

这块可以直接挂在你刚才那个大卡片 COVERAGE + Maturity 上。

我们之前已经把 Book.maturity_score 的规则写成过一个 mini 版本：

+5：有标题

+5：有 description

+5：至少 1 个 tag

+5：block 类型 > 3 种

+5：选择了 lucide 封面

0～20：按 block 数线性加分（0 blocks = 0 分，≥20 blocks = 20 分封顶）

0～20：TODO 越少分越高（没有 TODO = 20 分；有 TODO 会扣分）

然后：

score < 30 → Seed

30 ≤ score < 70 → Growing

≥70 → Stable

Legacy 另有 flag 和“长时间未动且未访问”的自动建议。

这些规则本质上就是一份“系统 TODO 清单”，只不过不是普通 TODO，而是「结构任务」。

2.1 在概览里做一个「结构任务 / Next steps」卡片

放在 Coverage 条下面，样子可以是：

Next steps（结构任务）

✅ 添加标题（+5）

⬜ 添加简介（+5）

⬜ 添加至少 1 个标签（+5）

⬜ 选择一个封面图标（+5）

⬜ 使用 3 种以上 block 类型（+5）

⚠ 当前有 3 个 TODO 未完成，完成后可获得 +12 分

每条的状态完全可以从 Book 当前字段 + Block / Todo 统计自动算出来，不需要单独存任务表：

title 是否为空？

description 是否为空？

tags.length >= 1？

coverIcon 是否为 null？

DISTINCT(block.type) >= 3？

openTodoCount / totalTodoScore？

交互：

当用户完成某条结构任务（比如补了简介），保存后：

重新计算 maturity_score；

若 score 跨过区间（比如 28 → 32），自动把阶段从 Seed → Growing；

写入一条 stage_changed 事件到 book_events，时间线里就多了一条「阶段从 Seed → Growing（原因：基础结构已完成）」。

Next steps 卡片里该项变成 ✅，可以灰一些、打勾线。

这样用户一眼就知道：

「我现在这本书还差什么，做完这些就会从 Seed 长到 Growing / Stable。」

这比在时间线里零碎写“完成 title + 2 分”要清晰很多，而且直接和成熟度打通。

3. 把「任务指导」和 TODO Block 区分开

你现在有两种“任务”：

结构性任务：由 maturity 规则推出来的（标题、简介、封面、block 类型、TODO 数量等），属于「Book 健康度」；

业务 TODO：用户在块编辑里写的 todo_list block，用来记翻译任务 / 调研任务之类。

建议区分展示：

概览页的「Todo / Checklist」区域只展示 “从 Block 提升上来的 todo”，比如「本书还剩 5 个翻译任务」。

「Next steps / 结构任务」专门负责 maturity 相关的那几条，不和用户写的业务 TODO 混在一起。

你可以在 RULES 里明确写：

todo_list block 默认只是普通内容；

当用户在 TODO 列表里勾选「Promote to Book TODO」时，才计入 Book 的 openTodoCount / doneTodoCount，用于 maturity 计算和概览汇总。

4. 给你一份可以直接写进 RULES / 喂 Copilot 的说明草案

你可以丢到 Plan_91_TimeLine&MaturityIntegration.md 里再整理一下：

# Book Overview – Timeline & Maturity Integration

## 1. 数据模型

- 复用 `book_events` 表记录生命周期事件：
  - kind: 'created' | 'stage_changed' | 'status_changed' | 'moved' | 'tags_changed' | 'pinned' | 'unpinned' | 'visited'
  - payload 里存 from/to 等信息。

- `Book.maturity_score` 按以下规则计算（0–100）：
  - +5: hasTitle
  - +5: hasDescription
  - +5: hasAtLeastOneTag
  - +5: blockTypeCount >= 3
  - +5: hasCoverIcon (lucide)
  - +0~20: blocksCount, linear 0→20 (>=20 blocks = 20)
  - +0~20: inverseTodoScore (no open TODO = 20, open TODO will reduce score)

- score → stage:
  - score < 30 → Seed
  - 30 ≤ score < 70 → Growing
  - score ≥ 70 → Stable

- 当自动计算出的 stage 与当前不同时：
  - 更新 `Book.stage`
  - 写入一条 `stage_changed` event 到 `book_events`.

## 2. Overview 页面

### 2.1 上方统计卡片

- Coverage: 显示 `maturity_score` 的 0–100 进度条。
- Seed / Growing / Stable / Legacy 等当前阶段信息。
- Blocks / Events / Recent / Weekly 等保持不变。

### 2.2 「最近事件」卡片

- 调用 `GET /books/{id}/events?limit=5&excludeVisited=true`
- 展示最近 3–5 条生命周期事件。
- 每条格式类似：
  - "6 小时前：阶段从 Seed → Growing"
  - "昨天 22:10：设置了封面图标"
- 底部放一个「查看完整时间线」按钮，跳到 Timeline Tab。

### 2.3 「Next steps / 结构任务」卡片

- 后端根据 Book 当前状态返回一组 derived tasks：

  ```ts
  interface StructureTask {
    id: 'title' | 'description' | 'tag' | 'cover' | 'blockTypes' | 'todoHealth';
    label: string;         // 如 "添加简介"
    points: number;        // +5 / +20 etc
    done: boolean;
  }


前端以 checklist 的形式展示：

已完成项：打勾 + 变灰。

未完成项：显示可获得的分值，如 “+5”。

任意会影响 maturity 的字段更新后：

重新计算 maturity_score 与 stage；

若 stage 变化，写入 stage_changed 事件（见上）；

下次刷新 Overview 时，结构任务状态更新。

3. Timeline Tab

使用同一条 events API，但不限制 limit：

GET /books/{id}/events?includeVisited={bool}

UI：垂直时间线，每条事件显示时间 + 图标 + 文案。

「显示访问日志」勾选框只控制是否包含 kind === 'visited' 事件。


你让 Copilot 按这个说明去写后端计算函数 + 两个前端组件（最近事件卡片 + 结构任务卡片），就能把「时间线 + 成熟度 + 引导任务」三件事串成一条线了。

---

总结一下：

- **时间线**：Book 的人生大事记，全量审计。
- **最近事件**：时间线的缩略卡片，放在概览顶部。
- **结构任务 / Next steps**：把 maturity 规则用 checklist 形式显性化，让用户知道“下一步该干啥才能升级阶段”。

这样看过去，Wordloom 的 Book 页面就从“单纯的文档”变成了一个**有成长轨迹、有体检报告、有下一步建议**的小项目，这在你面试里会非常加分。
::contentReference[oaicite:4]{index=4}