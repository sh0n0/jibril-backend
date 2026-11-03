from collections.abc import Iterator
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from elasticsearch import helpers

from jibril_backend.corpus.reddit import download, read_comments
from jibril_backend.corpus.search import REDDIT_MAPPINGS, ensure_index, get_client


class Command(BaseCommand):
    help = (
        "Download ConvoKit subreddit corpora and index them into Elasticsearch. "
        "Re-running for an already indexed subreddit overwrites its documents."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "subreddits",
            nargs="+",
            help="Subreddit names, case-sensitive (e.g. AskAnAmerican).",
        )
        parser.add_argument(
            "--comments-only",
            action="store_true",
            help="Skip thread-starting posts.",
        )
        parser.add_argument(
            "--data-dir",
            type=Path,
            default=settings.BASE_DIR / "data" / "reddit",
            help="Where corpora are downloaded (default: data/reddit).",
        )
        parser.add_argument(
            "--recreate",
            action="store_true",
            help="Delete and recreate the whole index first (drops every subreddit).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        client = get_client()
        index = settings.REDDIT_INDEX
        ensure_index(client, index, REDDIT_MAPPINGS, recreate=options["recreate"])

        for subreddit in options["subreddits"]:
            self.stdout.write(f"Downloading {subreddit}...")
            corpus_dir = download(subreddit, options["data_dir"])

            def actions(corpus_dir: Path = corpus_dir) -> Iterator[dict[str, Any]]:
                for comment in read_comments(
                    corpus_dir, comments_only=options["comments_only"]
                ):
                    yield {"_index": index, "_id": comment["id"], "_source": comment}

            indexed, _ = helpers.bulk(client, actions(), chunk_size=2000)
            self.stdout.write(
                self.style.SUCCESS(f"Indexed {indexed} documents from r/{subreddit}.")
            )
        client.indices.refresh(index=index)
