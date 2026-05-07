from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    """検索リクエストパラメータ。"""

    # ---------------------------------------------
    # 既存 API 互換パラメータ
    # ---------------------------------------------
    q: str = ""
    bulk: bool | str = False
    prefecture_code: str | None = Field(default=None, alias="prefectureCode")
    pref_code: str | None = Field(default=None, alias="prefCode")
    corporate_number: str | None = Field(default=None, alias="corporateNumber")
    corporate_numbers: str | None = Field(default=None, alias="corporateNumbers")
    size: int | str | None = 10
    from_: int | str | None = Field(default=0, alias="from")
    match_mode: str | None = Field(default=None, alias="match_mode")
    match_mode_camel: str | None = Field(default=None, alias="matchMode")
    exact: bool | int | str | None = None

    # ---------------------------------------------
    # snake_case / alias 双方の受け付け
    # ---------------------------------------------
    model_config = ConfigDict(populate_by_name=True)


class SearchResponse(BaseModel):
    """検索レスポンスペイロード。"""

    total: int
    hits: list[dict[str, Any]]
    has_more: bool = False
