# ADR-080: Block Editor Integration, Minimal Domain Model, Ordering & Soft Delete Strategy

Date: 2025-11-21
Status: Accepted (Phase 0 pending implementation)
Authors: Architecture Team
Supersedes: N/A
References: DDD_RULES.yaml (block_domain_extensions), HEXAGONAL_RULES.yaml (block_editor_hexagonal), VISUAL_RULES.yaml (block_editor + key_rules), ADR-079 (Pagination V2), Eric Evans DDD, Hexagonal Architecture Principles

## 1. Context
现有 Book 内容需要拆分为多个独立 Block，以支持:
- 细粒度编辑（按段/按元素，而非整篇）
- 有序重排（拖拽 & 键盘快捷）
- 软删除与 Paperballs 三层恢复策略
- 媒体与富类型渐进扩展（代码块、图片、视频、表格、任务列表等）
- 避免 Domain 被富文本渲染细节污染（保持聚合最简）

需求与限制:
- 必须与 Pagination Contract V2 对齐（items,total,page,page_size,has_more）
- 保留与 Book 的一对多关系，但 Block 不嵌套其他 Block（线性序列）
- 需要高效的重排策略（避免 O(n) 全量重写）
- 软删除需支持上下文恢复（prev/next/section_path 三层回退）
- 富类型新增不能导致核心 Domain 结构频繁变动

## 2. Decision
采用独立 Block 聚合根，字段最小化:
```
id, book_id, type, order(Decimal 36,18), content(string/JSON ≤20KB), meta(optional raw JSON string), created_at, updated_at, soft_deleted_at
```
关键策略:
1. Ordering: 使用 Fractional Index (Decimal 36,18)，重排生成 prev 与 next 之间的新序号；密度不足时局部 rebase（仅影响冲突区段）。
2. Content Model: content 始终为字符串；复杂结构 JSON.stringify 存储；Domain 不解析 AST；CODE/IMAGE/VIDEO 仅存内容标识或 media_id。
3. Media Association: IMAGE/VIDEO 块仅保存 media_id + alt/caption；真实 URL 通过 Media 模块查询端口获得，避免耦合存储。
4. Soft Delete: 软删除设置 soft_deleted_at，删除时捕捉 deleted_prev_id / deleted_next_id / section_path；恢复时三层策略：prev+next → next 缺失用节尾 → 双缺失末尾插入。
5. Idempotent Updates: 300 秒窗口内相同 content_hash 的重复更新被忽略，减少保存抖动。
6. Events: 最小事件集 (BlockCreated, BlockContentChanged, BlockReordered(batch), BlockSoftDeleted, BlockRestored)。
7. Pagination: 所有列表使用 V2 契约；has_more 后端权威计算；前端不再推断。
8. Plugin Architecture (前端): blockPlugins: { type: { renderer, editor, icon, shortcuts, validate } } 增量接入，不修改核心 Editor。
9. Markdown 长度控制：≥15KB 警告；>20KB 拒绝保存 (422 BLOCK_CONTENT_TOO_LARGE)。

## 3. Alternatives
| 方案 | 描述 | 放弃原因 |
|------|------|----------|
| 嵌套 Block 集合在 Book 聚合内部 | Block 作为 Book 内部数组 | 大列表更新易锁定 + 违反独立聚合根扩展性；重排困难 |
| 单一长 Markdown 字段 | 整篇内容不拆分 | 无法局部编辑、重排、软删除与恢复；性能与协作差 |
| 整数序号重排 (sequence_index 0..N-1) | 每次拖拽 O(n) 重写序号 | 大量行重排成本高；频繁写放大；并发冲突难处理 |
| 强制服务器渲染 HTML (保存时生成 html_cache) | 后端立即渲染 | 增加耦合与阻塞链路；渲染策略变化需频繁修改 Domain |
| 内嵌媒体 URL/路径 | content 直接存 URL | 存储与 CDN 改变导致 Domain 泄漏外部细节；不可迁移 |

## 4. Consequences
正面:
- 最小聚合结构降低复杂度与演进成本
- Fractional Index 允许高频重排不影响整体性能
- 软删除恢复语义清晰，支持上下文定位
- 媒体与富类型扩展不破坏现有领域模型
- 前端插件体系易于渐进引入新类型

负面 / 代价:
- Decimal precision 需数据库与 ORM 正确处理 (NUMERIC(36,18))
- 局部 rebase 逻辑稍复杂（需测试覆盖）
- 幂等内容更新需维护 content_hash（hash 算法选择与碰撞概率评估）
- JSON 字符串内容对类型安全较弱（需前端校验与 validate 钩子）

## 5. Implementation Steps & Timeline (Phases)
Phase 0 (Nov 21 - Nov 23):
- 后端：建表 / 聚合模型 / Create + List + UpdateContent + SoftDelete + Restore 基础用例（TEXT/HEADING）
- 前端：BlockList 只读渲染 + InlineCreateBar + 基础分页（has_more 消费）
- 测试：模型不变式 + 分页用例 + 长度边界 (14KB/15KB/20KB/21KB)

Phase 1 (Nov 23 - Nov 27):
- 前端：编辑组件 (textarea) + 300ms debounce + Ctrl+S 强制保存
- 后端：Idempotent 更新窗口逻辑（content_hash 缓存表 / 内存 LRU 可选）
- 状态指示：保存中 / 已保存 / 保存失败重试 3 次
- 测试：并发编辑 + 幂等窗口（重复提交忽略）

Phase 2 (Nov 27 - Nov 30):
- 前端：拖拽重排 + 键盘快捷 Alt+↑/↓；批量 reorder 接口
- 后端：new_key_between(prev,next) + 局部 rebase 逻辑 + 事务原子性
- 测试：高频重排序列稳定性 + rebase 冲突回退

Phase 3 (Nov 30 - Dec 02):
- 前端：Paperballs 视图 (/paperballs) + 恢复动画插入
- 后端：删除时捕捉 prev/next/section_path；恢复 3 层策略
- 测试：三层恢复覆盖率 + 缺失邻居场景

Phase 4 (Dec 02 - Dec 05):
- 前端：IMAGE/VIDEO 块编辑器 + media_id 选择/撤销
- 后端：MediaRepository.exists 校验 + 仅存 media_id
- 测试：不存在媒资错误映射 BLOCK_MEDIA_NOT_FOUND + alt/caption 验证

Phase 5 (Dec 05 - Dec 10):
- 前端：插件注册体系 (blockPlugins) + CODE/TABLE/LIST/QUOTE/TASK 类型
- 后端：枚举扩展 + 无需结构变更；可选 meta 字段使用 JSON 字符串
- 测试：插件渲染注册/卸载回归 + DTO 枚举大小写转换

## 6. Testing Guidelines
- 边界测试：内容长度、枚举非法、Fractional Index 精度溢出
- 重排测试：连续拖拽 50 次后序号仍唯一；局部 rebase 不影响未涉及区段
- 恢复测试：Paperballs 三层定位各场景 (prev+next / next 缺失 / 双缺失)
- 幂等测试：相同内容重复编辑 10 次仅一次写入
- 媒体测试：无效 media_id 返回 404；有效 media_id 正常关联
- 插件测试：新增类型不破坏旧类型渲染与保存；卸载插件类型安全降级为 TEXT（只读）

## 7. Security & Integrity
- 仅允许从属于当前用户权限范围的 book_id 创建 Block
- 媒体关联验证避免跨 Library 泄露资源
- 软删除恢复检查 Block 与 Book 归属一致
- 避免 HTML/脚本注入：前端渲染层负责 Markdown → HTML 过滤 (sanitize)

## 8. Monitoring & Metrics
- block_content_update_latency_ms
- block_batch_reorder_size_avg
- paperballs_restore_attempts
- paperballs_restore_fallback_level (1|2|3)
- block_content_hash_deduplicated_count

## 9. Future Extensions
- 后端延迟渲染 html_cache 字段（独立适配器，不进 Domain）
- 全文检索：索引 Block content + media alt/caption
- 协同编辑：OT / CRDT 层（保持与最小 Domain 解耦）
- 活动流：BlockContentChanged & BlockReordered 聚合到 Chronicle 模块

## 10. Rollback Plan
若 Fractional Index 方案出现无法接受的密度冲突：
- 临时切换为 timestamp-based ordering (降级) 并限制拖拽频率
- 执行全量 rebase 迁移脚本 recalibrate_orders.sql
- 保留旧 order 备份列 (order_backup) 以支持恢复

## 11. Decision Summary
采用最小 Block 聚合 + Fractional Index + 软删除 Paperballs + 插件式富类型 + 媒体关联通过 ID，不嵌入富结构或 URL。保持 Hexagonal/DDD 边界纯净并支持渐进扩展。

## 12. Status & Next Actions
- VISUAL_RULES/HEXAGONAL_RULES/DDD_RULES 已更新对应章节
- 下一步：数据库迁移 + 后端 Phase 0 用例 + 前端 BlockList & InlineCreateBar

---
END ADR-080
