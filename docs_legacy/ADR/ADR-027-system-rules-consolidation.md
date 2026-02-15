# ADR-027: System Rules Consolidation - DDD + Hexagonal Architecture Unification

**Status:** ACCEPTED ✅
**Date:** 2025-11-13
**DecisionMaker:** Architecture Team
**Supersedes:** DDD_RULES.yaml (v3.0)
**Related ADRs:** ADR-001, ADR-008 through ADR-026

---

## 摘要

整合分散的 DDD 规则和 Hexagonal 架构约束为单一统一的系统规则库（**SYSTEM_RULES.yaml**），形成整个 Wordloom 后端系统的"架构宪法"。

---

## 问题陈述

### 背景

在 Hexagonal Architecture 完整转换（8 步完成，135+ 文件，5000+ 代码行）之后，存在两个并行的规则文档：

1. **DDD_RULES.yaml**
   - 记录业务不变量（Invariants）和政策（Policies）
   - 26 条核心规则（RULE-001 到 RULE-026）
   - 14 条业务政策（POLICY-001 到 POLICY-014）
   - Domain 层的"业务真相"

2. **隐含的 Hexagonal 约束**
   - 散落在代码注释、PR 描述、临时文档中
   - 没有集中的"官方规则表"
   - 包括：
     - 端口定义（入站/出站）
     - 适配器约束（DTO 转换、异常映射）
     - 依赖倒转原则（DI 容器、工厂方法）
     - 测试策略（单元/集成/E2E）
     - 错误映射（HTTP 状态码）
     - 可观测性规范（结构化日志）
     - 性能约束（分页、索引、缓存）

### 风险

**单一事实源的缺失**：
- ❌ 开发者在 DDD_RULES.yaml 和代码中的 Hexagonal 实现之间的不一致
- ❌ 新成员需查阅多个文档才能理解系统架构
- ❌ 规则更新时容易遗漏 Hexagonal 部分
- ❌ 架构决策的可追踪性降低

---

## 决策

**将 DDD_RULES.yaml 升级为 SYSTEM_RULES.yaml**，采用统一的架构规则库，包含三大章节：

1. **metadata** - 架构宣言（声明支持 DDD + Hexagonal）
2. **ddd** - 业务不变量和政策（原有 DDD_RULES.yaml 的全部内容）
3. **hexagonal** - 架构约束和实现规范（新增，整合所有架构约束）

### 结构设计

```yaml
metadata:
  version: "3.1"
  architecture: ["DDD", "Hexagonal"]  # ← 架构宣言

ddd:
  description: "Domain-Driven Design - 业务规则"
  invariants:    # RULE-001 到 RULE-026
  policies:      # POLICY-001 到 POLICY-014

hexagonal:
  description: "Hexagonal Architecture - 系统边界与实现"
  ports:         # 入站/出站端口定义
  adapters:      # 适配器约束与模式
  di:            # 依赖倒转与组合根
  testing:       # 测试金字塔与策略
  error_mapping: # 异常到 HTTP 状态码映射
  observability: # 结构化日志与追踪
  performance:   # 性能约束与优化
```

### 信息架构原理

| 维度 | DDD 部分 | Hexagonal 部分 |
|-----|---------|----------------|
| **关注点** | 业务逻辑 | 系统边界 |
| **内容** | 不变量、聚合根、政策 | 端口、适配器、DI、测试 |
| **来源** | Domain 层代码 | Router/Infrastructure/Testing |
| **变更频率** | 低（业务稳定）| 中（架构优化） |
| **受众** | 域专家、业务分析师 | 架构师、后端工程师 |

---

## 原因

### 1. 单一事实源原则（Single Source of Truth）

- ✅ **一个文件**统管所有系统规则
- ✅ **一个版本号**（version: "3.1"）
- ✅ **一个更新日志**（changelog 同时记录 DDD 和 Hexagonal 的演进）
- ✅ **避免分歧**：不需要在两个平行规则库之间同步

### 2. 层次化架构可见性

- ✅ **顶层**（metadata）：整体架构宣言
- ✅ **中层**（ddd）：业务逻辑规则
- ✅ **下层**（hexagonal）：实现约束

开发者可以按需阅读不同层级：
- 产品经理只看 `ddd.invariants`（业务规则）
- 架构师看 `hexagonal`（系统边界）
- 新成员看 `metadata`（快速入门）

### 3. ADR 与规则库的配合

- **规则库**（SYSTEM_RULES.yaml）：**是什么**（架构决策的内容）
- **ADR**：**为什么**（架构决策的原因和权衡）

例如：
- ADR-001：为什么选择 Independent Aggregate Roots？
- ADR-027：为什么需要统一 SYSTEM_RULES.yaml？
- SYSTEM_RULES.yaml：具体的聚合根定义、约束、检查点

### 4. 测试金字塔的完整定义

Hexagonal 部分定义了完整的测试策略：
- 单元测试（Domain Logic）
- 集成测试（Repository + Service）
- API 测试（Router 端点）
- E2E 测试（完整工作流）

### 5. 错误处理的一致性

Hexagonal 的 `error_mapping` 部分定义：
- Domain Exception → HTTP Status Code 映射
- 统一的错误响应格式
- 构建可预测的 API 错误处理

---

## 权衡

### 赞成

| 优势 | 说明 |
|------|------|
| 单一真实来源 | 避免文档漂移 |
| 完整的架构文档 | 业务规则 + 技术约束一体 |
| 易于维护 | 一个文件、一个版本号 |
| 新成员快速上手 | 所有规则集中在一处 |
| ADR 参考统一 | 所有 ADR 都指向同一个规则库 |

### 反对

| 劣势 | 缓解策略 |
|------|---------|
| 文件可能过大（3000+ 行） | 使用 Markdown 目录导航、IDE outline |
| 跨域关系复杂 | 使用 `cross_domain_events` 部分明确定义 |
| 变更冲突风险增加 | 使用 Git 分支策略、code review |
| 历史追踪困难 | 使用 changelog + git blame |

---

## 实现详情

### 1. 文件变更

```bash
# 重命名文件
backend/docs/DDD_RULES.yaml → backend/docs/SYSTEM_RULES.yaml

# 保留向后兼容
backend/docs/DDD_RULES.yaml (deprecated symlink 或注释指向 SYSTEM_RULES.yaml)
```

### 2. 内容整合

#### 来源于原 DDD_RULES.yaml
- `metadata` 部分（扩展 architecture 字段）
- `ddd.invariants` - 全部 26 条规则
- `ddd.policies` - 全部 14 条政策
- `ddd.aggregates` - 10 个 Domain 的定义
- `changelog` - 历史记录

#### 新增 Hexagonal 部分
基于以下源文档：
- `3_SystemRules.md`（推荐结构）
- Step 8 完成报告中的架构设计
- 各 Router 文件中的 DTO 模式注释
- main.py 中的 DI + EventBus 配置
- 各 Router 中的异常处理代码
- conftest.py 中的测试模式

### 3. 版本号

```yaml
metadata:
  version: "3.1"  # 从 3.0 → 3.1
  # 说明：major.minor 增量
  # 3.0: DDD_RULES.yaml（仅 DDD）
  # 3.1: SYSTEM_RULES.yaml（DDD + Hexagonal）
```

### 4. 向后兼容

```yaml
# 在文件头添加：
# ============================================
# 历史迁移说明
# ============================================
# DDD_RULES.yaml (v3.0) 已升级为 SYSTEM_RULES.yaml (v3.1)
# 所有原 DDD 规则保留在 ddd: 章节
# 新增 hexagonal: 章节记录架构实现约束
# 请参考 ADR-027 了解详情
# ============================================
```

---

## 后续影响

### 1. 文档引用更新

所有现有文档更新指向：
```yaml
# 之前：
adr_reference: "DDD_RULES.yaml - RULE-001"

# 之后：
adr_reference: "SYSTEM_RULES.yaml - ddd.invariants.RULE-001"
```

### 2. Code Review 检查清单

在审核涉及架构的 PR 时：
```
- [ ] 变更是否遵守 SYSTEM_RULES.yaml 中的规则？
- [ ] 是否需要更新 SYSTEM_RULES.yaml？
- [ ] 是否需要新增 ADR？
- [ ] Hexagonal 的哪些部分受到影响？
```

### 3. 入职流程

新成员首次阅读顺序：
1. README.md - 项目概述
2. SYSTEM_RULES.yaml - metadata 章节（5 分钟）
3. SYSTEM_RULES.yaml - hexagonal 章节（30 分钟）
4. 具体 ADR（如 ADR-001, ADR-008）- 深度理解（1 小时）
5. 相应模块的代码（domain.py, service.py, repository.py）

### 4. CI/CD 集成

```yaml
# 未来可添加的 CI 检查：
- lint SYSTEM_RULES.yaml YAML 格式
- 验证所有 ADR 在 SYSTEM_RULES.yaml 中被引用
- 检查代码中的异常是否在 error_mapping 中定义
- 验证测试覆盖率是否符合 testing.pyramid 的目标
```

---

## Hexagonal 部分详细说明

### ports（端口）

**入站端口（Inbound Ports）**：
- REST API（FastAPI，42 个端点）
- CLI（Command-line，预留）
- Job/Scheduler（预留）
- Test Adapters（pytest fixtures）

**出站端口（Outbound Ports）**：
- Repository（数据持久化）
- EventBus（事件发布）
- Storage（文件上传）
- Search Engine（全文搜索，预留）
- Cache（缓存，预留）
- Email Service（邮件通知，预留）

### adapters（适配器）

**关键约束**：
```
❌ 不得返回 ORM 对象
❌ 不得泄露 SDK 类型
❌ 不得绕过异常映射
✅ 必须使用 DTO 模式
✅ 必须完整的错误处理
✅ 必须结构化日志
```

**模式示例**：

入站适配器（Router）：
```python
# 正确示例 ✅
@router.post("/tags")
async def create_tag(request: CreateTagRequest, di: DIContainer = Depends(...)):
    use_case = await di.get_create_tag_use_case()  # DI 工厂
    response = await use_case.execute(request)     # UseCase
    return TagResponse(**response.dict())           # DTO 响应
```

出站适配器（Repository）：
```python
# 正确示例 ✅
class TagRepositoryImpl(ITagRepository):
    def _to_domain(self, model: TagModel) -> Tag:
        """将 ORM 模型转换为 Domain 对象"""
        return Tag(...)

    def _to_model(self, tag: Tag) -> TagModel:
        """将 Domain 对象转换为 ORM 模型"""
        return TagModel(...)
```

### di（依赖倒转）

**Composition Root 模式**：
```
Request
  ↓
Router (入站适配器)
  ↓ depends_on
DIContainer.get_instance()
  ↓ factory
UseCase(Repository, EventBus)
  ↓ calls
Repository.save(domain_entity)
  ↓ transforms
ORM Model
  ↓
Database
```

**好处**：
- 高层模块不依赖低层模块
- 都依赖抽象（接口）
- 低耦合、高内聚
- 易于测试（Mock Repository）

### testing（测试金字塔）

```
      E2E (50% coverage)
     /  \
    /    \
   /      \
  / API    \
 / (75%)    \
/____________\
|Integration  |  (80% coverage)
|Tests        |
|_____________|
|    Unit     |
| Tests (90%) |  (Domain Logic)
|_____________|

从下至上：单元 → 集成 → API → E2E
```

### error_mapping（错误映射）

统一的错误响应格式：
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Tag name must be 1-50 characters",
  "resource": "tag",
  "resource_id": "tag-uuid-123",
  "request_id": "request-uuid"
}
```

HTTP 状态码映射：
- 404 NotFound
- 409 Conflict (RULE-001 重复违反)
- 422 ValidationError
- 500 InternalServerError

### observability（可观测性）

**必备日志字段**：
- request_id（请求追踪）
- user_id（用户追踪）
- resource（资源类型）
- resource_id（资源 ID）
- operation（操作类型）
- error_code（错误代码）
- latency_ms（性能）
- timestamp（时间戳）

### performance（性能）

- 分页：default_limit=20, max_limit=100
- 查询优化：使用数据库索引，避免 N+1
- 缓存：三层策略（请求内、会话、Redis）
- 索引：library_id, bookshelf_id, book_id, soft_deleted_at, usage_count

---

## 验证和验收

### 检查清单

- ✅ SYSTEM_RULES.yaml 文件创建
- ✅ metadata 部分完整
- ✅ ddd 部分包含所有 26 条规则
- ✅ hexagonal 部分涵盖 7 个子域（ports, adapters, di, testing, error_mapping, observability, performance）
- ✅ 所有 ADR 在文件中被引用
- ✅ changelog 记录迁移信息
- ✅ 向后兼容说明添加

### 测试方案

1. **格式验证**：YAML 语法检查
2. **一致性检查**：所有 RULE 在代码中实现
3. **参考完整性**：所有 ADR 都有关联
4. **可读性测试**：新成员能否快速找到特定规则

### 推出计划

**Phase 1**（立即）：
- 创建 SYSTEM_RULES.yaml
- 更新所有 ADR 的 adr_reference 字段
- 发布 PR（带 ADR-027）

**Phase 2**（1 周内）：
- 更新所有文档中的规则引用
- 更新 Code Review 检查清单
- 组织团队讨论（如有必要）

**Phase 3**（1 个月内）：
- 考虑弃用 DDD_RULES.yaml
- 收集反馈，迭代 SYSTEM_RULES.yaml 结构
- 考虑 CI/CD 集成

---

## 相关文档

| 文档 | 关系 | 说明 |
|------|------|------|
| ADR-001 | 前置 | Independent Aggregate Roots 的定义 |
| ADR-008 - ADR-026 | 前置 | 各个 Domain 和 Adapter 的设计决策 |
| 3_SystemRules.md | 参考 | Hexagonal 结构的推荐方案 |
| backend/docs/SYSTEM_RULES.yaml | 本体 | 统一规则库 |
| backend/api/app/main.py | 实现参考 | DI + EventBus 初始化 |
| backend/api/dependencies.py | 实现参考 | DIContainer 工厂方法 |
| backend/api/app/modules/*/routers/*.py | 实现参考 | 路由适配器与异常映射 |

---

## 总结

通过创建 **SYSTEM_RULES.yaml**，Wordloom 后端获得了：

1. ✅ **单一事实源**：所有架构规则集中管理
2. ✅ **完整的文档**：业务逻辑 + 技术约束
3. ✅ **清晰的分层**：metadata → ddd → hexagonal
4. ✅ **易于维护**：一个文件、一个版本号、一个 changelog
5. ✅ **新成员友好**：入职流程清晰，快速查阅
6. ✅ **ADR 系统完整**：规则库与 ADR 配合形成"架构宪法"

这是从 DDD_RULES.yaml（v3.0）向 SYSTEM_RULES.yaml（v3.1）的进化，标志着 Wordloom 后端架构成熟度从"理论"阶段进入"生产就绪"阶段。

---

## 附录：从 DDD_RULES.yaml 迁移到 SYSTEM_RULES.yaml

### 脚本示例（供参考）

```bash
# 1. 备份原文件
cp backend/docs/DDD_RULES.yaml backend/docs/DDD_RULES.yaml.bak

# 2. 创建新文件（已由 SYSTEM_RULES.yaml 完成）
touch backend/docs/SYSTEM_RULES.yaml

# 3. 更新所有文档引用
find . -name "*.md" -o -name "*.py" | xargs grep -l "DDD_RULES.yaml" | \
  xargs sed -i 's|DDD_RULES.yaml|SYSTEM_RULES.yaml|g'

# 4. 验证 YAML 格式
python -c "import yaml; yaml.safe_load(open('backend/docs/SYSTEM_RULES.yaml'))"

# 5. 测试文档可读性
# 使用 IDE outline 导航，或在线 YAML 查看工具
```

### 文件大小预期

| 部分 | 预计行数 |
|------|---------|
| metadata | 50-80 |
| ddd.invariants | 1200-1500 |
| ddd.policies | 300-400 |
| hexagonal | 1500-2000 |
| file_structure | 100-150 |
| adr_references | 50-100 |
| changelog | 100-150 |
| **总计** | **3300-4380** |

---

## Decision

✅ **ACCEPTED**

本 ADR 记录了将 DDD_RULES.yaml 升级为 SYSTEM_RULES.yaml、统一所有架构规则为单一事实源的决策。

---

*文档生成时间：2025-11-13*
*下一步：实施 Phase 1 - 创建 SYSTEM_RULES.yaml 并更新所有 ADR 引用*

