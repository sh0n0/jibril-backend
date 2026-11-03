from typing import Any

from rest_framework import serializers

# Some response fields are named "source", which can't be a class attribute on
# a Serializer (it would shadow Field.source), so those serializers build their
# fields in get_fields.

_Fields = dict[str, serializers.Field[Any, Any, Any, Any]]


def _counts() -> serializers.DictField:
    return serializers.DictField(child=serializers.IntegerField())


class SearchQuerySerializer(serializers.Serializer[None]):
    q = serializers.CharField(
        help_text=(
            'Simple query string: "exact phrase", +must, -not, prefix*. '
            "Terms are ANDed."
        )
    )
    stem = serializers.BooleanField(
        default=False, help_text="Match inflected forms (English stemming)."
    )
    size = serializers.IntegerField(default=20, min_value=1, max_value=100)
    offset = serializers.IntegerField(default=0, min_value=0, max_value=10_000)


# OANC


class OancSearchQuerySerializer(SearchQuerySerializer):
    mode = serializers.ChoiceField(choices=["written", "spoken"], required=False)
    genre = serializers.CharField(
        required=False, help_text="e.g. journal, fiction, telephone"
    )
    # Filters on the "source" field; named so as not to shadow Serializer.source.
    subcorpus = serializers.CharField(
        required=False, help_text="e.g. slate, switchboard, 911report"
    )


class SentenceSerializer(serializers.Serializer[dict[str, Any]]):
    def get_fields(self) -> _Fields:
        return {
            "doc_id": serializers.CharField(),
            "sentence_id": serializers.CharField(),
            "position": serializers.IntegerField(),
            "text": serializers.CharField(),
            "highlight": serializers.CharField(
                allow_null=True, help_text="text with matches wrapped in <em>."
            ),
            "mode": serializers.ChoiceField(choices=["written", "spoken"]),
            "genre": serializers.CharField(),
            "source": serializers.CharField(),
            "title": serializers.CharField(),
            "domain": serializers.CharField(),
            "subdomain": serializers.CharField(),
            "subject": serializers.CharField(),
            "medium": serializers.CharField(),
        }


class OancFacetsSerializer(serializers.Serializer[dict[str, Any]]):
    def get_fields(self) -> _Fields:
        return {"mode": _counts(), "genre": _counts(), "source": _counts()}


class OancSearchResultSerializer(serializers.Serializer[dict[str, Any]]):
    total = serializers.IntegerField()
    results = SentenceSerializer(many=True)
    facets = OancFacetsSerializer(help_text="Hit counts per value, for each facet.")


# Reddit


class RedditSearchQuerySerializer(SearchQuerySerializer):
    subreddit = serializers.CharField(required=False, help_text="e.g. AskReddit")
    kind = serializers.ChoiceField(
        choices=["post", "comment"],
        required=False,
        help_text="Only thread-starting posts, or only comments.",
    )
    min_score = serializers.IntegerField(required=False)
    sort = serializers.ChoiceField(
        choices=["relevance", "score", "new"], default="relevance"
    )


class CommentSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.CharField()
    thread_id = serializers.CharField()
    reply_to = serializers.CharField(allow_null=True)
    is_post = serializers.BooleanField()
    text = serializers.CharField()
    highlight = serializers.CharField(
        allow_null=True, help_text="text with matches wrapped in <em>."
    )
    thread_title = serializers.CharField()
    subreddit = serializers.CharField()
    score = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    permalink = serializers.URLField()


class RedditFacetsSerializer(serializers.Serializer[dict[str, Any]]):
    subreddit = _counts()


class RedditSearchResultSerializer(serializers.Serializer[dict[str, Any]]):
    total = serializers.IntegerField()
    results = CommentSerializer(many=True)
    facets = RedditFacetsSerializer(help_text="Hit counts per subreddit.")
