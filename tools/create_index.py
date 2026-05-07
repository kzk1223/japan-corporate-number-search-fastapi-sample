import argparse
from typing import Any

from app.clients.opensearch import create_opensearch_client
from app.core.config import Settings


# ---------------------------------------------
# index body 生成
# ---------------------------------------------
def make_index_body() -> dict[str, Any]:
    """OpenSearch index settings / mappings 生成。"""
    return {
        "settings": {
            "analysis": {
                "normalizer": {
                    "lowercase_norm": {
                        "type": "custom",
                        "filter": ["lowercase"],
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "corporateNumber": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword", "ignore_above": 256},
                    },
                },
                "name": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword", "ignore_above": 256},
                        "keyword_norm": {
                            "type": "keyword",
                            "normalizer": "lowercase_norm",
                            "doc_values": False,
                            "ignore_above": 256,
                        },
                    },
                },
                "furigana": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword", "ignore_above": 256},
                    },
                },
                "prefectureCode": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword", "ignore_above": 256},
                    },
                },
                "cityCode": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword", "ignore_above": 256},
                    },
                },
            }
        },
    }


# ---------------------------------------------
# index / alias 作成
# ---------------------------------------------
def create_index(index_name: str, alias_name: str) -> dict[str, Any]:
    """index 作成と alias 付与。"""
    client = create_opensearch_client(Settings())
    if not client.indices.exists(index=index_name):
        client.indices.create(index=index_name, body=make_index_body())

    client.indices.update_aliases(
        body={
            "actions": [
                {"add": {"index": index_name, "alias": alias_name}},
            ]
        }
    )
    return {"ok": True, "index": index_name, "alias": alias_name}


# ---------------------------------------------
# CLI 引数解析
# ---------------------------------------------
def parse_args() -> argparse.Namespace:
    """コマンドライン引数解析。"""
    parser = argparse.ArgumentParser(description="Create OpenSearch index and alias.")
    parser.add_argument("--index", required=True, help="Target index name.")
    parser.add_argument("--alias", default="company", help="Search alias name.")
    return parser.parse_args()


# ---------------------------------------------
# CLI エントリポイント
# ---------------------------------------------
def main() -> None:
    """index 作成コマンド実行。"""
    args = parse_args()
    result = create_index(index_name=args.index, alias_name=args.alias)
    print(result)


if __name__ == "__main__":
    main()
