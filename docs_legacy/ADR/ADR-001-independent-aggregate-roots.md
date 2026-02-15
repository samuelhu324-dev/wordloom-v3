  AD-001:
    title: "独立聚合根模式（Independent Aggregate Roots）"
    description: |
      采用完全独立的聚合根设计，而非嵌套模型。
      - Library、Bookshelf、Book、Block 都是独立的 AggregateRoot
      - 通过 FK（外键）建立关联，而非对象包含
      - Service 层负责跨聚合的协调和业务逻辑

    benefits:
      - 解决大型对象锁问题（高并发下不竞争）
      - 数据库查询简化（按 ID 直接查，无 JOIN 复杂度）
      - 聚合体积小，修改成本低
      - Block 编辑时不需要锁 整个 Book→Bookshelf→Library

    tradeoffs:
      - Service 层变复杂（需要协调多个聚合）
      - 需要 Repository 提供额外查询方法（如 get_by_bookshelf_id）
      - 级联删除逻辑在 Service/Infra 层

    implementation_files:
      - library/domain.py
      - bookshelf/domain.py
      - book/domain.py
      - block/domain.py
      - */service.py

    related_rules:
      - RULE-004 through RULE-014
      - POLICY-003, POLICY-005, POLICY-007
