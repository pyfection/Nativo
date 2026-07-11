"""
Service utilities for document/text processing.

Auto-link suggestions walk the text content, normalise each token, and
look it up in an index built from `WordForm.form` for the text's language.
Matches become `TextWordLink` rows pointing at the matched WordForm.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.text import Text
from app.models.text_word_link import TextWordLink, TextWordLinkStatus
from app.models.word import Lexeme, LexemeStatus, SpellingVariant, WordForm
from app.utils.text_normalize import fold_for_match as _strip_diacritics
from app.utils.text_normalize import iter_tokens as _iter_tokens

# Confidence tiers. A token matching exactly ONE word form in the language is
# auto-confirmed — there is nothing for a human to decide. Homographs (several
# forms sharing the spelling, e.g. Bavarian `san` are/sow) need a human to
# pick the sense, so they stay suggestions at a distinct middle confidence.
# Matches on a recorded non-standard spelling rank lowest.
_AMBIGUOUS_MATCH_CONFIDENCE = 0.8
_VARIANT_MATCH_CONFIDENCE = 0.5

# Note marker on auto-confirmed links, so they're auditable (and could be
# demoted in bulk if a later dictionary addition turns a spelling into a
# homograph — accepted risk for now, see ROADMAP).
AUTO_CONFIRM_NOTE = "Auto-confirmed: unique exact match"


def _build_word_form_index(word_forms: Iterable[WordForm]) -> dict[str, list[WordForm]]:
    index: dict[str, list[WordForm]] = defaultdict(list)
    for wf in word_forms:
        normalized = _strip_diacritics(wf.form)
        if normalized:
            index[normalized].append(wf)
        if wf.romanization:
            normalized_rom = _strip_diacritics(wf.romanization)
            if normalized_rom and normalized_rom != normalized:
                index[normalized_rom].append(wf)
    return index


def _build_variant_index(db: Session, language_id) -> dict[str, list[WordForm]]:
    """Folded non-standard spellings for the language → the WordForm(s) they
    map to. `SpellingVariant.normalized` is already folded the same way tokens
    are, so this keys on it directly."""
    rows = (
        db.query(SpellingVariant.normalized, WordForm)
        .join(WordForm, WordForm.id == SpellingVariant.word_form_id)
        .join(Lexeme, Lexeme.id == WordForm.lexeme_id)
        .filter(
            Lexeme.language_id == language_id,
            Lexeme.status == LexemeStatus.PUBLISHED,
        )
        .all()
    )
    index: dict[str, list[WordForm]] = defaultdict(list)
    for normalized, word_form in rows:
        index[normalized].append(word_form)
    return index


def suggest_links_for_text(
    db: Session,
    text: Text,
    *,
    creator_id: UUID | None = None,
    replace_existing_suggestions: bool = False,
) -> list[TextWordLink]:
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
    # Published only: pending suggestions and archived entries must not link
    # (let alone auto-confirm) themselves into texts.
    word_forms = (
        db.query(WordForm)
        .join(Lexeme, Lexeme.id == WordForm.lexeme_id)
        .filter(
            Lexeme.language_id == text.language_id,
            Lexeme.status == LexemeStatus.PUBLISHED,
        )
        .all()
    )
    form_index = _build_word_form_index(word_forms)
    variant_index = _build_variant_index(db, text.language_id)

    created_links: list[TextWordLink] = []
    for token, start, end in _iter_tokens(text.content):
        if (start, end) in rejected_spans:
            continue
        if (start, end) in existing_spans:
            continue

        normalized = _strip_diacritics(token)
        matches = form_index.get(normalized)

        status = TextWordLinkStatus.SUGGESTED
        if matches:
            if len(matches) == 1:
                # Unique exact match — nothing for a human to decide.
                selected = matches[0]
                confidence = 1.0
                status = TextWordLinkStatus.CONFIRMED
                notes = AUTO_CONFIRM_NOTE
            else:
                # Homograph: several forms share this spelling. Prefer an exact
                # case-insensitive match; fall back to lemma; then first — but
                # a human must confirm the sense.
                selected = next(
                    (wf for wf in matches if wf.form.casefold() == token.casefold()),
                    None,
                )
                if selected is None:
                    selected = next((wf for wf in matches if wf.is_lemma), matches[0])
                confidence = _AMBIGUOUS_MATCH_CONFIDENCE
                notes = f"Ambiguous: {len(matches)} forms share this spelling"
        else:
            # No standard form — try recorded non-standard spellings. When a
            # variant is ambiguous (maps to several forms) we still suggest a
            # best guess (lemma, else first) at lower confidence for the human
            # to confirm or redirect.
            variant_matches = variant_index.get(normalized)
            if not variant_matches:
                continue
            selected = next((wf for wf in variant_matches if wf.is_lemma), variant_matches[0])
            confidence = _VARIANT_MATCH_CONFIDENCE
            notes = f"Auto-matched via alternative spelling '{token}' → '{selected.form}'"

        link = TextWordLink(
            text_id=text.id,
            word_form_id=selected.id,
            start_char=start,
            end_char=end,
            status=status,
            confidence=confidence,
            notes=notes,
            created_by_id=creator_id,
        )
        db.add(link)
        created_links.append(link)
        existing_spans[(start, end)] = link

    return created_links


def compute_link_coverage(text: Text, links: list[TextWordLink]) -> float:
    """Fraction of word-ish tokens covered by confirmed link spans.

    This is the number the learning path gates on (LINK_COVERAGE_THRESHOLD
    in learning_service) and what the editor-facing coverage badges show.
    """
    tokens = list(_iter_tokens(text.content or ""))
    if not tokens:
        return 0.0
    spans = [
        (link.start_char, link.end_char)
        for link in links
        if link.status == TextWordLinkStatus.CONFIRMED
    ]
    covered = 0
    for _token, start, end in tokens:
        if any(s <= start and end <= e for s, e in spans):
            covered += 1
    return covered / len(tokens)


def refresh_document_suggestions(
    db: Session,
    document_id: UUID,
    *,
    creator_id: UUID | None = None,
) -> dict[UUID, list[TextWordLink]]:
    texts = db.query(Text).filter(Text.document_id == document_id).all()
    suggestions: dict[UUID, list[TextWordLink]] = {}

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
