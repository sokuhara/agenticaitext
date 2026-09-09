"""Tools the agent may use. Every tool is a plain Python function with limits built in.

PROJECT_ROOT is the vibe-chat folder (the parent of this agent/ folder), whatever the
current working directory is.
"""

import difflib
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Files the agent may overwrite: .py files directly under the project root, or under tests/.
WRITE_ROOTS = [PROJECT_ROOT, PROJECT_ROOT / "tests"]

# Files whose "before" state we keep, so we can show a diff without git.
WATCHED_FILES = ["app.py", "tests/test_app.py"]


def _safe_path(path: str) -> Path:
    """Resolve a path and refuse anything outside the project."""
    target = (PROJECT_ROOT / path).resolve()
    if PROJECT_ROOT not in target.parents and target != PROJECT_ROOT:
        raise ValueError("Files outside the project cannot be accessed.")
    return target


def read_file(path: str) -> str:
    """Read a file inside the project (first 4000 characters)."""
    return _safe_path(path).read_text(encoding="utf-8")[:4000]


def write_file(path: str, content: str) -> str:
    """Overwrite a .py file directly under the project root or under tests/."""
    target = _safe_path(path)
    if not any(root == target.parent for root in WRITE_ROOTS):
        raise ValueError("Only files directly under the project root or under tests/ may be written.")
    if target.suffix != ".py":
        raise ValueError("Only .py files may be written.")
    target.write_text(content, encoding="utf-8")
    return f"Updated {path}"


def run_tests() -> str:
    """Run pytest in the project and return the tail of its output."""
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return (r.stdout + r.stderr)[-4000:]


def tests_pass() -> bool:
    r = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=120)
    return r.returncode == 0


# ---- diff without git ---------------------------------------------------------

def snapshot() -> dict:
    """Remember the current content of the watched files."""
    out = {}
    for rel in WATCHED_FILES:
        p = PROJECT_ROOT / rel
        out[rel] = p.read_text(encoding="utf-8") if p.exists() else ""
    return out


def make_diff(before: dict) -> str:
    """Unified diff between a snapshot and the files as they are now."""
    chunks = []
    for rel, old in before.items():
        p = PROJECT_ROOT / rel
        new = p.read_text(encoding="utf-8") if p.exists() else ""
        if old == new:
            continue
        chunks.append("".join(difflib.unified_diff(
            old.splitlines(keepends=True), new.splitlines(keepends=True),
            fromfile=f"{rel} (before)", tofile=f"{rel} (after)")))
    return "\n".join(chunks) if chunks else "(no changes)"


TOOLS = {"read_file": read_file, "write_file": write_file, "run_tests": run_tests}
