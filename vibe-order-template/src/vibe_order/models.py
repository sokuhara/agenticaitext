"""データ構造の定義。

PART 6 でここに MenuItem / Order / OrderStatus を実装します。
いまはヘルスチェック用の最小の型だけがあります。
"""

from pydantic import BaseModel


class Health(BaseModel):
    """ヘルスチェックの応答."""

    status: str = "ok"


# PART 6.3.1 でここに追加する:
#   class OrderStatus(StrEnum): ...
#   class MenuItem(BaseModel): ...
#   class Order(BaseModel): ...
