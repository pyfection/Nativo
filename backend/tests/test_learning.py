"""
Tests for the guided learning path: implicit scoring + sequencing.

The invariants that matter:
- Click/complete score transitions (first-contact jump to 4, click floor at
  0, +1/-1 afterwards, caps respected).
- An abandoned text (no completion) changes nothing except clicked words.
- The sequencer excludes under-linked texts, orders easiest-first, respects
  the new-word budget from the latest difficulty rating, and never returns
  an empty recommendation while any unread eligible text exists.
"""

import os
import uuid
from datetime import UTC, datetime

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

sqlalchemy = pytest.importorskip("sqlalchemy")
from app.database import Base  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.learning import (  # noqa: E402
    SCORE_MAX,
    SCORE_MIN,
    DifficultyRating,
    UserLexemeKnowledge,
)
from app.models.text import DocumentType, Text  # noqa: E402
from app.models.text_word_link import TextWordLink, TextWordLinkStatus  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.word import Lexeme, LexemeStatus, WordForm  # noqa: E402
from app.services import learning_service  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

engine = create_engine("sqlite:///:memory:", future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


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


def _language(db: Session) -> Language:
    lang = Language(
        id=uuid.uuid4(),
        name=f"Lang-{uuid.uuid4().hex[:6]}",
        iso_639_3=None,
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(lang)
    db.flush()
    return lang


def _lexeme(db: Session, language: Language, creator: User, lemma: str) -> Lexeme:
    lexeme = Lexeme(
        id=uuid.uuid4(),
        language_id=language.id,
        lemma=lemma,
        created_by_id=creator.id,
        status=LexemeStatus.PUBLISHED,
    )
    db.add(lexeme)
    db.flush()
    form = WordForm(id=uuid.uuid4(), lexeme_id=lexeme.id, form=lemma, is_lemma=True)
    db.add(form)
    db.flush()
    lexeme._test_form = form  # convenience handle for linking
    return lexeme


def _text_with_words(
    db: Session,
    language: Language,
    creator: User,
    title: str,
    lexemes: list[Lexeme],
    link_status: TextWordLinkStatus = TextWordLinkStatus.CONFIRMED,
    trailing_unlinked: str = "",
) -> Text:
    """A text whose content is exactly the lexemes' forms, fully linked."""
    words = [lx._test_form.form for lx in lexemes]
    content = " ".join(words) + trailing_unlinked
    document = Document(id=uuid.uuid4(), created_by_id=creator.id)
    db.add(document)
    db.flush()
    text = Text(
        id=uuid.uuid4(),
        document_id=document.id,
        language_id=language.id,
        title=title,
        content=content,
        document_type=DocumentType.STORY,
        created_by_id=creator.id,
        is_primary=True,
    )
    db.add(text)
    db.flush()
    offset = 0
    for lx in lexemes:
        form = lx._test_form
        start = content.index(form.form, offset)
        end = start + len(form.form)
        offset = end
        db.add(
            TextWordLink(
                id=uuid.uuid4(),
                text_id=text.id,
                word_form_id=form.id,
                start_char=start,
                end_char=end,
                status=link_status,
            )
        )
    db.flush()
    return text


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def test_click_floors_at_zero_and_first_click_starts_at_zero(db: Session):
    user, lang = _user(db), _language(db)
    lx = _lexeme(db, lang, user, "servus")

    row = learning_service.record_click(db, user.id, lx.id)
    assert row.score == SCORE_MIN

    row = learning_service.record_click(db, user.id, lx.id)
    assert row.score == SCORE_MIN  # already at the floor


def test_completion_bonus_first_contact_jumps_to_max(db: Session):
    user, lang = _user(db), _language(db)
    lx1 = _lexeme(db, lang, user, "servus")
    lx2 = _lexeme(db, lang, user, "brezn")
    text = _text_with_words(db, lang, user, "T", [lx1, lx2])

    learning_service.complete_text(db, user.id, text, DifficultyRating.JUST_RIGHT)

    for lx in (lx1, lx2):
        assert db.get(UserLexemeKnowledge, (user.id, lx.id)).score == SCORE_MAX


def test_clicked_words_are_excluded_from_completion_bonus(db: Session):
    user, lang = _user(db), _language(db)
    lx1 = _lexeme(db, lang, user, "servus")
    lx2 = _lexeme(db, lang, user, "brezn")
    text = _text_with_words(db, lang, user, "T", [lx1, lx2])

    learning_service.record_click(db, user.id, lx1.id)
    learning_service.complete_text(
        db, user.id, text, DifficultyRating.JUST_RIGHT, clicked_lexeme_ids={lx1.id}
    )

    assert db.get(UserLexemeKnowledge, (user.id, lx1.id)).score == SCORE_MIN
    assert db.get(UserLexemeKnowledge, (user.id, lx2.id)).score == SCORE_MAX


def test_repeat_exposure_increments_and_caps(db: Session):
    user, lang = _user(db), _language(db)
    lx = _lexeme(db, lang, user, "servus")
    text1 = _text_with_words(db, lang, user, "T1", [lx])
    text2 = _text_with_words(db, lang, user, "T2", [lx])

    # Clicked in the first text -> 0, then completed -> stays 0 (excluded).
    learning_service.record_click(db, user.id, lx.id)
    learning_service.complete_text(
        db, user.id, text1, DifficultyRating.CHALLENGING, clicked_lexeme_ids={lx.id}
    )
    assert db.get(UserLexemeKnowledge, (user.id, lx.id)).score == SCORE_MIN

    # Read without clicking in the second text -> +1.
    learning_service.complete_text(db, user.id, text2, DifficultyRating.JUST_RIGHT)
    assert db.get(UserLexemeKnowledge, (user.id, lx.id)).score == SCORE_MIN + 1

    # Re-completing caps at SCORE_MAX eventually.
    for _ in range(10):
        learning_service.complete_text(db, user.id, text2, DifficultyRating.EASY)
    assert db.get(UserLexemeKnowledge, (user.id, lx.id)).score == SCORE_MAX


def test_abandoned_text_updates_nothing_but_clicks(db: Session):
    user, lang = _user(db), _language(db)
    lx1 = _lexeme(db, lang, user, "servus")
    lx2 = _lexeme(db, lang, user, "brezn")
    _text_with_words(db, lang, user, "T", [lx1, lx2])

    learning_service.record_click(db, user.id, lx1.id)
    # No complete_text call: lx2 must remain untracked.
    assert db.get(UserLexemeKnowledge, (user.id, lx1.id)) is not None
    assert db.get(UserLexemeKnowledge, (user.id, lx2.id)) is None


# ---------------------------------------------------------------------------
# Sequencing
# ---------------------------------------------------------------------------


def test_path_orders_unread_texts_easiest_first(db: Session):
    user, lang = _user(db), _language(db)
    common = [_lexeme(db, lang, user, f"common{i}") for i in range(3)]
    rare = [_lexeme(db, lang, user, f"rare{i}") for i in range(5)]

    easy = _text_with_words(db, lang, user, "easy", common)
    hard = _text_with_words(db, lang, user, "hard", common + rare)

    path = learning_service.get_learning_path(db, lang.id, user_id=user.id)
    assert [e["title"] for e in path] == ["easy", "hard"]
    assert path[0]["state"] == "recommended"
    assert path[1]["state"] == "upcoming"
    assert path[0]["text_id"] == easy.id
    assert path[1]["text_id"] == hard.id


def test_cold_start_prefers_fewest_unique_most_frequent(db: Session):
    """Anonymous path: same word count, more frequent vocabulary wins."""
    user, lang = _user(db), _language(db)
    frequent = [_lexeme(db, lang, user, f"freq{i}") for i in range(3)]
    obscure = [_lexeme(db, lang, user, f"obs{i}") for i in range(3)]

    # `frequent` words appear in two extra texts, raising their corpus counts.
    _text_with_words(db, lang, user, "filler1", frequent)
    _text_with_words(db, lang, user, "filler2", frequent)
    _text_with_words(db, lang, user, "candidate-frequent", frequent)
    _text_with_words(db, lang, user, "candidate-obscure", obscure)

    path = learning_service.get_learning_path(db, lang.id, user_id=None)
    titles = [e["title"] for e in path]
    assert titles.index("candidate-frequent") < titles.index("candidate-obscure")


def test_budget_from_latest_rating_and_too_hard_fallback(db: Session):
    user, lang = _user(db), _language(db)
    known = [_lexeme(db, lang, user, f"known{i}") for i in range(2)]
    fresh = [_lexeme(db, lang, user, f"fresh{i}") for i in range(6)]

    first = _text_with_words(db, lang, user, "first", known)
    _text_with_words(db, lang, user, "next", known + fresh)

    # Completing `first` as TOO_HARD sets the budget to zero; "next" (6 new
    # words) exceeds it, but with no zero-new alternative it must still be
    # recommended rather than nothing.
    learning_service.complete_text(db, user.id, first, DifficultyRating.TOO_HARD)
    path = learning_service.get_learning_path(db, lang.id, user_id=user.id)

    states = {e["title"]: e["state"] for e in path}
    assert states["first"] == "completed"
    assert states["next"] == "recommended"
    assert path[0]["title"] == "first"  # completed texts lead the line


def test_underlinked_texts_are_excluded(db: Session):
    user, lang = _user(db), _language(db)
    linked = [_lexeme(db, lang, user, "servus")]

    # Content has many unlinked tokens beyond the single linked word.
    _text_with_words(
        db,
        lang,
        user,
        "half-linked",
        linked,
        trailing_unlinked=" und no vui mehra unverlinkte weata dahinta",
    )
    good = _text_with_words(db, lang, user, "fully-linked", linked)

    path = learning_service.get_learning_path(db, lang.id, user_id=user.id)
    assert [e["title"] for e in path] == ["fully-linked"]
    assert path[0]["text_id"] == good.id


def test_suggested_links_do_not_count(db: Session):
    user, lang = _user(db), _language(db)
    lx = _lexeme(db, lang, user, "servus")
    _text_with_words(
        db, lang, user, "only-suggested", [lx], link_status=TextWordLinkStatus.SUGGESTED
    )

    path = learning_service.get_learning_path(db, lang.id, user_id=user.id)
    assert path == []  # suggested-only text has 0% confirmed coverage


def test_known_pct_reflects_user_knowledge(db: Session):
    user, lang = _user(db), _language(db)
    lx1 = _lexeme(db, lang, user, "servus")
    lx2 = _lexeme(db, lang, user, "brezn")

    first = _text_with_words(db, lang, user, "first", [lx1])
    _text_with_words(db, lang, user, "second", [lx1, lx2])

    learning_service.complete_text(db, user.id, first, DifficultyRating.EASY)
    path = learning_service.get_learning_path(db, lang.id, user_id=user.id)

    second = next(e for e in path if e["title"] == "second")
    assert second["new_lexeme_count"] == 1
    assert second["known_pct"] == 50.0
