1️⃣ 最推荐方案：用「前后邻居 + 排序 key」双保险

这是很多编辑器/笔记工具背后常见的设计（Notion 一类），思路是：

位置 = 邻居关系 + 一个可排序的 sort_key
而不是单纯“第 17 段”。

1.1 Block 多加几列

给每个 Block 加这些字段（部分你已经有类似的了）：

Block
- id
- book_id
- sort_key          ← 排序用的数字（比如 10, 20, 30...）
- is_deleted
- deleted_at
- deleted_prev_id   ← 删除时它前一个 Block 的 id（可以为 None）
- deleted_next_id   ← 删除时它后一个 Block 的 id（可以为 None）
- deleted_section_path  ← 删除时所在章节路径（如果你有多级结构的话）


你之前说“自由拖拽有 position_id 一说”，可以直接把它升级成 sort_key。

1.2 删除时做什么？

当用户删除一个 Block：

is_deleted = True

deleted_at = now()

查出当时的 prev_block_id / next_block_id（同一本 book 内）

存进 deleted_prev_id / deleted_next_id

（可选）记录章节 path：deleted_section_path，比如 "chapter-2/section-1"

注意：不动其它 block 的 sort_key；
只是把这个 block 从“活跃列表”里排除。

1.3 恢复时的算法（实用版）

伪代码示意：

def restore_block(block):
    assert block.is_deleted

    # 1. 先找“原来在它前面”的 block
    if block.deleted_prev_id:
        prev = find_block(block.deleted_prev_id)
        if prev and not prev.is_deleted and prev.book_id == block.book_id:
            block.sort_key = new_key_between(prev.sort_key, next_sort_key_of(prev))
            block.is_deleted = False
            return

    # 2. 前一个不在了，找“原来在它后面”的 block
    if block.deleted_next_id:
        nxt = find_block(block.deleted_next_id)
        if nxt and not nxt.is_deleted and nxt.book_id == block.book_id:
            block.sort_key = new_key_between(prev_sort_key_of(nxt), nxt.sort_key)
            block.is_deleted = False
            return

    # 3. 前后都不在了，就退而求其次：放到该章节或整本书的末尾
    block.sort_key = last_sort_key_in_same_section_or_book() + 10
    block.is_deleted = False


new_key_between(a, b) 可以是：

如果用整数 + 空间：
a = 10, b = 20 → 取 15

如果没有空间或你懒得想 → 直接给他一个略大一点的值，然后异步做一次“全局 reindex”（比如所有 sort_key 重排成 10, 20, 30）。

1.4 这个方案的优点

拖拽不怕：你后面怎么拖拽、怎么插段落，恢复时只要邻居还在，就能插回正确的“语义位置”。

多次删除/恢复也不怕：上下文信息一直在（prev/next + section path）。

实现难度适中：不需要 CRDT，不需要学一堆论文，纯数据表 + 应用层逻辑就能搞定。

特别适合你现在的阶段：单人编辑、并发不高，这套已经比 90% side-project 高配了。

3️⃣ 更“工业级”的思路（可以先知道，不急着用）
3.1 链表式结构 / CRDT 思路
一些协作编辑器（Google Docs / Figma / Notion 的底层）会用类似：


每个 block 有一个逻辑位置 ID（比如「生成于谁之后」）；


整个文档是个“逻辑列表”，而不是“第 1、第 2、第 3”。


这玩意再往深走，就会遇到：


OT（Operational Transform）


CRDT（Conflict-free Replicated Data Type）


优点：多端同步、多用户并发下也能稳住。
缺点：你现在的项目阶段，有点杀鸡用屠龙刀。
3.2 事件溯源（Event Sourcing）
另一条路线：你本来就有 BlockDeleted / BlockRestored 事件；
理论上可以做到：


当前文档状态 = 从所有事件回放得到；


恢复时只要“撤销”某个删除事件，或者追加一个“恢复”事件。


这个需要整个系统都走 Event Sourcing，你现在还在 hexagonal + DDD 分层阶段，完全可以等后面“Wordloom v5 神教版”再搞。

4️⃣ 给你一个可以写进 DDD_RULES 的“金条”
你可以直接把这段写进规则文件里（改改格式就行）：
paperballs_positioning:
  invariants:
    - id: PAPERBALLS-POS-001
      text: "Block 删除时必须记录其前后邻居（prev_block_id, next_block_id）与章节路径。"

    - id: PAPERBALLS-POS-002
      text: >
        从 Paperballs 恢复 Block 时，优先插入到原 prev_block 之后；
        若 prev_block 已不存在，则插入到原 next_block 之前；
        若两者均不存在，则插入到同章节或整本书的末尾。

    - id: PAPERBALLS-POS-003
      text: "Block 的位置由 sort_key 决定；sort_key 允许通过在前后值之间插入新值进行局部调整，必要时可进行全局重排。"

这样以后你翻文档 / 刷代码，都知道自己当年脑子里想的是哪套逻辑。

5️⃣ 总结一口气说完


想要“恢复 block 回原位”，最稳的是：


删除时记录：前后邻居 ID + 原章节路径 + 当前 sort_key；


恢复时：优先靠邻居插回，同步刷新 sort_key；


实在插不回原语境，就放到末尾，同时给用户一个小提示。




这套设计：


对用户：几乎总能“回到原句子附近”，误删不再心惊胆战；


对你这个架构：只是在 Block 上加几个字段 + 两个用例逻辑，和 paperballs 视图完美契合；


对未来：可以平滑进化到更复杂的排序/协作模型，不用推翻重来。




你可以先按这个“邻居 + sort_key”版本实现，等哪天你真要做多人协作编辑，再考虑 CRDT 那套大杀器也不迟。