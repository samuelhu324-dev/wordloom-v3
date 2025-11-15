commit c9f4a7b2d5e8f1c3a6b9d2e5f8a1b4c7

Author: Wordloom Backend Team <backend@wordloom.dev>
Date:   Wed Nov 13 2025 14:10:00 +0800

    feat(tag,media): complete tag & media modules with multi-entity association

    ## 中文

    完成 Tag 和 Media 两个核心模块的实现（~6000 行生产级代码）。

    ### Tag 模块
    - Tag AggregateRoot + TagAssociation：支持 Bookshelf/Book/Block 独立打标签
    - 多级分类架构（parent_tag_id）：为 >500 tags 规模预留扩展
    - 12+ 异常类 + 13 个查询方法 + 7 个 API 端点

    ### Media 模块
    - Media 完整生命周期：ACTIVE → TRASH（30 天保留）→ PURGED（自动清理）
    - 独立关联模型：Bookshelf/Book/Block 各自关联，无级联
    - MIME 验证、元数据提取（图片尺寸、视频时长）、配额强制（POLICY-009）
    - 11+ 异常类 + 15 个查询方法 + 10 个 API 端点

    ### 核心设计
    - **完全独立关联**：无自动同步，符合 DDD 原则
    - **软删除机制**：30 天垃圾保留 (POLICY-010)，用户可恢复
    - **并行上传支持**：前端 Promise.all + 后端并发处理
    - **文件系统隔离**：storage_key 映射实际路径，便于迁移

    ### 文件结构
    ```
    backend/api/app/modules/
    ├── tag/
    │   ├── domain.py / exceptions.py / models.py / schemas.py
    │   ├── repository.py / service.py / router.py / __init__.py
    │   └── tests/
    └── media/
        ├── domain.py / exceptions.py / models.py / schemas.py
        ├── repository.py / service.py / router.py / __init__.py
        └── tests/
    ```

    ### 关键策略
    - POLICY-001: Tag 名称全局唯一
    - POLICY-009: 存储配额强制（超额 429）
    - POLICY-010: 30 天垃圾保留 + 自动清理

    ### 文档
    - ADR-025: Tag 设计文档
    - ADR-026: Media 设计文档
    - DDD_RULES.yaml 已更新

    ---

    ## English

    Complete implementation of Tag and Media modules (~6000 lines production code).

    ### Tag Module
    - Tag AggregateRoot + TagAssociation: Independent tagging on Bookshelf/Book/Block
    - Multi-level hierarchy (parent_tag_id): Scalable to >500 tags
    - 12+ exceptions + 13 queries + 7 API endpoints

    ### Media Module
    - Complete lifecycle: ACTIVE → TRASH (30-day retention) → PURGED (auto-cleanup)
    - Independent association: Each entity associated separately, NO cascade
    - MIME validation, metadata extraction (image dimensions, video duration),
      quota enforcement (POLICY-009)
    - 11+ exceptions + 15 queries + 10 API endpoints

    ### Core Design Principles
    - **Complete Independence**: NO automatic sync, follows DDD principles
    - **Soft-Delete**: 30-day trash retention (POLICY-010), user-recoverable
    - **Concurrent Upload**: Frontend Promise.all + backend concurrency handling
    - **File System Isolation**: storage_key maps to physical path, migration-friendly

    ### Directory Structure
    ```
    backend/api/app/modules/
    ├── tag/
    │   ├── domain.py / exceptions.py / models.py / schemas.py
    │   ├── repository.py / service.py / router.py / __init__.py
    │   └── tests/
    └── media/
        ├── domain.py / exceptions.py / models.py / schemas.py
        ├── repository.py / service.py / router.py / __init__.py
        └── tests/
    ```

    ### Key Policies
    - POLICY-001: Tag name uniqueness (global)
    - POLICY-009: Storage quota enforcement (429 on overflow)
    - POLICY-010: 30-day trash retention + auto-purge

    ### Documentation
    - ADR-025: Tag architecture & design
    - ADR-026: Media architecture & design
    - DDD_RULES.yaml updated

    Related: #PHASE-1-DOMAIN, #POLICY-009, #POLICY-010