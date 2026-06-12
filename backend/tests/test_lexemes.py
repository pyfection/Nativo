"""
Tests for the Lexeme / WordForm service layer.

Focus is on the invariants that are easy to get wrong:
- Synonym / antonym / translation writes canonicalise the pair so the
  CHECK constraint (lexeme_id < other_id) is satisfied no matter which
  side initiates the link.
- Re-reading the link returns the *other* lexeme from either endpoint.
- Rhyme keys are derived from IPA on create and updated when IPA changes.
- Lemma promotion demotes the prior canonical form.
"""
import uuid
from datetime import UTC, datetime

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")
from app.database import Base  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.word import Lexeme, LexemeStatus, WordForm  # noqa: E402
from app.schemas.word import (  # noqa: E402
    AntonymCreate,
    LexemeCreate,
    SynonymCreate,
    TranslationCreate,
    WordFormCreate,
    WordFormCreateNested,
    WordFormUpdate,
)
from app.services import lexeme_service  # noqa: E402
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
def db_session() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _now() -> datetime:
    return datetime.now(UTC)


def _seed_user(session: Session) -> User:
    now = _now()
    user = User(
        id=uuid.uuid4(),
        email=f"u-{uuid.uuid4()}@example.com",
        username=f"user-{uuid.uuid4().hex[:8]}",
        hashed_password="x",
        role=UserRole.ADMIN,
        is_active=True,
        is_superuser=True,
        created_at=now,
        updated_at=now,
    )
    session.add(user)
    session.flush()
    return user


def _seed_language(session: Session, name: str = "Test Language", iso: str = "tst") -> Language:
    now = _now()
    lang = Language(
        id=uuid.uuid4(),
        name=name,
        native_name=name,
        iso_639_3=iso,
        managed=True,
        created_at=now,
        updated_at=now,
    )
    session.add(lang)
    session.flush()
    return lang


def _create(
    db: Session,
    user: User,
    language: Language,
    lemma: str,
    *,
    ipa: str | None = None,
) -> Lexeme:
    return lexeme_service.create_lexeme(
        db,
        LexemeCreate(
            language_id=language.id,
            lemma=lemma,
            lemma_form=WordFormCreateNested(
                form=lemma, is_lemma=True, ipa_pronunciation=ipa
            ),
        ),
        creator_id=user.id,
    )


# ---------------------------------------------------------------------------
# Rhyme keys
# ---------------------------------------------------------------------------


def test_rhyme_keys_are_set_from_ipa_on_create(db_session: Session):
    user = _seed_user(db_session)
    lang = _seed_language(db_session)
    lexeme = _create(db_session, user, lang, "cat", ipa="kˈæt")

    form = db_session.query(WordForm).filter(WordForm.lexeme_id == lexeme.id).first()
    assert form.rhyme_key == "æt"
    assert form.near_rhyme_key is not None and "æ" in form.near_rhyme_key


def test_rhyme_keys_update_when_ipa_changes(db_session: Session):
    user = _seed_user(db_session)
    lang = _seed_language(db_session)
    lexeme = _create(db_session, user, lang, "cat", ipa="kˈæt")
    form = db_session.query(WordForm).filter(WordForm.lexeme_id == lexeme.id).first()

    lexeme_service.update_word_form(
        db_session, form, WordFormUpdate(ipa_pronunciation="kˈʊt")
    )
    db_session.refresh(form)
    assert form.rhyme_key == "ʊt"


def test_find_rhymes_matches_same_language_only(db_session: Session):
    user = _seed_user(db_session)
    lang_a = _seed_language(db_session, name="Lang A", iso="laa")
    lang_b = _seed_language(db_session, name="Lang B", iso="lbb")

    cat = _create(db_session, user, lang_a, "cat", ipa="kˈæt")
    bat = _create(db_session, user, lang_a, "bat", ipa="bˈæt")
    _create(db_session, user, lang_b, "fat", ipa="fˈæt")  # different language

    cat_form = db_session.query(WordForm).filter(WordForm.lexeme_id == cat.id).first()

    matches = lexeme_service.find_rhymes(db_session, cat_form.id)
    assert {m.lexeme_id for m in matches} == {bat.id}


# ---------------------------------------------------------------------------
# Symmetric synonyms
# ---------------------------------------------------------------------------


def test_synonym_link_is_visible_from_either_endpoint(db_session: Session):
    user = _seed_user(db_session)
    lang = _seed_language(db_session)
    a = _create(db_session, user, lang, "buy")
    b = _create(db_session, user, lang, "purchase")

    # Initiate from either side — service canonicalises.
    lexeme_service.add_synonym(db_session, a.id, SynonymCreate(other_lexeme_id=b.id))

    a_links = lexeme_service.list_synonyms(db_session, a.id)
    b_links = lexeme_service.list_synonyms(db_session, b.id)

    assert {l.id for l in a_links} == {b.id}
    assert {l.id for l in b_links} == {a.id}


def test_synonym_canonicalisation_works_from_higher_id_first(db_session: Session):
    """
    If the *higher* UUID initiates the link, the service must still write
    (low, high) — otherwise the CHECK constraint would reject it.
    """
    user = _seed_user(db_session)
    lang = _seed_language(db_session)
    a = _create(db_session, user, lang, "buy")
    b = _create(db_session, user, lang, "purchase")

    high, low = (a, b) if a.id > b.id else (b, a)
    lexeme_service.add_synonym(
        db_session, high.id, SynonymCreate(other_lexeme_id=low.id)
    )

    assert len(lexeme_service.list_synonyms(db_session, high.id)) == 1
    assert len(lexeme_service.list_synonyms(db_session, low.id)) == 1


def test_synonym_rejects_self_link(db_session: Session):
    from fastapi import HTTPException

    user = _seed_user(db_session)
    lang = _seed_language(db_session)
    a = _create(db_session, user, lang, "buy")

    with pytest.raises(HTTPException):
        lexeme_service.add_synonym(
            db_session, a.id, SynonymCreate(other_lexeme_id=a.id)
        )


def test_synonym_rejects_cross_language(db_session: Session):
    from fastapi import HTTPException

    user = _seed_user(db_session)
    lang_a = _seed_language(db_session, name="A", iso="laa")
    lang_b = _seed_language(db_session, name="B", iso="lbb")
    a = _create(db_session, user, lang_a, "buy")
    b = _create(db_session, user, lang_b, "purchase")

    with pytest.raises(HTTPException):
        lexeme_service.add_synonym(
            db_session, a.id, SynonymCreate(other_lexeme_id=b.id)
        )


# ---------------------------------------------------------------------------
# Antonyms & translations follow the same symmetric pattern
# ---------------------------------------------------------------------------


def test_antonym_link_visible_from_either_side(db_session: Session):
    user = _seed_user(db_session)
    lang = _seed_language(db_session)
    hot = _create(db_session, user, lang, "hot")
    cold = _create(db_session, user, lang, "cold")

    lexeme_service.add_antonym(
        db_session, hot.id, AntonymCreate(other_lexeme_id=cold.id)
    )

    assert {l.id for l in lexeme_service.list_antonyms(db_session, hot.id)} == {cold.id}
    assert {l.id for l in lexeme_service.list_antonyms(db_session, cold.id)} == {hot.id}


def test_translation_link_requires_different_languages(db_session: Session):
    from fastapi import HTTPException

    user = _seed_user(db_session)
    lang = _seed_language(db_session)
    a = _create(db_session, user, lang, "house")
    b = _create(db_session, user, lang, "home")

    with pytest.raises(HTTPException):
        lexeme_service.add_translation(
            db_session, a.id, TranslationCreate(other_lexeme_id=b.id), creator_id=user.id
        )


def test_translation_link_visible_from_either_side(db_session: Session):
    user = _seed_user(db_session)
    lang_en = _seed_language(db_session, name="English", iso="eng")
    lang_de = _seed_language(db_session, name="German", iso="deu")
    house = _create(db_session, user, lang_en, "house")
    haus = _create(db_session, user, lang_de, "Haus")

    lexeme_service.add_translation(
        db_session,
        house.id,
        TranslationCreate(other_lexeme_id=haus.id, notes="cognate"),
        creator_id=user.id,
    )

    assert {l.id for l in lexeme_service.list_translations(db_session, house.id)} == {haus.id}
    assert {l.id for l in lexeme_service.list_translations(db_session, haus.id)} == {house.id}


# ---------------------------------------------------------------------------
# Lemma management
# ---------------------------------------------------------------------------


def test_promoting_a_form_demotes_the_previous_lemma(db_session: Session):
    user = _seed_user(db_session)
    lang = _seed_language(db_session)
    lexeme = _create(db_session, user, lang, "go")

    inflected = lexeme_service.create_word_form(
        db_session,
        WordFormCreate(
            lexeme_id=lexeme.id,
            form="went",
            is_lemma=False,
        ),
    )

    # Promote 'went'
    lexeme_service.update_word_form(
        db_session, inflected, WordFormUpdate(is_lemma=True)
    )
    db_session.expire_all()

    forms = db_session.query(WordForm).filter(WordForm.lexeme_id == lexeme.id).all()
    lemma_forms = [f for f in forms if f.is_lemma]
    assert len(lemma_forms) == 1
    assert lemma_forms[0].form == "went"

    refreshed_lexeme = db_session.query(Lexeme).filter(Lexeme.id == lexeme.id).first()
    assert refreshed_lexeme.lemma == "went"
