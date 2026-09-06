"""MCPサーバに、Clineを使わずに接続して確かめる。

    python3 08_mcp_client.py

07_mcp_server.py を子プロセスとして起動し、
ツール一覧の取得と get_kitchen_board の呼び出しを行います。

これが通れば、サーバ側は正しく作れています。
Clineで見えない場合は、Cline側の設定の問題です。
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

SERVER = Path(__file__).parent / "07_mcp_server.py"


async def run() -> int:
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError as e:
        print("mcp が入っていません:", e)
        print("  uv add mcp")
        return 1

    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])

    print("サーバを起動して接続します:", SERVER.name)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("\n--- ツール一覧 ---")
            tools = await session.list_tools()
            for t in tools.tools:
                print(f"  {t.name}: {t.description}")
            names = [t.name for t in tools.tools]
            if "get_kitchen_board" not in names:
                print("  !! get_kitchen_board が公開されていません")
                return 1

            print("\n--- 呼び出し ---")
            result = await session.call_tool("get_kitchen_board", {})
            for c in result.content:
                print(getattr(c, "text", c)[:500])

    print("\n=> 接続と呼び出しに成功しました。")
    print("   次は data/kitchen_board.json を書き換えて、もう一度実行してください。")
    print("   返る内容が変われば、Agentは『いまの状況』を取りに行けています。")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
