import pytest
from fastapi.testclient import TestClient

from vibe_order.app import app
from vibe_order.repository import menu, orders


@pytest.fixture(autouse=True)
def _clean_repositories():
    """各テストの前後で、メモリ上のデータを空にする."""
    orders.clear()
    menu.clear()
    yield
    orders.clear()
    menu.clear()


@pytest.fixture
def client():
    """サーバを起動せずにAPIを呼ぶクライアント（中身は httpx）."""
    with TestClient(app) as c:
        yield c
