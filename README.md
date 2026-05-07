# Corporation Number Search API

FastAPI と OpenSearch 2.x を利用した法人番号検索 API サンプルです。

国税庁法人番号公表サイトで提供されている基本3情報ダウンロード CSV を OpenSearch に投入し、法人名、法人番号、都道府県コードで検索する構成を想定しています。

## Features

- `GET /search` / `POST /search` による検索 API
- 法人名による部分一致検索
- 法人名の完全一致寄り検索
- 法人番号による絞り込み
- 都道府県コードによる絞り込み
- 複数キーワードを扱う bulk 検索
- OpenSearch alias `company` 経由の検索
- OpenSearch 2.x ローカル実行用 Docker Compose
- index / alias 初期化用 `tools/create_index.py`

## Requirements

- Python 3.12+
- Docker
- Docker Compose
- OpenSearch 2.x

## Data Source

検索対象データは、国税庁法人番号公表サイトの「基本3情報ダウンロード」で提供される CSV を想定しています。

- [基本3情報ダウンロード](https://www.houjin-bangou.nta.go.jp/download/)
- [全件データのダウンロード](https://www.houjin-bangou.nta.go.jp/download/zenken/)
- [法人番号システム Web-API](https://www.houjin-bangou.nta.go.jp/webapi/index.html)

全件データは CSV / XML 形式で提供され、CSV は Shift-JIS 版と Unicode 版があります。ファイルは ZIP 形式で提供され、全国分または都道府県・国外単位で取得できます。

法人番号システム Web-API も提供されていますが、全件データの取得には対応していません。初期投入データには、基本3情報ダウンロードの CSV を利用する前提です。

## CSV Format

投入対象 CSV は、国税庁法人番号公表サイトのリソース定義に基づく以下の列順を想定します。

| No | Field | Description |
|---:|---|---|
| 1 | `sequenceNumber` | 一連番号 |
| 2 | `corporateNumber` | 法人番号 |
| 3 | `process` | 処理区分 |
| 4 | `correct` | 訂正区分 |
| 5 | `updateDate` | 更新年月日 |
| 6 | `changeDate` | 変更年月日 |
| 7 | `name` | 商号又は名称 |
| 8 | `nameImageId` | 商号又は名称イメージID |
| 9 | `kind` | 法人種別 |
| 10 | `prefectureName` | 国内所在地都道府県 |
| 11 | `cityName` | 国内所在地市区町村 |
| 12 | `streetNumber` | 国内所在地丁目番地等 |
| 13 | `addressImageId` | 国内所在地イメージID |
| 14 | `prefectureCode` | 都道府県コード |
| 15 | `cityCode` | 市区町村コード |
| 16 | `postCode` | 郵便番号 |
| 17 | `addressOutside` | 国外所在地 |
| 18 | `addressOutsideImageId` | 国外所在地イメージID |
| 19 | `closeDate` | 登記記録の閉鎖等年月日 |
| 20 | `closeCause` | 登記記録の閉鎖等の事由 |
| 21 | `successorCorporateNumber` | 承継先法人番号 |
| 22 | `changeCause` | 変更事由の詳細 |
| 23 | `assignmentDate` | 法人番号指定年月日 |
| 24 | `latest` | 最新履歴 |
| 25 | `enName` | 商号又は名称英語表記 |
| 26 | `enPrefectureName` | 国内所在地都道府県英語表記 |
| 27 | `enCityName` | 国内所在地市区町村英語表記 |
| 28 | `enAddressOutside` | 国外所在地英語表記 |
| 29 | `furigana` | フリガナ |
| 30 | `hihyoji` | 検索対象除外 |

## Setup

```bash
docker compose up -d
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m tools.create_index --index company_v1 --alias company
```

macOS / Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m tools.create_index --index company_v1 --alias company
```

## Environment Variables

```env
OPENSEARCH_URL=http://localhost:9200
OPENSEARCH_INDEX=company
OPENSEARCH_USER=
OPENSEARCH_PASSWORD=
OPENSEARCH_VERIFY_CERTS=false
```

`OPENSEARCH_INDEX` は検索対象の alias を指定します。標準では `company` を使用します。

## OpenSearch Index

このサンプルでは、`name.keyword_norm` に `lowercase` normalizer を適用します。ICU plugin は必須にしません。

文字列フィールドは既存 API 互換のため、`.keyword` subfield を持つ形を基本とします。

最小 mapping 例。

```json
{
  "settings": {
    "analysis": {
      "normalizer": {
        "lowercase_norm": {
          "type": "custom",
          "filter": ["lowercase"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "corporateNumber": {
        "type": "text",
        "fields": {
          "keyword": { "type": "keyword", "ignore_above": 256 }
        }
      },
      "name": {
        "type": "text",
        "fields": {
          "keyword": { "type": "keyword", "ignore_above": 256 },
          "keyword_norm": {
            "type": "keyword",
            "normalizer": "lowercase_norm",
            "doc_values": false,
            "ignore_above": 256
          }
        }
      },
      "furigana": {
        "type": "text",
        "fields": {
          "keyword": { "type": "keyword", "ignore_above": 256 }
        }
      },
      "prefectureCode": {
        "type": "text",
        "fields": {
          "keyword": { "type": "keyword", "ignore_above": 256 }
        }
      },
      "cityCode": {
        "type": "text",
        "fields": {
          "keyword": { "type": "keyword", "ignore_above": 256 }
        }
      }
    }
  }
}
```

index / alias は以下のコマンドで作成します。

```bash
python -m tools.create_index --index company_v1 --alias company
```

## Sample Data Import

サンプル CSV は別途用意します。

最小動作確認では、以下のような NDJSON を OpenSearch Bulk API で投入できます。

```json
{"index":{"_index":"company_v1","_id":"1234567890123"}}
{"corporateNumber":"1234567890123","name":"サンプル株式会社","prefectureCode":"13","cityCode":"13101","furigana":"サンプル","latest":"1"}
```

```bash
curl -X POST "http://localhost:9200/_bulk" -H "Content-Type: application/x-ndjson" --data-binary "@sample-data/sample.ndjson"
```

投入後に refresh します。

```bash
curl -X POST "http://localhost:9200/company_v1/_refresh"
```

## Run

```bash
uvicorn app.main:app --reload
```

API は標準で以下に起動します。

```text
http://127.0.0.1:8000
```

## API

### Health Check

```http
GET /health
```

### Search

```http
GET /search?q=サンプル株式会社&size=10
```

主な query parameter。

| Parameter | Description |
|---|---|
| `q` | 検索キーワード。カンマ区切りで複数指定可能 |
| `bulk` | `true` / `1` の場合、複数キーワードを個別検索 |
| `prefectureCode` | 都道府県コード |
| `prefCode` | `prefectureCode` の別名 |
| `corporateNumber` | 法人番号 |
| `corporateNumbers` | 複数法人番号 |
| `size` | 取得件数 |
| `from` | 取得開始位置 |
| `match_mode` | `exact` / `eq` の場合、完全一致寄り検索 |
| `matchMode` | `match_mode` の別名 |
| `exact` | `1` の場合、完全一致寄り検索 |

レスポンス例。

```json
{
  "total": 1,
  "hits": [
    {
      "_id": "1234567890123",
      "_source": {
        "corporateNumber": "1234567890123",
        "name": "サンプル株式会社",
        "prefectureCode": "13"
      }
    }
  ],
  "has_more": false
}
```

### POST Search

```http
POST /search
Content-Type: application/json
```

```json
{
  "q": "サンプル株式会社",
  "prefectureCode": "13",
  "size": 10
}
```

## Bulk Search

`bulk=true` の場合、`q` に指定された複数キーワードを分割して検索します。

```http
GET /search?bulk=true&q=サンプル株式会社,テスト合同会社
```

bulk 検索では、ヒット件数が 1 件だけのキーワードのみ採用します。0 件または 2 件以上のキーワードは曖昧な候補として除外します。

## Notes

- OpenSearch はローカル開発用の認証なし構成を想定しています。
- 認証なし構成をそのまま本番環境で使用しないでください。
- `from + size` は OpenSearch の標準的な制限に合わせ、最大 10000 件以内で扱います。
- reindex / cleanup / promote / delete 系の管理 API は含めません。
