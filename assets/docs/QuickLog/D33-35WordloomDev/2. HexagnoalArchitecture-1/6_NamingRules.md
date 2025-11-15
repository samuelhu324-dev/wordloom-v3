🎯 为什么要用 I 前缀？

原因 1：接口 vs 实现的明确区分
在 Hexagonal 架构 中：
Port（抽象接口）              Adapter（具体实现）
─────────────────────────────────────────────
ILibraryRepository       →     SQLAlchemyLibraryRepository
ITagRepository           →     SQLAlchemyTagRepository
IBookRepository          →     SQLAlchemyBookRepository

如果都叫 LibraryRepository：
# ❌ 混乱！哪个是接口？哪个是实现？
class LibraryRepository(ABC): pass          # 接口？
class LibraryRepository(LibraryRepository): pass  # 实现？ 冲突！

原因 2：编程约定（来自多种语言）
语言	约定	例子
Java	接口用 I 前缀	ILibraryRepository
C#	接口用 I 前缀	ILibraryRepository
Python	接口用 I 前缀（PEP 8 扩展）	ILibraryRepository
TypeScript	接口用 I 前缀	ILibraryRepository
Go	接口用 er 后缀	LibraryRepository → RepositoryInterface

Wordloom 遵循 Java/C#/Python 的 I 前缀约定。

原因 3：Hexagonal 架构的 Port 术语
Port（入站/出站端口）= 系统与外界的边界
├─ Input Port  = UseCase Interface (ICreateLibraryUseCase)
└─ Output Port = Repository Interface (ILibraryRepository)

Adapter（适配器）= 实现 Port 的具体代码
├─ HTTP Adapter = FastAPI Router
├─ Repository Adapter = SQLAlchemyLibraryRepository
└─ EventBus Adapter = EventBus

所以：

✅ ILibraryRepository = Port（抽象）
✅ SQLAlchemyLibraryRepository = Adapter（具体）

完整的命名规范（所有 6 个模块）
Module     | Port Interface         | Adapter Implementation
-----------|------------------------|-------------------------------
Library    | ILibraryRepository     | SQLAlchemyLibraryRepository
Bookshelf  | IBookshelfRepository   | SQLAlchemyBookshelfRepository
Book       | IBookRepository        | SQLAlchemyBookRepository
Block      | IBlockRepository       | SQLAlchemyBlockRepository
Tag        | ITagRepository         | SQLAlchemyTagRepository
Media      | IMediaRepository       | SQLAlchemyMediaRepository

UseCase    | Port Interface         | Implementation
-----------|------------------------|-------------------------------
Create     | ICreateLibraryUseCase  | CreateLibraryUseCase
Get        | IGetLibraryUseCase     | GetLibraryUseCase
Delete     | IDeleteLibraryUseCase  | DeleteLibraryUseCase
Rename     | IRenameLibraryUseCase  | RenameLibraryUseCase
