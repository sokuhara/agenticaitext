"""データ構造のテスト。

PART 6.3.1 で、ここに受け入れ条件を書きます。

  - 12番テーブルに1件      -> 通る
  - 0番 / 100番テーブル    -> 落ちる
  - 価格が0                -> 落ちる
  - 商品名が空             -> 落ちる
  - 品目がゼロ             -> 落ちる
"""

from vibe_order.models import Health


def test_health_default():
    assert Health().status == "ok"


# PART 6.3.1 でここに追加する
