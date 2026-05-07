from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """環境変数から読み込むアプリケーション設定。"""

    # ---------------------------------------------
    # アプリケーション設定
    # ---------------------------------------------
    app_name: str = "Corporation Number Search API"

    # ---------------------------------------------
    # OpenSearch 接続設定
    # ---------------------------------------------
    opensearch_url: str = "http://localhost:9200"
    opensearch_index: str = "company"
    opensearch_user: str | None = None
    opensearch_password: str | None = None
    opensearch_verify_certs: bool = False

    # ---------------------------------------------
    # 検索制御設定
    # ---------------------------------------------
    max_size: int = 1001
    max_result_window: int = 10000
    bulk_search_max_size: int = 1
    bulk_search_chunk_size: int = 1
    bulk_search_max_workers: int = 8
    request_timeout: int = 60

    # ---------------------------------------------
    # 設定読み込み
    # ---------------------------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
