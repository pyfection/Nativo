"""
Service utilities for document/text processing.
"""
from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.text import Text
from app.models.text_word_link import TextWordLink, TextWordLinkStatus
from app.models.word import Word

TOKEN_PATTERN = re.compile(r"\b[\w'-]+\b", re.UNICODE)


def _strip_diacritics(value: str) -> str:
    """
    Normalize a string by stripping diacritics and applying case-folding.
    """
    normalized = unicodedata.normalize("NFD", value)
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return without_marks.casefold()


def _iter_tokens(content: str) -> Iterable[Tuple[str, int, int]]:
    """
    Iterate over tokens in the content, yielding (token, start, end).
    """
    for match in TOKEN_PATTERN.finditer(content or ""):
        yield match.group(0), match.start(), match.end()


def _build_word_index(words: Iterable[Word]) -> Dict[str, List[Word]]:
    """
    Build a lookup from normalized token to list of Word objects.
    """
    index: Dict[str, List[Word]] = defaultdict(list)
    for word in words:
        normalized = _strip_diacritics(word.word)
        if normalized:
            index[normalized].append(word)
    return index


def suggest_links_for_text(
    db: Session,
    text: Text,
    *,
    creator_id: Optional[UUID] = None,
    replace_existing_suggestions: bool = False,
) -> List[TextWordLink]:
    """
    Generate suggested TextWordLink records for a Text instance.

    Args:
        db: Database session.
        text: Text record to analyze.
        creator_id: Optional user ID attributed to auto-generated links.
        replace_existing_suggestions: If True, existing suggested links will be removed
            before generating new ones. Confirmed or rejected links remain untouched.

    Returns:
        List of TextWordLink suggestions added to the session.
    """
    if not text.language_id or not text.content:
        return []

    existing_links = db.query(TextWordLink).filter(TextWordLink.text_id == text.id).all()

    if replace_existing_suggestions:
        for link in existing_links:
            if link.status == TextWordLinkStatus.SUGGESTED:
                db.delete(link)
        db.flush()
        existing_links = [
            link for link in existing_links if link.status != TextWordLinkStatus.SUGGESTED
        ]

    existing_spans = {(link.start_char, link.end_char): link for link in existing_links}
    rejected_spans = {
        (link.start_char, link.end_char)
        for link in existing_links
        if link.status == TextWordLinkStatus.REJECTED
    }

    # Preload words for the text's language and build lookup.
    words = db.query(Word).filter(Word.language_id == text.language_id).all()
    word_index = _build_word_index(words)

    created_links: List[TextWordLink] = []
    for token, start, end in _iter_tokens(text.content):
        if (start, end) in rejected_spans:
            continue
        if (start, end) in existing_spans:
            continue

        normalized = _strip_diacritics(token)
        matches = word_index.get(normalized)
        if not matches:
            continue

        # Prefer an exact case-insensitive match; fall back to first candidate.
        selected_word = next(
            (w for w in matches if w.word.casefold() == token.casefold()),
            matches[0],
        )

        link = TextWordLink(
            text_id=text.id,
            word_id=selected_word.id,
            start_char=start,
            end_char=end,
            status=TextWordLinkStatus.SUGGESTED,
            confidence=1.0,
            created_by_id=creator_id,
        )
        db.add(link)
        created_links.append(link)
        existing_spans[(start, end)] = link

    return created_links


def refresh_document_suggestions(
    db: Session,
    document_id: UUID,
    *,
    creator_id: Optional[UUID] = None,
) -> Dict[UUID, List[TextWordLink]]:
    """
    Rebuild link suggestions for all texts in a document.

    Returns a dictionary mapping text IDs to lists of new suggestions.
    """
    texts = db.query(Text).filter(Text.document_id == document_id).all()
    suggestions: Dict[UUID, List[TextWordLink]] = {}

    for text in texts:
        created = suggest_links_for_text(
            db,
            text,
            creator_id=creator_id,
            replace_existing_suggestions=True,
        )
        if created:
            suggestions[text.id] = created

    return suggestions

