"""
Service layer for spelling variants and spelling correction.

A SpellingVariant maps a non-standard spelling back to the WordForm whose
`form` is the standard. Two read paths sit on top of that mapping:

- `resolve_token` — "how is this properly written?" for a single token.
- `suggest_corrections_for_text` — scan a whole Text and propose standard
  spellings for the tokens that match a known variant.

Both are deliberately *suggest-only*: a variant string is not unique (homographs
across lexemes), so resolution returns candidates and never rewrites content on
its own. Confirming a correction is a separate, human-driven step:
`correct_texts` applies one confirmed fix ("gibd's" is now written "gibds")
across a language's texts.
"""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.text import DocumentType, Text
from app.models.text_word_link import TextWordLink
from app.models.word import Lexeme, SpellingVariant, WordForm
from app.schemas.word import (
    SpellingCandidate,
    SpellingCorrection,
    SpellingResolution,
    SpellingVariantCreate,
)
from app.services.document_service import suggest_links_for_text
from app.utils.text_normalize import fold_for_match, iter_tokens

# ---------------------------------------------------------------------------
# Variant CRUD
# ---------------------------------------------------------------------------


def list_variants(db: Session, word_form_id: UUID) -> list[SpellingVariant]:
    return (
        db.query(SpellingVariant)
        .filter(SpellingVariant.word_form_id == word_form_id)
        .order_by(SpellingVariant.variant.asc())
        .all()
    )


def add_variant(
    db: Session,
    word_form: WordForm,
    data: SpellingVariantCreate,
    creator_id: UUID | None = None,
) -> SpellingVariant:
    variant_text = data.variant.strip()
    if not variant_text:
        raise HTTPException(status_code=400, detail="Variant spelling cannot be empty")

    # A variant that already equals the standard form is a no-op, not a variant.
    if variant_text.casefold() == word_form.form.casefold():
        raise HTTPException(
            status_code=400,
            detail="That spelling is already the standard form",
        )

    existing = (
        db.query(SpellingVariant)
        .filter(
            SpellingVariant.word_form_id == word_form.id,
            SpellingVariant.variant == variant_text,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="This spelling variant already exists")

    # `normalized` is derived from `variant` by the model's validator.
    variant = SpellingVariant(
        word_form_id=word_form.id,
        variant=variant_text,
        note=data.note,
        created_by_id=creator_id,
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


def delete_variant(db: Session, variant: SpellingVariant) -> None:
    db.delete(variant)
    db.commit()


# ---------------------------------------------------------------------------
# Resolution / correction
# ---------------------------------------------------------------------------


def _candidate(variant: SpellingVariant, word_form: WordForm) -> SpellingCandidate:
    return SpellingCandidate(
        word_form_id=word_form.id,
        lexeme_id=word_form.lexeme_id,
        standard_form=word_form.form,
        lemma=word_form.lexeme.lemma if word_form.lexeme else word_form.form,
        note=variant.note,
    )


def _build_standard_index(word_forms: list[WordForm]) -> dict[str, list[WordForm]]:
    """Folded standard spellings (form + romanization) for the language."""
    index: dict[str, list[WordForm]] = defaultdict(list)
    for wf in word_forms:
        normalized = fold_for_match(wf.form)
        if normalized:
            index[normalized].append(wf)
        if wf.romanization:
            normalized_rom = fold_for_match(wf.romanization)
            if normalized_rom and normalized_rom != normalized:
                index[normalized_rom].append(wf)
    return index


def _build_variant_index(
    db: Session, language_id: UUID
) -> dict[str, list[tuple[SpellingVariant, WordForm]]]:
    """Folded non-standard spellings for the language → (variant, word_form)."""
    rows = (
        db.query(SpellingVariant, WordForm)
        .join(WordForm, WordForm.id == SpellingVariant.word_form_id)
        .join(Lexeme, Lexeme.id == WordForm.lexeme_id)
        .filter(Lexeme.language_id == language_id)
        .all()
    )
    index: dict[str, list[tuple[SpellingVariant, WordForm]]] = defaultdict(list)
    for variant, word_form in rows:
        index[variant.normalized].append((variant, word_form))
    return index


def _dedupe_candidates(
    matches: list[tuple[SpellingVariant, WordForm]],
) -> list[SpellingCandidate]:
    seen: set[UUID] = set()
    candidates: list[SpellingCandidate] = []
    for variant, word_form in matches:
        if word_form.id in seen:
            continue
        seen.add(word_form.id)
        candidates.append(_candidate(variant, word_form))
    return candidates


def resolve_token(db: Session, language_id: UUID, token: str) -> SpellingResolution:
    normalized = fold_for_match(token)

    standard_forms = (
        db.query(WordForm)
        .join(Lexeme, Lexeme.id == WordForm.lexeme_id)
        .filter(Lexeme.language_id == language_id)
        .all()
    )
    already_standard = normalized in _build_standard_index(standard_forms)

    candidates: list[SpellingCandidate] = []
    if not already_standard:
        matches = _build_variant_index(db, language_id).get(normalized, [])
        candidates = _dedupe_candidates(matches)

    return SpellingResolution(
        token=token,
        normalized=normalized,
        already_standard=already_standard,
        candidates=candidates,
    )


def suggest_corrections_for_text(db: Session, text: Text) -> list[SpellingCorrection]:
    """
    Walk a Text and propose standard spellings for tokens that match a known
    variant. Tokens that already match a standard form are left alone. Nothing
    is mutated — the caller decides what to apply.
    """
    if not text.language_id or not text.content:
        return []

    standard_forms = (
        db.query(WordForm)
        .join(Lexeme, Lexeme.id == WordForm.lexeme_id)
        .filter(Lexeme.language_id == text.language_id)
        .all()
    )
    standard_index = _build_standard_index(standard_forms)
    variant_index = _build_variant_index(db, text.language_id)

    corrections: list[SpellingCorrection] = []
    for token, start, end in iter_tokens(text.content):
        normalized = fold_for_match(token)
        if normalized in standard_index:
            continue  # already a standard spelling
        matches = variant_index.get(normalized)
        if not matches:
            continue

        candidates = _dedupe_candidates(matches)
        corrections.append(
            SpellingCorrection(
                start_char=start,
                end_char=end,
                original=token,
                ambiguous=len(candidates) > 1,
                candidates=candidates,
            )
        )
    return corrections


# ---------------------------------------------------------------------------
# Applying a confirmed fix
# ---------------------------------------------------------------------------


def _match_case(original: str, new: str) -> str:
    """Carry a sentence-initial capital (or all caps) over to the fix."""
    if len(original) > 1 and original.isupper():
        return new.upper()
    if original[:1].isupper() and new[:1].islower():
        return new[:1].upper() + new[1:]
    return new


def correct_texts(
    db: Session, language_id: UUID, old: str, new: str, *, user_id: UUID | None = None
) -> int:
    """Rewrite every token spelled `old` as `new` in the language's texts
    (not the writing standard, which quotes wrong spellings on purpose).
    Word links keep pointing at the same words, and the changed texts get
    fresh link suggestions. Returns how many texts changed. Does not commit.
    """
    target = fold_for_match(old)
    if not target or target == fold_for_match(new):
        return 0
    changed = 0
    texts = (
        db.query(Text)
        .filter(
            Text.language_id == language_id, Text.document_type != DocumentType.WRITING_STANDARD
        )
        .all()
    )
    for text in texts:
        content = text.content or ""
        hits = [(s, e, tok) for tok, s, e in iter_tokens(content) if fold_for_match(tok) == target]
        if not hits:
            continue
        pieces, last, shifts = [], 0, []
        for start, end, token in hits:
            replacement = _match_case(token, new)
            pieces += [content[last:start], replacement]
            last = end
            shifts.append((end, len(replacement) - (end - start)))
        pieces.append(content[last:])
        text.content = "".join(pieces)

        # A position moves by the growth of every replaced word ending at or
        # before it (so a link on the word itself stretches with it).
        def moved(pos: int) -> int:
            return pos + sum(delta for end, delta in shifts if end <= pos)

        for link in db.query(TextWordLink).filter(TextWordLink.text_id == text.id):
            link.start_char, link.end_char = moved(link.start_char), moved(link.end_char)
        db.flush()
        suggest_links_for_text(db, text, creator_id=user_id)
        changed += 1
    return changed
