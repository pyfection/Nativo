import uuid
from datetime import UTC, datetime

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")
from app.database import Base  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.text import DocumentType, Text  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.word import Lexeme, LexemeStatus, SpellingVariant, WordForm  # noqa: E402
from app.schemas.word import SpellingVariantCreate  # noqa: E402
from app.services import spelling_service  # noqa: E402
from fastapi import HTTPException  # noqa: E402
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
        email="test@example.com",
        username="test-user",
        hashed_password="hashed",
        role=UserRole.ADMIN,
        is_active=True,
        is_superuser=True,
        created_at=now,
        updated_at=now,
    )
    session.add(user)
    return user


def _seed_language(session: Session) -> Language:
    now = _now()
    language = Language(
        id=uuid.uuid4(),
        name="Test Language",
        native_name="Test Language",
        iso_639_3="tst",
        managed=True,
        created_at=now,
        updated_at=now,
    )
    session.add(language)
    return language


def _seed_form(session: Session, language: Language, user: User, form_value: str) -> WordForm:
    now = _now()
    lexeme = Lexeme(
        id=uuid.uuid4(),
        language_id=language.id,
        lemma=form_value,
        created_by_id=user.id,
        status=LexemeStatus.DRAFT,
        created_at=now,
        updated_at=now,
    )
    session.add(lexeme)
    session.flush()
    word_form = WordForm(
        id=uuid.uuid4(),
        lexeme_id=lexeme.id,
        form=form_value,
        is_lemma=True,
        created_at=now,
        updated_at=now,
    )
    session.add(word_form)
    session.flush()
    return word_form


def _seed_text(session: Session, language: Language, user: User, content: str) -> Text:
    now = _now()
    document = Document(id=uuid.uuid4(), created_by_id=user.id, created_at=now, updated_at=now)
    session.add(document)
    session.flush()
    text = Text(
        id=uuid.uuid4(),
        title="Sample",
        content=content,
        document_type=DocumentType.STORY,
        language_id=language.id,
        document_id=document.id,
        is_primary=True,
        created_by_id=user.id,
        created_at=now,
        updated_at=now,
    )
    session.add(text)
    session.flush()
    return text


# ---------------------------------------------------------------------------
# Variant CRUD
# ---------------------------------------------------------------------------


def test_add_variant_derives_normalized_key(db_session: Session):
    user = _seed_user(db_session)
    language = _seed_language(db_session)
    form = _seed_form(db_session, language, user, "aih")
    db_session.commit()

    variant = spelling_service.add_variant(
        db_session, form, SpellingVariantCreate(variant="Éich", note="older"), creator_id=user.id
    )

    assert variant.variant == "Éich"
    assert variant.normalized == "eich"  # case- and diacritic-folded
    assert variant.note == "older"


def test_add_variant_rejects_duplicate(db_session: Session):
    user = _seed_user(db_session)
    language = _seed_language(db_session)
    form = _seed_form(db_session, language, user, "aih")
    db_session.commit()

    spelling_service.add_variant(db_session, form, SpellingVariantCreate(variant="eich"))
    with pytest.raises(HTTPException) as exc:
        spelling_service.add_variant(db_session, form, SpellingVariantCreate(variant="eich"))
    assert exc.value.status_code == 400


def test_add_variant_rejects_standard_form(db_session: Session):
    user = _seed_user(db_session)
    language = _seed_language(db_session)
    form = _seed_form(db_session, language, user, "aih")
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        spelling_service.add_variant(db_session, form, SpellingVariantCreate(variant="AIH"))
    assert exc.value.status_code == 400


def test_delete_variant(db_session: Session):
    user = _seed_user(db_session)
    language = _seed_language(db_session)
    form = _seed_form(db_session, language, user, "aih")
    db_session.commit()

    variant = spelling_service.add_variant(db_session, form, SpellingVariantCreate(variant="eich"))
    spelling_service.delete_variant(db_session, variant)

    assert db_session.query(SpellingVariant).count() == 0


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


def test_resolve_token_returns_standard_candidate(db_session: Session):
    user = _seed_user(db_session)
    language = _seed_language(db_session)
    form = _seed_form(db_session, language, user, "aih")
    spelling_service.add_variant(db_session, form, SpellingVariantCreate(variant="eich"))
    db_session.commit()

    result = spelling_service.resolve_token(db_session, language.id, "eich")

    assert result.already_standard is False
    assert len(result.candidates) == 1
    assert result.candidates[0].standard_form == "aih"


def test_resolve_token_folds_case_and_diacritics(db_session: Session):
    user = _seed_user(db_session)
    language = _seed_language(db_session)
    form = _seed_form(db_session, language, user, "aih")
    spelling_service.add_variant(db_session, form, SpellingVariantCreate(variant="eich"))
    db_session.commit()

    result = spelling_service.resolve_token(db_session, language.id, "ÉICH")

    assert len(result.candidates) == 1
    assert result.candidates[0].standard_form == "aih"


def test_resolve_token_already_standard(db_session: Session):
    user = _seed_user(db_session)
    language = _seed_language(db_session)
    form = _seed_form(db_session, language, user, "aih")
    spelling_service.add_variant(db_session, form, SpellingVariantCreate(variant="eich"))
    db_session.commit()

    result = spelling_service.resolve_token(db_session, language.id, "aih")

    assert result.already_standard is True
    assert result.candidates == []


def test_resolve_token_unknown(db_session: Session):
    user = _seed_user(db_session)
    language = _seed_language(db_session)
    _seed_form(db_session, language, user, "aih")
    db_session.commit()

    result = spelling_service.resolve_token(db_session, language.id, "qqq")

    assert result.already_standard is False
    assert result.candidates == []


# ---------------------------------------------------------------------------
# Document correction
# ---------------------------------------------------------------------------


def test_suggest_corrections_flags_variant_skips_standard(db_session: Session):
    user = _seed_user(db_session)
    language = _seed_language(db_session)
    form = _seed_form(db_session, language, user, "aih")
    spelling_service.add_variant(db_session, form, SpellingVariantCreate(variant="eich"))
    # "aih" appears in standard form too — it must not be flagged.
    text = _seed_text(db_session, language, user, "eich and aih")
    db_session.commit()

    corrections = spelling_service.suggest_corrections_for_text(db_session, text)

    assert len(corrections) == 1
    correction = corrections[0]
    assert correction.original == "eich"
    assert text.content[correction.start_char : correction.end_char] == "eich"
    assert correction.ambiguous is False
    assert correction.candidates[0].standard_form == "aih"


def test_suggest_corrections_marks_ambiguous(db_session: Session):
    user = _seed_user(db_session)
    language = _seed_language(db_session)
    form_a = _seed_form(db_session, language, user, "aih")
    form_b = _seed_form(db_session, language, user, "ay")
    spelling_service.add_variant(db_session, form_a, SpellingVariantCreate(variant="eich"))
    spelling_service.add_variant(db_session, form_b, SpellingVariantCreate(variant="eich"))
    text = _seed_text(db_session, language, user, "eich")
    db_session.commit()

    corrections = spelling_service.suggest_corrections_for_text(db_session, text)

    assert len(corrections) == 1
    assert corrections[0].ambiguous is True
    assert len(corrections[0].candidates) == 2


def test_suggest_corrections_empty_without_content(db_session: Session):
    user = _seed_user(db_session)
    language = _seed_language(db_session)
    text = _seed_text(db_session, language, user, "")
    db_session.commit()

    assert spelling_service.suggest_corrections_for_text(db_session, text) == []
