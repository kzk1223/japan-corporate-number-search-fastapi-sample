from app.core.config import Settings
from app.schemas.search import SearchRequest
from app.services.search_query import build_search_body, prepare_search_request


def test_build_search_body_uses_match_all_without_keywords() -> None:
    """キーワード未指定時に match_all クエリを生成すること。"""
    body = build_search_body(
        keywords=[],
        pref_codes=[],
        corp_numbers=[],
        size=10,
        from_=0,
        is_exact_match=False,
        sort_config=[],
    )
    assert body["query"] == {"match_all": {}}
    assert body["size"] == 10
    assert body["from"] == 0


def test_build_search_body_uses_exact_terms_query() -> None:
    """完全一致検索時に正規化済み terms クエリを生成すること。"""
    body = build_search_body(
        keywords=["ＡＢＣ株式会社"],
        pref_codes=[],
        corp_numbers=[],
        size=10,
        from_=0,
        is_exact_match=True,
        sort_config=[],
    )
    assert body["query"] == {"terms": {"name.keyword_norm": ["abc株式会社"]}}


def test_build_search_body_adds_filters() -> None:
    """都道府県コードと法人番号フィルタを付与すること。"""
    body = build_search_body(
        keywords=[],
        pref_codes=["13"],
        corp_numbers=["1234567890123"],
        size=10,
        from_=0,
        is_exact_match=False,
        sort_config=[],
    )
    filters = body["query"]["bool"]["filter"]
    assert {"terms": {"prefectureCode.keyword": ["13"]}} in filters
    assert {"terms": {"corporateNumber.keyword": ["1234567890123"]}} in filters


def test_prepare_search_request_clamps_result_window() -> None:
    """from と size を OpenSearch result window 内へ丸めること。"""
    settings = Settings(max_size=1001, max_result_window=10000)
    prepared = prepare_search_request(
        SearchRequest(q="", size=5000, from_=9000),
        settings,
    )
    assert prepared.from_ == 9000
    assert prepared.size == 1000
    assert prepared.over_requested is True


def test_prepare_search_request_bulk_enables_exact_match() -> None:
    """bulk 検索時に完全一致検索を既定化すること。"""
    settings = Settings()
    prepared = prepare_search_request(
        SearchRequest(q="A,B", bulk="1"),
        settings,
    )
    assert prepared.keywords == ["A", "B"]
    assert prepared.is_bulk is True
    assert prepared.is_exact_match is True
