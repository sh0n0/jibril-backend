from rest_framework import serializers


class SearchQuerySerializer(serializers.Serializer[None]):
    q = serializers.CharField()
    mode = serializers.ChoiceField(choices=["written", "spoken"], required=False)
    genre = serializers.CharField(required=False)
    # Filters on the "source" field; named so as not to shadow Serializer.source.
    subcorpus = serializers.CharField(required=False)
    stem = serializers.BooleanField(
        default=False, help_text="Match inflected forms (English stemming)."
    )
    size = serializers.IntegerField(default=20, min_value=1, max_value=100)
    offset = serializers.IntegerField(default=0, min_value=0, max_value=10_000)
