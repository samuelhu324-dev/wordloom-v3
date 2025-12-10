---
title: ADR-090 Tag Request Shape And Error Diagnostics (Plan34)
status: Draft
date: 2025-11-23
tags: backend, api, tag, dx, frontend, docs
---

# 决策摘要
将 Tag 聚合的 HTTP 协议收缩为「独立 CRUD + 他域仅传 tagIds」的双轨结构，同时保留 FastAPI 默认 422 错误格式，利用 detail.loc/msg 作为调试入口。配合三份规则文档（HEXAGONAL_RULES / DDD_RULES / VISUAL_RULES）更新，实现前后端一致的 Tag 管理与诊断流程。

# 背景问题
- 混合负载：书库/书籍更新接口同时承载“新建 Tag + 关联 Tag”，导致前后端对请求形状认知不同（列表、对象、字符串混杂），频繁触发 422。
- 语义混乱：Book 状态 (seed/growing/stable/legacy) 曾作为「系统 Tag」存在，删改 Tag 时可能误删状态。
- 缓存漂移：前端页面各自缓存 Tag 列表，未刷新时提交旧 ID → 404/409。
- 错误不可读：422 detail 被忽略，缺乏定位问题的统一流程。

# 目标
1. Tag 聚合只处理 name/color/icon/description/level，自身 CRUD 与多对多关联完全解耦。
2. 其它聚合仅接受 `tagIds: UUID[]`，通过幂等替换完成增删。
3. Status 与 Tag 分离：生命周期字段进入 Book 聚合，Tag 只承载用户自定义标签。
4. 文档与规则同步，形成可执行的调试清单（detail.loc/msg 必须附在工单上）。

# 方案细节
| 维度 | 决策 | 说明 |
|------|------|------|
| API 协议 | Tag CRUD 独立；关联端点仅收 `tagIds` | 解除“一包多意图”，后端不再在 Bookshelf/Book 请求体内解析 name |
| DTO | `CreateTagRequest` 保留 Pydantic 结构；Bookshelf/Book 仅暴露 `tagIds` | Hexagonal Adapter 继续接受 dataclass，路由层执行最小映射 |
| 错误处理 | **Option A**：保留 FastAPI 默认 422 detail | detail.loc/msg 提供精确路径；配套文档指导解读 |
| 前端状态 | `allTags` + `selectedTagIds` 双状态 | 新建标签通过 POST /tags -> push id -> PUT 目标资源 |
| Status 边界 | 状态枚举迁移到 Book 聚合 | 清理“系统 Tag” 符号，防止误删 |

## 接口契约
```http
POST /api/v1/tags
Body: {"name": "Lab", "color": "#4A90E2", "icon": null, "description": null}
→ 201 { "id": "uuid", "name": "Lab", ... }

PUT /api/v1/books/{id}/tags
Body: {"tagIds": ["uuid-1", "uuid-2"]}
→ 200 {"tagIds": [...]} (幂等替换)
```

## 错误诊断流程
1. 捕获 FastAPI 返回的 detail；示例：
   ```json
   {
     "detail": [
       {
         "loc": ["body", "tagIds", 0],
         "msg": "value is not a valid UUID",
         "type": "type_error.uuid"
       }
     ]
   }
   ```
2. 前端直接显示 msg，并提示刷新 Tag 列表或修正输入。
3. QA/支持在工单附上 detail 原文，定位是 shape 还是数据问题。

# 迁移步骤
1. **文档同步**：更新 HEXAGONAL_RULES / DDD_RULES / VISUAL_RULES（本 ADR 配套提交）。
2. **后端路由**：确保 /tags 静态路由在 /{tag_id} 前；Bookshelf/Book 更新 DTO 改为 `tagIds` 单字段。
3. **前端改造**：TagSelector 使用 `selectedTagIds`，新建流程分两步，所有提交使用幂等替换。
4. **数据清理**：将 seed/growing/stable/legacy 迁移到 Book.status，Tag 表删除对应记录。
5. **监控**：统计 422 detail 中包含 `tagIds` 的次数，评估改造完成度。

# 风险与缓解
- **旧客户端仍发送 name**：提供短期兼容层（记录 warning + 转换），设置截止日期。
- **历史数据缺少 UUID**：迁移脚本补全或标记为需要手动处理。
- **状态迁移影响统计**：与 Chronicle/报表协同调整，验证新字段来源。

# 不采纳的方案
| 方案 | 原因 |
|------|------|
| Option B：全局自定义错误包装 | 会丢失 FastAPI detail.loc，且需重写所有异常映射；调试成本增大 |
| 继续使用合并请求体 | 触发形状不一致，调试困难；违背单一职责 |

# 当前状态
- 文档变更：✅ 已更新三份 RULES 文件，等待后端/前端代码调整。
- 实施负责人：后端（Tag Router）@backend-team，前端（Tag Selector）@frontend-team。
- 预期完成：2025-11-25 前完成接口改造并通过冒烟测试。

# 后续工作
1. 编写自动化测试：覆盖 POST /tags + PUT /books/{id}/tags 的 happy path 与错误示例。
2. 提供示例 HAR（成功与失败）给支持团队。
3. 清理旧 UI 文案中“标签或状态”混用的描述。
