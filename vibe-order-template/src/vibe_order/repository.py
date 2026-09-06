"""メモリ上の簡単なリポジトリ。

データベースは使いません。アプリの起動中だけデータが残ります。
再起動すれば消えます。保存先の選択はこの教材の主題ではありません。
"""

from typing import Any


class MemoryRepository:
    """辞書1つだけの最小のリポジトリ."""

    def __init__(self) -> None:
        self._items: dict[int, Any] = {}
        self._next_id = 1

    def add(self, item: Any) -> int:
        item_id = self._next_id
        self._items[item_id] = item
        self._next_id += 1
        return item_id

    def get(self, item_id: int) -> Any | None:
        return self._items.get(item_id)

    def all(self) -> list[Any]:
        return list(self._items.values())

    def clear(self) -> None:
        self._items.clear()
        self._next_id = 1


orders = MemoryRepository()
menu = MemoryRepository()
