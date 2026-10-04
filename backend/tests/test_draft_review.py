"""
Tests for reviewing LLM-drafted word batches.

The contract under test:
- A bot account's suggestions are never auto-promoted into edit rights, no
  matter how many get approved.
- Glosses drafted with a word follow it: approving the word publishes its
  drafted glosses, rejecting it archives the ones nothing else uses. Other
  people's pending lexemes are never touched.
- A reviewer can fix a draft while approving it (spelling, forms, part of
  speech, glosses) in one atomic step.
- `draft_confidence` survives only on suggestions and is cleared on approval.
"""

import os
import uuid
from datetime import UTC, datetime

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

sqlalchemy = pytest.importorskip("sqlalchemy")
from app.api.v1.endpoints.words import (  # noqa: E402
    create_lexeme,
    list_suggestions,
    reject_lexeme,
    verify_lexeme,
)
from app.database import Base  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.user_language import ProficiencyLevel, UserLanguage  # noqa: E402
from app.models.word import Lexeme, LexemeStatus, WordForm  # noqa: E402
from app.schemas.word import (  # noqa: E402
    FormCorrection,
    GlossCorrection,
    LexemeCreate,
    LexemeRejection,
    LexemeReviewCorrections,
    PartOfSpeech,
    TranslationCreate,
    WordFormCreateNested,
)
from app.services import lexeme_service  # noqa: E402
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


def _user(db: Session, *, is_bot: bool = False) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"u-{uuid.uuid4().hex[:8]}@example.com",
        username=f"user-{uuid.uuid4().hex[:8]}",
        hashed_password="x",
        role=UserRole.PUBLIC,
        is_active=True,
        is_bot=is_bot,
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(user)
    db.flush()
    return user


def _language(db: Session, name: str) -> Language:
    lang = Language(id=uuid.uuid4(), name=name, created_at=_now(), updated_at=_now())
    db.add(lang)
    db.flush()
    return lang


def _join(db: Session, user: User, lang: Language, *, edit=False, verify=False) -> None:
    db.add(
        UserLanguage(
            user_id=user.id,
            language_id=lang.id,
            proficiency_level=ProficiencyLevel.NATIVE,
            can_edit=edit,
            can_verify=verify,
        )
    )
    db.flush()


def _payload(lang: Language, lemma: str, forms: tuple[str, ...] = (), confidence=None):
    return LexemeCreate(
        language_id=lang.id,
        lemma=lemma,
        lemma_form=WordFormCreateNested(form=lemma, is_lemma=True),
        additional_forms=[WordFormCreateNested(form=f) for f in forms] or None,
        draft_confidence=confidence,
    )


@pytest.fixture
def world(db: Session):
    bar = _language(db, "Bavarian")
    eng = _language(db, "English")
    bot = _user(db, is_bot=True)
    reviewer = _user(db)
    _join(db, reviewer, bar, edit=True, verify=True)
    _join(db, reviewer, eng, edit=True, verify=True)
    db.commit()
    return bar, eng, bot, reviewer


async def _draft(db, bot, bar, eng, lemma, gloss, forms=(), confidence="high"):
    """What the batch importer does: a pending word plus a pending gloss."""
    word = await create_lexeme(_payload(bar, lemma, forms, confidence), current_user=bot, db=db)
    gloss_lx = await create_lexeme(_payload(eng, gloss), current_user=bot, db=db)
    lexeme_service.add_translation(
        db, word.id, TranslationCreate(other_lexeme_id=gloss_lx.id), creator_id=bot.id
    )
    return word, gloss_lx


def _status(db: Session, lexeme_id) -> LexemeStatus:
    db.expire_all()
    return db.query(Lexeme).filter(Lexeme.id == lexeme_id).one().status


async def test_bot_is_never_auto_promoted(db: Session, world):
    bar, eng, bot, reviewer = world
    _join(db, bot, bar)  # even with a membership row, where promotion lives
    db.commit()
    for i in range(8):
        word = await create_lexeme(_payload(bar, f"voat{i}"), current_user=bot, db=db)
        await verify_lexeme(word.id, current_user=reviewer, db=db)

    membership = db.query(UserLanguage).filter(UserLanguage.user_id == bot.id).one()
    assert membership.can_edit is False


async def test_confidence_is_kept_on_suggestions_and_cleared_on_approval(db: Session, world):
    bar, eng, bot, reviewer = world
    word, _ = await _draft(db, bot, bar, eng, "hund", "dog", confidence="medium")
    assert word.status == LexemeStatus.PENDING_REVIEW
    assert word.draft_confidence == "medium"

    queue = await list_suggestions(language_id=bar.id, current_user=reviewer, db=db)
    assert queue[0].draft_confidence == "medium"
    assert [t.lemma for t in queue[0].translations] == ["dog"]

    approved = await verify_lexeme(word.id, current_user=reviewer, db=db)
    assert approved.draft_confidence is None

    # An editor's own entry never carries a confidence.
    own = await create_lexeme(_payload(bar, "kads", confidence="low"), current_user=reviewer, db=db)
    assert own.draft_confidence is None


async def test_approving_publishes_drafted_glosses_only(db: Session, world):
    bar, eng, bot, reviewer = world
    word, gloss = await _draft(db, bot, bar, eng, "hund", "dog")
    # Someone else's pending English word, linked too, must stay pending.
    stranger = _user(db)
    foreign = await create_lexeme(_payload(eng, "hound"), current_user=stranger, db=db)
    lexeme_service.add_translation(
        db, word.id, TranslationCreate(other_lexeme_id=foreign.id), creator_id=stranger.id
    )

    await verify_lexeme(word.id, current_user=reviewer, db=db)

    assert _status(db, word.id) == LexemeStatus.PUBLISHED
    assert _status(db, gloss.id) == LexemeStatus.PUBLISHED
    assert _status(db, foreign.id) == LexemeStatus.PENDING_REVIEW


async def test_rejecting_archives_orphaned_drafted_glosses(db: Session, world):
    bar, eng, bot, reviewer = world
    word, gloss = await _draft(db, bot, bar, eng, "hund", "dog")
    # "dog" is also drafted for a second word, so it must survive that reject.
    other, shared = await _draft(db, bot, bar, eng, "wauwau", "puppy")
    lexeme_service.add_translation(
        db, other.id, TranslationCreate(other_lexeme_id=gloss.id), creator_id=bot.id
    )

    await reject_lexeme(word.id, LexemeRejection(reason="wrong"), current_user=reviewer, db=db)
    assert _status(db, word.id) == LexemeStatus.ARCHIVED
    assert _status(db, gloss.id) == LexemeStatus.PENDING_REVIEW

    await reject_lexeme(other.id, None, current_user=reviewer, db=db)
    assert _status(db, gloss.id) == LexemeStatus.ARCHIVED
    assert _status(db, shared.id) == LexemeStatus.ARCHIVED


async def test_approve_with_corrections(db: Session, world):
    bar, eng, bot, reviewer = world
    # A published English "the dog" already exists; the draft glossed "hound".
    existing = await create_lexeme(_payload(eng, "dog"), current_user=reviewer, db=db)
    await verify_lexeme(existing.id, current_user=reviewer, db=db)
    word, drafted = await _draft(db, bot, bar, eng, "hunt", "hound", forms=("hunda", "hundn"))
    forms = {f.form: f for f in word.forms}

    await verify_lexeme(
        word.id,
        LexemeReviewCorrections(
            lemma="hund",
            part_of_speech=PartOfSpeech.NOUN,
            forms=[
                FormCorrection(id=forms["hunda"].id, form="hunt", notes="plural"),
                FormCorrection(id=forms["hundn"].id, delete=True),
            ],
            glosses=[GlossCorrection(language_id=eng.id, lemmas=["dog", "hound dog"])],
        ),
        current_user=reviewer,
        db=db,
    )

    db.expire_all()
    fixed = db.query(Lexeme).filter(Lexeme.id == word.id).one()
    assert fixed.status == LexemeStatus.PUBLISHED
    assert fixed.lemma == "hund"
    assert fixed.part_of_speech == PartOfSpeech.NOUN
    assert sorted((f.form, f.is_lemma) for f in fixed.forms) == [("hund", True), ("hunt", False)]

    glosses = {t.lemma: t.id for t in lexeme_service.list_translations(db, word.id)}
    assert set(glosses) == {"dog", "hound dog"}
    assert glosses["dog"] == existing.id  # linked to the existing entry, not a duplicate
    new_gloss = db.query(Lexeme).filter(Lexeme.id == glosses["hound dog"]).one()
    assert new_gloss.status == LexemeStatus.PUBLISHED  # the reviewer typed it
    assert [f.form for f in new_gloss.forms] == ["hound dog"]
    # The discarded draft gloss is archived, not published.
    assert _status(db, drafted.id) == LexemeStatus.ARCHIVED


async def test_corrections_cannot_touch_other_words_or_the_lemma_form(db: Session, world):
    bar, eng, bot, reviewer = world
    word, _ = await _draft(db, bot, bar, eng, "hund", "dog")
    other, _ = await _draft(db, bot, bar, eng, "kads", "cat")

    with pytest.raises(HTTPException) as excinfo:
        await verify_lexeme(
            word.id,
            LexemeReviewCorrections(forms=[FormCorrection(id=other.forms[0].id, form="x")]),
            current_user=reviewer,
            db=db,
        )
    assert excinfo.value.status_code == 400

    with pytest.raises(HTTPException):
        await verify_lexeme(
            word.id,
            LexemeReviewCorrections(forms=[FormCorrection(id=word.forms[0].id, delete=True)]),
            current_user=reviewer,
            db=db,
        )
    db.rollback()
    assert db.query(WordForm).filter(WordForm.lexeme_id == word.id).count() == 1
