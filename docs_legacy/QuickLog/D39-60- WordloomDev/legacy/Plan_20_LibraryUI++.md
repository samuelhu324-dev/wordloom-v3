二、结合 Wordloom，这个页面我会怎么设计排序逻辑？

假设你这个页面显示的是 Library 卡片，每个 Library 下面还有 Bookshelf / Book。

1）默认排序：按“最近活动时间（Last activity）倒序”

“最近活动时间”建议定义成：
这个 Library 或它的任何下级（Bookshelf / Book / Block）被编辑、创建、删除、移动时，都刷新一次 last_activity_at。

这样用户只要在某个书架里干过活，这个 Library 就会自动浮到最前——非常贴合“工作区”的直觉。

你现在卡片下方已经有 today、views，那就再加一个内部字段：last_activity_at，用它来排序就行。

2）支持手动置顶：Pinned libraries

在默认“最近活动排序”的基础上再加一层规则：

第一段：Pinned（置顶）Libraries

用户手动点一个小“钉子”图标，把某些长期的核心库固定在最上面。

这一段的排序方式：纯手动拖拽 或 “在 pinned 里也按 last_activity_at 排”都可以，
我偏向“允许拖拽”，给用户多一点控制权。

第二段：普通 Libraries

用前面说的 last_activity_at DESC 排序。

第三段：Archived / Basement

你的 Basement 本来就是“回收站/地下室”，这类库可以：

要么完全不出现在主列表，只在 Basement 页面。

要么在主列表的最底部，用一个“已归档”小标签淡淡显示。

3）排序切换：给右上角加一个 Sort 下拉

你现在右上角已经有 view switch（grid / list）了，很自然可以加一个 Sort：

Sort by：

Last activity（默认）

Created time

Name (A → Z)

Most viewed（有一天你要做使用分析的时候就能用了）

逻辑是：

视图切换（网格 / 列表）只影响展示形态，不改变排序规则。

排序规则统一在一个 dropdown 里控制，用图标 + 文本（比如：⏱ Last active）。

三、你问的关键：编辑之后“要不要跳位置”？怎么“更新书架”？

结合上面的实践，我建议你这样定义行为：

当用户在某 Library 下：

新建 / 删除 / 重命名 Bookshelf

在 Bookshelf 里增删 Book 或 Block

保存 Book 的内容修改

……这些都算“活动”

触发的时候：

更新：

bookshelf.last_activity_at = now()

library.last_activity_at = now()（级联）

回到 Libraries 页面时：

如果当前排序模式是 Last activity：

这个 Library 卡片会自动排到前面（除非被置顶区拦着）。

如果当前排序是 Name / Created time：

排序不变，只更新时间信息，不打乱用户的 mental map。

这就对应了你问的：

「时间顺序，修订顺序？」

你可以把默认的“修订顺序”理解为：按 last_activity（最后活动）时间倒序。

真正是否“跳位置”，由当前用户选的排序规则决定。

总结一份“靠谱参考方案”给你拍板：

业界成熟组合：

默认：

顶部有 Pinned / 收藏区，手动拖拽排序。

其余项目按 Last activity（最后编辑/打开时间）倒序。

排序可切换：

Last activity / Created time / Name / Most viewed。

编辑行为：

更新项目自己的 last_activity_at，并向上更新父级（Library）。

仅在当前排序依据是时间时，卡片位置会发生调整。

归档 / 回收：

Basement 单独视图，或者永远沉在最底部。