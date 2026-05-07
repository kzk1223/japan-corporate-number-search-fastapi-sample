from opensearchpy import OpenSearch

from app.core.config import Settings


# ---------------------------------------------
# OpenSearch クライアント生成
# ---------------------------------------------
def create_opensearch_client(settings: Settings) -> OpenSearch:
    """アプリケーション設定に基づく OpenSearch クライアント生成。"""
    http_auth = None
    if settings.opensearch_user and settings.opensearch_password:
        http_auth = (settings.opensearch_user, settings.opensearch_password)

    # ---------------------------------------------
    # 認証なしローカル構成を初期値とする接続設定
    # ---------------------------------------------
    return OpenSearch(
        hosts=[settings.opensearch_url],
        http_auth=http_auth,
        verify_certs=settings.opensearch_verify_certs,
        timeout=settings.request_timeout,
    )
