来，给你一个可以直接丢进 DDD_RULES / HEXAGONAL_RULES / DEVLOG 的搜索方案总结。

1. 搜索的目标与范围（Phase 1）

目标：
先做一个统一的「搜索后端」，支持：

全局搜索：一个关键字，查多种实体

Book 内搜索：限定在某本书的 Blocks

未来可以扩展 Loom 词条专用搜索

搜索对象（SearchEntityType）：

entry：翻译词条（未来 Loom 模块）

library：库

bookshelf：书架 ✅

book：书

block：书中的内容块

tag：标签

Bookshelf 也纳入搜索：便于按书架名快速定位一片区域（Grammar、Exam、Writing等）。

2. Hexagonal 视角下的 Search 结构
2.1 Domain 模型
SearchEntityType = Literal["entry", "library", "bookshelf", "book", "block", "tag"]

@dataclass
class SearchQuery:
    text: str
    type: Optional[SearchEntityType] = None   # None = 全局搜索
    book_id: Optional[int] = None            # 限定某本 Book 内搜索
    limit: int = 20
    offset: int = 0

@dataclass
class SearchHit:
    type: SearchEntityType
    id: int
    title: str
    snippet: str
    score: float
    path: str        # 如 "Library A / Shelf B / Book C"

@dataclass
class SearchResult:
    total: int
    hits: list[SearchHit]


以后无论换不换实现（Postgres / search_index / Elastic），前端只认这套结构。

2.2 Application 层：SearchPort + SearchService
class SearchPort(ABC):
    @abstractmethod
    def search(self, query: SearchQuery) -> SearchResult:
        ...

class SearchService:
    def __init__(self, search_port: SearchPort):
        self._search_port = search_port

    def handle(self, query: SearchQuery) -> SearchResult:
        # 将来可以在这里加权限 / 日志 / 过滤
        return self._search_port.search(query)


应用层只依赖 SearchPort 抽象；

具体用什么实现（PostgresSearchAdapter / ElasticSearchAdapter）都在 infra 层。

3. Infra 实现（Phase 1：Postgres 简化全文搜索）
3.1 不上 Elastic，只用 Postgres 自带全文搜索

核心语法：

WHERE to_tsvector(content) @@ plainto_tsquery(:q)


含义：

to_tsvector(content)：把文本拆词、词干化，变成可检索的向量；

plainto_tsquery(:q)：把用户输入的查询词变成 tsquery；

@@：匹配运算符。

今天的简化版：

先不建 search_vector 字段；

也不写 trigger；

搜索时直接在 SQL 里用 to_tsvector(content) 即可；

将来性能不够，再：

增加 search_vector 列；

用 trigger 或 ORM 维护；

建 GIN 索引。

3.2 PostgresSearchAdapter 示例逻辑
class PostgresSearchAdapter(SearchPort):
    def __init__(self, session_factory):
        self._session_factory = session_factory

    def search(self, query: SearchQuery) -> SearchResult:
        text = query.text.strip()
        if not text:
            return SearchResult(total=0, hits=[])

        hits: list[SearchHit] = []
        total = 0
        with self._session_factory() as session:
            # Block
            if query.type in (None, "block"):
                block_hits, block_total = self._search_blocks(session, query)
                hits.extend(block_hits)
                total += block_total

            # Bookshelf / Book / Tag / Entry / Library 类似加方法即可

        hits.sort(key=lambda h: h.score, reverse=True)
        return SearchResult(total=total, hits=hits)


Block 的搜索（示意）：

def _search_blocks(self, session: Session, query: SearchQuery):
    sql = """
    SELECT id, content, book_id,
           ts_rank_cd(to_tsvector(content), plainto_tsquery(:q)) AS score
    FROM blocks
    WHERE to_tsvector(content) @@ plainto_tsquery(:q)
    {book_filter}
    ORDER BY score DESC
    LIMIT :limit OFFSET :offset
    """
    # ...


Bookshelf / Book / Tag / Entry类同，只是查不同表、组装不同 title/snippet/path。

4. HTTP API：统一 /search 入口

/search GET 接口示例：

@router.get("/")
def search(
    q: str = Query(..., min_length=1),
    type: str | None = Query(None, regex="^(entry|library|bookshelf|book|block|tag)$"),
    book_id: int | None = None,
    limit: int = 20,
    offset: int = 0,
    service: SearchService = Depends(get_search_service),
):
    query = SearchQuery(
        text=q,
        type=type,
        book_id=book_id,
        limit=limit,
        offset=offset,
    )
    result = service.handle(query)
    return {
        "total": result.total,
        "hits": [hit.__dict__ for hit in result.hits],
    }


前端 Phase 1 能做的 vertical slice：

顶部全局搜索框：只传 q；

Book 编辑页内“搜索本书”：传 q + book_id；

将来：

“只搜 Tag” → 传 type=tag

“只搜 Bookshelf” → type=bookshelf

5. 后续演化路线（但不是今天要做的）
5.1 优化 Postgres 版全文检索（不换技术栈）

当数据多了 / 查询慢了，可以升级为：

给常搜字段加 search_vector 列：

ALTER TABLE blocks ADD COLUMN search_vector tsvector;
CREATE INDEX idx_blocks_search_fts ON blocks USING GIN (search_vector);


用 trigger 或 ORM，在插入/更新时更新 search_vector；

搜索时 WHERE search_vector @@ plainto_tsquery(:q)，性能更好。

5.2 引入 search_index 表（仍然只用 Postgres）

当你觉得“跨多表搜索 + JOIN 太重”时，可以：

建一张专门做搜索的表：

CREATE TABLE search_index (
  id          bigserial primary key,
  entity_type text not null,
  entity_id   bigint not null,
  text        text not null,
  tags        text[],
  path        text,
  updated_at  timestamptz not null default now()
);


用现有 EventBus 维护索引：

BlockCreated/Updated/Deleted → 对应地插/改/删 search_index 里的 block 记录；

EntryCreated/Updated/Deleted 等同理。

PostgresSearchAdapter 只查 search_index 一张表即可。

这一整套仍然是 Postgres 内部方案，不强制上 Elastic。

5.3 真要上 Elastic / OpenSearch 的时候

也是换一个 ElasticSearchAdapter(SearchPort)；

SearchService 和前端接口不变；

SearchEntityType / SearchResult 结构不变。

这是再后面的事，可以等 Wordloom 真有用户量再考虑。

6. 总体心智模型（一句话版）

现在：Search = 一个独立的 Hexagonal 端口 + 用 Postgres 实现的全文搜索,
支持 Entry / Library / Bookshelf / Book / Block / Tag，前端统一 /search 调用；

以后：

可以在 Postgres 内做 search_vector 优化；

可以再进化到 search_index + EventBus；

再极端一点才需要挪到 Elastic 等专业搜索引擎。

你今天要落地的，只是这条“简化版 PostgresSearchAdapter + /search API + 前端 vertical slice”，
已经足够专业、好讲故事，又不会把未来的自己锁死。