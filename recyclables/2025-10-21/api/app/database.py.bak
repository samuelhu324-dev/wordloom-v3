# app/database.py
from pathlib import Path
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# —— 新增：尽量使用统一的 path_manager（在项目根）；失败则回退到旧逻辑 ——
def _import_pm():
    try:
        from path_manager import PM  # 项目根目录下
        return PM
    except Exception:
        return None

def _resolve_sqlite_path_fallback() -> str:
    """
    兼容你当前的多处位置：优先已有的，再回退到根目录 app.db
    返回 SQLAlchemy 的 sqlite URL 形式，如 sqlite:///D:/xxx/app.db
    """
    repo_root = Path(__file__).resolve().parents[2]
    candidates = [
        repo_root / "app.db",
        repo_root / "storage" / "wordloom.db",
        repo_root / "app" / "app.db",
    ]
    for p in candidates:
        if p.exists():
            return f"sqlite:///{p.as_posix()}"
    # 默认回退到根目录 app.db（不存在会自动创建）
    return f"sqlite:///{(repo_root / 'app.db').as_posix()}"

PM = _import_pm()

def _build_sqlite_url() -> str:
    # 1) 显式 URL 优先（兼容历史变量名）
    url = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
    if url:
        return url
    # 2) 统一真源：BACKEND_DB（若设置则由它构造 URL）
    backend_db = os.getenv("BACKEND_DB")
    if backend_db:
        return f"sqlite:///{Path(backend_db).as_posix()}"
    # 3) 有 path_manager 则用它的默认（WordloomBackend/storage/wordloom.db）
    if PM is not None:
        return f"sqlite:///{PM.backend_db.as_posix()}"
    # 4) 最后回退到原来的“猜测路径”逻辑
    return _resolve_sqlite_path_fallback()

# 统一的数据库 URL
DATABASE_URL = _build_sqlite_url()

# 创建 Engine / Session
engine = create_engine(
    DATABASE_URL,
    future=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)

# 依赖函数（FastAPI 会用到）
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
