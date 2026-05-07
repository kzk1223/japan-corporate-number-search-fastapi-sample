from fastapi import FastAPI

from .routers import health, search


# ---------------------------------------------
# FastAPI アプリケーション生成
# ---------------------------------------------
def create_app() -> FastAPI:
    """FastAPI アプリケーションインスタンス生成。"""
    app = FastAPI(
        title="Corporation Number Search API",
        version="0.1.0",
    )

    # ---------------------------------------------
    # ルーター登録
    # ---------------------------------------------
    app.include_router(health.router)
    app.include_router(search.router)
    return app


# ---------------------------------------------
# ASGI エントリポイント
# ---------------------------------------------
app = create_app()
