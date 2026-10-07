"""
Quick Contribute: a deck of small tasks built from a language's data gaps.

Every card is something the platform is missing and one person can fill in
seconds, and the deck only deals cards the user is allowed to act on:

- define_word (anyone signed in): a word used in published texts that no
  dictionary entry matches, most frequent first. Editors' answers publish;
  everyone else's land as suggestions for review, with a drafted gloss.
- record_audio (can_edit): a published word with no recording, most-used
  first.
- confirm_link (can_edit): a suggested text-to-word link (homograph picks and
  spelling-variant matches the linker couldn't auto-confirm).
- review_word (can_verify): someone else's pending word suggestion.
- vote (can_edit or can_verify): an open proposal the user hasn't voted on.

The deck is computed at read time, like the learning path; nothing about it
is stored. Answers go through the existing endpoints (upload, link update,
verify/reject, vote), except define_word, which needs word + gloss in one
step and lives here.

define_word scans every published text of the language per request. That's
fine at today's corpus size; cache the unknown-token index if it isn't.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from itertools import zip_longest
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.change_proposal import ChangeProposal, ProposalStatus, ProposalVote
from app.models.language import Language
from app.models.text import DocumentType, Text, TextStatus
from app.models.text_word_link import TextWordLink, TextWordLinkStatus
from app.models.user import User
from app.models.word import Lexeme, LexemeStatus, SpellingVariant, WordForm, word_form_audio
from app.schemas.contribute import (
    ConfirmLinkTask,
    DefineWordAnswer,
    DefineWordTask,
    RecordAudioTask,
    ReviewWordTask,
    TextContext,
    VoteTask,
)
from app.schemas.word import LexemeCreate, WordFormCreate, WordFormCreateNested
from app.services import lexeme_service, proposal_service
from app.services.auth_service import can_user_edit_language, can_user_verify_language
from app.utils.text_normalize import fold_for_match, iter_tokens

# Characters of context either side of the word on a card.
SNIPPET_RADIUS = 60


def _key(kind: str, ident: object) -> str:
    return f"{kind}:{ident}"


def _excluded(exclude: Iterable[str], kind: str) -> set[str]:
    prefix = f"{kind}:"
    return {key[len(prefix) :] for key in exclude if key.startswith(prefix)}


def _uuids(values: Iterable[str]) -> set[UUID]:
    out = set()
    for value in values:
        try:
            out.add(UUID(value))
        except ValueError:
            continue
    return out


def _context(text: Text, start: int, end: int) -> TextContext:
    """A word-boundary excerpt around content[start:end]."""
    content = text.content or ""
    lo = max(0, start - SNIPPET_RADIUS)
    hi = min(len(content), end + SNIPPET_RADIUS)
    if lo > 0:
        cut = content.find(" ", lo, start)
        lo = cut + 1 if cut != -1 else lo
    if hi < len(content):
        cut = content.rfind(" ", end, hi)
        hi = cut if cut != -1 else hi
    prefix = "…" if lo > 0 else ""
    suffix = "…" if hi < len(content) else ""
    offset = len(prefix) - lo
    return TextContext(
        text_id=text.id,
        document_id=text.document_id,
        title=text.title,
        snippet=f"{prefix}{content[lo:hi]}{suffix}",
        highlight_start=start + offset,
        highlight_end=end + offset,
    )


# ---------------------------------------------------------------------------
# Task sources
# ---------------------------------------------------------------------------


def _known_spellings(db: Session, language_id: UUID) -> set[str]:
    """Folded spellings the dictionary already has (any live entry,
    suggestions included, so a word isn't suggested twice)."""
    live = Lexeme.status != LexemeStatus.ARCHIVED
    known: set[str] = set()
    for form, romanization in (
        db.query(WordForm.form, WordForm.romanization)
        .join(Lexeme, Lexeme.id == WordForm.lexeme_id)
        .filter(Lexeme.language_id == language_id, live)
    ):
        known.add(fold_for_match(form))
        if romanization:
            known.add(fold_for_match(romanization))
    for (normalized,) in (
        db.query(SpellingVariant.normalized)
        .join(WordForm, WordForm.id == SpellingVariant.word_form_id)
        .join(Lexeme, Lexeme.id == WordForm.lexeme_id)
        .filter(Lexeme.language_id == language_id, live)
    ):
        known.add(normalized)
    return known


def define_word_tasks(
    db: Session, language_id: UUID, limit: int, skip: set[str]
) -> list[DefineWordTask]:
    texts = (
        db.query(Text)
        .filter(
            Text.language_id == language_id,
            Text.status == TextStatus.PUBLISHED,
            # The writing standard quotes spellings on purpose, wrong ones too.
            Text.document_type != DocumentType.WRITING_STANDARD,
        )
        .order_by(Text.created_at.asc())
        .all()
    )
    if not texts:
        return []

    linked: dict[UUID, list[tuple[int, int]]] = {}
    for text_id, start, end in db.query(
        TextWordLink.text_id, TextWordLink.start_char, TextWordLink.end_char
    ).filter(
        TextWordLink.text_id.in_([t.id for t in texts]),
        TextWordLink.status != TextWordLinkStatus.REJECTED,
    ):
        linked.setdefault(text_id, []).append((start, end))

    known = _known_spellings(db, language_id)
    counts: Counter[str] = Counter()
    spellings: dict[str, Counter[str]] = {}
    first_seen: dict[str, tuple[Text, int, int]] = {}
    for text in texts:
        spans = linked.get(text.id, [])
        for token, start, end in iter_tokens(text.content):
            if any(ch.isdigit() for ch in token):
                continue
            folded = fold_for_match(token)
            if folded in known or folded in skip:
                continue
            if any(s <= start and end <= e for s, e in spans):
                continue
            counts[folded] += 1
            spellings.setdefault(folded, Counter())[token] += 1
            first_seen.setdefault(folded, (text, start, end))

    tasks = []
    # most_common is stable, so ties keep first-appearance order.
    for folded, count in counts.most_common(limit):
        text, start, end = first_seen[folded]
        # Show the commonest spelling; on a tie prefer lower case, since a
        # capital is often just the start of a sentence.
        token = max(spellings[folded].items(), key=lambda kv: (kv[1], kv[0] == kv[0].lower()))[0]
        tasks.append(
            DefineWordTask(
                key=_key("define_word", folded),
                token=token,
                occurrences=count,
                context=_context(text, start, end),
            )
        )
    return tasks


def record_audio_tasks(
    db: Session, language_id: UUID, limit: int, skip: set[str]
) -> list[RecordAudioTask]:
    uses = (
        select(WordForm.lexeme_id, func.count(TextWordLink.id).label("uses"))
        .join(TextWordLink, TextWordLink.word_form_id == WordForm.id)
        .where(TextWordLink.status == TextWordLinkStatus.CONFIRMED)
        .group_by(WordForm.lexeme_id)
        .subquery()
    )
    use_count = func.coalesce(uses.c.uses, 0)
    rows = (
        db.query(WordForm, Lexeme, use_count)
        .join(Lexeme, Lexeme.id == WordForm.lexeme_id)
        .outerjoin(uses, uses.c.lexeme_id == Lexeme.id)
        .filter(
            Lexeme.language_id == language_id,
            Lexeme.status == LexemeStatus.PUBLISHED,
            WordForm.is_lemma.is_(True),
            WordForm.id.notin_(select(word_form_audio.c.word_form_id)),
            WordForm.id.notin_(_uuids(skip)),
        )
        .order_by(use_count.desc(), Lexeme.lemma.asc())
        .limit(limit)
        .all()
    )
    translations = lexeme_service.translations_for(db, [lexeme.id for _, lexeme, _ in rows])
    return [
        RecordAudioTask(
            key=_key("record_audio", form.id),
            lexeme_id=lexeme.id,
            word_form_id=form.id,
            form=form.form,
            ipa_pronunciation=form.ipa_pronunciation,
            translations=translations[lexeme.id],
            uses=count,
        )
        for form, lexeme, count in rows
    ]


def confirm_link_tasks(
    db: Session, language_id: UUID, limit: int, skip: set[str]
) -> list[ConfirmLinkTask]:
    rows = (
        db.query(TextWordLink, Text, WordForm, Lexeme)
        .join(Text, Text.id == TextWordLink.text_id)
        .join(WordForm, WordForm.id == TextWordLink.word_form_id)
        .join(Lexeme, Lexeme.id == WordForm.lexeme_id)
        .filter(
            Text.language_id == language_id,
            Text.status == TextStatus.PUBLISHED,
            Lexeme.status == LexemeStatus.PUBLISHED,
            TextWordLink.status == TextWordLinkStatus.SUGGESTED,
            TextWordLink.id.notin_(_uuids(skip)),
        )
        .order_by(TextWordLink.confidence.desc().nulls_last(), TextWordLink.created_at.asc())
        .limit(limit)
        .all()
    )
    translations = lexeme_service.translations_for(db, list({lx.id for *_, lx in rows}))
    return [
        ConfirmLinkTask(
            key=_key("confirm_link", link.id),
            link_id=link.id,
            context=_context(text, link.start_char, link.end_char),
            lexeme_id=lexeme.id,
            word_form_id=form.id,
            form=form.form,
            lemma=lexeme.lemma,
            confidence=link.confidence,
            translations=translations[lexeme.id],
        )
        for link, text, form, lexeme in rows
    ]


def review_word_tasks(
    db: Session, user: User, language_id: UUID, limit: int, skip: set[str]
) -> list[ReviewWordTask]:
    rows = (
        db.query(Lexeme, User.username)
        .options(selectinload(Lexeme.forms))
        .outerjoin(User, User.id == Lexeme.created_by_id)
        .filter(
            Lexeme.language_id == language_id,
            Lexeme.status == LexemeStatus.PENDING_REVIEW,
            Lexeme.created_by_id != user.id,  # nobody reviews their own
            Lexeme.id.notin_(_uuids(skip)),
        )
        .order_by(Lexeme.created_at.asc())
        .limit(limit)
        .all()
    )
    translations = lexeme_service.translations_for(db, [lexeme.id for lexeme, _ in rows])
    tasks = []
    for lexeme, username in rows:
        lemma_form = next((f for f in lexeme.forms if f.is_lemma), None)
        tasks.append(
            ReviewWordTask(
                key=_key("review_word", lexeme.id),
                lexeme_id=lexeme.id,
                lemma=lexeme.lemma,
                part_of_speech=lexeme.part_of_speech,
                ipa_pronunciation=lemma_form.ipa_pronunciation if lemma_form else None,
                notes=lexeme.notes,
                creator_username=username,
                translations=translations[lexeme.id],
            )
        )
    return tasks


def vote_tasks(
    db: Session, user: User, language_id: UUID, limit: int, skip: set[str]
) -> list[VoteTask]:
    voted = select(ProposalVote.proposal_id).where(ProposalVote.user_id == user.id)
    proposals = (
        db.query(ChangeProposal)
        .filter(
            ChangeProposal.language_id == language_id,
            ChangeProposal.status == ProposalStatus.OPEN,
            ChangeProposal.id.notin_(voted),
            ChangeProposal.id.notin_(_uuids(skip)),
        )
        .order_by(ChangeProposal.created_at.asc())
        .limit(limit)
        .all()
    )
    return [
        VoteTask(key=_key("vote", p.id), proposal=proposal_service.to_schema(db, p))
        for p in proposals
    ]


def build_deck(
    db: Session, user: User, language_id: UUID, *, limit: int, exclude: Iterable[str] = ()
) -> list:
    """Up to `limit` tasks the user may act on, interleaved across kinds so
    the deck stays varied."""
    exclude = list(exclude)
    can_edit = can_user_edit_language(db, user.id, language_id)
    can_verify = can_user_verify_language(db, user.id, language_id)

    pools: list[list] = []
    if can_verify:
        pools.append(
            review_word_tasks(db, user, language_id, limit, _excluded(exclude, "review_word"))
        )
    if can_edit or can_verify:
        pools.append(vote_tasks(db, user, language_id, limit, _excluded(exclude, "vote")))
    if can_edit:
        pools.append(confirm_link_tasks(db, language_id, limit, _excluded(exclude, "confirm_link")))
        pools.append(record_audio_tasks(db, language_id, limit, _excluded(exclude, "record_audio")))
    pools.append(define_word_tasks(db, language_id, limit, _excluded(exclude, "define_word")))

    deck = [task for row in zip_longest(*pools) for task in row if task is not None]
    return deck[:limit]


# ---------------------------------------------------------------------------
# define_word answer
# ---------------------------------------------------------------------------


def define_word(db: Session, user: User, language_id: UUID, answer: DefineWordAnswer) -> Lexeme:
    """Add the word from a define_word card, with its gloss.

    Editors publish directly; anyone else's word (and a new gloss entry for
    it) lands pending review. When the citation form the user typed is
    already in the dictionary, an editor's answer adds the token seen in the
    text as another form of that entry instead of duplicating it.
    """
    if db.get(Language, language_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")

    lemma = answer.lemma.strip()
    token = (answer.token or "").strip()
    gloss = (answer.gloss or "").strip()
    if not lemma:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The word is empty")
    if gloss:
        if answer.gloss_language_id is None or answer.gloss_language_id == language_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A meaning needs another language to be written in",
            )
        if db.get(Language, answer.gloss_language_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Meaning language not found"
            )

    can_edit = can_user_edit_language(db, user.id, language_id)
    new_form = token and fold_for_match(token) != fold_for_match(lemma)

    existing = (
        db.query(Lexeme)
        .filter(
            Lexeme.language_id == language_id,
            func.lower(Lexeme.lemma) == lemma.lower(),
            Lexeme.status != LexemeStatus.ARCHIVED,
        )
        .first()
    )
    if existing is not None:
        if not (can_edit and new_form):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"“{existing.lemma}” is already in the dictionary",
            )
        lexeme_service.create_word_form(db, WordFormCreate(lexeme_id=existing.id, form=token))
        db.refresh(existing)
        return existing

    lexeme = lexeme_service.create_lexeme(
        db,
        LexemeCreate(
            language_id=language_id,
            lemma=lemma,
            part_of_speech=answer.part_of_speech,
            lemma_form=WordFormCreateNested(form=lemma),
            additional_forms=[WordFormCreateNested(form=token)] if new_form else None,
        ),
        creator_id=user.id,
        status=LexemeStatus.PUBLISHED if can_edit else LexemeStatus.PENDING_REVIEW,
    )
    if gloss:
        lexeme_service.add_gloss(
            db, lexeme, answer.gloss_language_id, gloss, user.id, publish=can_edit
        )
        db.commit()
        db.refresh(lexeme)
    return lexeme
