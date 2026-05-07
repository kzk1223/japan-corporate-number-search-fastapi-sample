from typing import Any

from app.core.config import Settings
from app.schemas.search import SearchRequest
from app.services.search_service import SearchService


class FakeOpenSearchClient:
    """検索サービステスト用 OpenSearch 代替クライアント。"""

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        """応答キューを持つ代替クライアント初期化。"""
        self.responses = responses
        self.requests: list[dict[str, Any]] = []

    def search(self, **kwargs: Any) -> dict[str, Any]:
        """キュー先頭の検索応答返却。"""
        self.requests.append(kwargs)
        return self.responses.pop(0)


def test_search_once_returns_total_and_hits() -> None:
    """通常検索が OpenSearch hits を返すこと。"""
    hit = {"_id": "1", "_source": {"name": "Sample"}}
    client = FakeOpenSearchClient(
        [{"hits": {"total": {"value": 1}, "hits": [hit]}}],
    )
    service = SearchService(client=client, settings=Settings(opensearch_index="company"))

    response = service.search(SearchRequest(q="Sample"))

    assert response.total == 1
    assert response.hits == [hit]
    assert response.has_more is False
    assert client.requests[0]["index"] == "company"


def test_bulk_search_keeps_only_unique_single_hit_results() -> None:
    """bulk 検索が一意ヒットのみ採用し ID 重複を排除すること。"""
    hit = {"_id": "1", "_source": {"name": "Sample"}}
    client = FakeOpenSearchClient(
        [
            {"hits": {"total": {"value": 1}, "hits": [hit]}},
            {"hits": {"total": {"value": 2}, "hits": [{"_id": "2"}, {"_id": "3"}]}},
            {"hits": {"total": {"value": 1}, "hits": [hit]}},
        ],
    )
    settings = Settings(
        opensearch_index="company",
        bulk_search_chunk_size=1,
        bulk_search_max_workers=1,
    )
    service = SearchService(client=client, settings=settings)

    response = service.search(SearchRequest(q="A,B,C", bulk=True))

    assert response.total == 1
    assert response.hits == [hit]
    assert response.has_more is False
    assert len(client.requests) == 3
