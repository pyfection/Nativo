"""
Tests for Quick Contribute's outside-source and translation cards.

The contract under test:
- Outside text is stored as sentence snippets (editors of the language only,
  duplicates skipped).
- confirm_spelling cards show unknown words from same-language snippets
  (with the source), and a word unknown in our own texts gets only the
  define card.
- Answering: a known standard spelling gains the source's spelling as a
  variant — directly for editors, as a proposal one reviewer settles for
  everyone else; an unknown one becomes a new word carrying the variant.
- translate_word / translate_text cards only come from languages the user
  has joined; words already translated (or proposed) and documents that
  already have a version in this language are left out.
- Translating a snippet turns it into a Document (published original +
  translation, pending for non-editors).
- Reviewed additions can't be voted on and never show up as vote cards.
"""

import os
import uuid
from datetime import UTC, datetime

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

sqlalchemy = pytest.importorskip("sqlalchemy")
from app.api.v1.endpoints.contribute import (  # noqa: E402
    add_source_text,
    confirm_spelling,
    translate_text,
    translate_word,
)
from app.api.v1.endpoints.proposals import review, vote  # noqa: E402
from app.database import Base  # noqa: E402
from app.models.change_proposal import ChangeProposal, ProposalStatus, ProposalType  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.source_snippet import SourceSnippet  # noqa: E402
from app.models.text import DocumentType, Text, TextStatus  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.user_language import ProficiencyLevel, UserLanguage  # noqa: E402
from app.models.word import Lexeme, LexemeStatus, SpellingVariant, WordForm  # noqa: E402
from app.schemas.contribute import (  # noqa: E402
    SourceTextCreate,
    SpellingAnswer,
    TranslateTextAnswer,
    TranslateWordAnswer,
)
from app.schemas.proposal import AdditionReview, VoteCreate  # noqa: E402
from app.services import contribute_service, lexeme_service, source_service  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

engine = create_engine("sqlite:///:memory:", future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)

URL = "https://bar.wikipedia.org/wiki/Minga"


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


def _language(db: Session, name: str) -> Language:
    lang = Language(id=uuid.uuid4(), name=f"{name}-{uuid.uuid4().hex[:6]}")
    db.add(lang)
    db.flush()
    return lang


def _join(db: Session, user: User, lang: Language, *, can_edit=False, can_verify=False):
    db.add(
        UserLanguage(
            user_id=user.id,
            language_id=lang.id,
            proficiency_level=ProficiencyLevel.FLUENT,
            can_edit=can_edit,
            can_verify=can_verify,
        )
    )
    db.flush()


def _word(db: Session, lang: Language, creator: User, lemma: str, **kw) -> WordForm:
    lexeme = Lexeme(
        id=uuid.uuid4(),
        language_id=lang.id,
        lemma=lemma,
        created_by_id=creator.id,
        status=LexemeStatus.PUBLISHED,
        **kw,
    )
    db.add(lexeme)
    db.flush()
    form = WordForm(id=uuid.uuid4(), lexeme_id=lexeme.id, form=lemma, is_lemma=True)
    db.add(form)
    db.flush()
    return form


def _snippet(db: Session, lang: Language, content: str) -> SourceSnippet:
    snippet = SourceSnippet(
        language_id=lang.id,
        content=content,
        source_url=URL,
        source_title="Minga",
        license="CC BY-SA 4.0",
    )
    db.add(snippet)
    db.flush()
    return snippet


def _text(db: Session, lang: Language, author: User, content: str, document=None) -> Text:
    if document is None:
        document = Document(id=uuid.uuid4(), created_by_id=author.id)
        db.add(document)
        db.flush()
    text = Text(
        title="Story",
        content=content,
        document_type=DocumentType.STORY,
        language_id=lang.id,
        document_id=document.id,
        created_by_id=author.id,
    )
    db.add(text)
    db.flush()
    return text


def _deck(db: Session, user: User, lang: Language):
    return contribute_service.build_deck(db, user, lang.id, limit=30)


def _of(deck, kind: str):
    return [task for task in deck if task.type == kind]


# ---------------------------------------------------------------------------
# Storing outside text
# ---------------------------------------------------------------------------


def test_split_sentences_keeps_prose_only():
    text = "Minga is d Hauptstod vo Bayern. Kurz.\n1 2 3 4 5 6\nDe Isar fliasst durch d Stod!"
    assert source_service.split_sentences(text) == [
        "Minga is d Hauptstod vo Bayern.",
        "De Isar fliasst durch d Stod!",
    ]


def test_add_source_text_needs_edit_rights_and_skips_duplicates(db: Session):
    lang = _language(db, "Bavarian")
    editor, viewer = _user(db), _user(db)
    _join(db, editor, lang, can_edit=True)
    _join(db, viewer, lang)
    data = SourceTextCreate(
        source_url=URL, source_title="Minga", text="Minga is d Hauptstod vo Bayern."
    )

    with pytest.raises(HTTPException) as exc:
        add_source_text(lang.id, data, current_user=viewer, db=db)
    assert exc.value.status_code == 403

    assert add_source_text(lang.id, data, current_user=editor, db=db).created == 1
    assert add_source_text(lang.id, data, current_user=editor, db=db).created == 0


# ---------------------------------------------------------------------------
# Spelling confirmation
# ---------------------------------------------------------------------------


def test_spelling_cards_come_from_snippets_with_their_source(db: Session):
    lang = _language(db, "Bavarian")
    editor = _user(db)
    _join(db, editor, lang, can_edit=True)
    for known in ("mia", "fahrn", "ham", "a"):
        _word(db, lang, editor, known)
    _snippet(db, lang, "Mia fahrn auf d Wiesn.")
    _text(db, lang, editor, "Mia ham a Wiesn.")  # "Wiesn" is unknown here too

    deck = _deck(db, editor, lang)
    spelling = _of(deck, "confirm_spelling")
    assert [t.token for t in spelling] == ["auf", "d"]
    card = spelling[0]
    assert (card.source.source_url, card.source.license) == (URL, "CC BY-SA 4.0")
    assert card.source.snippet[card.source.highlight_start : card.source.highlight_end] == "auf"
    # Unknown in our own texts as well: only the define card for it.
    assert [t.token for t in _of(deck, "define_word")] == ["Wiesn"]


async def test_suggested_spelling_of_known_word_goes_to_one_reviewer(db: Session):
    lang = _language(db, "Bavarian")
    suggester, reviewer = _user(db), _user(db)
    _join(db, suggester, lang)
    _join(db, reviewer, lang, can_verify=True)
    hoamat = _word(db, lang, reviewer, "Hoamat")
    snippet = _snippet(db, lang, "I bin in da Hoamad.")

    result = confirm_spelling(
        lang.id,
        SpellingAnswer(token="Hoamad", standard="Hoamat", snippet_id=snippet.id),
        current_user=suggester,
        db=db,
    )

    assert result.outcome == "proposed"
    assert db.query(SpellingVariant).count() == 0  # nothing changes before review
    # Pending, so nobody is asked about it again...
    assert "Hoamad" not in [t.token for t in _of(_deck(db, suggester, lang), "confirm_spelling")]
    # ...but the reviewer gets it, with the source noted.
    [card] = _of(_deck(db, reviewer, lang), "review_addition")
    assert (card.lemma, card.variant) == ("Hoamat", "Hoamad")
    assert URL in card.note

    await review(card.proposal_id, AdditionReview(approve=True), current_user=reviewer, db=db)
    [variant] = db.query(SpellingVariant).all()
    assert (variant.word_form_id, variant.variant) == (hoamat.id, "Hoamad")


async def test_reviewed_additions_are_not_voted_on(db: Session):
    lang = _language(db, "Bavarian")
    suggester, reviewer = _user(db), _user(db)
    _join(db, suggester, lang)
    _join(db, reviewer, lang, can_edit=True, can_verify=True)
    _word(db, lang, reviewer, "Hoamat")
    confirm_spelling(
        lang.id, SpellingAnswer(token="Hoamad", standard="Hoamat"), current_user=suggester, db=db
    )
    proposal = db.query(ChangeProposal).one()

    assert _of(_deck(db, reviewer, lang), "vote") == []
    with pytest.raises(HTTPException) as exc:
        await vote(proposal.id, VoteCreate(choice="approve"), current_user=reviewer, db=db)
    assert exc.value.status_code == 400
    # The author can't settle their own addition.
    with pytest.raises(HTTPException) as exc:
        await review(proposal.id, AdditionReview(approve=True), current_user=suggester, db=db)
    assert exc.value.status_code == 403


def test_editor_spelling_is_recorded_directly_and_repeats_conflict(db: Session):
    lang = _language(db, "Bavarian")
    editor = _user(db)
    _join(db, editor, lang, can_edit=True)
    form = _word(db, lang, editor, "Hoamat")
    answer = SpellingAnswer(token="Hoamad", standard="Hoamat")

    assert confirm_spelling(lang.id, answer, current_user=editor, db=db).outcome == "published"
    assert [v.variant for v in db.query(SpellingVariant).filter_by(word_form_id=form.id)] == [
        "Hoamad"
    ]
    with pytest.raises(HTTPException) as exc:
        confirm_spelling(lang.id, answer, current_user=editor, db=db)
    assert exc.value.status_code == 409


def test_unknown_standard_spelling_becomes_a_new_word(db: Session):
    lang = _language(db, "Bavarian")
    english = _language(db, "English")
    suggester = _user(db)
    snippet = _snippet(db, lang, "Mia gengan in d Kiach.")

    result = confirm_spelling(
        lang.id,
        SpellingAnswer(
            token="Kiach",
            standard="Kiacha",
            snippet_id=snippet.id,
            gloss="church",
            gloss_language_id=english.id,
        ),
        current_user=suggester,
        db=db,
    )

    assert result.outcome == "suggested"
    lexeme = db.get(Lexeme, result.lexeme_id)
    assert (lexeme.lemma, lexeme.status, lexeme.source) == (
        "Kiacha",
        LexemeStatus.PENDING_REVIEW,
        URL,
    )
    assert [v.variant for v in lexeme.forms[0].spelling_variants] == ["Kiach"]
    [gloss] = lexeme_service._translation_partners(db, lexeme.id)
    assert gloss.lemma == "church"


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------


def test_translation_cards_only_from_languages_the_user_speaks(db: Session):
    bavarian = _language(db, "Bavarian")
    english = _language(db, "English")
    speaker, monolingual = _user(db), _user(db)
    _join(db, speaker, bavarian)
    _join(db, speaker, english)
    _join(db, monolingual, bavarian)
    house = _word(db, english, speaker, "house")
    church = _word(db, english, speaker, "church")
    haus = _word(db, bavarian, speaker, "Haus")
    lexeme_service.add_translation(
        db,
        haus.lexeme_id,
        lexeme_service.TranslationCreate(other_lexeme_id=house.lexeme_id),
        speaker.id,
    )
    open_doc = _text(db, english, speaker, "The church is old.")
    done = _text(db, english, speaker, "The house is new.")
    _text(db, bavarian, speaker, "Des Haus is nei.", document=done.document)
    _snippet(db, english, "Munich is the capital of Bavaria.")

    deck = _deck(db, speaker, bavarian)
    assert [t.source_lexeme_id for t in _of(deck, "translate_word")] == [church.lexeme_id]
    texts = _of(deck, "translate_text")
    assert [(t.text_id, t.content) for t in texts] == [
        (open_doc.id, "The church is old."),
        (None, "Munich is the capital of Bavaria."),
    ]
    assert texts[1].source_url == URL

    deck = _deck(db, monolingual, bavarian)
    assert _of(deck, "translate_word") == _of(deck, "translate_text") == []


async def test_translate_word_new_existing_and_proposed(db: Session):
    bavarian = _language(db, "Bavarian")
    english = _language(db, "English")
    editor, suggester, reviewer = _user(db), _user(db), _user(db)
    _join(db, editor, bavarian, can_edit=True)
    _join(db, reviewer, bavarian, can_verify=True)
    house = _word(db, english, editor, "house")
    church = _word(db, english, editor, "church")
    dog = _word(db, english, editor, "dog")
    kiacha = _word(db, bavarian, editor, "Kiacha")

    new = translate_word(
        bavarian.id,
        TranslateWordAnswer(source_lexeme_id=house.lexeme_id, lemma="Haus"),
        current_user=suggester,
        db=db,
    )
    assert new.outcome == "suggested"
    assert db.get(Lexeme, new.lexeme_id).status == LexemeStatus.PENDING_REVIEW
    assert contribute_service._translation_exists(db, new.lexeme_id, house.lexeme_id)

    linked = translate_word(
        bavarian.id,
        TranslateWordAnswer(source_lexeme_id=church.lexeme_id, lemma="kiacha"),
        current_user=editor,
        db=db,
    )
    assert (linked.outcome, linked.lexeme_id) == ("published", kiacha.lexeme_id)
    assert contribute_service._translation_exists(db, kiacha.lexeme_id, church.lexeme_id)

    _word(db, bavarian, editor, "Hund")
    proposed = translate_word(
        bavarian.id,
        TranslateWordAnswer(source_lexeme_id=dog.lexeme_id, lemma="Hund"),
        current_user=suggester,
        db=db,
    )
    assert proposed.outcome == "proposed"
    assert not contribute_service._translation_exists(db, proposed.lexeme_id, dog.lexeme_id)
    [card] = _of(_deck(db, reviewer, bavarian), "review_addition")
    assert (card.lemma, card.other_lemma) == ("Hund", "dog")
    await review(card.proposal_id, AdditionReview(approve=False), current_user=reviewer, db=db)
    assert db.get(ChangeProposal, card.proposal_id).status == ProposalStatus.REJECTED
    assert not contribute_service._translation_exists(db, proposed.lexeme_id, dog.lexeme_id)


def test_translating_a_snippet_makes_a_document(db: Session):
    bavarian = _language(db, "Bavarian")
    english = _language(db, "English")
    suggester = _user(db)
    _join(db, suggester, english)
    snippet = _snippet(db, english, "Munich is the capital of Bavaria.")

    result = translate_text(
        bavarian.id,
        TranslateTextAnswer(snippet_id=snippet.id, content="Minga is d Hauptstod vo Bayern."),
        current_user=suggester,
        db=db,
    )

    assert result.outcome == "suggested"
    texts = {t.language_id: t for t in db.query(Text).filter_by(document_id=result.document_id)}
    original, translation = texts[english.id], texts[bavarian.id]
    assert (original.status, original.source) == (TextStatus.PUBLISHED, URL)
    assert (translation.status, translation.title) == (TextStatus.PENDING_REVIEW, "Minga")
    db.refresh(snippet)
    assert snippet.document_id == result.document_id
    # It's no longer offered, and a second translation into the language conflicts.
    assert _of(_deck(db, suggester, bavarian), "translate_text") == []
    with pytest.raises(HTTPException) as exc:
        translate_text(
            bavarian.id,
            TranslateTextAnswer(text_id=original.id, content="Nomoi"),
            current_user=suggester,
            db=db,
        )
    assert exc.value.status_code == 409


def test_translate_text_needs_exactly_one_source(db: Session):
    bavarian = _language(db, "Bavarian")
    user = _user(db)
    with pytest.raises(HTTPException) as exc:
        translate_text(bavarian.id, TranslateTextAnswer(content="x"), current_user=user, db=db)
    assert exc.value.status_code == 400


def test_proposed_type_is_listed_separately(db: Session):
    """Recommendation listings (review page, word page) stay votes-only."""
    lang = _language(db, "Bavarian")
    suggester, editor = _user(db), _user(db)
    _join(db, editor, lang, can_edit=True)
    form = _word(db, lang, editor, "Hoamat")
    confirm_spelling(
        lang.id, SpellingAnswer(token="Hoamad", standard="Hoamat"), current_user=suggester, db=db
    )
    from app.services import proposal_service

    assert proposal_service.list_proposals(db, lang.id, ProposalStatus.OPEN) == []
    assert proposal_service.list_for_lexeme(db, form.lexeme_id) == []
    assert db.query(ChangeProposal).one().proposal_type == ProposalType.ADD_SPELLING_VARIANT
