from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from opensearchpy import OpenSearch

from .clients.opensearch import create_opensearch_client
from .core.config import Settings
from .services.search_service import SearchService


# ---------------------------------------------
# 設定依存
# ---------------------------------------------
@lru_cache
def get_settings() -> Settings:
    """アプリケーション設定のキャッシュ取得。"""
    return Settings()


# ---------------------------------------------
# OpenSearch クライアント依存
# ---------------------------------------------
@lru_cache
def get_opensearch_client_cached() -> OpenSearch:
    """OpenSearch クライアントのキャッシュ取得。"""
    return create_opensearch_client(get_settings())


def get_opensearch_client() -> OpenSearch:
    """OpenSearch クライアント依存の取得。"""
    return get_opensearch_client_cached()


# ---------------------------------------------
# サービス依存
# ---------------------------------------------
def get_search_service(
    client: Annotated[OpenSearch, Depends(get_opensearch_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SearchService:
    """検索サービス依存の取得。"""
    return SearchService(client=client, settings=settings)
