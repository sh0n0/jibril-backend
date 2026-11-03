from collections.abc import Iterator
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from elasticsearch import helpers

from jibril_backend.corpus.reddit import read_comments
from jibril_backend.corpus.search import REDDIT_MAPPINGS, ensure_index, get_client


class Command(BaseCommand):
    help = "Index a ConvoKit Reddit corpus into Elasticsearch."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "path",
            type=Path,
            nargs="?",
            default=settings.BASE_DIR / "data" / "reddit" / "reddit-corpus-small",
            help="An unpacked ConvoKit corpus directory "
            "(default: data/reddit/reddit-corpus-small).",
        )
        parser.add_argument(
            "--recreate",
            action="store_true",
            help="Delete and recreate the index first.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        corpus_dir: Path = options["path"]
        if not (corpus_dir / "utterances.json").is_file():
            raise CommandError(f"{corpus_dir} has no utterances.json")

        client = get_client()
        index = settings.REDDIT_INDEX
        ensure_index(client, index, REDDIT_MAPPINGS, recreate=options["recreate"])

        def actions() -> Iterator[dict[str, Any]]:
            for comment in read_comments(corpus_dir):
                yield {"_index": index, "_id": comment["id"], "_source": comment}

        indexed, _ = helpers.bulk(client, actions(), chunk_size=2000)
        client.indices.refresh(index=index)
        self.stdout.write(
            self.style.SUCCESS(f"Indexed {indexed} posts/comments into '{index}'.")
        )
