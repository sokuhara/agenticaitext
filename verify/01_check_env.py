"""環境チェック。何が入っていて、何が足りないかを一覧にする。

    python3 01_check_env.py

ネットワークもモデルも不要。これだけは必ず最初に実行してください。
"""

from __future__ import annotations

import importlib.util
import platform
import shutil
import subprocess
import sys

COMMANDS = ["uv", "git", "make", "ollama", "ffmpeg", "ffprobe", "gh"]
MODULES = [
    ("fastapi", "PART 5-6 のアプリ"),
    ("pydantic", "PART 6 のデータ定義"),
    ("jinja2", "PART 6 の画面"),
    ("httpx", "PART 6 のAPIテスト"),
    ("pytest", "make check"),
    ("ruff", "make check"),
    ("ollama", "PART 7.1"),
    ("langchain", "PART 7.2"),
    ("langchain_ollama", "PART 7.2"),
    ("langgraph", "PART 7.3-7.4 / PART 8"),
    ("mcp", "PART 7.5"),
    ("PIL", "PART 8 のスライド生成"),
]


def main() -> int:
    print(f"Python {platform.python_version()}  ({sys.executable})")
    if sys.version_info < (3, 12):
        print("  !! Python 3.12 以上が必要です")

    print("\n--- コマンド ---")
    for c in COMMANDS:
        path = shutil.which(c)
        mark = "OK " if path else "なし"
        ver = ""
        if path:
            try:
                r = subprocess.run([c, "--version"], capture_output=True, text=True, timeout=10)
                ver = (r.stdout or r.stderr).strip().splitlines()[0][:50]
            except Exception:
                ver = ""
        print(f"  {mark} {c:<8} {ver}")

    print("\n--- Pythonパッケージ ---")
    missing = []
    for mod, why in MODULES:
        found = importlib.util.find_spec(mod) is not None
        print(f"  {'OK ' if found else 'なし'} {mod:<18} {why}")
        if not found:
            missing.append(mod)

    print("\n--- まとめ ---")
    if missing:
        print("  足りないもの:", ", ".join(missing))
        print("  テンプレートの依存は `make install` で入ります。")
        print("  PART 7 は  uv add ollama langchain langchain-ollama langgraph mcp")
    else:
        print("  すべて揃っています。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
