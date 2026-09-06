"""FastAPI アプリケーション。

PART 6 でここに注文のエンドポイントを実装します。
いまは起動確認用のヘルスチェックと、空の一覧画面だけがあります。
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from vibe_order.models import Health

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

app = FastAPI(title="Vibe Order")


@app.get("/api/health", response_model=Health)
async def health() -> Health:
    """起動確認用。"""
    return Health()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """注文一覧の画面。"""
    return TEMPLATES.TemplateResponse(request, "orders.html", {"orders": []})


# PART 6.3.2 でここに追加する:
#   GET  /api/orders
#   POST /api/orders
#   POST /api/orders/{id}/status
