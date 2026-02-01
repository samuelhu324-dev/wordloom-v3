Elastic = 把 SQL 的两阶段搜索
          固化成倒排索引 + 查询引擎
          第一阶段永远在 index 内完成

Stage 1：搜索阶段（search_index）

用 search_index 做“搜索引擎式”的工作

目标：快、宽、容忍噪声

做的事：

trigram / FTS 命中候选 block_id

按 event_version / updated_at 排序

用 candidate_limit 控制规模（比如 100 / 200）

⚠️ 这一阶段 不关心：

block 是否软删除

tag 是否删除

是否属于某本 book

权限、租户等业务规则

Stage 2：业务过滤与组装（blocks + tag_associations）

用 Stage 1 的候选 block_id 回表

重新应用业务语义：

blocks.soft_deleted_at IS NULL

tags.deleted_at IS NULL

entity_type='block'

JOIN tag_associations

把 tags 聚合回结果

👉 这是“像业务系统一样思考”的阶段