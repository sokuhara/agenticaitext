"""ollama.chat の応答がどんな形で返るかを確かめる。

    python3 03_ollama_shape.py

PART 7.1 で唯一、ライブラリのバージョン差で壊れうる箇所です。
教材のコードは dict() で包んで揃えていますが、それが効くかをここで見ます。

必要なもの: ollama が動いていること、モデルが1つ入っていること
"""

from __future__ import annotations

import json
import sys

MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen3.8:27b"

SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "ファイルを読む",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    }
]


def main() -> int:
    try:
        import ollama
    except ImportError:
        print("ollama が入っていません:  uv add ollama")
        return 1

    print(f"model = {MODEL}")
    reply = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": "README.md を読んでください"}],
        tools=SCHEMA,
    )

    print("\n--- 生の応答の型 ---")
    print(type(reply))

    print("\n--- reply['message'] ---")
    msg = reply["message"]
    print(type(msg))

    print("\n--- 教材と同じ扱いができるか ---")
    ok = True
    try:
        d = dict(msg)
        print("  dict(msg)            : OK  keys =", list(d)[:6])
    except Exception as e:
        print("  dict(msg)            : 失敗", e)
        ok = False
        d = {}

    calls = d.get("tool_calls") or []
    print(f"  tool_calls           : {len(calls)} 件")

    if calls:
        try:
            fn = dict(dict(calls[0])["function"])
            print("  function name        :", fn["name"])
            print("  function arguments   :", dict(fn["arguments"]))
        except Exception as e:
            print("  function の取り出し  : 失敗", e)
            ok = False
    else:
        print("  !! ツール呼び出しが返りませんでした。")
        print("     モデルが tools に対応していない可能性があります。")
        print("     ollama のライブラリ一覧で tools 対応を確認してください。")
        ok = False

    print("\n--- 応答全体（先頭のみ） ---")
    try:
        print(json.dumps(dict(reply), ensure_ascii=False, default=str)[:600])
    except Exception:
        print(str(reply)[:600])

    print("\n=>", "教材のコードはそのまま動きます" if ok else "教材のコードに手直しが要ります")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
