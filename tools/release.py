# -*- coding: utf-8 -*-
"""
Wordloom release helper (scoped)
- 自动读取最近一次 commit 的 subject（或手动指定 --bump）
- 根据提交类型决定版本号提升：feat→minor，fix→patch（也可 --bump major|minor|patch）
- 解析 scope：
    feat(api): ...        → 同步 bump 根 + 后端 WordloomBackend/api/VERSION
    feat(frontend): ...   → 同步 bump 根 + 前端 WordloomFrontend/streamlit/VERSION
    （都没有时只 bump 根 VERSION；也可用 --scope 覆盖）
- 写入 VERSION / 更新 CHANGELOG（插到最前）
- git add/commit/tag/push

用法：
    python tools/release.py
    python tools/release.py --bump minor
    python tools/release.py --scope api --bump patch
"""
import argparse
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

# === 路径 ===
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHANGELOG    = PROJECT_ROOT / "CHANGELOG.md"
ROOT_VER     = PROJECT_ROOT / "VERSION"
API_VER      = PROJECT_ROOT / "WordloomBackend" / "api" / "VERSION"
FE_VER       = PROJECT_ROOT / "WordloomFrontend" / "streamlit" / "VERSION"

# === 基础工具 ===
def run(cmd: str) -> str:
    res = subprocess.run(cmd, text=True, shell=True,
                         capture_output=True, cwd=str(PROJECT_ROOT))
    if res.returncode != 0:
        raise RuntimeError(f"[cmd error] {cmd}\n{res.stderr.strip()}")
    return res.stdout.strip()

def git_inside_repo() -> bool:
    try:
        return run("git rev-parse --is-inside-work-tree") == "true"
    except Exception:
        return False

def get_latest_commit_subject() -> str:
    try:
        return run("git log -1 --pretty=%s")
    except Exception:
        return ""

def detect_bump_from_msg(msg: str) -> str | None:
    m = msg.lower().strip()
    if m.startswith("feat"):
        return "minor"
    if m.startswith("fix"):
        return "patch"
    return None

def detect_scope_from_msg(msg: str) -> str | None:
    # Conventional Commits: type(scope): subject
    m = re.match(r"^[a-zA-Z]+(?:\(([^)]+)\))?:", msg.strip())
    if not m:
        return None
    scope = m.group(1) or ""
    scope = scope.lower()
    if "api" in scope or "backend" in scope:
        return "api"
    if "frontend" in scope or "streamlit" in scope or "ui" in scope:
        return "frontend"
    return None

def bump_semver(v: str, bump: str) -> str:
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", v.strip())
    if not m:
        raise ValueError(f"非法版本号：{v}（需要形如 0.4.2）")
    major, minor, patch = map(int, m.groups())
    if bump == "major":
        major += 1; minor = 0; patch = 0
    elif bump == "minor":
        minor += 1; patch = 0
    elif bump == "patch":
        patch += 1
    else:
        raise ValueError(f"未知 bump 类型：{bump}")
    return f"{major}.{minor}.{patch}"

def ensure_file_with_default(p: Path, default="0.1.0") -> str:
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(default, encoding="utf-8")
        print(f"⚠️ 未找到 {p.as_posix()}，已自动创建为 {default}")
    return p.read_text(encoding="utf-8").strip()

def ensure_changelog():
    if not CHANGELOG.exists():
        CHANGELOG.write_text("# 📜 Wordloom Changelog\n", encoding="utf-8")

def prepend_changelog(new_entries: list[tuple[str,str]]):
    """
    new_entries: [(version_label, line), ...]
    版本块合并为一个日期区块，例：
      ## [0.5.0] - 2025-10-17
      - feat(api): xxx
      - fix(frontend): yyy
    """
    ensure_changelog()
    today = datetime.now().strftime("%Y-%m-%d")
    lines = []
    # 取最大的那个（通常是根版本）作为显示标题
    title_version = new_entries[0][0]
    lines.append(f"\n## [{title_version}] - {today}\n")
    for _, line in new_entries:
        lines.append(f"- {line}\n")
    block = "".join(lines)

    old = CHANGELOG.read_text(encoding="utf-8")
    if old.startswith("#"):
        idx = old.find("\n")
        combined = old[:idx+1] + block + old[idx+1:] if idx != -1 else old + block
    else:
        combined = "# 📜 Wordloom Changelog\n" + block + old
    CHANGELOG.write_text(combined, encoding="utf-8")

def ensure_remote_and_commits():
    if not git_inside_repo():
        raise SystemExit("❌ 不是 Git 仓库。请在 Wordloom 根目录初始化后再运行。")
    try:
        _ = run("git remote -v")
    except Exception:
        raise SystemExit("❌ 未配置远端（git remote）。请先添加 origin。")
    try:
        run("git rev-parse HEAD")
    except Exception:
        raise SystemExit("❌ 当前仓库没有任何提交。请先提交一次再运行。")

# === 主流程 ===
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bump", choices=["major","minor","patch"],
                    help="手动指定版本递增类型（默认：根据最近一次 commit 自动判断）")
    ap.add_argument("--scope", choices=["api","frontend","root","all"],
                    help="手动指定影响范围（默认：根据 commit scope 自动判断；root=仅全局；all=根+前端+后端）")
    args = ap.parse_args()

    ensure_remote_and_commits()

    last_msg = get_latest_commit_subject()
    if not last_msg:
        raise SystemExit("❌ 读取不到最近一次提交信息。请先提交一次。")
    print(f"🧾 最近一次提交：{last_msg}")

    bump_type = args.bump or detect_bump_from_msg(last_msg)
    if not bump_type:
        print("⚠️ 不是 feat/fix（且未指定 --bump），不升级版本。")
        return

    auto_scope = detect_scope_from_msg(last_msg)
    scope = args.scope or auto_scope or "root"

    # 读取/准备现有版本
    root_v = ensure_file_with_default(ROOT_VER)
    api_v  = ensure_file_with_default(API_VER)
    fe_v   = ensure_file_with_default(FE_VER)

    targets = []
    if scope == "root":
        targets = [("root", ROOT_VER, root_v)]
    elif scope == "api":
        targets = [("root", ROOT_VER, root_v), ("api", API_VER, api_v)]
    elif scope == "frontend":
        targets = [("root", ROOT_VER, root_v), ("frontend", FE_VER, fe_v)]
    elif scope == "all":
        targets = [("root", ROOT_VER, root_v), ("api", API_VER, api_v), ("frontend", FE_VER, fe_v)]

    bumped = []
    for name, path, old in targets:
        newv = bump_semver(old, bump_type)
        path.write_text(newv, encoding="utf-8")
        bumped.append((name, path, old, newv))

    # 组装 CHANGELOG（以根版本号作为该次标题）
    title_version = [b for b in bumped if b[0] == "root"][0][3] if any(b[0]=="root" for b in bumped) else bumped[0][3]
    entries = [(title_version, last_msg)]
    prepend_changelog(entries)

    # 提交 & 打标签 & 推送
    paths = " ".join([str(p[1].relative_to(PROJECT_ROOT)).replace("\\","/") for p in bumped])
    run(f"git add {paths} CHANGELOG.md")
    run(f'git commit -m "chore(release): bump {",".join([b[0] for b in bumped])} to {title_version} ({bump_type})"')
    run(f'git tag -a v{title_version} -m "release {title_version}"')
    run("git push")
    run("git push --tags")

    print("✅ 已发布：")
    for name, _, old, new in bumped:
        print(f"   - {name}: {old} → {new} ({bump_type})")
    print(f"   - tag: v{title_version}")

if __name__ == "__main__":
    main()
