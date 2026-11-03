from typing import Any

from django.conf import settings
from elasticsearch import Elasticsearch

INDEX_SETTINGS: dict[str, Any] = {
    # Single-node cluster: replicas would never be assigned and leave it yellow.
    "number_of_shards": 1,
    "number_of_replicas": 0,
}

_TEXT: dict[str, Any] = {
    "type": "text",
    "fields": {"english": {"type": "text", "analyzer": "english"}},
}

OANC_MAPPINGS: dict[str, Any] = {
    "dynamic": "strict",
    "properties": {
        "doc_id": {"type": "keyword"},
        "sentence_id": {"type": "keyword"},
        "position": {"type": "integer"},
        "text": _TEXT,
        "mode": {"type": "keyword"},
        "genre": {"type": "keyword"},
        "source": {"type": "keyword"},
        "title": {"type": "text", "fields": {"raw": {"type": "keyword"}}},
        "domain": {"type": "keyword"},
        "subdomain": {"type": "keyword"},
        "subject": {"type": "keyword"},
        "medium": {"type": "keyword"},
    },
}

REDDIT_MAPPINGS: dict[str, Any] = {
    "dynamic": "strict",
    "properties": {
        "id": {"type": "keyword"},
        "thread_id": {"type": "keyword"},
        "reply_to": {"type": "keyword"},
        "is_post": {"type": "boolean"},
        "text": _TEXT,
        "thread_title": {"type": "text"},
        "subreddit": {"type": "keyword"},
        "score": {"type": "integer"},
        "created_at": {"type": "date"},
        "permalink": {"type": "keyword", "index": False},
    },
}


def get_client() -> Elasticsearch:
    return Elasticsearch(
        settings.ELASTICSEARCH_URL,
        basic_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD),
    )


def ensure_index(
    client: Elasticsearch, index: str, mappings: dict[str, Any], *, recreate: bool
) -> None:
    if recreate:
        client.indices.delete(index=index, ignore_unavailable=True)
    if not client.indices.exists(index=index):
        client.indices.create(index=index, settings=INDEX_SETTINGS, mappings=mappings)
