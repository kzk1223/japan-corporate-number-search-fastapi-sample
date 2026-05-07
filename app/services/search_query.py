import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings
from app.schemas.search import SearchRequest


@dataclass(frozen=True)
class PreparedSearchRequest:
    """正規化済み検索リクエスト値。"""

    keywords: list[str]
    pref_codes: list[str]
    corp_numbers: list[str]
    size: int
    from_: int
    is_bulk: bool
    is_exact_match: bool
    over_requested: bool
    sort_config: list[dict[str, Any]]


# ---------------------------------------------
# 入力値正規化
# ---------------------------------------------
def normalize_string(value: str) -> str:
    """NFKC によるユーザー入力正規化。"""
    return unicodedata.normalize("NFKC", value) if value else ""


def parse_bool(value: bool | str | None) -> bool:
    """既存 API 互換の真偽値解析。"""
    if isinstance(value, bool):
        return value
    return str(value or "").lower() in ("1", "true", "yes", "on")


def parse_int(value: int | str | None, default: int) -> int:
    """フォールバック付き整数値解析。"""
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def parse_list_param(
    value: str | None,
    validator: Callable[[str], bool],
) -> list[str]:
    """カンマ・空白区切りリストパラメータ解析。"""
    if not value:
        return []

    normalized_value = normalize_string(value)
    tokens: list[str] = []
    for token_group in normalized_value.replace("、", ",").replace("　", " ").split(","):
        tokens.extend(token_group.strip().split())

    return [token for token in tokens if validator(token)]


def is_valid_corporate_number(value: str) -> bool:
    """法人番号として有効な値かの判定。"""
    return value.isdigit() and len(value) == 13


def is_valid_prefecture_code(value: str) -> bool:
    """都道府県コードとして有効な値かの判定。"""
    return len(value) == 2 and value.isdigit() and "01" <= value <= "47"


def escape_wildcard(value: str) -> str:
    """OpenSearch wildcard 特殊文字のエスケープ。"""
    if not value:
        return ""
    return value.replace("\\", "\\\\").replace("*", "\\*").replace("?", "\\?")


# ---------------------------------------------
# ソート設定
# ---------------------------------------------
def build_sort_config() -> list[dict[str, Any]]:
    """既存 API 互換の標準ソート設定生成。"""
    return [
        {
            "furigana.keyword": {
                "order": "asc",
                "missing": "_last",
                "unmapped_type": "keyword",
            }
        },
        {
            "name.keyword": {
                "order": "asc",
                "missing": "_last",
                "unmapped_type": "keyword",
            }
        },
        {
            "prefectureCode.keyword": {
                "order": "asc",
                "missing": "_last",
                "unmapped_type": "keyword",
            }
        },
        {
            "cityCode.keyword": {
                "order": "asc",
                "missing": "_last",
                "unmapped_type": "keyword",
            }
        },
    ]


def prepare_search_request(
    request: SearchRequest,
    settings: Settings,
) -> PreparedSearchRequest:
    """検索実行用リクエストパラメータ正規化。"""
    # ---------------------------------------------
    # 検索モード判定
    # ---------------------------------------------
    is_bulk = parse_bool(request.bulk)
    keywords = [keyword.strip() for keyword in (request.q or "").split(",") if keyword.strip()]
    req_size = parse_int(request.size, 10)
    req_from = max(0, parse_int(request.from_, 0))
    match_mode = (request.match_mode or request.match_mode_camel or "").lower()
    is_exact_match = match_mode in ("exact", "eq") or str(request.exact) == "1" or is_bulk

    size = max(0, req_size)
    from_ = req_from
    over_requested = False

    # ---------------------------------------------
    # OpenSearch 結果ウィンドウ制限
    # ---------------------------------------------
    if size > settings.max_size:
        size = settings.max_size
        over_requested = True

    if from_ + size > settings.max_result_window:
        over_requested = True
        from_ = max(0, min(req_from, settings.max_result_window - 1))
        size = max(0, min(size, settings.max_result_window - from_))

    # ---------------------------------------------
    # フィルタ条件解析
    # ---------------------------------------------
    pref_codes = parse_list_param(
        request.prefecture_code or request.pref_code,
        is_valid_prefecture_code,
    )
    corp_numbers = parse_list_param(
        request.corporate_number or request.corporate_numbers,
        is_valid_corporate_number,
    )

    if corp_numbers and not keywords and not pref_codes and req_size == 10:
        size = max(size, len(corp_numbers))

    return PreparedSearchRequest(
        keywords=keywords,
        pref_codes=pref_codes,
        corp_numbers=corp_numbers,
        size=size,
        from_=from_,
        is_bulk=is_bulk,
        is_exact_match=is_exact_match,
        over_requested=over_requested,
        sort_config=build_sort_config(),
    )


def build_search_body(
    keywords: list[str],
    pref_codes: list[str],
    corp_numbers: list[str],
    size: int,
    from_: int = 0,
    is_exact_match: bool = False,
    sort_config: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """正規化済み値からの OpenSearch 検索 body 生成。"""
    # ---------------------------------------------
    # クエリ本体
    # ---------------------------------------------
    if not keywords:
        query: dict[str, Any] = {"match_all": {}}
    else:
        clean_keywords = [keyword.strip() for keyword in keywords if keyword.strip()]
        if not clean_keywords:
            query = {"match_none": {}}
        elif is_exact_match:
            normalized_keywords = [normalize_string(keyword).lower() for keyword in clean_keywords]
            query = {"terms": {"name.keyword_norm": normalized_keywords}}
        else:
            should_clauses: list[dict[str, Any]] = []
            for keyword in clean_keywords:
                normalized_keyword = normalize_string(keyword).lower()
                escaped_normalized = escape_wildcard(normalized_keyword)
                escaped_raw = escape_wildcard(keyword)

                should_clauses.append(
                    {
                        "wildcard": {
                            "name.keyword_norm": {
                                "value": f"*{escaped_normalized}*",
                                "rewrite": "constant_score",
                                "boost": 3.0,
                            }
                        }
                    }
                )
                should_clauses.append(
                    {
                        "wildcard": {
                            "name.keyword": {
                                "value": f"*{escaped_raw}*",
                                "rewrite": "constant_score",
                                "boost": 0.5,
                            }
                        }
                    }
                )

            query = {
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": 1,
                }
            }

    # ---------------------------------------------
    # フィルタ条件
    # ---------------------------------------------
    filters: list[dict[str, Any]] = []
    if pref_codes:
        filters.append({"terms": {"prefectureCode.keyword": pref_codes}})
    if corp_numbers:
        filters.append({"terms": {"corporateNumber.keyword": corp_numbers}})

    if filters:
        if "bool" not in query:
            if "match_all" in query:
                query = {"bool": {}}
            else:
                query = {"bool": {"must": query}}
        query["bool"].setdefault("filter", []).extend(filters)

    # ---------------------------------------------
    # 最終リクエスト body
    # ---------------------------------------------
    body: dict[str, Any] = {
        "query": query,
        "size": size,
        "from": from_,
        "track_total_hits": True,
    }

    if sort_config:
        body["sort"] = sort_config

    return body
