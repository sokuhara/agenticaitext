"""起動確認。このテストは最初から通ります。

PART 5.6 の演習では、このファイルを一時的に壊して
make check が落ちることを確認します。
"""


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_index_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Vibe Order" in r.text
