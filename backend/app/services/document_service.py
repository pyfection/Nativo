"""
Service utilities for document/text processing.

Auto-link suggestions walk the text content, normalise each token, and
look it up in an index built from `WordForm.form` for the text's language.
Matches become `TextWordLink` rows pointing at the matched WordForm.
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
from app.models.word import Lexeme, WordForm

TOKEN_PATTERN = re.compile(r"\b[\w'-]+\b", re.UNICODE)


def _strip_diacritics(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return without_marks.casefold()


def _iter_tokens(content: str) -> Iterable[Tuple[str, int, int]]:
    for match in TOKEN_PATTERN.finditer(content or ""):
        yield match.group(0), match.start(), match.end()


def _build_word_form_index(word_forms: Iterable[WordForm]) -> Dict[str, List[WordForm]]:
    index: Dict[str, List[WordForm]] = defaultdict(list)
    for wf in word_forms:
        normalized = _strip_diacritics(wf.form)
        if normalized:
            index[normalized].append(wf)
        if wf.romanization:
            normalized_rom = _strip_diacritics(wf.romanization)
            if normalized_rom and normalized_rom != normalized:
                index[normalized_rom].append(wf)
    return index


def suggest_links_for_text(
    db: Session,
    text: Text,
    *,
    creator_id: Optional[UUID] = None,
    replace_existing_suggestions: bool = False,
) -> List[TextWordLink]:
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

    # Preload all WordForms whose parent Lexeme is in this Text's language.
    word_forms = (
        db.query(WordForm)
        .join(Lexeme, Lexeme.id == WordForm.lexeme_id)
        .filter(Lexeme.language_id == text.language_id)
        .all()
    )
    form_index = _build_word_form_index(word_forms)

    created_links: List[TextWordLink] = []
    for token, start, end in _iter_tokens(text.content):
        if (start, end) in rejected_spans:
            continue
        if (start, end) in existing_spans:
            continue

        normalized = _strip_diacritics(token)
        matches = form_index.get(normalized)
        if not matches:
            continue

        # Prefer an exact case-insensitive match; fall back to lemma; then first.
        selected = next(
            (wf for wf in matches if wf.form.casefold() == token.casefold()),
            None,
        )
        if selected is None:
            selected = next((wf for wf in matches if wf.is_lemma), matches[0])

        link = TextWordLink(
            text_id=text.id,
            word_form_id=selected.id,
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
