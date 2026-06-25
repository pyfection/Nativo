"""
Service layer for spelling variants and spelling correction.

A SpellingVariant maps a non-standard spelling back to the WordForm whose
`form` is the standard. Two read paths sit on top of that mapping:

- `resolve_token` — "how is this properly written?" for a single token.
- `suggest_corrections_for_text` — scan a whole Text and propose standard
  spellings for the tokens that match a known variant.

Both are deliberately *suggest-only*: a variant string is not unique (homographs
across lexemes), so resolution returns candidates and never rewrites content on
its own. Confirming a correction is a separate, human-driven step.
"""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.text import Text
from app.models.word import Lexeme, SpellingVariant, WordForm
from app.schemas.word import (
    SpellingCandidate,
    SpellingCorrection,
    SpellingResolution,
    SpellingVariantCreate,
)
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
