"""PART 7.1 の最小Agentを、単体で動かす。

    python3 04_agent_min.py [モデル名]

使い捨てのプロジェクトを /tmp に作り、そこで動かします。
教材のリポジトリは触りません。

確認すること:
  - ツール呼び出しのループが回るか
  - _safe_path がプロジェクト外を弾くか
  - Agentが落ちているテストを直せるか
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen3.8:27b"

BROKEN = '''def add(a: int, b: int) -> int:
    """2つの数を足す。"""
    return a - b        # BUG
'''

TEST = '''from calc import add


def test_add():
    assert add(2, 3) == 5
'''

MAKEFILE = """check:
\tpython3 -m pytest -q
"""

# ---------------------------------------------------------------- ツール

PROJECT_ROOT = Path(tempfile.mkdtemp(prefix="agent-min-")).resolve()
WRITE_ROOTS = [PROJECT_ROOT]


def _safe_path(path: str) -> Path:
    target = (PROJECT_ROOT / path).resolve()
    if PROJECT_ROOT not in target.parents and target != PROJECT_ROOT:
        raise ValueError("プロジェクト外のファイルは扱えません")
    return target


def read_file(path: str) -> str:
    return _safe_path(path).read_text(encoding="utf-8")[:4000]


def write_file(path: str, content: str) -> str:
    target = _safe_path(path)
    if not any(r == target.parent or r in target.parents for r in WRITE_ROOTS):
        raise ValueError("書き換えを許していない場所です")
    if target.suffix != ".py":
        raise ValueError(".py 以外は書き換えません")
    target.write_text(content, encoding="utf-8")
    return f"{path} を更新しました"


def run_tests() -> str:
    r = subprocess.run(
        ["python3", "-m", "pytest", "-q"],
        cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=120,
    )
    return (r.stdout + r.stderr)[-2000:]


TOOLS = {"read_file": read_file, "write_file": write_file, "run_tests": run_tests}

SCHEMA = [
    {"type": "function", "function": {
        "name": "read_file", "description": "プロジェクト内のファイルを読む",
        "parameters": {"type": "object",
                       "properties": {"path": {"type": "string"}},
                       "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "write_file", "description": "プロジェクト内の .py を書き換える",
        "parameters": {"type": "object",
                       "properties": {"path": {"type": "string"},
                                      "content": {"type": "string"}},
                       "required": ["path", "content"]}}},
    {"type": "function", "function": {
        "name": "run_tests", "description": "テストを実行して結果を返す",
        "parameters": {"type": "object", "properties": {}}}},
]


def agent(goal: str, max_steps: int = 12) -> str:
    import ollama

    messages = [{"role": "user", "content": goal}]
    for step in range(max_steps):
        reply = ollama.chat(model=MODEL, messages=messages, tools=SCHEMA)
        msg = dict(reply["message"])
        messages.append(msg)

        calls = msg.get("tool_calls") or []
        if not calls:
            return msg.get("content", "")

        for call in calls:
            fn = dict(dict(call)["function"])
            name, args = fn["name"], dict(fn["arguments"])
            print(f"  [{step}] {name}({args})")
            try:
                result = TOOLS[name](**args)
            except Exception as e:
                result = f"ERROR: {e}"
            messages.append({"role": "tool", "content": str(result)})
    return "打ち切りました（最大ステップ数に到達）"


def main() -> int:
    (PROJECT_ROOT / "calc.py").write_text(BROKEN, encoding="utf-8")
    (PROJECT_ROOT / "test_calc.py").write_text(TEST, encoding="utf-8")
    (PROJECT_ROOT / "Makefile").write_text(MAKEFILE, encoding="utf-8")
    print("作業ディレクトリ:", PROJECT_ROOT)

    print("\n=== 事前チェック: 安全策 ===")
    try:
        read_file("../../etc/passwd")
        print("  !! 失敗: プロジェクト外が読めてしまいました")
        return 1
    except ValueError:
        print("  OK  プロジェクト外は読めません")

    print("\n=== 事前チェック: テストは落ちているか ===")
    before = run_tests()
    print("  ", before.strip().splitlines()[-1] if before.strip() else "(出力なし)")

    print("\n=== Agent 実行 ===")
    out = agent("テストが落ちています。原因を調べて直し、テストを通してください。")
    print("\n--- Agentの最終出力 ---")
    print(out[:800])

    print("\n=== 事後チェック ===")
    after = run_tests()
    print("  ", after.strip().splitlines()[-1] if after.strip() else "(出力なし)")
    passed = "failed" not in after and "error" not in after.lower()
    print("\n=>", "テストが通りました" if passed else "まだ落ちています（モデルを大きくして再試行）")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
