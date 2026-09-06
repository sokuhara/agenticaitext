"""PART 7.2 が、いま入っているLangChainで動くかを確かめる。

    python3 05_langchain_agent.py [モデル名]

LangChain の Agent API は名前が変わり続けている部分です。
このスクリプトは、使える書き方を自動で探して報告します。
"""

from __future__ import annotations

import sys

MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen3.8:27b"


def find_agent_factory():
    """使える Agent 生成関数を探す。見つかった名前を返す。"""
    candidates = [
        ("langchain.agents", "create_agent"),
        ("langgraph.prebuilt", "create_react_agent"),
        ("langchain.agents", "create_tool_calling_agent"),
    ]
    for module, name in candidates:
        try:
            mod = __import__(module, fromlist=[name])
            fn = getattr(mod, name)
            return module, name, fn
        except (ImportError, AttributeError):
            continue
    return None, None, None


def main() -> int:
    try:
        from langchain_core.tools import tool
        from langchain_ollama import ChatOllama
    except ImportError as e:
        print("必要なパッケージがありません:", e)
        print("  uv add langchain langchain-ollama langgraph")
        return 1

    print("--- Agent生成関数を探す ---")
    module, name, factory = find_agent_factory()
    if factory is None:
        print("  見つかりませんでした。")
        print("  使用中のLangChainのドキュメントで、現在の関数名を確認してください。")
        return 1
    print(f"  使えるのは: from {module} import {name}")

    @tool
    def add_numbers(a: int, b: int) -> int:
        """2つの整数を足して返す。計算が必要なときに使う。"""
        return a + b

    llm = ChatOllama(model=MODEL)

    print("\n--- bind_tools だけの場合（ループは回らない） ---")
    bound = llm.bind_tools([add_numbers])
    r = bound.invoke("17 と 25 を足して")
    print("  tool_calls:", getattr(r, "tool_calls", None))
    print("  content   :", (r.content or "(空)")[:120])
    print("  => ツール呼び出しの『提案』までは出るが、実行はされない")

    print(f"\n--- {name} を使う場合（ループが回る） ---")
    try:
        if name == "create_react_agent":
            agent = factory(llm, [add_numbers])
        else:
            agent = factory(model=llm, tools=[add_numbers])
        out = agent.invoke({"messages": [("user", "17 と 25 を足して、結果だけ答えて")]})
        last = out["messages"][-1]
        print("  最終出力:", getattr(last, "content", last))
        ok = "42" in str(getattr(last, "content", last))
        print("\n=>", "42 が返りました。教材の7.2はこの書き方で動きます"
              if ok else "42 が返りませんでした。モデルのtools対応を確認してください")
        return 0 if ok else 1
    except TypeError as e:
        print("  引数が合いません:", e)
        print("  この関数のシグネチャを確認して、教材のコードを合わせてください。")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
