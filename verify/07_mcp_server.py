"""PART 7.5 の厨房ボードMCPサーバ。教材と同じものです。

単体では起動確認だけできます。

    python3 07_mcp_server.py --selftest    データが読めるかだけ見る
    python3 07_mcp_server.py               MCPサーバとして起動（stdio）

Clineから使う場合の設定:

    {"mcpServers": {"kitchen-board": {
        "command": "python3",
        "args": ["<このファイルの絶対パス>"]}}}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data" / "kitchen_board.json"


def load_board() -> list[dict]:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def selftest() -> int:
    print("データファイル:", DATA_PATH)
    if not DATA_PATH.exists():
        print("  !! ありません")
        return 1
    board = load_board()
    print(f"  {len(board)} 件読めました")
    for o in board:
        alert = " [アレルギー警告]" if o["allergy_alert"] else ""
        print(f"   #{o['order_id']} {o['item']:<18} {o['status']:<8} "
              f"{o['wait_minutes']}分{alert}")
    print("\n=> データは読めます。次は 08_mcp_client.py で接続を確認してください。")
    return 0


if "--selftest" in sys.argv:
    raise SystemExit(selftest())

from mcp.server.fastmcp import FastMCP  # noqa: E402

mcp = FastMCP("Kitchen Board")


@mcp.tool()
def get_kitchen_board() -> list[dict]:
    """現在の厨房ボードを取得する。注文の優先順位を判断するときだけ使う。"""
    return load_board()


if __name__ == "__main__":
    mcp.run(transport="stdio")
