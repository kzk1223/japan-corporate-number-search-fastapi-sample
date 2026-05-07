from fastapi import APIRouter


# ---------------------------------------------
# ヘルスチェックルーター
# ---------------------------------------------
router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """アプリケーション稼働状態の返却。"""
    return {"status": "ok"}
