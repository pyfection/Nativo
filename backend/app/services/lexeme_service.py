"""
Service layer for Lexemes and WordForms.

Responsibilities:
- Lexeme CRUD that also manages the canonical lemma WordForm.
- WordForm CRUD that keeps rhyme_key / near_rhyme_key in sync with IPA.
- Symmetric relation writes (synonyms / antonyms / translations) that
  canonicalise the pair as `(min_id, max_id)` so the CHECK constraint passes
  and the row exists exactly once.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Iterable, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, delete, func, insert, or_, select, update
from sqlalchemy.orm import Session

from app.models.language import Language
from app.models.tag import Tag
from app.models.word import (
    Lexeme,
    LexemeStatus,
    WordForm,
    lexeme_antonyms,
    lexeme_synonyms,
    lexeme_translations,
)
from app.schemas.word import (
    AntonymCreate,
    AntonymLink,
    LexemeCreate,
    LexemeUpdate,
    SynonymCreate,
    SynonymLink,
    TranslationCreate,
    TranslationLink,
    WordFormCreate,
    WordFormCreateNested,
    WordFormUpdate,
)
from app.utils.rhyme import compute_near_rhyme_key, compute_rhyme_key


def _now() -> datetime:
    return datetime.now(UTC)


def _resolve_tags(db: Session, tag_names: Iterable[str] | None) -> list[Tag]:
    if not tag_names:
        return []

    resolved: list[Tag] = []
    seen: set[str] = set()
    for raw in tag_names:
        if not raw:
            continue
        cleaned = raw.strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        tag = db.query(Tag).filter(func.lower(Tag.name) == key).first()
        if not tag:
            tag = Tag(name=cleaned)
            db.add(tag)
            db.flush()
        resolved.append(tag)
    return resolved


def _apply_rhyme_keys(word_form: WordForm) -> None:
    word_form.rhyme_key = compute_rhyme_key(word_form.ipa_pronunciation)
    word_form.near_rhyme_key = compute_near_rhyme_key(word_form.ipa_pronunciation)


# ---------------------------------------------------------------------------
# Lexeme CRUD
# ---------------------------------------------------------------------------


def create_lexeme(
    db: Session,
    data: LexemeCreate,
    creator_id: UUID,
    status: LexemeStatus | None = None,
) -> Lexeme:
    """Create a lexeme with its canonical form.

    `status` overrides the model default (DRAFT) — the endpoint passes
    PENDING_REVIEW when the creator lacks edit permission (suggester tier).
    """
    payload = data.model_dump(
        exclude={"lemma_form", "additional_forms", "tags"}, exclude_unset=False
    )
    if status is not None:
        payload["status"] = status

    lexeme = Lexeme(**payload, created_by_id=creator_id)
    db.add(lexeme)
    db.flush()

    if data.tags:
        lexeme.tags = _resolve_tags(db, data.tags)

    # Lemma WordForm — denormalised lemma string mirrors this form.
    lemma_form_data = data.lemma_form.model_dump()
    confirmed_at_ids = lemma_form_data.pop("confirmed_at_location_ids", None) or []
    lemma_form_data["is_lemma"] = True
    lemma_form_data["form"] = lemma_form_data.get("form") or data.lemma
    lemma_form = WordForm(**lemma_form_data, lexeme_id=lexeme.id)
    _apply_rhyme_keys(lemma_form)
    db.add(lemma_form)
    db.flush()
    if confirmed_at_ids:
        _set_word_form_locations(db, lemma_form.id, confirmed_at_ids)

    # Mirror the canonical form back onto the Lexeme.
    lexeme.lemma = lemma_form.form

    for extra in data.additional_forms or []:
        _create_word_form_from_nested(db, lexeme.id, extra, is_lemma=False)

    db.commit()
    db.refresh(lexeme)
    return lexeme


def update_lexeme(db: Session, lexeme: Lexeme, data: LexemeUpdate) -> Lexeme:
    update_data = data.model_dump(exclude_unset=True)
    tag_names = update_data.pop("tags", None)

    for field, value in update_data.items():
        setattr(lexeme, field, value)

    if tag_names is not None:
        lexeme.tags = _resolve_tags(db, tag_names)

    # If the lemma string changed, mirror it onto the canonical form.
    if "lemma" in update_data:
        canonical = (
            db.query(WordForm)
            .filter(WordForm.lexeme_id == lexeme.id, WordForm.is_lemma.is_(True))
            .first()
        )
        if canonical and canonical.form != lexeme.lemma:
            canonical.form = lexeme.lemma

    db.commit()
    db.refresh(lexeme)
    return lexeme


# ---------------------------------------------------------------------------
# WordForm CRUD
# ---------------------------------------------------------------------------


def _create_word_form_from_nested(
    db: Session,
    lexeme_id: UUID,
    data: WordFormCreateNested,
    *,
    is_lemma: bool = False,
) -> WordForm:
    payload = data.model_dump()
    confirmed_at_ids = payload.pop("confirmed_at_location_ids", None) or []
    payload["is_lemma"] = is_lemma if not data.is_lemma else data.is_lemma
    word_form = WordForm(**payload, lexeme_id=lexeme_id)
    _apply_rhyme_keys(word_form)
    db.add(word_form)
    db.flush()
    if confirmed_at_ids:
        _set_word_form_locations(db, word_form.id, confirmed_at_ids)
    return word_form


def create_word_form(db: Session, data: WordFormCreate) -> WordForm:
    lexeme = db.query(Lexeme).filter(Lexeme.id == data.lexeme_id).first()
    if not lexeme:
        raise HTTPException(status_code=404, detail="Lexeme not found")

    payload = data.model_dump()
    confirmed_at_ids = payload.pop("confirmed_at_location_ids", None) or []

    if payload.get("is_lemma"):
        _demote_existing_lemma(db, lexeme.id)

    word_form = WordForm(**payload)
    _apply_rhyme_keys(word_form)
    db.add(word_form)
    db.flush()
    if confirmed_at_ids:
        _set_word_form_locations(db, word_form.id, confirmed_at_ids)

    if word_form.is_lemma:
        lexeme.lemma = word_form.form

    db.commit()
    db.refresh(word_form)
    return word_form


def update_word_form(db: Session, word_form: WordForm, data: WordFormUpdate) -> WordForm:
    update_data = data.model_dump(exclude_unset=True)
    confirmed_at_ids = update_data.pop("confirmed_at_location_ids", None)

    promoted_to_lemma = update_data.get("is_lemma") is True and not word_form.is_lemma
    if promoted_to_lemma:
        _demote_existing_lemma(db, word_form.lexeme_id, exclude_id=word_form.id)

    for field, value in update_data.items():
        setattr(word_form, field, value)

    if "ipa_pronunciation" in update_data:
        _apply_rhyme_keys(word_form)

    if confirmed_at_ids is not None:
        _set_word_form_locations(db, word_form.id, confirmed_at_ids)

    if word_form.is_lemma:
        lexeme = db.query(Lexeme).filter(Lexeme.id == word_form.lexeme_id).first()
        if lexeme and lexeme.lemma != word_form.form:
            lexeme.lemma = word_form.form

    db.commit()
    db.refresh(word_form)
    return word_form


def _demote_existing_lemma(db: Session, lexeme_id: UUID, *, exclude_id: UUID | None = None) -> None:
    query = db.query(WordForm).filter(
        WordForm.lexeme_id == lexeme_id, WordForm.is_lemma.is_(True)
    )
    if exclude_id is not None:
        query = query.filter(WordForm.id != exclude_id)
    for existing in query.all():
        existing.is_lemma = False


def _set_word_form_locations(
    db: Session, word_form_id: UUID, location_ids: list[UUID]
) -> None:
    from app.models.word import word_form_locations

    db.execute(
        delete(word_form_locations).where(
            word_form_locations.c.word_form_id == word_form_id
        )
    )
    now = _now()
    for loc_id in location_ids:
        db.execute(
            insert(word_form_locations).values(
                word_form_id=word_form_id,
                location_id=loc_id,
                created_at=now,
            )
        )


# ---------------------------------------------------------------------------
# Symmetric relations (synonyms / antonyms / translations)
# ---------------------------------------------------------------------------


def _ordered_pair(a: UUID, b: UUID) -> tuple[UUID, UUID]:
    return (a, b) if a < b else (b, a)


def add_synonym(db: Session, lexeme_id: UUID, data: SynonymCreate) -> SynonymLink:
    if lexeme_id == data.other_lexeme_id:
        raise HTTPException(status_code=400, detail="A lexeme can't be a synonym of itself")

    own = db.query(Lexeme).filter(Lexeme.id == lexeme_id).first()
    other = db.query(Lexeme).filter(Lexeme.id == data.other_lexeme_id).first()
    if not own or not other:
        raise HTTPException(status_code=404, detail="Lexeme not found")
    if own.language_id != other.language_id:
        raise HTTPException(
            status_code=400, detail="Synonyms must share the same language"
        )

    low, high = _ordered_pair(lexeme_id, data.other_lexeme_id)
    existing = db.execute(
        select(lexeme_synonyms).where(
            and_(
                lexeme_synonyms.c.lexeme_id == low,
                lexeme_synonyms.c.synonym_id == high,
            )
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Synonym link already exists")

    db.execute(
        insert(lexeme_synonyms).values(
            lexeme_id=low,
            synonym_id=high,
            nuance=data.nuance,
            notes=data.notes,
            created_at=_now(),
        )
    )
    db.commit()

    return SynonymLink(
        id=other.id,
        lemma=other.lemma,
        language_id=other.language_id,
        part_of_speech=other.part_of_speech,
        nuance=data.nuance,
        notes=data.notes,
    )


def remove_synonym(db: Session, lexeme_id: UUID, other_id: UUID) -> None:
    low, high = _ordered_pair(lexeme_id, other_id)
    result = db.execute(
        delete(lexeme_synonyms).where(
            and_(
                lexeme_synonyms.c.lexeme_id == low,
                lexeme_synonyms.c.synonym_id == high,
            )
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Synonym link not found")
    db.commit()


def list_synonyms(db: Session, lexeme_id: UUID) -> list[SynonymLink]:
    rows = db.execute(
        select(
            lexeme_synonyms.c.lexeme_id,
            lexeme_synonyms.c.synonym_id,
            lexeme_synonyms.c.nuance,
            lexeme_synonyms.c.notes,
        ).where(
            or_(
                lexeme_synonyms.c.lexeme_id == lexeme_id,
                lexeme_synonyms.c.synonym_id == lexeme_id,
            )
        )
    ).fetchall()

    other_ids = [r.synonym_id if r.lexeme_id == lexeme_id else r.lexeme_id for r in rows]
    return _build_links(db, other_ids, rows, SynonymLink, nuance_key="nuance")


def add_antonym(db: Session, lexeme_id: UUID, data: AntonymCreate) -> AntonymLink:
    if lexeme_id == data.other_lexeme_id:
        raise HTTPException(status_code=400, detail="A lexeme can't be an antonym of itself")

    own = db.query(Lexeme).filter(Lexeme.id == lexeme_id).first()
    other = db.query(Lexeme).filter(Lexeme.id == data.other_lexeme_id).first()
    if not own or not other:
        raise HTTPException(status_code=404, detail="Lexeme not found")
    if own.language_id != other.language_id:
        raise HTTPException(
            status_code=400, detail="Antonyms must share the same language"
        )

    low, high = _ordered_pair(lexeme_id, data.other_lexeme_id)
    existing = db.execute(
        select(lexeme_antonyms).where(
            and_(
                lexeme_antonyms.c.lexeme_id == low,
                lexeme_antonyms.c.antonym_id == high,
            )
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Antonym link already exists")

    db.execute(
        insert(lexeme_antonyms).values(
            lexeme_id=low,
            antonym_id=high,
            antonym_type=data.antonym_type,
            notes=data.notes,
            created_at=_now(),
        )
    )
    db.commit()

    return AntonymLink(
        id=other.id,
        lemma=other.lemma,
        language_id=other.language_id,
        part_of_speech=other.part_of_speech,
        antonym_type=data.antonym_type,
        notes=data.notes,
    )


def remove_antonym(db: Session, lexeme_id: UUID, other_id: UUID) -> None:
    low, high = _ordered_pair(lexeme_id, other_id)
    result = db.execute(
        delete(lexeme_antonyms).where(
            and_(
                lexeme_antonyms.c.lexeme_id == low,
                lexeme_antonyms.c.antonym_id == high,
            )
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Antonym link not found")
    db.commit()


def list_antonyms(db: Session, lexeme_id: UUID) -> list[AntonymLink]:
    rows = db.execute(
        select(
            lexeme_antonyms.c.lexeme_id,
            lexeme_antonyms.c.antonym_id,
            lexeme_antonyms.c.antonym_type,
            lexeme_antonyms.c.notes,
        ).where(
            or_(
                lexeme_antonyms.c.lexeme_id == lexeme_id,
                lexeme_antonyms.c.antonym_id == lexeme_id,
            )
        )
    ).fetchall()

    other_ids = [r.antonym_id if r.lexeme_id == lexeme_id else r.lexeme_id for r in rows]
    return _build_links(
        db, other_ids, rows, AntonymLink, antonym_type_key="antonym_type"
    )


def add_translation(
    db: Session, lexeme_id: UUID, data: TranslationCreate, creator_id: UUID
) -> TranslationLink:
    if lexeme_id == data.other_lexeme_id:
        raise HTTPException(status_code=400, detail="A lexeme can't translate itself")

    own = db.query(Lexeme).filter(Lexeme.id == lexeme_id).first()
    other = db.query(Lexeme).filter(Lexeme.id == data.other_lexeme_id).first()
    if not own or not other:
        raise HTTPException(status_code=404, detail="Lexeme not found")
    if own.language_id == other.language_id:
        raise HTTPException(
            status_code=400, detail="Translation must be in a different language"
        )

    low, high = _ordered_pair(lexeme_id, data.other_lexeme_id)
    existing = db.execute(
        select(lexeme_translations).where(
            and_(
                lexeme_translations.c.lexeme_id == low,
                lexeme_translations.c.translation_id == high,
            )
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Translation already exists")

    db.execute(
        insert(lexeme_translations).values(
            lexeme_id=low,
            translation_id=high,
            notes=data.notes,
            created_at=_now(),
            created_by_id=creator_id,
        )
    )
    db.commit()

    return TranslationLink(
        id=other.id,
        lemma=other.lemma,
        language_id=other.language_id,
        part_of_speech=other.part_of_speech,
        notes=data.notes,
    )


def remove_translation(db: Session, lexeme_id: UUID, other_id: UUID) -> None:
    low, high = _ordered_pair(lexeme_id, other_id)
    result = db.execute(
        delete(lexeme_translations).where(
            and_(
                lexeme_translations.c.lexeme_id == low,
                lexeme_translations.c.translation_id == high,
            )
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Translation not found")
    db.commit()


def update_translation_notes(
    db: Session, lexeme_id: UUID, other_id: UUID, notes: Optional[str]
) -> TranslationLink:
    low, high = _ordered_pair(lexeme_id, other_id)
    result = db.execute(
        update(lexeme_translations)
        .where(
            and_(
                lexeme_translations.c.lexeme_id == low,
                lexeme_translations.c.translation_id == high,
            )
        )
        .values(notes=notes)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Translation not found")
    db.commit()

    other = db.query(Lexeme).filter(Lexeme.id == other_id).first()
    return TranslationLink(
        id=other.id,
        lemma=other.lemma,
        language_id=other.language_id,
        part_of_speech=other.part_of_speech,
        notes=notes,
    )


def list_translations(db: Session, lexeme_id: UUID) -> list[TranslationLink]:
    rows = db.execute(
        select(
            lexeme_translations.c.lexeme_id,
            lexeme_translations.c.translation_id,
            lexeme_translations.c.notes,
        ).where(
            or_(
                lexeme_translations.c.lexeme_id == lexeme_id,
                lexeme_translations.c.translation_id == lexeme_id,
            )
        )
    ).fetchall()

    other_ids = [
        r.translation_id if r.lexeme_id == lexeme_id else r.lexeme_id for r in rows
    ]
    return _build_links(db, other_ids, rows, TranslationLink)


def _build_links(
    db: Session,
    other_ids: list[UUID],
    rows: list,
    link_cls: type,
    *,
    nuance_key: str | None = None,
    antonym_type_key: str | None = None,
) -> list:
    if not other_ids:
        return []
    lexemes = {
        lx.id: lx for lx in db.query(Lexeme).filter(Lexeme.id.in_(other_ids)).all()
    }
    languages = {
        lang.id: lang
        for lang in db.query(Language)
        .filter(Language.id.in_({lx.language_id for lx in lexemes.values()}))
        .all()
    }

    out: list = []
    for row, other_id in zip(rows, other_ids):
        lx = lexemes.get(other_id)
        if not lx:
            continue
        kwargs = dict(
            id=lx.id,
            lemma=lx.lemma,
            language_id=lx.language_id,
            language_name=languages[lx.language_id].name if lx.language_id in languages else None,
            part_of_speech=lx.part_of_speech,
            notes=row.notes if "notes" in row._fields else None,
        )
        if nuance_key:
            kwargs["nuance"] = getattr(row, nuance_key)
        if antonym_type_key:
            kwargs["antonym_type"] = getattr(row, antonym_type_key)
        out.append(link_cls(**kwargs))
    return out


# ---------------------------------------------------------------------------
# Rhyme search
# ---------------------------------------------------------------------------


def find_rhymes(
    db: Session,
    word_form_id: UUID,
    *,
    near: bool = False,
    limit: int = 50,
) -> list[WordForm]:
    """
    Return WordForms in the same language whose `rhyme_key` matches the
    target's (or `near_rhyme_key` if `near=True`). Excludes the target form.
    """
    target = db.query(WordForm).filter(WordForm.id == word_form_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="WordForm not found")

    key = target.near_rhyme_key if near else target.rhyme_key
    if not key:
        return []

    target_lexeme = db.query(Lexeme).filter(Lexeme.id == target.lexeme_id).first()
    if not target_lexeme:
        return []

    key_column = WordForm.near_rhyme_key if near else WordForm.rhyme_key
    return (
        db.query(WordForm)
        .join(Lexeme, Lexeme.id == WordForm.lexeme_id)
        .filter(
            key_column == key,
            WordForm.id != word_form_id,
            Lexeme.language_id == target_lexeme.language_id,
        )
        .limit(limit)
        .all()
    )
