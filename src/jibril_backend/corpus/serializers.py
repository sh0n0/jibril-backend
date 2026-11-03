from typing import Any

from rest_framework import serializers


class SearchQuerySerializer(serializers.Serializer[None]):
    q = serializers.CharField(
        help_text=(
            'Simple query string: "exact phrase", +must, -not, prefix*. '
            "Terms are ANDed."
        )
    )
    mode = serializers.ChoiceField(choices=["written", "spoken"], required=False)
    genre = serializers.CharField(
        required=False, help_text="e.g. journal, fiction, telephone"
    )
    # Filters on the "source" field; named so as not to shadow Serializer.source.
    subcorpus = serializers.CharField(
        required=False, help_text="e.g. slate, switchboard, 911report"
    )
    stem = serializers.BooleanField(
        default=False, help_text="Match inflected forms (English stemming)."
    )
    size = serializers.IntegerField(default=20, min_value=1, max_value=100)
    offset = serializers.IntegerField(default=0, min_value=0, max_value=10_000)


# The response fields below include "source", which can't be a class attribute
# on a Serializer (it would shadow Field.source), so they're built in get_fields.


class SentenceSerializer(serializers.Serializer[dict[str, Any]]):
    def get_fields(self) -> dict[str, serializers.Field[Any, Any, Any, Any]]:
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


class FacetsSerializer(serializers.Serializer[dict[str, Any]]):
    def get_fields(self) -> dict[str, serializers.Field[Any, Any, Any, Any]]:
        def counts() -> serializers.DictField:
            return serializers.DictField(child=serializers.IntegerField())

        return {"mode": counts(), "genre": counts(), "source": counts()}


class SearchResultSerializer(serializers.Serializer[dict[str, Any]]):
    total = serializers.IntegerField()
    results = SentenceSerializer(many=True)
    facets = FacetsSerializer(help_text="Hit counts per value, for each facet.")
