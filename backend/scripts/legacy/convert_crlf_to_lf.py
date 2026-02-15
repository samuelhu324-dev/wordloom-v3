from __future__ import annotations

import subprocess
from pathlib import Path


def _repo_root() -> Path:
    # backend/scripts/convert_crlf_to_lf.py -> repo root
    return Path(__file__).resolve().parents[2]


def _git_ls_files(root: Path, pattern: str) -> list[Path]:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "ls-files", "-z", "--", pattern],
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return []
    items = [p for p in out.split(b"\x00") if p]
    return [root / p.decode("utf-8") for p in items]


def _has_crlf(path: Path) -> bool:
    data = path.read_bytes()
    return b"\r\n" in data


def _convert(path: Path) -> bool:
    data = path.read_bytes()
    new = data.replace(b"\r\n", b"\n")
    # Just in case there are stray CR characters.
    new = new.replace(b"\r", b"")
    if new == data:
        return False
    path.write_bytes(new)
    return True


def main() -> int:
    root = _repo_root()

    candidates: set[Path] = set()
    # NOTE: git pathspec `*.sh` only matches repo-root.
    # Use recursive glob pathspecs to cover the whole repo.
    for pattern in [
        ":(glob)**/*.sh",
        ":(glob)**/.env*",
    ]:
        candidates.update(_git_ls_files(root, pattern))

    # Also include local/ignored envs that are commonly created.
    for extra in [
        root / ".env.dev",
        root / ".env.test",
        root / "backend/.env.devtest.5435.dev",
        root / "backend/.env.devtest.5435.test",
    ]:
        candidates.add(extra)

    existing = sorted([p for p in candidates if p.is_file()])
    crlf_before = [p for p in existing if _has_crlf(p)]

    print(f"[crlf] candidates checked: {len(existing)}")
    print(f"[crlf] CRLF found (before): {len(crlf_before)}")
    for p in crlf_before:
        print("  -", p.relative_to(root).as_posix())

    changed = 0
    for p in crlf_before:
        if _convert(p):
            changed += 1

    crlf_after = [p for p in existing if _has_crlf(p)]
    print(f"[crlf] converted: {changed}")
    print(f"[crlf] CRLF found (after): {len(crlf_after)}")
    for p in crlf_after:
        print("  -", p.relative_to(root).as_posix())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
