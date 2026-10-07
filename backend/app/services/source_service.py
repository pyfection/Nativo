"""
Outside sources: store text from a web page as sentence snippets.

Snippets feed Quick Contribute (spelling confirmation in the same language,
translation from languages a user speaks). Only sentences are kept, each
with the page's URL, title and licence so cards can credit and link it.
Fetching happens elsewhere (backend/scripts/harvest_wikipedia.py, the MCP
tool); the server never fetches arbitrary URLs itself.
"""

from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.source_snippet import SourceSnippet

# Sentence-ish chunks: split after terminal punctuation or at line breaks.
_SENTENCE_BREAK = re.compile(r"(?<=[.!?…])\s+|\n+")
MIN_WORDS = 3
MAX_WORDS = 40
MAX_CHARS = 400


def split_sentences(text: str) -> list[str]:
    """Sentences worth a card: whole-ish, prose, not too long."""
    out = []
    for raw in _SENTENCE_BREAK.split(text or ""):
        sentence = " ".join(raw.split())
        words = sentence.split(" ")
        if not (MIN_WORDS <= len(words) <= MAX_WORDS) or len(sentence) > MAX_CHARS:
            continue
        # Skip list debris, references, tables: mostly-letters prose only.
        letters = sum(ch.isalpha() for ch in sentence)
        if letters < 0.6 * len(sentence.replace(" ", "")):
            continue
        out.append(sentence)
    return out


def add_text(
    db: Session,
    language_id: UUID,
    *,
    source_url: str,
    source_title: str,
    text: str,
    license: str | None,
    creator_id: UUID | None,
) -> list[SourceSnippet]:
    """Split `text` into snippets, skipping sentences already stored for the
    language. Does not commit."""
    sentences = list(dict.fromkeys(split_sentences(text)))
    if not sentences:
        return []
    seen = {
        content
        for (content,) in db.query(SourceSnippet.content).filter(
            SourceSnippet.language_id == language_id,
            SourceSnippet.content.in_(sentences),
        )
    }
    created = [
        SourceSnippet(
            language_id=language_id,
            content=sentence,
            source_url=source_url,
            source_title=source_title,
            license=license,
            created_by_id=creator_id,
        )
        for sentence in sentences
        if sentence not in seen
    ]
    db.add_all(created)
    db.flush()
    return created
