"""Reader for the OANC 1.0.1 UTF-8 release (stand-off XCES annotations)."""

import re
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from pathlib import Path
from typing import TypedDict

XCES = "{http://www.xces.org/schema/2003}"

_WHITESPACE = re.compile(r"\s+")


class Sentence(TypedDict):
    doc_id: str
    sentence_id: str
    position: int
    text: str
    mode: str
    genre: str
    source: str
    title: str
    domain: str
    subdomain: str
    subject: str
    medium: str


def find_documents(root: Path) -> Iterator[Path]:
    """Yield the ``.txt`` file of every document under an OANC ``data`` dir."""
    yield from sorted(root.rglob("*.txt"))


def read_sentences(txt_path: Path, root: Path) -> Iterator[Sentence]:
    stem = txt_path.with_suffix("")
    # Paths look like {written_1,written_2,spoken}/<genre>/<source>/.../<doc>.txt
    parts = txt_path.relative_to(root).parts
    mode = parts[0].split("_")[0]
    genre = parts[1] if len(parts) > 2 else ""
    source = parts[2] if len(parts) > 3 else ""
    doc_id = stem.relative_to(root).as_posix()

    header = _read_header(stem.with_suffix(".anc"))
    text = txt_path.read_text(encoding="utf-8")
    sentences_path = stem.parent / f"{stem.name}-s.xml"

    # Offsets in the -s.xml annotation are character offsets into the .txt.
    for position, struct in enumerate(ET.parse(sentences_path).iter(f"{XCES}struct")):
        start, end = int(struct.attrib["from"]), int(struct.attrib["to"])
        sentence = _WHITESPACE.sub(" ", text[start:end]).strip()
        if not sentence:
            continue
        feat = struct.find(f"{XCES}feat[@name='id']")
        sentence_id = feat.attrib["value"] if feat is not None else str(position)
        yield {
            "doc_id": doc_id,
            "sentence_id": sentence_id,
            "position": position,
            "text": sentence,
            "mode": mode,
            "genre": genre,
            "source": source,
            **header,
        }


class _Header(TypedDict):
    title: str
    domain: str
    subdomain: str
    subject: str
    medium: str


def _read_header(anc_path: Path) -> _Header:
    if not anc_path.exists():
        return {"title": "", "domain": "", "subdomain": "", "subject": "", "medium": ""}
    tree = ET.parse(anc_path)

    def find(tag: str) -> str:
        return (tree.findtext(f".//{XCES}{tag}") or "").strip()

    return {
        "title": find("title"),
        "domain": find("domain"),
        "subdomain": find("subdomain"),
        "subject": find("subject"),
        "medium": find("medium"),
    }
