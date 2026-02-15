- [ ] <Delete/Recycle-1>

- <Within 30s>

- In Wordloom, I treat deletion as a high-risk operation, not just a delete row.
  I constrained deletes to higher-level aggregates like Book, while lower-level content stays protected.
  Deletes are soft by default, with a recycle step for recovery, to avoid breaking historical references.
  The goal was reducing long-term risk, not adding features.

- <Within 90s>

  - I realised the real risk wasn’t whether data could be deleted, but whether deletion silently changed system semantics.
    So I did three things:
    I constrained deletes to higher-level aggregates to avoid cascading effects;
    I made deletes soft and reversible;
    and I enforced consistent read-path filtering so deleted data behaves predictably everywhere.
    This makes future evolution safer without relying on perfect discipline.

<!---------------------------------------------------------------------------------------------------
  ---------------------------------------------------------------------------------------------------
  -------------------------------------------------------------------------------------------------->

- [ ] <Aggregation_Boundary/Couping_Control-2> 

- <Within 30s>

  - Early on, Wordloom was fairly coupled, so I restructured it around clearer aggregates like Library, Book, and Block.
    Each layer owns its data and rules, and changes don’t propagate upward unexpectedly.
    The goal wasn’t textbook DDD, but limiting the blast radius of changes.

- <Within 90s>

  - As the system grew, the biggest issue wasn’t performance, but unpredictable side effects.
    I redefined aggregation boundaries: Library handles lifecycle, Book handles structure, Block owns content only.
    Cross-aggregate changes go through application orchestration or events.
    This keeps evolution local and predictable, which is critical for long-running systems.

<!---------------------------------------------------------------------------------------------------
  ---------------------------------------------------------------------------------------------------
  -------------------------------------------------------------------------------------------------->   

  - [ ] <Schema_Evolution-3>

- <Within 30s>

  - I treat schema changes as long-term evolution, not one-off refactors.
    I version migrations with Alembic and allow old and new structures to coexist temporarily, avoiding big-bang changes.
    The focus is keeping the system stable while it evolves.

- <Within 90s>

  - During the v2 to v3 transition, I treated v3 as greenfield and kept v2 as legacy in parallel.
    I migrated data incrementally with versioned schemas, isolating risk.
    For me, schema evolution isn’t about elegance — it’s about having a rollback path.

<!---------------------------------------------------------------------------------------------------
  ---------------------------------------------------------------------------------------------------
  -------------------------------------------------------------------------------------------------->   

- [ ] <Safe_Feature_Delivery-1>

- My strategy for delivering a new feature is: first, lock down the scope, 
  then implement it as an independent use case, and define a stable contract through an API schema.
  For implementation, I’d ship a first version using the database’s full-text / fuzzy search, 
  to avoid introducing additional infrastructure and the complexity of keeping search indexes in sync.
- For testing, I’d first ensure the business rules are correct—such as range filtering, soft-delete filtering, 
  and permission checks—then add integration tests for the use case, and finally run a regression checklist.
- For rollout, I’d add a feature flag or a fallback mechanism, 
  so if anything goes wrong we can quickly disable the feature or degrade safely.

- 在 Wordloom 里我加过 [功能X]。我先把需求范围锁死，把它做成独立 use case，并用 API schema 固化契约。
- 实现上我先用 Postgres 全文/模糊搜索 做 MVP，避免引入额外搜索基础设施和索引同步成本；等价值验证后再考虑更重的方案。
- 测试上先覆盖 过滤规则（范围/软删除/权限） 的单测，再补 use case 的集成测试，最后用 checklist 做回归。
- 上线时加了 feature flag / fallback，确保出问题能快速关闭或降级。

1- 
S3 / GCS / Azure Blob / MinIO

2- 
Blob / Asset（文件本体）：以 hash 为唯一身份
blob(hash, size, mime, storage_key, created_at...)
Reference（引用关系）：业务实体指向 blob
ref(entity_type, entity_id, blob_hash, role, display_order, created_at...)