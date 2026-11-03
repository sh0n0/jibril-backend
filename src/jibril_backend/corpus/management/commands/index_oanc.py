from collections.abc import Iterator
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from elasticsearch import helpers

from jibril_backend.corpus.oanc import find_documents, read_sentences
from jibril_backend.corpus.search import OANC_MAPPINGS, ensure_index, get_client


class Command(BaseCommand):
    help = "Index OANC sentences into Elasticsearch."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "path",
            type=Path,
            nargs="?",
            default=settings.BASE_DIR / "data" / "OANC" / "data",
            help="The OANC 'data' directory (default: data/OANC/data).",
        )
        parser.add_argument(
            "--recreate",
            action="store_true",
            help="Delete and recreate the index first.",
        )
        parser.add_argument(
            "--limit", type=int, help="Only index the first N documents."
        )

    def handle(self, *args: Any, **options: Any) -> None:
        root: Path = options["path"]
        if not root.is_dir():
            raise CommandError(f"{root} is not a directory")

        client = get_client()
        index = settings.OANC_INDEX
        ensure_index(client, index, OANC_MAPPINGS, recreate=options["recreate"])

        documents = list(find_documents(root))[: options["limit"]]

        def actions() -> Iterator[dict[str, Any]]:
            for i, path in enumerate(documents, 1):
                for sentence in read_sentences(path, root):
                    yield {
                        "_index": index,
                        "_id": f"{sentence['doc_id']}#{sentence['sentence_id']}",
                        "_source": sentence,
                    }
                if i % 500 == 0:
                    self.stdout.write(f"{i}/{len(documents)} documents")

        indexed, _ = helpers.bulk(client, actions(), chunk_size=2000)
        client.indices.refresh(index=index)
        self.stdout.write(
            self.style.SUCCESS(
                f"Indexed {indexed} sentences from {len(documents)} documents "
                f"into '{index}'."
            )
        )
