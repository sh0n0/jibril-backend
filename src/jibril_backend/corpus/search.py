from typing import Any

from django.conf import settings
from elasticsearch import Elasticsearch

INDEX_SETTINGS: dict[str, Any] = {
    # Single-node cluster: replicas would never be assigned and leave it yellow.
    "number_of_shards": 1,
    "number_of_replicas": 0,
}

INDEX_MAPPINGS: dict[str, Any] = {
    "dynamic": "strict",
    "properties": {
        "doc_id": {"type": "keyword"},
        "sentence_id": {"type": "keyword"},
        "position": {"type": "integer"},
        "text": {
            "type": "text",
            "fields": {"english": {"type": "text", "analyzer": "english"}},
        },
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


def get_client() -> Elasticsearch:
    return Elasticsearch(
        settings.ELASTICSEARCH_URL,
        basic_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD),
    )
