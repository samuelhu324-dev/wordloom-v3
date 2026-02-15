#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$BACKEND_DIR/.." && pwd)"

cd "$BACKEND_DIR"

if [[ -f "$BACKEND_DIR/.venv_linux/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$BACKEND_DIR/.venv_linux/bin/activate"
fi

echo "VIRTUAL_ENV=${VIRTUAL_ENV-}"
echo "which python3=$(command -v python3)"

python3 - <<'PY'
import os
import site
import sys

print("executable=", sys.executable)
print("version=", sys.version)
print("flags=", sys.flags)
print("has_ps1=", hasattr(sys, "ps1"))
print("PYTHONINSPECT=", os.getenv("PYTHONINSPECT"))
print("PYTHONSTARTUP=", os.getenv("PYTHONSTARTUP"))
print("PYTHONNOUSERSITE=", os.getenv("PYTHONNOUSERSITE"))
print("cwd=", os.getcwd())
print("path0=", sys.path[0])
print("site_file=", getattr(site, "__file__", None))
print("usersite=", site.getusersitepackages() if hasattr(site, "getusersitepackages") else None)
print("sitepackages=", site.getsitepackages() if hasattr(site, "getsitepackages") else None)

# Attempt imports that could trigger a banner/REPL.
mods = ("sitecustomize", "usercustomize")
for mod in mods:
  try:
    m = __import__(mod)
    print(f"imported {mod}: OK file={getattr(m, '__file__', None)}")
  except Exception as e:
    print(f"imported {mod}: {type(e).__name__}: {e}")
PY
