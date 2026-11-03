from typing import Any

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from jibril_backend.corpus.search import get_client
from jibril_backend.corpus.serializers import (
    OancSearchQuerySerializer,
    OancSearchResultSerializer,
    RedditSearchQuerySerializer,
    RedditSearchResultSerializer,
)


def _search(
    index: str,
    data: dict[str, Any],
    *,
    filters: list[dict[str, Any]],
    facets: dict[str, int],
    sort: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run a highlighted full-text search over ``text`` with facet counts.

    ``facets`` maps each keyword field to the number of buckets to return.
    """
    field = "text.english" if data["stem"] else "text"
    result = get_client().search(
        index=index,
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
        aggs={f: {"terms": {"field": f, "size": n}} for f, n in facets.items()},
        sort=sort,
        size=data["size"],
        from_=data["offset"],
        track_total_hits=True,
    )
    return {
        "total": result["hits"]["total"]["value"],
        "results": [
            {
                **hit["_source"],
                "highlight": hit.get("highlight", {}).get(field, [None])[0],
            }
            for hit in result["hits"]["hits"]
        ],
        "facets": {
            f: {b["key"]: b["doc_count"] for b in result["aggregations"][f]["buckets"]}
            for f in facets
        },
    }


class SentenceSearchView(APIView):
    """Full-text search over OANC sentences."""

    # Query parameter -> indexed field.
    FILTERS = {"mode": "mode", "genre": "genre", "subcorpus": "source"}

    @extend_schema(
        parameters=[OancSearchQuerySerializer], responses=OancSearchResultSerializer
    )
    def get(self, request: Request) -> Response:
        params = OancSearchQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        data: dict[str, Any] = params.validated_data

        result = _search(
            settings.OANC_INDEX,
            data,
            filters=[
                {"term": {f: data[p]}} for p, f in self.FILTERS.items() if p in data
            ],
            facets={"mode": 2, "genre": 50, "source": 50},
        )
        return Response(OancSearchResultSerializer(result).data)


class CommentSearchView(APIView):
    """Full-text search over Reddit posts and comments."""

    SORTS = {
        "relevance": None,
        "score": [{"score": "desc"}],
        "new": [{"created_at": "desc"}],
    }

    @extend_schema(
        parameters=[RedditSearchQuerySerializer],
        responses=RedditSearchResultSerializer,
    )
    def get(self, request: Request) -> Response:
        params = RedditSearchQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        data: dict[str, Any] = params.validated_data

        filters: list[dict[str, Any]] = []
        if "subreddit" in data:
            filters.append({"term": {"subreddit": data["subreddit"]}})
        if "kind" in data:
            filters.append({"term": {"is_post": data["kind"] == "post"}})
        if "min_score" in data:
            filters.append({"range": {"score": {"gte": data["min_score"]}}})

        result = _search(
            settings.REDDIT_INDEX,
            data,
            filters=filters,
            facets={"subreddit": 100},
            sort=self.SORTS[data["sort"]],
        )
        return Response(RedditSearchResultSerializer(result).data)
