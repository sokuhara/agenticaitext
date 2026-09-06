#!/usr/bin/env bash
#
# PART 7 用のブランチを作る。
# テストが1件だけ落ちる状態にして、Agentに直させる。
#
#   使い方:  ./scripts/make_challenge_branch.sh
#
set -euo pipefail

git switch -c agent-challenge 2>/dev/null || {
  echo "agent-challenge は既にあります。作り直す場合は git branch -D agent-challenge を実行してください。" >&2
  exit 1
}

mkdir -p src/vibe_order

cat > src/vibe_order/pricing.py <<'PY'
"""注文金額の計算。"""

from decimal import Decimal


def line_total(price: Decimal, quantity: int) -> Decimal:
    """1品目の小計を返す。"""
    # BUG: 数量を掛けていない
    return price


def order_total(lines: list[tuple[Decimal, int]]) -> Decimal:
    """注文全体の合計を返す。"""
    return sum((line_total(p, q) for p, q in lines), Decimal("0"))
PY

cat > tests/test_pricing.py <<'PY'
from decimal import Decimal

from vibe_order.pricing import line_total, order_total


def test_line_total_multiplies_quantity():
    assert line_total(Decimal("800"), 3) == Decimal("2400")


def test_order_total_sums_lines():
    lines = [(Decimal("800"), 2), (Decimal("500"), 1)]
    assert order_total(lines) == Decimal("2100")
PY

git add -A
git commit -m "chore: add failing pricing test for PART 7"

echo "==> agent-challenge ブランチを作りました"
echo "==> make check を実行すると、テストが2件落ちます"
echo "==> どのテストが落ちているかは読まずに、Agentに調べさせてください"
