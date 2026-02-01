Status: ✅ Completed — 2025-12-06

先给结论：这一步先不写代码，只把“Basement 回收系统”的落地实施计划用中文整理出来，完全贴合你已经给出的目录结构和 Plan_173A。

下面这份可以直接当“实施 checklist”用。

一、总体目标与边界

目标：
在后端 Domain/Hexagonal 架构里落地 Book 的 Basement（软删除）机制。
为 Block 增加软删除标记 deleted_at，但暂不暴露前端回收站 UI。
明确不动的部分：
不改编辑器键盘逻辑（Enter/Backspace/Shift+Enter 等）。
不改 Block 现有内容结构（text/metadata 等字段保持不变）。
不引入新 Domain 端口以外的 UI 逻辑，本计划只做后端 + 最小 API。
二、backend/api/app/modules/basement 模块结构规划

参考 modules/maturity，在 basement 下创建：

domain/
__init__.py
entities.py（Book/Basement 相关领域模型扩展）
value_objects.py（如有需要定义 BookStatus 等枚举/VO）
repositories.py（Basement 相关仓储接口定义，可复用现有 Book/Block 仓储抽象）
services.py 或 use_cases.py（领域服务可选，如果需要跨聚合逻辑）
application/
__init__.py
use_cases.py：
MoveBookToBasementUseCase
RestoreBookFromBasementUseCase
HardDeleteBookUseCase
SoftDeleteBlockUseCase
routers/
__init__.py
basement_router.py：
定义 /admin/books/{book_id}/move-to-basement
/admin/books/{book_id}/restore-from-basement
/admin/books/{book_id}（仅 basement 状态下允许硬删）
/admin/libraries/{library_id}/basement/books
schemas.py
请求/响应 DTO（Pydantic）：
MoveBookToBasementRequest（可包含 reason?: str）
BasementBookResponse（包含 id,title,bookshelf_id,previous_bookshelf_id,moved_to_basement_at 等）
exceptions.py
BookNotInBasementError
BookAlreadyInBasementError
ForbiddenBasementOperationError（权限/状态错误统一用）
设计要点：basement 模块本身主要是“Application + API 组合层”，Domain 的核心字段修改仍在 book/block 原有 Domain 内完成（下面三、四）。

三、Domain：Book 聚合扩展（支持 Basement）

在 book_models.py 所对应的 Domain 层（看你当前 Book domain 放在何处，一般在 domain 或类似目录）中，按 Plan_173A 要求扩展：

新增 BookStatus 枚举 / 类型：

在 domain 层定义：
BookStatus = Literal["active", "basement", "deleted"] 或 Enum。
Book 实体新增字段：

status: BookStatus = "active"
previous_bookshelf_id: Optional[UUID]
moved_to_basement_at: Optional[datetime]
新增领域方法：

move_to_basement(now: datetime) -> None
仅当 status == "active" 时允许，否则抛领域异常。
设置：
status = "basement"
previous_bookshelf_id = self.bookshelf_id
moved_to_basement_at = now
restore_from_basement() -> None
仅当 status == "basement" 时允许。
设置：
status = "active"
bookshelf_id = previous_bookshelf_id（如存在）
mark_deleted(now: datetime) -> None
仅当 status == "basement" 时允许。
设置：
status = "deleted"
（可选）记录内部删除时间字段，用于审计。
单元测试计划：

active → basement → active 正常。
active → deleted 抛错。
basement → deleted 成功。
basement → basement/deleted → basement 抛错。
四、Domain：Block 聚合扩展（软删除标记）

在 Block 对应 Domain（domain 或 modules/block/domain 等）：

Block 新增字段：

deleted_at: Optional[datetime] = None
领域方法：

soft_delete(now: datetime)：deleted_at = now
restore()：deleted_at = None
不改变：

不改 kind/content/index 等字段。
暂不新增 Block 级“回收站视图”，仅为未来 Admin 工具准备。
测试计划：

调用 soft_delete 后，deleted_at 非空。
restore 后，deleted_at 变回 None。
五、基础设施：数据库 models & migrations

books 表迁移

在 database 现有迁移体系里新增 migration：
新增字段：
ALTER TABLE books
  ADD COLUMN status VARCHAR(32) NOT NULL DEFAULT 'active',
  ADD COLUMN previous_bookshelf_id UUID NULL,
  ADD COLUMN moved_to_basement_at TIMESTAMP NULL;

同步到 book_models.py：
Pydantic/SQLAlchemy 模型中添加相同字段映射。
blocks 表迁移

新增字段：
ALTER TABLE blocks
  ADD COLUMN deleted_at TIMESTAMP NULL;

block_models.py 同步新增 deleted_at.
测试验证：

check_schema.py / 现有 schema 校验脚本跑一遍，确认字段一致。
在本地创建一条书 + block，手动 update 字段，确认 ORM 能映射。

六、基础设施：Repository 实现（infra/database + infra/storage）

结合你截图中的目录：

BookRepository 扩展

在 Domain 抽象（如 modules/book/domain/repositories.py）：
class BookRepository(Protocol):
    async def find_by_id(self, book_id: UUID) -> Optional[Book]: ...
    async def find_active_by_library(self, library_id: UUID) -> list[Book]: ...
    async def find_basement_by_library(self, library_id: UUID) -> list[Book]: ...
    async def save(self, book: Book) -> None: ...

在基础设施层：

library_repository_impl.py / book_repository_impl.py 中实现：
find_active_by_library: WHERE status = 'active'
find_basement_by_library: WHERE status = 'basement'
更新现有“列出 books”查询，让默认列表只返回 status='active'。
BlockRepository 扩展

Domain 抽象（新建 backend/api/app/modules/basement/domain/repositories.py 中可引用）：

class BlockRepository(Protocol):
    async def find_by_book(self, book_id: UUID) -> list[Block]:  # 只返回 active
    async def find_deleted_by_book(self, book_id: UUID) -> list[Block]:  # 可选
    async def soft_delete(self, block_id: UUID, now: datetime) -> None:
    async def restore(self, block_id: UUID) -> None:

基础设施实现：
block_repository_impl.py：
find_by_book: WHERE deleted_at IS NULL
find_deleted_by_book: WHERE deleted_at IS NOT NULL
soft_delete: UPDATE blocks SET deleted_at = now WHERE id = ...
restore: UPDATE blocks SET deleted_at = NULL WHERE id = ...
infra 层其他扩展（如需要）

在 tests 中新增针对 Basement 的 repository 级测试。
如果有统一的 storage_manager / UnitOfWork，在其中注册 basement 用例需要的 repo。

七、Application 用例实现（modules/basement/application）

在 backend/api/app/modules/basement/application/use_cases.py 中实现：

MoveBookToBasementUseCase

输入：book_id, now, current_user
流程：
book = book_repo.find_by_id(book_id)
权限检查（是否可操作该 book）
book.move_to_basement(now)
book_repo.save(book)
RestoreBookFromBasementUseCase

输入：book_id, current_user
流程：
book = book_repo.find_by_id(book_id)
book.restore_from_basement()
book_repo.save(book)
HardDeleteBookUseCase

输入：book_id, now, current_user
流程：
book = book_repo.find_by_id(book_id)
要求 status == 'basement'，否则抛 BookNotInBasementError
book.mark_deleted(now)
book_repo.save(book)
物理/逻辑删除该 book 下 blocks：
简化版：DELETE FROM blocks WHERE book_id = ...
或：调用 block_repo.soft_delete(...) 批量软删（按当前策略选择）。
SoftDeleteBlockUseCase

输入：block_id, now, current_user
流程：
调 block_repo.soft_delete(block_id, now)
后续前端的“删除 Block”请求指向这个 UseCase，而不是直接物理删。
UseCase 测试：

使用 infra 的 fake repo / in-memory 实现，验证状态流转和异常。
八、FastAPI 路由与 API Schema（modules/basement/routers + schemas）

在 backend/api/app/modules/basement/routers/basement_router.py 中定义路由：

POST /admin/books/{book_id}/move-to-basement
Body：可选 { "reason": string | null }
调用 MoveBookToBasementUseCase
POST /admin/books/{book_id}/restore-from-basement
调用 RestoreBookFromBasementUseCase
DELETE /admin/books/{book_id}
语义：仅对 status='basement' 的书做硬删/标记删除。
调用 HardDeleteBookUseCase
GET /admin/libraries/{library_id}/basement/books
调用 book_repo.find_basement_by_library
返回 List[BasementBookResponse]。
在 schemas.py 中定义：

BasementBookResponse：
id: UUID
title: str
bookshelf_id: UUID | None
previous_bookshelf_id: UUID | None
moved_to_basement_at: datetime | None
status: Literal["basement"]
MoveBookToBasementRequest（可选）：
reason: str | None
九、前端影响（本计划只列出最小要求，后续可单独起 Plan）

当前 Plan_173A 的重点在后端和 Domain，因此前端只做最小对齐：

Book 列表 API 过滤
确认前端请求的 Books 列表 API 已只返回 status='active'，不需要额外 UI 逻辑。
删除入口重定向（未来 Plan）
后续某个前端 Plan（例如 Plan_174）再把 “删除 Book” 按钮从硬删改为调用 /move-to-basement。
Basement 页面 UI（未来 Plan）
单独起 Plan（比如 Plan_175A Basement UI）设计 /admin/libraries/[libraryId]/basement 页面，这次暂不实现。
十、测试与验收 checklist

Domain 层
Book move_to_basement / restore_from_basement / mark_deleted 单测。
Block soft_delete / restore 单测。
Repository / Infra
find_active_by_library 不包含 basement/deleted。
find_basement_by_library 仅返回 basement。
find_by_book 忽略 deleted_at 不为空的 blocks。
UseCase
Move/Restore/HardDelete/SoftDelete 都有 happy path + invalid 状态测试。
API 集成
move-to-basement 后：
正常列表 API 不再返回该书。
Basement 列表 API 返回该书。
restore-from-basement 后相反。
DELETE /admin/books/{book_id} 只能在 basement 状态下成功，其余状态返回 4xx。
数据校验
迁移脚本执行后，check_schema.py 通过。
手动插入几条测试数据，验证 ORM 映射字段正确。
如果你愿意，下一步我可以按这份计划，在 modules/basement 下先帮你把 domain + application + routers 框架文件和基础仓储接口骨架写出来（不一次性写完所有实现），方便你在 VS Code 里边看边调整。