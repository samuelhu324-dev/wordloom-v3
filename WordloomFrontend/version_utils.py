from pathlib import Path

def read_version() -> str:
    # 尝试从仓库根目录读取 VERSION
    # 若失败，回退到 dev 标记
    try:
        repo_root = Path(__file__).resolve().parents[2]  # 调整父级层数以匹配你的结构
        ver_file = repo_root / "VERSION"
        return ver_file.read_text(encoding="utf-8").strip()
    except Exception:
        return "0.0.0-dev"
