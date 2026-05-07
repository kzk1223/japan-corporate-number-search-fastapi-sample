from concurrent.futures import ThreadPoolExecutor
from typing import Any

from opensearchpy import OpenSearch
from opensearchpy.exceptions import OpenSearchException

from app.core.config import Settings
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_query import (
    PreparedSearchRequest,
    build_search_body,
    prepare_search_request,
)


class SearchServiceError(RuntimeError):
    """検索サービス実行エラー。"""


class SearchService:
    """OpenSearch を利用する検索サービス。"""

    def __init__(self, client: OpenSearch, settings: Settings) -> None:
        """検索サービス初期化。"""
        self.client = client
        self.settings = settings

    def search(self, request: SearchRequest) -> SearchResponse:
        """法人検索の実行。"""
        prepared_request = prepare_search_request(request, self.settings)
        try:
            # ---------------------------------------------
            # bulk 検索と通常検索の分岐
            # ---------------------------------------------
            if prepared_request.is_bulk and prepared_request.keywords:
                return self._search_bulk(prepared_request)
            return self._search_once(prepared_request)
        except OpenSearchException as exc:
            raise SearchServiceError(str(exc)) from exc

    def _search_once(self, prepared_request: PreparedSearchRequest) -> SearchResponse:
        """単発 OpenSearch 検索の実行。"""
        # ---------------------------------------------
        # 検索 body 生成
        # ---------------------------------------------
        body = build_search_body(
            keywords=prepared_request.keywords,
            pref_codes=prepared_request.pref_codes,
            corp_numbers=prepared_request.corp_numbers,
            size=prepared_request.size,
            from_=prepared_request.from_,
            is_exact_match=prepared_request.is_exact_match,
            sort_config=prepared_request.sort_config,
        )

        # ---------------------------------------------
        # OpenSearch 検索実行
        # ---------------------------------------------
        result = self.client.search(
            index=self.settings.opensearch_index,
            body=body,
            request_timeout=self.settings.request_timeout,
        )
        hits_info = result.get("hits", {})
        hits = hits_info.get("hits", [])
        total = self._extract_total(hits_info.get("total", {}))

        has_more = False
        # ---------------------------------------------
        # 上限超過時の継続有無判定
        # ---------------------------------------------
        if prepared_request.over_requested:
            has_more = len(hits) == self.settings.max_size or total > (
                prepared_request.from_ + prepared_request.size
            )

        return SearchResponse(total=total, hits=hits, has_more=has_more)

    def _search_bulk(self, prepared_request: PreparedSearchRequest) -> SearchResponse:
        """複数キーワード検索の実行。"""
        # ---------------------------------------------
        # キーワードチャンク生成
        # ---------------------------------------------
        chunk_size = max(1, self.settings.bulk_search_chunk_size)
        keyword_chunks = [
            prepared_request.keywords[index : index + chunk_size]
            for index in range(0, len(prepared_request.keywords), chunk_size)
        ]
        per_chunk_limit = min(
            self.settings.bulk_search_max_size,
            self.settings.max_result_window,
        )

        def execute_chunk(chunk_keywords: list[str]) -> dict[str, Any]:
            """キーワードチャンク単位の検索実行。"""
            body = build_search_body(
                keywords=chunk_keywords,
                pref_codes=prepared_request.pref_codes,
                corp_numbers=prepared_request.corp_numbers,
                size=per_chunk_limit,
                from_=0,
                is_exact_match=prepared_request.is_exact_match,
                sort_config=prepared_request.sort_config,
            )
            result = self.client.search(
                index=self.settings.opensearch_index,
                body=body,
                request_timeout=self.settings.request_timeout,
            )
            return result.get("hits", {})

        # ---------------------------------------------
        # チャンク並列検索
        # ---------------------------------------------
        all_hits: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=self.settings.bulk_search_max_workers) as executor:
            futures = [executor.submit(execute_chunk, chunk) for chunk in keyword_chunks]
            for future in futures:
                hits_info = future.result()
                hits_list = hits_info.get("hits", [])
                total = self._extract_total(hits_info.get("total", {}))
                if total == 1:
                    all_hits.extend(hits_list)

        # ---------------------------------------------
        # 重複排除とページング
        # ---------------------------------------------
        unique_hits = self._unique_hits_by_id(all_hits)
        total_hits = len(unique_hits)
        start = min(prepared_request.from_, total_hits)
        if prepared_request.size > 0:
            end = min(prepared_request.from_ + prepared_request.size, total_hits)
        else:
            end = total_hits

        final_hits = unique_hits[start:end]
        has_more = prepared_request.over_requested or end < total_hits
        return SearchResponse(total=total_hits, hits=final_hits, has_more=has_more)

    @staticmethod
    def _extract_total(total_info: Any) -> int:
        """OpenSearch total 値の抽出。"""
        if isinstance(total_info, dict):
            return int(total_info.get("value", 0) or 0)
        return int(total_info or 0)

    @staticmethod
    def _unique_hits_by_id(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """OpenSearch document id による検索結果重複排除。"""
        seen_ids: set[str] = set()
        unique_hits: list[dict[str, Any]] = []
        for hit in hits:
            doc_id = hit.get("_id")
            if doc_id is not None:
                if doc_id in seen_ids:
                    continue
                seen_ids.add(doc_id)
            unique_hits.append(hit)
        return unique_hits
