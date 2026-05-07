from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_search_service
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import SearchService, SearchServiceError


# ---------------------------------------------
# 検索ルーター
# ---------------------------------------------
router = APIRouter(tags=["search"])


# ---------------------------------------------
# GET 検索エンドポイント
# ---------------------------------------------
@router.get("/search", response_model=SearchResponse)
def search_get(
    service: Annotated[SearchService, Depends(get_search_service)],
    q: str = "",
    bulk: bool | str = False,
    prefecture_code: Annotated[str | None, Query(alias="prefectureCode")] = None,
    pref_code: Annotated[str | None, Query(alias="prefCode")] = None,
    corporate_number: Annotated[str | None, Query(alias="corporateNumber")] = None,
    corporate_numbers: Annotated[str | None, Query(alias="corporateNumbers")] = None,
    size: int | str | None = 10,
    from_: Annotated[int | str | None, Query(alias="from")] = 0,
    match_mode: Annotated[str | None, Query(alias="match_mode")] = None,
    match_mode_camel: Annotated[str | None, Query(alias="matchMode")] = None,
    exact: bool | int | str | None = None,
) -> SearchResponse:
    """クエリパラメータによる法人検索。"""
    # ---------------------------------------------
    # 既存互換パラメータのリクエストモデル化
    # ---------------------------------------------
    request = SearchRequest(
        q=q,
        bulk=bulk,
        prefecture_code=prefecture_code,
        pref_code=pref_code,
        corporate_number=corporate_number,
        corporate_numbers=corporate_numbers,
        size=size,
        from_=from_,
        match_mode=match_mode,
        match_mode_camel=match_mode_camel,
        exact=exact,
    )

    # ---------------------------------------------
    # 検索実行
    # ---------------------------------------------
    try:
        return service.search(request)
    except SearchServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


# ---------------------------------------------
# POST 検索エンドポイント
# ---------------------------------------------
@router.post("/search", response_model=SearchResponse)
def search_post(
    request: SearchRequest,
    service: Annotated[SearchService, Depends(get_search_service)],
) -> SearchResponse:
    """JSON body による法人検索。"""
    try:
        return service.search(request)
    except SearchServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
