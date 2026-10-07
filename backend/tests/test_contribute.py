"""
Tests for Quick Contribute: the task deck and the define-word answer.

The contract under test:
- The deck only deals cards the user may act on: define_word for anyone,
  record_audio + confirm_link for editors, review_word for verifiers, vote
  for editors and verifiers.
- define_word cards are words used in published texts that no live entry
  (published or pending, spelling variants included) matches, most frequent
  first; linked spans, numbers, the writing standard and unpublished texts
  don't count.
- Skipped keys sent back as `exclude` stay out of the deck.
- Defining a word: editors publish it with its gloss; anyone else's lands
  pending with a drafted gloss that approval publishes too.
"""

import os
import uuid
from datetime import UTC, datetime

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

sqlalchemy = pytest.importorskip("sqlalchemy")
from app.api.v1.endpoints.contribute import define_word, get_tasks  # noqa: E402
from app.api.v1.endpoints.words import verify_lexeme  # noqa: E402
from app.database import Base  # noqa: E402
from app.models.audio import Audio  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.text import DocumentType, Text, TextStatus  # noqa: E402
from app.models.text_word_link import TextWordLink, TextWordLinkStatus  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.user_language import ProficiencyLevel, UserLanguage  # noqa: E402
from app.models.word import (  # noqa: E402
    Lexeme,
    LexemeRecommendation,
    LexemeStatus,
    SpellingVariant,
    WordForm,
    word_form_audio,
)
from app.schemas.contribute import DefineWordAnswer  # noqa: E402
from app.schemas.proposal import RecommendationProposalCreate  # noqa: E402
from app.services import contribute_service, lexeme_service, proposal_service  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

engine = create_engine("sqlite:///:memory:", future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


@pytest.fixture(autouse=True)
def database_schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _now() -> datetime:
    return datetime.now(UTC)


def _user(db: Session) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"u-{uuid.uuid4()}@example.com",
        username=f"user-{uuid.uuid4().hex[:8]}",
        hashed_password="x",
        role=UserRole.PUBLIC,
        is_active=True,
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(user)
    db.flush()
    return user


def _language(db: Session, name: str = "Bavarian") -> Language:
    lang = Language(
        id=uuid.uuid4(),
        name=f"{name}-{uuid.uuid4().hex[:6]}",
        proposal_approval_threshold=2,
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(lang)
    db.flush()
    return lang


def _member(db: Session, lang: Language, *, can_edit=False, can_verify=False) -> User:
    user = _user(db)
    db.add(
        UserLanguage(
            user_id=user.id,
            language_id=lang.id,
            proficiency_level=ProficiencyLevel.NATIVE,
            can_edit=can_edit,
            can_verify=can_verify,
        )
    )
    db.flush()
    return user


def _text(
    db: Session,
    lang: Language,
    author: User,
    content: str,
    *,
    status: TextStatus = TextStatus.PUBLISHED,
    document_type: DocumentType = DocumentType.STORY,
) -> Text:
    document = Document(id=uuid.uuid4(), created_by_id=author.id)
    db.add(document)
    db.flush()
    text = Text(
        id=uuid.uuid4(),
        title="Sample",
        content=content,
        document_type=document_type,
        status=status,
        language_id=lang.id,
        document_id=document.id,
        created_by_id=author.id,
    )
    db.add(text)
    db.flush()
    return text


def _word(
    db: Session, lang: Language, creator: User, lemma: str, status=LexemeStatus.PUBLISHED
) -> WordForm:
    lexeme = Lexeme(
        id=uuid.uuid4(), language_id=lang.id, lemma=lemma, created_by_id=creator.id, status=status
    )
    db.add(lexeme)
    db.flush()
    form = WordForm(id=uuid.uuid4(), lexeme_id=lexeme.id, form=lemma, is_lemma=True)
    db.add(form)
    db.flush()
    return form


def _link(db: Session, text: Text, form: WordForm, word: str, status, confidence=0.8):
    start = text.content.index(word)
    link = TextWordLink(
        text_id=text.id,
        word_form_id=form.id,
        start_char=start,
        end_char=start + len(word),
        status=status,
        confidence=confidence,
    )
    db.add(link)
    db.flush()
    return link


def _deck(db: Session, user: User, lang: Language, exclude=()):
    return contribute_service.build_deck(db, user, lang.id, limit=30, exclude=exclude)


def _types(deck) -> list[str]:
    return [task.type for task in deck]


# ---------------------------------------------------------------------------
# The deck
# ---------------------------------------------------------------------------


def test_suggester_only_gets_define_cards_most_frequent_first(db: Session):
    lang = _language(db)
    editor = _member(db, lang, can_edit=True)
    suggester = _member(db, lang)
    _word(db, lang, editor, "servus")
    _text(db, lang, editor, "Servus Oma. Da Hund und da Hund schlafa, 1990.")

    deck = _deck(db, suggester, lang)

    assert set(_types(deck)) == {"define_word"}
    tokens = [t.token for t in deck]
    assert tokens[:2] == ["da", "Hund"]  # two occurrences each, first-seen order
    assert "Servus" not in tokens  # already in the dictionary (case-folded)
    assert "1990" not in tokens
    hund = deck[1]
    assert hund.occurrences == 2
    ctx = hund.context
    assert ctx.snippet[ctx.highlight_start : ctx.highlight_end] == "Hund"


def test_define_cards_skip_known_linked_and_non_corpus_text(db: Session):
    lang = _language(db)
    editor = _member(db, lang, can_edit=True)
    pending = _word(db, lang, editor, "katz", status=LexemeStatus.PENDING_REVIEW)
    db.add(SpellingVariant(word_form_id=pending.id, variant="kaz", normalized="kaz"))
    archived = _word(db, lang, editor, "hoamat", status=LexemeStatus.ARCHIVED)
    text = _text(db, lang, editor, "katz kaz hoamat bua")
    _link(db, text, archived, "bua", TextWordLinkStatus.SUGGESTED)
    _text(db, lang, editor, "unpublisht", status=TextStatus.PENDING_REVIEW)
    _text(db, lang, editor, "standardwort", document_type=DocumentType.WRITING_STANDARD)

    tokens = [t.token for t in _deck(db, editor, lang) if t.type == "define_word"]

    # Archived entries don't count as known; a linked span does.
    assert tokens == ["hoamat"]


def test_editor_gets_audio_and_link_cards_but_not_reviews(db: Session):
    lang = _language(db)
    editor = _member(db, lang, can_edit=True)
    often = _word(db, lang, editor, "oft")
    rarely = _word(db, lang, editor, "selten")
    recorded = _word(db, lang, editor, "scho")
    _word(db, lang, editor, "vorschlag", status=LexemeStatus.PENDING_REVIEW)
    text = _text(db, lang, editor, "oft oft selten scho")
    first = text.content.index("oft")
    for start in (first, text.content.index("oft", first + 1)):
        db.add(
            TextWordLink(
                text_id=text.id,
                word_form_id=often.id,
                start_char=start,
                end_char=start + 3,
                status=TextWordLinkStatus.CONFIRMED,
            )
        )
    suggested = _link(db, text, rarely, "selten", TextWordLinkStatus.SUGGESTED)
    audio = Audio(id=uuid.uuid4(), file_path="/uploads/a.webm", uploaded_by_id=editor.id)
    db.add(audio)
    db.flush()
    db.execute(
        word_form_audio.insert().values(
            word_form_id=recorded.id, audio_id=audio.id, is_primary=True, created_at=_now()
        )
    )

    deck = _deck(db, editor, lang)

    assert "review_word" not in _types(deck)
    audio_cards = [t for t in deck if t.type == "record_audio"]
    assert [t.form for t in audio_cards] == ["oft", "selten"]  # most used first, recorded left out
    assert audio_cards[0].uses == 2
    link_cards = [t for t in deck if t.type == "confirm_link"]
    assert [t.link_id for t in link_cards] == [suggested.id]
    ctx = link_cards[0].context
    assert ctx.snippet[ctx.highlight_start : ctx.highlight_end] == "selten"


def test_verifier_reviews_others_suggestions_and_votes_once(db: Session):
    lang = _language(db)
    editor = _member(db, lang, can_edit=True)
    verifier = _member(db, lang, can_verify=True)
    suggester = _member(db, lang)
    theirs = _word(db, lang, suggester, "gfrei", status=LexemeStatus.PENDING_REVIEW)
    _word(db, lang, verifier, "mei", status=LexemeStatus.PENDING_REVIEW)
    target = _word(db, lang, editor, "semmel")
    proposal = proposal_service.propose_recommendation(
        db,
        db.get(Lexeme, target.lexeme_id),
        RecommendationProposalCreate(recommendation=LexemeRecommendation.PREFERRED),
        editor,
    )

    deck = _deck(db, verifier, lang)
    reviews = [t for t in deck if t.type == "review_word"]
    assert [t.lexeme_id for t in reviews] == [theirs.lexeme_id]
    assert reviews[0].creator_username == suggester.username
    votes = [t for t in deck if t.type == "vote"]
    assert [t.proposal.id for t in votes] == [proposal.id]

    # The author's proposal already counts as their vote.
    assert "vote" not in _types(_deck(db, editor, lang))


def test_deck_interleaves_kinds_and_honours_exclude(db: Session):
    lang = _language(db)
    editor = _member(db, lang, can_edit=True)
    _word(db, lang, editor, "oans")
    _word(db, lang, editor, "zwoa")
    _text(db, lang, editor, "drei vier")

    deck = _deck(db, editor, lang)
    assert _types(deck) == ["record_audio", "define_word", "record_audio", "define_word"]

    skipped = [deck[0].key, deck[1].key]
    rest = _deck(db, editor, lang, exclude=skipped)
    assert [t.key for t in rest] == [deck[2].key, deck[3].key]


async def test_tasks_endpoint_404s_on_unknown_language(db: Session):
    user = _user(db)
    with pytest.raises(HTTPException) as exc:
        get_tasks(uuid.uuid4(), limit=10, exclude=[], current_user=user, db=db)
    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# Defining a word
# ---------------------------------------------------------------------------


async def test_suggester_definition_lands_pending_with_drafted_gloss(db: Session):
    lang = _language(db)
    english = _language(db, "English")
    verifier = _member(db, lang, can_verify=True)
    suggester = _member(db, lang)

    result = define_word(
        lang.id,
        DefineWordAnswer(token="Hunde", lemma="Hund", gloss="dog", gloss_language_id=english.id),
        current_user=suggester,
        db=db,
    )

    assert result.status == LexemeStatus.PENDING_REVIEW
    lexeme = db.get(Lexeme, result.lexeme_id)
    assert sorted(f.form for f in lexeme.forms) == ["Hund", "Hunde"]  # token kept as a form
    [gloss] = lexeme_service._translation_partners(db, lexeme.id)
    assert (gloss.lemma, gloss.status) == ("dog", LexemeStatus.PENDING_REVIEW)

    # The new word now shows up in the reviewer's deck, and approving it
    # publishes the drafted gloss along with it.
    assert [t.lexeme_id for t in _deck(db, verifier, lang) if t.type == "review_word"] == [
        lexeme.id
    ]
    await verify_lexeme(lexeme.id, current_user=verifier, db=db)
    db.refresh(gloss)
    assert gloss.status == LexemeStatus.PUBLISHED


async def test_editor_definition_publishes_and_reuses_existing_gloss(db: Session):
    lang = _language(db)
    english = _language(db, "English")
    editor = _member(db, lang, can_edit=True)
    dog = _word(db, english, editor, "dog")

    result = define_word(
        lang.id,
        DefineWordAnswer(token="hund", lemma="Hund", gloss="dog", gloss_language_id=english.id),
        current_user=editor,
        db=db,
    )

    assert result.status == LexemeStatus.PUBLISHED
    lexeme = db.get(Lexeme, result.lexeme_id)
    assert [f.form for f in lexeme.forms] == ["Hund"]  # same word up to case: no extra form
    assert [g.id for g in lexeme_service._translation_partners(db, lexeme.id)] == [dog.lexeme_id]


async def test_known_lemma_adds_editor_form_but_conflicts_for_suggester(db: Session):
    lang = _language(db)
    editor = _member(db, lang, can_edit=True)
    suggester = _member(db, lang)
    form = _word(db, lang, editor, "sagn")

    with pytest.raises(HTTPException) as exc:
        define_word(
            lang.id, DefineWordAnswer(token="gsagt", lemma="sagn"), current_user=suggester, db=db
        )
    assert exc.value.status_code == 409

    result = define_word(
        lang.id, DefineWordAnswer(token="gsagt", lemma="sagn"), current_user=editor, db=db
    )
    assert result.lexeme_id == form.lexeme_id
    forms = db.query(WordForm).filter(WordForm.lexeme_id == form.lexeme_id).all()
    assert sorted(f.form for f in forms) == ["gsagt", "sagn"]


async def test_gloss_must_be_in_another_language(db: Session):
    lang = _language(db)
    editor = _member(db, lang, can_edit=True)
    with pytest.raises(HTTPException) as exc:
        define_word(
            lang.id,
            DefineWordAnswer(lemma="Hund", gloss="Hund", gloss_language_id=lang.id),
            current_user=editor,
            db=db,
        )
    assert exc.value.status_code == 400
