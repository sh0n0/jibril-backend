"""Download and read ConvoKit per-subreddit Reddit corpora.

See https://zissou.infosci.cornell.edu/convokit/datasets/subreddit-corpus/.
Each subreddit is a zip of ``utterances.jsonl`` (posts and comments, one per
line) plus ``conversations.json`` (thread metadata such as titles).
"""

import json
import shutil
import urllib.request
import zipfile
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

BASE_URL = "https://zissou.infosci.cornell.edu/convokit/datasets/subreddit-corpus"

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


def corpus_url(subreddit: str) -> str:
    """Return the zip URL for ``subreddit`` (names are case-sensitive).

    The zips are bucketed into directories named ``<first>~-~<last>``, listed
    in subreddit-groupings.txt and bounded by plain string comparison.
    """
    with urllib.request.urlopen(f"{BASE_URL}/subreddit-groupings.txt") as f:
        groupings = f.read().decode().split()
    for group in groupings:
        first, last = group.split("~-~")
        if first <= subreddit <= last:
            return f"{BASE_URL}/corpus-zipped/{group}/{subreddit}.corpus.zip"
    raise ValueError(f"no corpus group contains {subreddit!r}")


def download(subreddit: str, data_dir: Path) -> Path:
    """Download and unpack ``subreddit`` into ``data_dir/<subreddit>``."""
    target = data_dir / subreddit
    if (target / "utterances.jsonl").is_file():
        return target
    target.mkdir(parents=True, exist_ok=True)
    zip_path = data_dir / f"{subreddit}.corpus.zip"
    with urllib.request.urlopen(corpus_url(subreddit)) as r, zip_path.open("wb") as f:
        shutil.copyfileobj(r, f)
    with zipfile.ZipFile(zip_path) as z:
        # Some archives wrap their files in a directory; flatten into target.
        for member in z.infolist():
            if member.is_dir():
                continue
            with (
                z.open(member) as src,
                (target / Path(member.filename).name).open("wb") as dst,
            ):
                shutil.copyfileobj(src, dst)
    zip_path.unlink()
    return target


def read_comments(corpus_dir: Path, *, comments_only: bool) -> Iterator[Comment]:
    """Yield posts and comments, skipping deleted/empty ones and bots.

    Usernames are deliberately dropped.
    """
    threads = json.loads((corpus_dir / "conversations.json").read_text())
    with (corpus_dir / "utterances.jsonl").open(encoding="utf-8") as lines:
        for line in lines:
            u = json.loads(line)
            is_post = u["reply_to"] is None
            text = u["text"].strip()
            if (
                (comments_only and is_post)
                or text in _SKIP_TEXT
                or u["user"] in _SKIP_USERS
            ):
                continue
            meta = u["meta"]
            # Comments in per-subreddit corpora have an empty permalink.
            permalink = meta.get("permalink") or (
                f"/r/{meta['subreddit']}/comments/{u['root']}/_/{u['id']}/"
            )
            yield {
                "id": u["id"],
                "thread_id": u["root"],
                "reply_to": u["reply_to"],
                "is_post": is_post,
                "text": text,
                "thread_title": threads.get(u["root"], {}).get("title", ""),
                "subreddit": meta["subreddit"],
                "score": meta["score"],
                "created_at": datetime.fromtimestamp(
                    int(u["timestamp"]), UTC
                ).isoformat(),
                "permalink": f"https://www.reddit.com{permalink}",
            }
