from typing import Any

from django.conf import settings
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from jibril_backend.corpus.search import get_client
from jibril_backend.corpus.serializers import SearchQuerySerializer

FACETS = ("mode", "genre", "source")
# Query parameter -> indexed field.
FILTERS = {"mode": "mode", "genre": "genre", "subcorpus": "source"}


class SentenceSearchView(APIView):
    """Full-text search over OANC sentences.

    ``q`` uses Elasticsearch's simple query string syntax: ``"exact phrase"``,
    ``+must``, ``-not``, ``prefix*``.
    """

    def get(self, request: Request) -> Response:
        params = SearchQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        data: dict[str, Any] = params.validated_data

        field = "text.english" if data["stem"] else "text"
        filters = [{"term": {f: data[p]}} for p, f in FILTERS.items() if p in data]
        result = get_client().search(
            index=settings.OANC_INDEX,
            query={
                "bool": {
                    "must": {
                        "simple_query_string": {
                            "query": data["q"],
                            "fields": [field],
                            "default_operator": "and",
                        }
                    },
                    "filter": filters,
                }
            },
            highlight={"fields": {field: {"number_of_fragments": 0}}},
            aggs={f: {"terms": {"field": f, "size": 50}} for f in FACETS},
            size=data["size"],
            from_=data["offset"],
            track_total_hits=True,
        )

        return Response(
            {
                "total": result["hits"]["total"]["value"],
                "results": [
                    {
                        **hit["_source"],
                        "highlight": hit.get("highlight", {}).get(field, [None])[0],
                    }
                    for hit in result["hits"]["hits"]
                ],
                "facets": {
                    f: {
                        b["key"]: b["doc_count"]
                        for b in result["aggregations"][f]["buckets"]
                    }
                    for f in FACETS
                },
            }
        )
