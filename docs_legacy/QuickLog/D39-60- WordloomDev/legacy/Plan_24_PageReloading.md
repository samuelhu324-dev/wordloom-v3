我直接给你一套「Library 正门」的刷新规则规范 + 实现思路，你以后 Bookshelf/Book 也可以照抄。

一、整体原则：Wordloom 的“刷新哲学”

不整页刷新，只做局部状态更新
用户在当前列表滚到哪儿，就停在哪儿，不跳闪、不回顶部。

乐观更新（Optimistic UI）为主，后台校准为辅
操作一按，UI 立刻变；网络只是“确认一下+纠错”。

弱反馈，而不是弹窗狂魔

成功：顶部/右上角一个小 toast「已更新」「已删除」，1.5–2 秒消失即可。

失败：toast + 回滚 UI。

列表视图是 Library 的“真相快照”

所有编辑结果最终要在这个界面收敛：名称、说明、封面、Pin、计数、时间。

列表自身不做复杂逻辑，只消费后端给的字段。

二、按操作拆：点击后 UI 应该怎么变？

下面都假设你用了某种库（react-query / SWR），但逻辑和库无关。

1. 插入/更换封面（upload/replace cover）

**用户动作：**点卡片上的“更换封面”，上传图片，点保存。

立刻的 UI 行为：

上传成功返回 coverUrl（带版本参数，比如 .../cover.jpg?v=3）。

该 Library 卡片上的封面图立即换成新图。

别用 window.location.reload()，只改这一项。

同时在列表模式的小缩略图也更新（本质是同一个 coverUrl）。

后台行为：

mutation 成功后：

可选 invalidate "libraries" 再拉一次，保证计数等字段同步；

但要注意不要把用户当前排序/过滤状态弄丢。

失败时：

封面退回旧图（用旧的 coverUrl）；

toast：「封面更新失败，请稍后重试」。

2. 更新内容（重命名 / 修改说明）

**用户动作：**在详情页面点“保存”，或在列表行内编辑名称/说明。

UI 规则：

保存成功 → 列表上的这一行立即更新

名称/说明文本改掉；

如果有 updated_at / last_activity_at 字段，也一并更新；
若当前排序方式是“按最近活动”，列表位置可能会挪动。

若你支持“回车即保存”的 inline-edit，建议：

输入框失焦 → 显示新文本，右上角小 loading；

接口失败再把文本改回旧值。

失败：

文本回滚；

inline 编辑框重新聚焦，并弹错误提示（例如：名称重复、长度过长）。

3. 删除 Library（移去 Basement）

你已经有 Basement 概念，所以可以这样：

点击删除后的 UI 行为：

列表中该 Library 立即淡出/收缩消失（乐观删除）。

页面底部出现一句：

「已移至 Basement 回收站。撤销」
“撤销”按钮 5–10 秒内有效。

后台行为：

实际是 soft delete：设 is_archived = true / 移入 Basement。

“撤销”就是把这个标记改回去。

失败情况：

如果删除 API 挂了：

把刚才从列表消掉的那一项再加回来；

toast 告诉用户「删除失败」。

列表刷新：

成功后，可以：

本地 state 里真的删掉那一行（不等重新 fetch），

后台悄悄 invalidate "libraries"，以防有别的统计字段受影响。

4. Pin / Unpin

Pin 很适合乐观更新，而且你有“正门大厅”的概念，可以做得有仪式感一点。

点 Pin：

当前项的 Pin 图标立即切换状态；

同时该 Library 跳到 Pinned 区域顶部（如果你采用“置顶区 + 普通区”的布局）；

若当前排序不是“Last activity”，排序逻辑保持不变，只是 pinned 的优先展示。

技术上：

前端先在本地 state 里改变 pinned 字段 + 调整排序；

后台调用 /libraries/:id/pin；

成功：无事发生；

失败：把 pinned 状态和位置回滚，toast 一句错误。

5. 新建 Library

创建成功后：

如果创建是在 modal 里完成，关掉 modal 的同时：

列表顶部插入一条新项（默认排序按“创建时间/最近活动”时）；

若当前列表被筛选过滤（search keyword）：

如果新建的名称不匹配搜索关键词，可以不显示，减少“诡异闪现感”；

或者在列表顶部临时高亮该行，告诉用户“这是刚创建的项”。

实现：

后端返回完整的 Library 对象；

前端把它直接 setLibraries(prev => [newLib, ...prev])；

后台可选再 invalidate 一次，以保证统计字段完全一致。

三、技术实现层面的推荐套路
1. 用 react-query / SWR 管理 Library 列表

举个抽象套路（伪代码）：

const { data: libraries, mutate } = useSWR("/api/libraries");

const updateLibrary = async (id, patch) => {
  await mutate(
    // optimistic update
    prev => prev?.map(lib => lib.id === id ? { ...lib, ...patch } : lib),
    { revalidate: false } // 先别立刻打接口
  );
  try {
    await api.patch(`/libraries/${id}`, patch);
    await mutate(); // 再次从服务端拉，做校准
  } catch (e) {
    // rollback
    await mutate(); // 直接重新拉远端数据
    toast.error("更新失败");
  }
};


Pin、更新封面、改说明都可以复用这个模式，只是 patch 不一样。

2. 统一一个「LibraryListStore」

如果你嫌每页都写一遍很烦，可以：

在 modules/libraries 里搞一个小 store（zustand / jotai / context 都行）；

所有操作都通过一组 action 完成，比如：

librariesStore.actions.update(id, patch)
librariesStore.actions.remove(id)
librariesStore.actions.insert(newLibrary)


Copilot 很适合帮你写这些“按 id 更新数组”的小样板。

四、跟 Wordloom 的风格怎么对齐？

从你现在 UI 和产品气质来看，可以加几个小细节，让体验更“wordloom 味”：

删除 → Basement 文案

toast 用「已送入 Basement 回收站」

撤销按钮叫「把它捞回来」。

Pin 的文案

比如叫「Pin to Lobby」/「显示在大厅顶部」

让用户感受到这真的是“正门大厅”的概念，而不是一个技术属性。

更新后的轻微动效

列表项更新后，轻微高亮一下 300ms，再淡回去；

Pin 移动时可以做一个稍微顺滑的位移动画，不要瞬移。

总体来说，只要你做到：

所有操作都是“按完立刻看到效果”（乐观更新）；

整个页面从不整页刷新 / 白屏；

失败时会自动回滚，不会留下半死不活的状态；

那就既符合业界规范，又和 Wordloom 的“书房型产品”气质很搭。