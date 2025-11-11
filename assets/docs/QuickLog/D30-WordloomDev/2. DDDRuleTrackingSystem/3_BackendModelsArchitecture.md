旧架构（orbit）：
Bookshelves（曾经的 Library）
  ├─ notes（曾经的 Book）
  ├─ tags（Block 的元数据）
  ├─ checkpoints（Block 的特殊类型）
  └─ media（Block 的附件）

新架构（v3）：
Library（现在明确的唯一容器）
  ├─ Bookshelf（可无限创建）
  │   ├─ Book（可无限创建）
  │   │   ├─ Block（可无限创建）
  │   │   ├─ tags（Block 的元数据）
  │   │   ├─ checkpoints（Block 的特殊标记）
  │   │   └─ media（Block 的附件）