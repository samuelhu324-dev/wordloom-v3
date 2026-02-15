总结：DDD_RULES 的正确用途

DDD_RULES 应该是：
✅ 业务规则的单一真实来源（SSOT: Single Source of Truth）
✅ 架构决策的追踪文档
✅ Domain/Service/Repository 三层的需求映射表
✅ 测试用例的参考标准
✅ PR Review 的检查清单

DDD_RULES 不应该记录：
❌ 每个 class 的具体实现（那是代码的职责）
❌ HTTP 状态码详情（那是 Router 的职责）
❌ SQL 语句（那是 Repository 的职责）
❌ 数据库 Migration 脚本（那是基础设施的职责）

现在你明白了吗？DDD_RULES 是"规则中心"，实现分散在各层，但各层都应该能对应回 RULES 中的某条规则！