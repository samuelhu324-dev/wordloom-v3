因为 Tag 本质上是一个“小小的独立系统 + 多对多关系”，而你又想把它“随手贴”在 Library / Book 上，结果就是：
边界一多、形状一不统一，就特别容易 422 + 各种不匹配。

我按“为什么 tag 尤其爱出事”拆开说，你一对照自己代码，大概能立刻看到是哪几类。

1. 422 的本质：前后端对“形状”理解不一样

在 FastAPI / Pydantic 里，422 一般就两个原因：

字段缺 / 多

后端 model 要 tags: list[int]

前端发的是 tags: [{"id": 1, "name": "Lab"}]
→ 形状不对，直接 422。

类型不对

后端要 List[int]，你传了 ["1", "2"] 或 [null]；

后端要 Optional[str]，你传了 {} 或某个奇怪结构。

Tag 系统几乎必然涉及：

嵌套 list（一个 Book 多个 tag）

新旧 tag 混在一起（有 id、有只带 name 的新建 tag）

这比单纯的 title: string 复杂太多，很容易让 DTO 和前端 state 产生“形状错位”。

2. 为什么偏偏是 Tag 爱出「不匹配」？
2.1 UI 要的是“名字”，后端要的是“ID”

典型矛盾：

用户在前端操作的是：["翻译", "学习日志", "EN-ZH"] 这些 名字；

你的数据库真正关系是：book_id ↔ tag_id；

于是中间必须有一层 mapping：

name → Tag(id, name, color) → 中间表 book_tags(book_id, tag_id)


这中间任何一步没写清楚就会变成：

前端直接把名字数组丢过去，后端却在等 id 数组；

一会儿传 id，一会儿传对象 { id, name }；

新建 tag 时，有的接口在 book DTO 里顺便塞新 tag 名，有的接口要求先单独调用 /tags…

结局就是：你自己都记不住哪个接口要什么形状，422 就成日常了。

2.2 Tag 常常是「多对多」，状态很多步

Book 创建/更新时，大概有这些情况：

只挂已有 tag：[1, 2, 3]

创建新 tag 再挂上去：["翻译", "学习"]

旧 tag + 新 tag 混着：["翻译", {id: 3, name: "EN-ZH"}]

删除某些 tag：[1, 3]，原来有 [1,2,3]

于是你后端的逻辑经常长成：

for tag_payload in payload.tags:
    if "id" in tag_payload:
        # 关联已有 tag
    else:
        # 创建新 tag 再关联


再加上事务 / 唯一约束 / 回滚：任何一个步骤抛异常，前端看到的可能就是一个莫名其妙的 422 或 500，而且 对象一半更新、一半没更新，就变成“难修”的那种 bug。

2.3 Tag 的“系统定义” vs “用户定义”混在一起

你现在已经有：

系统状态：seed / growing / stable / legacy（其实不应该放 tag 域）

用户标签：翻译实验室 学习日志 …

如果在某个时间点，它们都通过同一套接口、同一张表、同一种 DTO 往返，就容易出现：

有的地方当它是“状态”，只允许单选；

有的地方当它是普通 tag，多选、多删；

结果前端/后端逻辑写坏了，删一个 tag 把状态也删没了，或者相反。

这种“语义没分清”的错，一旦混进代码里，就会变成非常难清理的历史包袱。

2.4 Cache / 本地 state 跟服务器 Tag 列表不同步

还会有一类典型 bug：

前端缓存了一份 tag 列表；

你在另外一个页面新建/重命名/删除了某个 tag；

回到之前页面，该页面还在用旧列表，提交时发了一堆已经不存在或名字冲突的 tag；

后端一看：id 不存在 / 唯一约束冲突 → 422 or 409。

这种 bug 在 Tag / Category / Label 这种“被复用很多地方的小对象”上特别高发。

3. 怎么把 Tag 系统从「易炸」变成「能预测」？

给你一个“减雷”版的约定，可以直接写进 RULES / API 文档：

3.1 对外只用 “id 列表”，不要在 Book DTO 里塞完整 Tag 对象

API 约定：

POST /tags
Body：{ name: string, color?: string } → 返回 TagDTO {id, name, color}

GET /tags
返回你所有可见 tag 列表。

PUT /books/{id}/tags
Body：{ tagIds: number[] }
语义：整体替换 这本书的 tag 集合。

前端做的事：

UI 里维护两份 state：

allTags: TagDTO[]

selectedTagIds: number[]

提交之前只发 tagIds 数组；

如果用户输入了一个不存在的 tag 名：

先调用 POST /tags 拿到新 id；

然后把 id 放进 selectedTagIds 再调用 PUT /books/{id}/tags。

这样就不会出现：

有时候发 {id, name}，有时候发 "name"，有时候发 id；

后端每个接口都要写一遍“到底是创建还是关联”的判断。

3.2 Status（seed/growing/stable/legacy）从 Tag 域里搬出去

之前我们说过那句：

Status ≠ Tag

所以：

在 Book 聚合里放 status: BookStatus（枚举或 Value Object）；

Tag 聚合只管“用户自定义标签”；

API 上也是两个字段：

{
  "status": "stable",
  "tagIds": [1, 2, 3]
}


这样你在修 tag 相关 bug 时，就不用担心动到 lifecycle 状态；
Chronicle/统计里也更清楚到底是谁出了错。

3.3 一定要看 422 的详细错误信息

FastAPI 返回 422 时，Response 里一般会带类似：

{
  "detail": [
    {
      "loc": ["body", "tags", 0, "id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}


这实际上已经告诉你：“我在 body.tags[0].id 那里没找到字段”。
很多人调 tag 系统的时候，只看到 HTTP code 就骂 422，其实只要看 detail，很快就能对上是前端 shape 错了还是后端 pydantic 模型错了。

4. 简短总结一句

Tag 系统之所以特别容易冒出 422 和各种“不匹配”，是因为它同时踩中了这几颗雷：

多对多 + 列表嵌套；

UI 用名字，数据库用 id；

新建/复用/删除 3 种动作混在一个请求里；

有时还把“系统状态”也塞进同一套机制。

只要你把协议简化成：

Tag 自己是一个小聚合，用 /tags 单独 CRUD；
其它实体只通过 tagIds: number[] 跟它说话；
Status 另起一行。

再配合认真看 422 的 detail，这类 bug 的数量会直线下降，而且就算出了问题，也不会是那种“我都不知道从哪修起”的类型，而是“某个接口发错 shape，一眼就看见”的那种。

///////////////////////////////////////////////////////////////////////////

Plan: 对齐 Tag 简化策略并起草 ADR-090
TL;DR: 将 Plan34 的 Tag 形状/协议简化（独立 CRUD + 他域仅使用 tagIds + Status 分离 + 422 诊断指引）系统化写入三大规则文件：HEXAGONAL_RULES.yaml（端口/路由/多对多与上下文隔离）、DDD_RULES.yaml（聚合边界与枚举分离）、VISUAL_RULES.yaml（前端状态管理与交互契约）；新增 ADR-090 记录“Tag 协议收缩与防错策略”并列出迁移步骤与回滚策略。

Steps
标注规则映射: Plan34 要点 → 分类成 Architecture(端口/路由)、Domain(聚合边界)、API Contract(请求形状)、UI(State) 四块。
HEXAGONAL_RULES 增补: 路由顺序规范(/tags/most-used 优先) + Adapter 不做多动作（创建 vs 关联拆分）+ 多对多只暴露 tagIds + 错误 422 解读指引。
DDD_RULES 增补: Tag 聚合职责限定(不含 BookStatus) + Book.status 枚举独立 + Tag 与状态分离的“不混合”规则 + 多对多流程图（create→get id→replace）。
VISUAL_RULES 增补: 前端双状态 allTags[] / selectedTagIds[] 维护规范 + 新建流程 (先 POST /tags 再 PUT 关联) + 409/422 处理模式与缓存失效策略。
起草 ADR-090 结构: 背景 / 问题 / 决策 / 方案细节(协议表) / 迁移步骤 / 风险与回滚 / 不在范围 + 和旧实现差异对照。
汇总中文提议清单: 每文件新增章节标题与关键字段名、示例 JSON、错误示例 & 正确示例对照。
交付前检查: 去重已有相关条目（避免与现有 POLICY/CONVENTION 冲突），标记需要废弃的旧 Tag 用法说明。
Further Considerations
是否同时统一 ErrorResponse 格式？Option A 保留 FastAPI 默认 / Option B 全局包装。
迁移顺序建议：先文档与规则 → 后端路由/DTO 调整 → 前端调用改造 → 数据清理脚本。