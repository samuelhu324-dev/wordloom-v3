Status: ✅ Completed — 2025-12-06

对，先把 Domain 层“讲清楚”，再让前端/接口去“照着演戏”。
下面这份就是可以直接丢给 Copilot 的“计划书”，你可以整段贴过去当任务说明。

0. 范围 & 不要乱动的东西

本次改动目标：

给 Book 加上 Basement（软删除）机制。

给 Block 加上 软删除标记（deleted_at），但暂时不做用户可见的回收站 UI。

禁止动的：

编辑器键盘逻辑（Enter/Backspace/Shift+Enter 等）

现有 Block 内容结构（不改变 text/metadata 模型）

1. Domain 模型改动（Book / Block）

先改 Domain，再推到 infra / API / 前端。

1.1 Book 增加状态（支持 Basement）

在 Domain 层（例如 modules/library/books/domain）做这些事情：

定义 BookStatus 枚举：

export type BookStatus = 'active' | 'basement' | 'deleted';


给 Book 聚合增加字段：

class Book {
  // 已有字段：id, title, bookshelfId, ...
  status: BookStatus;              // 默认为 'active'
  previousBookshelfId?: string;    // 进入 basement 前所在 bookshelf，用于恢复
  movedToBasementAt?: Date | null; // 可选：记录时间
}


在 Book 上增加三个方法（领域行为）：

moveToBasement(now: Date): void
restoreFromBasement(): void
markDeleted(now: Date): void       // 真·硬删除前的标记（可选）


语义要求：

moveToBasement：

只有当 status === 'active' 才允许调用；

调用后：

status = 'basement'

previousBookshelfId = current bookshelfId

movedToBasementAt = now

restoreFromBasement：

只有 status === 'basement' 允许；

调用后：

status = 'active'

bookshelfId 设置为 previousBookshelfId（如果存在）

markDeleted：

只有 status === 'basement' 允许；

调用后：

status = 'deleted'（将来可以配合物理删除）

注意： Domain 层不要直接操作数据库，只更新实体字段和不变式检查即可。

1.2 Block 增加软删除标记

在 Block 领域模型里（例如 modules/book/blocks/domain）：

添加字段：

class Block {
  // 已有字段：id, bookId, index, kind, content, ...
  deletedAt?: Date | null;
}


定义两个领域操作：

softDelete(now: Date): void
restore(): void


语义要求：

softDelete：

将 deletedAt = now

restore：

将 deletedAt = null

此阶段 不引入 Block 回收站 UI，只是数据层准备好软删除字段，后续可以通过 Admin 工具或历史来恢复。

2. 仓储层（Repository）改动
2.1 BookRepository

在 Book 的仓储接口中增加/调整：

interface BookRepository {
  findById(id: BookId): Promise<Book | null>;

  // 新增
  findActiveByLibrary(libraryId: LibraryId): Promise<Book[]>;
  findBasementByLibrary(libraryId: LibraryId): Promise<Book[]>;

  save(book: Book): Promise<void>;
}


实现层（PostgreSQL 等）：

findActiveByLibrary：WHERE status = 'active'

findBasementByLibrary：WHERE status = 'basement'

现有查询列表的地方统一改为只查 status = 'active'。

2.2 BlockRepository

接口示例：

interface BlockRepository {
  findByBook(bookId: BookId): Promise<Block[]>;           // 只返回 active
  findDeletedByBook?(bookId: BookId): Promise<Block[]>;   // 可选，用于未来的 Admin

  softDelete(blockId: BlockId, now: Date): Promise<void>;
  restore(blockId: BlockId): Promise<void>;
}


实现要求：

findByBook 必须加 WHERE deleted_at IS NULL。

softDelete 只更新 deleted_at 字段，不做物理删除。

3. 应用层 UseCases（服务层）

在 Application 层（use cases / service）增加以下用例：

3.1 移动 Book 到 Basement
class MoveBookToBasementUseCase {
  constructor(private bookRepo: BookRepository) {}

  async execute({ bookId, now, currentUser }): Promise<void> {
    const book = await bookRepo.findById(bookId);
    // 1. 权限检查（可选：是否允许当前用户操作）
    // 2. Domain 行为
    book.moveToBasement(now);
    // 3. 持久化
    await bookRepo.save(book);
  }
}

3.2 从 Basement 恢复 Book
class RestoreBookFromBasementUseCase {
  constructor(private bookRepo: BookRepository) {}

  async execute({ bookId, currentUser }): Promise<void> {
    const book = await bookRepo.findById(bookId);
    book.restoreFromBasement();
    await bookRepo.save(book);
  }
}

3.3 在 Basement 中硬删除 Book
class HardDeleteBookUseCase {
  constructor(private bookRepo: BookRepository, private blockRepo: BlockRepository) {}

  async execute({ bookId, currentUser, now }): Promise<void> {
    const book = await bookRepo.findById(bookId);
    // 仅允许 basement 状态
    book.markDeleted(now);
    await bookRepo.save(book);

    // 物理删除相关 blocks（或标记 deleted_at，视当前策略而定）
    // 可以先简单实现为 DELETE FROM blocks WHERE book_id = ...
  }
}

3.4 删除 Block（软删除）
class SoftDeleteBlockUseCase {
  constructor(private blockRepo: BlockRepository) {}

  async execute({ blockId, now, currentUser }): Promise<void> {
    await blockRepo.softDelete(blockId, now);
  }
}


注意： 编辑器层面调用的“删除 block”API，应该指向这个用例，而不是直接物理 DELETE。

4. 基础设施层（数据库 & API）
4.1 数据库迁移

生成两条 migration：

books 表：

ALTER TABLE books
  ADD COLUMN status VARCHAR(32) NOT NULL DEFAULT 'active',
  ADD COLUMN previous_bookshelf_id UUID NULL,
  ADD COLUMN moved_to_basement_at TIMESTAMP NULL;


blocks 表：

ALTER TABLE blocks
  ADD COLUMN deleted_at TIMESTAMP NULL;


并在 ORM 模型中同步这些字段。

4.2 后端 HTTP API

新增/调整以下路由（可以根据现有路由风格微调命名）：

移动 Book 到 Basement

POST /admin/books/{bookId}/move-to-basement

Body: {}（或 { reason?: string }）

调用 MoveBookToBasementUseCase

从 Basement 恢复 Book

POST /admin/books/{bookId}/restore-from-basement

调用 RestoreBookFromBasementUseCase

在 Basement 中硬删除 Book

DELETE /admin/books/{bookId}

仅允许 status = 'basement' 的书执行

查询 Basement 里的 Book 列表

GET /admin/libraries/{libraryId}/basement/books

调用 bookRepo.findBasementByLibrary

Block 软删除 API（已有的话只改用例，若无则新增）

DELETE /admin/blocks/{blockId} → 调 SoftDeleteBlockUseCase

不物理删，只标记 deleted_at

5. 前端改动计划（在 Domain 完成后执行）

目标： UI 上出现 Basement 视图；普通视图自动过滤 Basement 书籍；Block 不需要新 UI。

5.1 Basement 页面

新增路由（示例）：

/admin/libraries/[libraryId]/basement

页面行为：

调 GET /admin/libraries/{libraryId}/basement/books

列出所有 status = 'basement' 的 Book：

显示书名、原 bookshelf（如果有）、移动时间

每条提供：

“恢复”按钮 → POST /.../restore-from-basement

“永久删除”按钮 → DELETE /admin/books/{bookId}（可加二次确认）

5.2 Library / Bookshelf 视图过滤

现有获取 Book 列表的 API 修改为只返回 status='active' 的 Book；

前端不用多写逻辑，只要适配新的返回值。

5.3 Book 删除按钮的行为

在 Book 详情 / 列表的“删除”按钮上，
把当前的“硬删”替换成“移入 Basement”：

调用 POST /.../move-to-basement

成功后从当前列表中移除（因为不再是 active）

Block 这边前端不用改 UI，继续用现有的删除入口，只是后端改成软删除。

6. 测试 & 验证点（给 Copilot 写测例的 checklist）

Book 领域单测：

moveToBasement / restoreFromBasement / markDeleted 在不同初始状态下的行为

保证不变式：

active → basement → active OK

active → deleted ❌（抛错）

basement → deleted ✅

Book UseCase 单测：

调用后 status 正确变化

previousBookshelfId 记录/恢复正确

非法状态下抛出合适的错误

Block 软删除单测：

调用 SoftDelete 后 deleted_at 被设置

findByBook 不返回软删 block

API / 集成测试：

move-to-basement 后，Book 不出现在 normal 列表，但出现在 Basement 列表

从 Basement 恢复后，反之

在 Basement 执行 DELETE 后，Book 与对应 blocks 不再出现在任何列表（或被标记 deleted）

你可以把这整份当成“Basement + Block 软删除 ADR 的实施计划”，
先让 Copilot从 Domain → Repo → UseCase → Migration → API 一路推过去，
最后再让它帮你改前端路由和小 UI。

编辑器那条线好不容易稳定了，这次我们就按 Domain→外层这一条干净路径来，尽量不再引入“鬼畜副作用”。
