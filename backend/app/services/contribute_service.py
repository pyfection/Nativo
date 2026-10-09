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
- confirm_spelling (anyone): a word as an outside source (SourceSnippet)
  writes it, for its standard spelling; the source is shown and linked.
- translate_word / translate_text (anyone, from the languages they've said
  they speak): a word with no translation into this language yet; a short
  internal text, or an outside snippet, with no version in this language.
- review_addition (can_verify): a suggester's spelling variant or
  translation link for an existing entry.

Non-editors never change published entries directly: new entries land
pending review, and additions to existing ones (a spelling variant, a
translation link) become ChangeProposals that one reviewer settles.

The deck is computed at read time, like the learning path; nothing about it
is stored. Answers go through the existing endpoints (upload, link update,
verify/reject, vote, proposal review) where one exists; the rest live here.

define_word and confirm_spelling scan every published text / stored snippet
of the language per request. That's fine at today's corpus size; cache the
unknown-token index if it isn't.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable
from itertools import zip_longest
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select, union, union_all
from sqlalchemy.orm import Session, selectinload

from app.models.change_proposal import (
    REVIEWED_TYPES,
    ChangeProposal,
    ProposalStatus,
    ProposalType,
    ProposalVote,
)
from app.models.document import Document
from app.models.language import Language
from app.models.source_snippet import SourceSnippet
from app.models.text import DocumentType, Text, TextStatus
from app.models.text_word_link import TextWordLink, TextWordLinkStatus
from app.models.user import User
from app.models.user_language import UserLanguage
from app.models.word import (
    Lexeme,
    LexemeStatus,
    SpellingVariant,
    WordForm,
    lexeme_translations,
    word_form_audio,
)
from app.schemas.contribute import (
    ConfirmLinkTask,
    ConfirmSpellingTask,
    ContributeResult,
    DefineWordAnswer,
    DefineWordResult,
    DefineWordTask,
    RecordAudioTask,
    ReviewAdditionTask,
    ReviewWordTask,
    SourceContext,
    SourceTextCreate,
    SpellingAnswer,
    TextContext,
    TranslateTextAnswer,
    TranslateTextTask,
    TranslateWordAnswer,
    TranslateWordTask,
    VoteTask,
)
from app.schemas.word import (
    LexemeCreate,
    TranslationCreate,
    WordFormCreate,
    WordFormCreateNested,
)
from app.services import lexeme_service, proposal_service, source_service, spelling_service
from app.services.auth_service import (
    can_user_edit_language,
    can_user_verify_language,
    require_language_edit_permission,
)
from app.services.document_service import suggest_links_for_text
from app.utils.text_normalize import fold_for_match, iter_tokens

# Characters of context either side of the word on a card.
SNIPPET_RADIUS = 60

# Texts offered for translation: short enough for one sitting.
MAX_TRANSLATE_CHARS = 1000

# Running prose worth translating (not lexeme definitions, notes, or the
# writing standard).
CORPUS_TYPES = (
    DocumentType.STORY,
    DocumentType.HISTORICAL_RECORD,
    DocumentType.BOOK,
    DocumentType.ARTICLE,
    DocumentType.TRANSCRIPTION,
    DocumentType.OTHER,
)


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


def _excerpt(content: str, start: int, end: int) -> tuple[str, int, int]:
    """A word-boundary excerpt around content[start:end], with the word's
    offsets inside it."""
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
    return f"{prefix}{content[lo:hi]}{suffix}", start + offset, end + offset


def _context(text: Text, start: int, end: int) -> TextContext:
    snippet, hl_start, hl_end = _excerpt(text.content or "", start, end)
    return TextContext(
        text_id=text.id,
        document_id=text.document_id,
        title=text.title,
        snippet=snippet,
        highlight_start=hl_start,
        highlight_end=hl_end,
    )


def _source_context(snippet: SourceSnippet, start: int, end: int) -> SourceContext:
    excerpt, hl_start, hl_end = _excerpt(snippet.content, start, end)
    return SourceContext(
        snippet_id=snippet.id,
        snippet=excerpt,
        highlight_start=hl_start,
        highlight_end=hl_end,
        source_url=snippet.source_url,
        source_title=snippet.source_title,
        license=snippet.license,
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
    # Spellings already proposed and waiting for a reviewer.
    for proposal in db.query(ChangeProposal).filter(
        ChangeProposal.language_id == language_id,
        ChangeProposal.proposal_type == ProposalType.ADD_SPELLING_VARIANT,
        ChangeProposal.status == ProposalStatus.OPEN,
    ):
        known.add(fold_for_match(proposal.payload.get("variant", "")))
    return known


def _rank_unknown(sources, known: set[str], skip: set[str], limit: int):
    """Unknown tokens across `sources` — (owner, content, covered spans)
    triples — most frequent first, as (folded, shown spelling, count, owner,
    start, end) of its first occurrence."""
    counts: Counter[str] = Counter()
    spellings: dict[str, Counter[str]] = {}
    first_seen: dict[str, tuple[object, int, int]] = {}
    for owner, content, spans in sources:
        for token, start, end in iter_tokens(content):
            if any(ch.isdigit() for ch in token):
                continue
            folded = fold_for_match(token)
            if folded in known or folded in skip:
                continue
            if any(s <= start and end <= e for s, e in spans):
                continue
            counts[folded] += 1
            spellings.setdefault(folded, Counter())[token] += 1
            first_seen.setdefault(folded, (owner, start, end))

    ranked = []
    # most_common is stable, so ties keep first-appearance order.
    for folded, count in counts.most_common(limit):
        owner, start, end = first_seen[folded]
        # Show the commonest spelling; on a tie prefer lower case, since a
        # capital is often just the start of a sentence.
        token = max(spellings[folded].items(), key=lambda kv: (kv[1], kv[0] == kv[0].lower()))[0]
        ranked.append((folded, token, count, owner, start, end))
    return ranked


def define_word_tasks(
    db: Session, language_id: UUID, limit: int, skip: set[str], known: set[str]
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

    sources = ((text, text.content, linked.get(text.id, [])) for text in texts)
    return [
        DefineWordTask(
            key=_key("define_word", folded),
            token=token,
            occurrences=count,
            context=_context(text, start, end),
        )
        for folded, token, count, text, start, end in _rank_unknown(sources, known, skip, limit)
    ]


def confirm_spelling_tasks(
    db: Session, language_id: UUID, limit: int, skip: set[str], known: set[str]
) -> list[ConfirmSpellingTask]:
    snippets = (
        db.query(SourceSnippet)
        .filter(SourceSnippet.language_id == language_id)
        .order_by(SourceSnippet.created_at.asc())
        .all()
    )
    sources = ((snippet, snippet.content, []) for snippet in snippets)
    return [
        ConfirmSpellingTask(
            key=_key("confirm_spelling", folded),
            token=token,
            occurrences=count,
            source=_source_context(snippet, start, end),
        )
        for folded, token, count, snippet, start, end in _rank_unknown(sources, known, skip, limit)
    ]


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
            ChangeProposal.proposal_type == ProposalType.SET_RECOMMENDATION,
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


def review_addition_tasks(
    db: Session, user: User, language_id: UUID, limit: int, skip: set[str]
) -> list[ReviewAdditionTask]:
    rows = (
        db.query(ChangeProposal, User.username)
        .outerjoin(User, User.id == ChangeProposal.created_by_id)
        .filter(
            ChangeProposal.language_id == language_id,
            ChangeProposal.proposal_type.in_(REVIEWED_TYPES),
            ChangeProposal.status == ProposalStatus.OPEN,
            or_(ChangeProposal.created_by_id.is_(None), ChangeProposal.created_by_id != user.id),
            ChangeProposal.id.notin_(_uuids(skip)),
        )
        .order_by(ChangeProposal.created_at.asc())
        .limit(limit)
        .all()
    )
    tasks = []
    for proposal, username in rows:
        payload = proposal.payload
        task = ReviewAdditionTask(
            key=_key("review_addition", proposal.id),
            proposal_id=proposal.id,
            proposal_type=proposal.proposal_type.value,
            lexeme_id=proposal.lexeme_id,
            lemma=proposal.lexeme.lemma,
            creator_username=username,
        )
        if proposal.proposal_type == ProposalType.ADD_SPELLING_VARIANT:
            form = db.get(WordForm, UUID(payload["word_form_id"]))
            task.lemma = form.form if form else task.lemma
            task.variant = payload.get("variant")
            task.note = payload.get("note")
            task.fix_texts = bool(payload.get("fix_texts"))
        else:
            other = db.get(Lexeme, UUID(payload["other_lexeme_id"]))
            if other is None:
                continue
            task.other_lemma = other.lemma
            task.other_language_id = other.language_id
        tasks.append(task)
    return tasks


def spoken_languages(db: Session, user: User, language_id: UUID) -> list[UUID]:
    """The other languages the user has said they speak (their memberships)."""
    return [
        lang_id
        for (lang_id,) in db.query(UserLanguage.language_id).filter(
            UserLanguage.user_id == user.id, UserLanguage.language_id != language_id
        )
    ]


def translate_word_tasks(
    db: Session, language_id: UUID, spoken: list[UUID], limit: int, skip: set[str]
) -> list[TranslateWordTask]:
    """Published words in the user's languages with no translation into this
    one, best-connected (most translated elsewhere) first."""
    t = lexeme_translations
    in_target = select(Lexeme.id).where(
        Lexeme.language_id == language_id, Lexeme.status != LexemeStatus.ARCHIVED
    )
    linked = union(
        select(t.c.lexeme_id).where(t.c.translation_id.in_(in_target)),
        select(t.c.translation_id).where(t.c.lexeme_id.in_(in_target)),
    )
    proposed = {
        UUID(p.payload["other_lexeme_id"])
        for p in db.query(ChangeProposal).filter(
            ChangeProposal.language_id == language_id,
            ChangeProposal.proposal_type == ProposalType.ADD_TRANSLATION,
            ChangeProposal.status == ProposalStatus.OPEN,
        )
    }
    ends = union_all(
        select(t.c.lexeme_id.label("lid")), select(t.c.translation_id.label("lid"))
    ).subquery()
    counts = select(ends.c.lid, func.count().label("n")).group_by(ends.c.lid).subquery()
    n = func.coalesce(counts.c.n, 0)
    rows = (
        db.query(Lexeme)
        .outerjoin(counts, counts.c.lid == Lexeme.id)
        .filter(
            Lexeme.language_id.in_(spoken),
            Lexeme.status == LexemeStatus.PUBLISHED,
            Lexeme.id.notin_(linked),
            Lexeme.id.notin_(proposed | _uuids(skip)),
        )
        .order_by(n.desc(), Lexeme.lemma.asc())
        .limit(limit)
        .all()
    )
    translations = lexeme_service.translations_for(db, [lexeme.id for lexeme in rows])
    return [
        TranslateWordTask(
            key=_key("translate_word", lexeme.id),
            source_lexeme_id=lexeme.id,
            lemma=lexeme.lemma,
            source_language_id=lexeme.language_id,
            part_of_speech=lexeme.part_of_speech,
            translations=translations[lexeme.id],
        )
        for lexeme in rows
    ]


def translate_text_tasks(
    db: Session, language_id: UUID, spoken: list[UUID], limit: int, skip: set[str]
) -> list[TranslateTextTask]:
    """Short texts in the user's languages with no version in this one —
    internal documents (shortest first) alternating with outside snippets."""
    skip_texts = _uuids(key[len("text:") :] for key in skip if key.startswith("text:"))
    skip_snippets = _uuids(key[len("snippet:") :] for key in skip if key.startswith("snippet:"))
    translated = select(Text.document_id).where(
        Text.language_id == language_id,
        Text.status != TextStatus.ARCHIVED,
        Text.document_id.isnot(None),
    )
    texts = (
        db.query(Text)
        .filter(
            Text.language_id.in_(spoken),
            Text.status == TextStatus.PUBLISHED,
            Text.document_type.in_(CORPUS_TYPES),
            Text.document_id.isnot(None),
            Text.document_id.notin_(translated),
            func.length(Text.content) <= MAX_TRANSLATE_CHARS,
            Text.id.notin_(skip_texts),
        )
        .order_by(func.length(Text.content).asc(), Text.created_at.asc())
        .limit(limit * 2)
        .all()
    )
    internal, documents = [], set()
    for text in texts:
        if text.document_id in documents:
            continue  # one card per document, from its shortest version
        documents.add(text.document_id)
        internal.append(
            TranslateTextTask(
                key=_key("translate_text", f"text:{text.id}"),
                source_language_id=text.language_id,
                title=text.title,
                content=text.content,
                text_id=text.id,
                document_id=text.document_id,
            )
        )
    snippets = (
        db.query(SourceSnippet)
        .filter(
            SourceSnippet.language_id.in_(spoken),
            SourceSnippet.document_id.is_(None),
            SourceSnippet.id.notin_(skip_snippets),
        )
        .order_by(SourceSnippet.created_at.asc())
        .limit(limit)
        .all()
    )
    external = [
        TranslateTextTask(
            key=_key("translate_text", f"snippet:{snippet.id}"),
            source_language_id=snippet.language_id,
            title=snippet.source_title,
            content=snippet.content,
            snippet_id=snippet.id,
            source_url=snippet.source_url,
            license=snippet.license,
        )
        for snippet in snippets
    ]
    mixed = [task for pair in zip_longest(internal, external) for task in pair if task]
    return mixed[:limit]


def build_deck(
    db: Session, user: User, language_id: UUID, *, limit: int, exclude: Iterable[str] = ()
) -> list:
    """Up to `limit` tasks the user may act on, interleaved across kinds so
    the deck stays varied."""
    exclude = list(exclude)
    can_edit = can_user_edit_language(db, user.id, language_id)
    can_verify = can_user_verify_language(db, user.id, language_id)

    known = _known_spellings(db, language_id)
    spoken = spoken_languages(db, user, language_id)

    pools: list[list] = []
    if can_verify:
        pools.append(
            review_word_tasks(db, user, language_id, limit, _excluded(exclude, "review_word"))
        )
        pools.append(
            review_addition_tasks(
                db, user, language_id, limit, _excluded(exclude, "review_addition")
            )
        )
    if can_edit or can_verify:
        pools.append(vote_tasks(db, user, language_id, limit, _excluded(exclude, "vote")))
    if can_edit:
        pools.append(confirm_link_tasks(db, language_id, limit, _excluded(exclude, "confirm_link")))
        pools.append(record_audio_tasks(db, language_id, limit, _excluded(exclude, "record_audio")))
    define = define_word_tasks(db, language_id, limit, _excluded(exclude, "define_word"), known)
    pools.append(define)
    # A word unknown in our own texts gets the define card, not both.
    defined = {task.key.split(":", 1)[1] for task in define}
    pools.append(
        [
            task
            for task in confirm_spelling_tasks(
                db, language_id, limit, _excluded(exclude, "confirm_spelling"), known
            )
            if task.key.split(":", 1)[1] not in defined
        ]
    )
    if spoken:
        pools.append(
            translate_word_tasks(
                db, language_id, spoken, limit, _excluded(exclude, "translate_word")
            )
        )
        pools.append(
            translate_text_tasks(
                db, language_id, spoken, limit, _excluded(exclude, "translate_text")
            )
        )

    deck = [task for row in zip_longest(*pools) for task in row if task is not None]
    return deck[:limit]


# ---------------------------------------------------------------------------
# Answers
# ---------------------------------------------------------------------------


def _require_language(db: Session, language_id: UUID) -> None:
    if db.get(Language, language_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")


def _check_gloss(db: Session, language_id: UUID, gloss: str, gloss_language_id: UUID | None):
    if not gloss:
        return
    if gloss_language_id is None or gloss_language_id == language_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A meaning needs another language to be written in",
        )
    if db.get(Language, gloss_language_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Meaning language not found"
        )


def _live_lexeme(db: Session, language_id: UUID, lemma: str) -> Lexeme | None:
    return (
        db.query(Lexeme)
        .filter(
            Lexeme.language_id == language_id,
            func.lower(Lexeme.lemma) == lemma.lower(),
            Lexeme.status != LexemeStatus.ARCHIVED,
        )
        .first()
    )


def _live_form(db: Session, language_id: UUID, spelling: str) -> WordForm | None:
    """The dictionary's form spelled this way (published, lemma forms first)."""
    folded = fold_for_match(spelling)
    forms = [
        form
        for form in db.query(WordForm)
        .join(Lexeme, Lexeme.id == WordForm.lexeme_id)
        .filter(
            Lexeme.language_id == language_id,
            Lexeme.status != LexemeStatus.ARCHIVED,
            func.lower(WordForm.form) == spelling.lower(),
        )
        if fold_for_match(form.form) == folded
    ]
    forms.sort(key=lambda f: (f.lexeme.status != LexemeStatus.PUBLISHED, not f.is_lemma))
    return forms[0] if forms else None


def _translation_exists(db: Session, a: UUID, b: UUID) -> bool:
    low, high = lexeme_service._ordered_pair(a, b)
    return (
        db.execute(
            select(lexeme_translations).where(
                and_(
                    lexeme_translations.c.lexeme_id == low,
                    lexeme_translations.c.translation_id == high,
                )
            )
        ).first()
        is not None
    )


def _new_lexeme(
    db: Session,
    user: User,
    language_id: UUID,
    lemma: str,
    part_of_speech,
    *,
    publish: bool,
    source=None,
) -> Lexeme:
    return lexeme_service.create_lexeme(
        db,
        LexemeCreate(
            language_id=language_id,
            lemma=lemma,
            part_of_speech=part_of_speech,
            source=source,
            lemma_form=WordFormCreateNested(form=lemma),
        ),
        creator_id=user.id,
        status=LexemeStatus.PUBLISHED if publish else LexemeStatus.PENDING_REVIEW,
    )


def _add_glosses(
    db: Session, lexeme: Lexeme, language_id: UUID, gloss: str, user_id: UUID, *, publish: bool
) -> None:
    """Link each comma-separated meaning as its own word in the gloss
    language ("there is, there are" → two entries). Does not commit."""
    meanings = {}
    for meaning in re.split(r"[,;]", gloss):
        meaning = " ".join(meaning.split())
        if meaning:
            meanings.setdefault(meaning.casefold(), meaning)
    for meaning in meanings.values():
        lexeme_service.add_gloss(db, lexeme, language_id, meaning, user_id, publish=publish)


SPELLING_FIX_NOTE = "Older spelling"


def _record_spelling_fix(
    db: Session, user: User, language_id: UUID, form: WordForm, seen: str, *, can_edit: bool
) -> str:
    """`seen` is a misspelling of `form`: an editor records it as a variant
    and corrects it in the texts now; anyone else proposes both for one
    reviewer. Returns the outcome. Does not commit."""
    if not can_edit:
        proposal_service.propose_addition(
            db,
            language_id=language_id,
            lexeme_id=form.lexeme_id,
            proposal_type=ProposalType.ADD_SPELLING_VARIANT,
            payload={
                "word_form_id": str(form.id),
                "variant": seen,
                "note": SPELLING_FIX_NOTE,
                "fix_texts": True,
            },
            author=user,
        )
        return "proposed"
    recorded = db.query(SpellingVariant.id).filter(
        SpellingVariant.word_form_id == form.id,
        SpellingVariant.normalized == fold_for_match(seen),
    )
    if recorded.first() is None:
        db.add(
            SpellingVariant(
                word_form_id=form.id, variant=seen, note=SPELLING_FIX_NOTE, created_by_id=user.id
            )
        )
        db.flush()
    spelling_service.correct_texts(db, language_id, seen, form.form, user_id=user.id)
    return "published"


def define_word(
    db: Session, user: User, language_id: UUID, answer: DefineWordAnswer
) -> DefineWordResult:
    """Add the word from a define_word card, with its gloss.

    Editors publish directly; anyone else's word (and a new gloss entry for
    it) lands pending review. When the citation form the user typed is
    already in the dictionary, an editor's answer adds the token seen in the
    text as another form of that entry instead of duplicating it.

    With `corrected`, the text misspells the word: the corrected spelling is
    the word, and the text's spelling becomes its spelling variant and is
    corrected in the texts (see _record_spelling_fix). If the corrected
    spelling is already in the dictionary, that fix is the whole answer.
    """
    _require_language(db, language_id)

    lemma = answer.lemma.strip()
    token = (answer.token or "").strip()
    corrected = (answer.corrected or "").strip()
    gloss = (answer.gloss or "").strip()
    seen = None
    if corrected and fold_for_match(corrected) != fold_for_match(token):
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Say which spelling is being corrected",
            )
        seen, token = token, corrected
    if not lemma:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The word is empty")

    can_edit = can_user_edit_language(db, user.id, language_id)

    if seen is not None:
        known_form = _live_form(db, language_id, token)
        if known_form is not None:
            outcome = _record_spelling_fix(
                db, user, language_id, known_form, seen, can_edit=can_edit
            )
            db.commit()
            lexeme = known_form.lexeme
            return DefineWordResult(lexeme_id=lexeme.id, status=lexeme.status, outcome=outcome)

    _check_gloss(db, language_id, gloss, answer.gloss_language_id)
    new_form = token and fold_for_match(token) != fold_for_match(lemma)

    existing = _live_lexeme(db, language_id, lemma)
    if existing is not None:
        if not (can_edit and new_form):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"“{existing.lemma}” is already in the dictionary",
            )
        form = lexeme_service.create_word_form(
            db, WordFormCreate(lexeme_id=existing.id, form=token)
        )
        if seen is not None:
            _record_spelling_fix(db, user, language_id, form, seen, can_edit=can_edit)
            db.commit()
        db.refresh(existing)
        return DefineWordResult(lexeme_id=existing.id, status=existing.status)

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
        _add_glosses(db, lexeme, answer.gloss_language_id, gloss, user.id, publish=can_edit)
    if seen is not None:
        form = next(f for f in lexeme.forms if fold_for_match(f.form) == fold_for_match(token))
        _record_spelling_fix(db, user, language_id, form, seen, can_edit=can_edit)
    db.commit()
    db.refresh(lexeme)
    return DefineWordResult(
        lexeme_id=lexeme.id,
        status=lexeme.status,
        outcome="published" if can_edit else "suggested",
    )


def confirm_spelling(
    db: Session, user: User, language_id: UUID, answer: SpellingAnswer
) -> ContributeResult:
    """Record how an outside source spells a word.

    If the standard spelling is in the dictionary, the source's spelling
    becomes one of its spelling variants (an editor adds it; anyone else
    proposes it for a reviewer). Otherwise the standard spelling is a new
    word (published or pending, like define_word) with the source's spelling
    recorded as its variant.
    """
    _require_language(db, language_id)
    token, standard = answer.token.strip(), answer.standard.strip()
    gloss = (answer.gloss or "").strip()
    if not token or not standard:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The word is empty")
    _check_gloss(db, language_id, gloss, answer.gloss_language_id)

    snippet = None
    if answer.snippet_id is not None:
        snippet = db.get(SourceSnippet, answer.snippet_id)
        if snippet is None or snippet.language_id != language_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    note = f"Seen in {snippet.source_title}: {snippet.source_url}"[:500] if snippet else None

    can_edit = can_user_edit_language(db, user.id, language_id)
    same = fold_for_match(token) == fold_for_match(standard)

    form = _live_form(db, language_id, standard)
    if form is not None:
        if same:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"“{form.form}” is already in the dictionary",
            )
        recorded = db.query(SpellingVariant.id).filter(
            SpellingVariant.word_form_id == form.id,
            SpellingVariant.normalized == fold_for_match(token),
        )
        if recorded.first() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"“{token}” is already recorded as a spelling of “{form.form}”",
            )
        if can_edit:
            db.add(
                SpellingVariant(
                    word_form_id=form.id, variant=token, note=note, created_by_id=user.id
                )
            )
            db.commit()
            return ContributeResult(outcome="published", lexeme_id=form.lexeme_id)
        proposal_service.propose_addition(
            db,
            language_id=language_id,
            lexeme_id=form.lexeme_id,
            proposal_type=ProposalType.ADD_SPELLING_VARIANT,
            payload={"word_form_id": str(form.id), "variant": token, "note": note},
            author=user,
        )
        db.commit()
        return ContributeResult(outcome="proposed", lexeme_id=form.lexeme_id)

    lexeme = _new_lexeme(
        db,
        user,
        language_id,
        standard,
        answer.part_of_speech,
        publish=can_edit,
        source=snippet.source_url[:500] if snippet else None,
    )
    if not same:
        lemma_form = next(f for f in lexeme.forms if f.is_lemma)
        db.add(
            SpellingVariant(
                word_form_id=lemma_form.id, variant=token, note=note, created_by_id=user.id
            )
        )
    if gloss:
        _add_glosses(db, lexeme, answer.gloss_language_id, gloss, user.id, publish=can_edit)
    db.commit()
    return ContributeResult(outcome="published" if can_edit else "suggested", lexeme_id=lexeme.id)


def translate_word(
    db: Session, user: User, language_id: UUID, answer: TranslateWordAnswer
) -> ContributeResult:
    """Link a word from another language to its translation here: an
    existing entry (editors link it, others propose the link) or a new one
    (published or pending)."""
    _require_language(db, language_id)
    source = db.get(Lexeme, answer.source_lexeme_id)
    if source is None or source.status != LexemeStatus.PUBLISHED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")
    if source.language_id == language_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Translation must be in a different language",
        )
    lemma = answer.lemma.strip()
    if not lemma:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The word is empty")

    can_edit = can_user_edit_language(db, user.id, language_id)
    existing = _live_lexeme(db, language_id, lemma)
    if existing is not None:
        if _translation_exists(db, existing.id, source.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"“{existing.lemma}” is already a translation of “{source.lemma}”",
            )
        if can_edit:
            lexeme_service.add_translation(
                db, existing.id, TranslationCreate(other_lexeme_id=source.id), user.id
            )
            return ContributeResult(outcome="published", lexeme_id=existing.id)
        proposal_service.propose_addition(
            db,
            language_id=language_id,
            lexeme_id=existing.id,
            proposal_type=ProposalType.ADD_TRANSLATION,
            payload={"other_lexeme_id": str(source.id)},
            author=user,
        )
        db.commit()
        return ContributeResult(outcome="proposed", lexeme_id=existing.id)

    lexeme = _new_lexeme(db, user, language_id, lemma, answer.part_of_speech, publish=can_edit)
    lexeme_service.add_translation(
        db, lexeme.id, TranslationCreate(other_lexeme_id=source.id), user.id
    )
    return ContributeResult(outcome="published" if can_edit else "suggested", lexeme_id=lexeme.id)


def _has_version_in(db: Session, document_id: UUID, language_id: UUID) -> bool:
    return (
        db.query(Text.id)
        .filter(
            Text.document_id == document_id,
            Text.language_id == language_id,
            Text.status != TextStatus.ARCHIVED,
        )
        .first()
        is not None
    )


def translate_text(
    db: Session, user: User, language_id: UUID, answer: TranslateTextAnswer
) -> ContributeResult:
    """Add a translation of an internal text, or of an outside snippet.

    A snippet's first translation turns it into a Document: the snippet
    itself becomes the published original (credited to its source — it was
    vetted when an editor added the source) and the translation is added
    beside it. Like any translation, it's published for editors of this
    language and pending review for everyone else.
    """
    _require_language(db, language_id)
    if (answer.text_id is None) == (answer.snippet_id is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Translate either a text or a source snippet",
        )
    content = answer.content.strip()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="The translation is empty"
        )
    can_edit = can_user_edit_language(db, user.id, language_id)

    if answer.text_id is not None:
        source = db.get(Text, answer.text_id)
        if source is None or source.status != TextStatus.PUBLISHED or source.document_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Text not found")
        if source.language_id == language_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Translation must be in a different language",
            )
        document_id, title, document_type = source.document_id, source.title, source.document_type
    else:
        snippet = db.get(SourceSnippet, answer.snippet_id)
        if snippet is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
        if snippet.language_id == language_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Translation must be in a different language",
            )
        if snippet.document_id is None:
            document = Document(created_by_id=user.id)
            db.add(document)
            db.flush()
            original = Text(
                title=snippet.source_title,
                content=snippet.content,
                document_type=DocumentType.ARTICLE,
                language_id=snippet.language_id,
                document_id=document.id,
                is_primary=True,
                source=snippet.source_url[:500],
                notes=f"Licence: {snippet.license}" if snippet.license else None,
                created_by_id=user.id,
                status=TextStatus.PUBLISHED,
            )
            db.add(original)
            db.flush()
            suggest_links_for_text(db, original, creator_id=user.id)
            snippet.document_id = document.id
        document_id, title, document_type = (
            snippet.document_id,
            snippet.source_title,
            DocumentType.ARTICLE,
        )

    if _has_version_in(db, document_id, language_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This text already has a version in this language",
        )
    translation = Text(
        title=((answer.title or "").strip() or title)[:500],
        content=content,
        document_type=document_type,
        language_id=language_id,
        document_id=document_id,
        created_by_id=user.id,
        status=TextStatus.PUBLISHED if can_edit else TextStatus.PENDING_REVIEW,
    )
    db.add(translation)
    db.flush()
    suggest_links_for_text(db, translation, creator_id=user.id)
    db.commit()
    return ContributeResult(
        outcome="published" if can_edit else "suggested", document_id=document_id
    )


def add_source_text(db: Session, user: User, language_id: UUID, data: SourceTextCreate) -> int:
    """Store an outside text as snippets (editors of its language only)."""
    _require_language(db, language_id)
    require_language_edit_permission(db, user, language_id)
    created = source_service.add_text(
        db,
        language_id,
        source_url=data.source_url.strip(),
        source_title=data.source_title.strip(),
        text=data.text,
        license=data.license,
        creator_id=user.id,
    )
    db.commit()
    return len(created)
