"""Reader for ConvoKit Reddit corpora (e.g. reddit-corpus-small)."""

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

# Utterances that carry no language worth searching.
_SKIP_TEXT = {"", "[deleted]", "[removed]"}
_SKIP_USERS = {"AutoModerator"}


class Comment(TypedDict):
    id: str
    thread_id: str
    reply_to: str | None
    is_post: bool
    text: str
    thread_title: str
    subreddit: str
    score: int
    created_at: str
    permalink: str


def read_comments(corpus_dir: Path) -> Iterator[Comment]:
    """Yield posts and comments, skipping deleted/empty ones and bots.

    Usernames are deliberately dropped.
    """
    threads = json.loads((corpus_dir / "conversations.json").read_text())
    utterances = json.loads((corpus_dir / "utterances.json").read_text())
    for u in utterances:
        text = u["text"].strip()
        if text in _SKIP_TEXT or u["user"] in _SKIP_USERS:
            continue
        meta = u["meta"]
        yield {
            "id": u["id"],
            "thread_id": u["root"],
            "reply_to": u["reply_to"],
            "is_post": u["reply_to"] is None,
            "text": text,
            "thread_title": threads.get(u["root"], {}).get("title", ""),
            "subreddit": meta["subreddit"],
            "score": meta["score"],
            "created_at": datetime.fromtimestamp(u["timestamp"], UTC).isoformat(),
            "permalink": f"https://www.reddit.com{meta['permalink']}",
        }
