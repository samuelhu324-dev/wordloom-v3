
import re
from pathlib import Path

# =========================
# Wordloom Markdown Path Fixer (robust path resolver)
# =========================

DOCS_DIR = Path(__file__).resolve().parent
STATIC_ROOT = DOCS_DIR.parent / "static"

MD_IMG_RE = re.compile(r'!\[(?P<alt>[^\]]*)\]\((?P<url>[^)\s]+)(?:\s+"[^"]*")?\)')
MD_LINK_RE = re.compile(r'(?<!\!)\[(?P<text>[^\]]*)\]\((?P<url>[^)\s]+)\)')
HTML_SRC_HREF_RE = re.compile(r'(?P<attr>\b(?:src|href))=(?P<q>["\'])(?P<url>.*?)(?P=q)')

DEFAULT_IMG_WIDTH = 480
ENABLE_MD_IMG_TO_HTML = True
PREFER_DIRS_BY_EXT = {
    "png": ["media/img", "thumb", "icons"],
    "jpg": ["media/img", "thumb"],
    "jpeg":["media/img", "thumb"],
    "gif": ["media/gif", "thumb"],
    "mp4": ["media/video"],
    "jfif":["icons", "media/img"],
    "ico": ["icons"],
    "otf": ["fonts"],
}

def _is_external(u: str) -> bool:
    low = u.lower()
    return (
        low.startswith('http://') or low.startswith('https://') or
        low.startswith('mailto:') or low.startswith('data:') or
        low.startswith('#') or '://' in u
    )

def _normalize_from_assets(u: str) -> str | None:
    u2 = u.replace("\\", "/")
    if "assets/static/" in u2:
        return "../static/" + u2.split("assets/static/", 1)[1]
    if u2.startswith("/assets/static/"):
        return "../static/" + u2[len("/assets/static/"):]
    if u2.startswith("./assets/static/"):
        return "../static/" + u2[len("./assets/static/"):]
    if u2.startswith("../assests/"):
        return "../static/" + u2[len("../assests/"):]
    return None

def _contains_static(u: str) -> str | None:
    u2 = u.replace("\\", "/")
    idx = u2.find("static/")
    if idx != -1:
        return "../static/" + u2[idx + len("static/"):]
    return None

def _guess_from_filename(filename: str) -> str | None:
    if "/" in filename or "\\" in filename:
        return None
    if not STATIC_ROOT.exists():
        return None

    name = Path(filename).name
    ext = name.split(".")[-1].lower()
    candidates = list(STATIC_ROOT.rglob(name))
    if not candidates:
        return None

    prefer = PREFER_DIRS_BY_EXT.get(ext, [])
    if prefer:
        for pref in prefer:
            for c in candidates:
                if f"/{pref}/" in c.as_posix():
                    rel = c.relative_to(STATIC_ROOT).as_posix()
                    return f"../static/{rel}"

    rel = candidates[0].relative_to(STATIC_ROOT).as_posix()
    return f"../static/{rel}"

def rewrite_url(url: str) -> str:
    u = url.replace("\\", "/").strip()
    if _is_external(u):
        return url
    if u.startswith("../static/"):
        return u

    fix = _normalize_from_assets(u)
    if fix:
        return fix

    fix = _contains_static(u)
    if fix:
        return fix

    if "/" not in u and "\\" not in u:
        guess = _guess_from_filename(u)
        if guess:
            return guess

    if u.startswith("./") and ("/" not in u[2:] and "\\" not in u[2:]):
        guess = _guess_from_filename(u[2:])
        if guess:
            return guess

    return u

def _md_img_to_html(alt: str, url: str) -> str:
    fixed = rewrite_url(url)
    alt_text = (alt or Path(fixed).stem)
    return (
        f'<a href="{fixed}" target="_blank">\\n'
        f'  <img src="{fixed}" width="{DEFAULT_IMG_WIDTH}" loading="lazy" alt="{alt_text}">\\n'
        f'</a>'
    )

def process_text(md: str) -> str:
    def md_img_sub(m: re.Match) -> str:
        alt = m.group("alt")
        url = m.group("url")
        if ENABLE_MD_IMG_TO_HTML:
            return _md_img_to_html(alt, url)
        else:
            fixed = rewrite_url(url)
            return f'![{alt}]({fixed})'

    md = MD_IMG_RE.sub(md_img_sub, md)

    def md_link_sub(m: re.Match) -> str:
        text = m.group("text")
        url = m.group("url")
        fixed = rewrite_url(url)
        return f'[{text}]({fixed})'
    md = MD_LINK_RE.sub(md_link_sub, md)

    def html_sub(m: re.Match) -> str:
        attr, q, url = m.group("attr"), m.group("q"), m.group("url")
        return f'{attr}={q}{rewrite_url(url)}{q}'
    md = HTML_SRC_HREF_RE.sub(html_sub, md)

    return md

def _resolve_path_arg(arg: str) -> Path:
    """
    更智能的路径解析：
    - 先按当前工作目录解析
    - 不存在且形如 "assets/docs/..." 的，改为基于仓库根（脚本的 ../../）拼接
    - 若是裸文件名 *.md，尝试在脚本所在的 DOCS_DIR 下寻找
    - 若是目录名 "assets/docs"、"." 等，同理做兼容
    """
    p = Path(arg)
    if p.exists():
        return p

    s = str(p).replace("\\", "/")

    # 1) 裸文件名（*.md） -> DOCS_DIR / name
    if p.suffix.lower() == ".md" and "/" not in s:
        cand = DOCS_DIR / p.name
        if cand.exists():
            return cand

    # 2) 传了 assets/docs/... -> 以仓库根推导
    repo_root = DOCS_DIR.parent.parent  # .../assets -> parent -> repo root
    if s.startswith("assets/"):
        cand = (repo_root / s).resolve()
        if cand.exists():
            return cand

    # 3) 在 DOCS_DIR 下再试一次（防止多余前缀）
    cand = (DOCS_DIR / s).resolve()
    if cand.exists():
        return cand

    # 4) 退回原值（让上层抛出 FileNotFoundError 以提示用户）
    return p

def fix_file(md_path: Path) -> Path:
    md_path = _resolve_path_arg(str(md_path))
    if not md_path.exists():
        raise FileNotFoundError(md_path)

    original = md_path.read_text(encoding="utf-8", errors="ignore")

    legacy = md_path.with_name(md_path.stem + "_legacy" + md_path.suffix)
    if not legacy.exists():
        legacy.write_text(original, encoding="utf-8")

    fixed = process_text(original)
    md_path.write_text(fixed, encoding="utf-8")
    print(f"✔ {md_path.name} fixed (backup: {legacy.name})")
    return md_path

def fix_tree(root: Path, pattern: str="*.md"):
    root = _resolve_path_arg(str(root))
    out = []
    for p in root.rglob(pattern):
        out.append(fix_file(p))
    return out

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Fix Markdown media paths to ../static/... and convert ![]() -> <a><img>.")
    ap.add_argument("paths", nargs="+", help="Files or directories to process")
    ap.add_argument("-g", "--glob", default="*.md", help="Glob for directories (default: *.md)")
    ap.add_argument("--no-html", action="store_true", help="Do NOT convert ![]() to <a><img>; only normalize paths")
    ap.add_argument("--width", type=int, default=DEFAULT_IMG_WIDTH, help="Image width in <img> tag (default: 480)")
    args = ap.parse_args()

    if args.no_html:
        globals()["ENABLE_MD_IMG_TO_HTML"] = False
    globals()["DEFAULT_IMG_WIDTH"] = args.width

    outputs = []
    for p in args.paths:
        P = _resolve_path_arg(p)
        if P.is_dir():
            outputs.extend(fix_tree(P, pattern=args.glob))
        else:
            outputs.append(fix_file(P))
    for o in outputs:
        print(o)
