import uuid
from datetime import UTC, datetime

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")
from app.database import Base  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.text import DocumentType, Text  # noqa: E402
from app.models.text_word_link import TextWordLink, TextWordLinkStatus  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.word import Lexeme, LexemeStatus, WordForm  # noqa: E402
from app.services.document_service import (  # noqa: E402
    refresh_document_suggestions,
    suggest_links_for_text,
)
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


def _seed_document(session: Session, user: User) -> Document:
    now = _now()
    document = Document(
        id=uuid.uuid4(),
        created_by_id=user.id,
        created_at=now,
        updated_at=now,
    )
    session.add(document)
    return document


def _seed_text(
    session: Session, document: Document, language: Language, user: User, content: str
) -> Text:
    now = _now()
    text = Text(
        id=uuid.uuid4(),
        title="Sample Text",
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
    return text


def _seed_lexeme_with_form(
    session: Session, language: Language, user: User, form_value: str
) -> WordForm:
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
    return word_form


def prepare_text_with_form(session: Session, content: str, form_value: str) -> Text:
    user = _seed_user(session)
    language = _seed_language(session)
    document = _seed_document(session, user)
    text = _seed_text(session, document, language, user, content)
    _seed_lexeme_with_form(session, language, user, form_value)
    session.commit()
    session.refresh(text)
    return text


def test_suggest_links_for_text_creates_suggestion(db_session: Session):
    text = prepare_text_with_form(db_session, content="Hello world", form_value="Hello")

    created = suggest_links_for_text(db_session, text)
    db_session.commit()

    assert len(created) == 1
    stored_links = db_session.query(TextWordLink).all()
    assert len(stored_links) == 1
    link = stored_links[0]
    assert link.status == TextWordLinkStatus.SUGGESTED
    assert link.start_char == 0
    assert text.content[link.start_char : link.end_char] == "Hello"
    assert link.word_form_id is not None


def test_suggest_links_skips_existing_span(db_session: Session):
    text = prepare_text_with_form(db_session, content="Hello world", form_value="Hello")

    suggest_links_for_text(db_session, text)
    db_session.commit()

    created_again = suggest_links_for_text(db_session, text)
    db_session.commit()

    assert len(created_again) == 0
    assert db_session.query(TextWordLink).count() == 1


def test_suggest_links_respects_rejected_spans(db_session: Session):
    text = prepare_text_with_form(db_session, content="Hello world", form_value="Hello")

    suggest_links_for_text(db_session, text)
    db_session.commit()

    link = db_session.query(TextWordLink).first()
    link.status = TextWordLinkStatus.REJECTED
    db_session.commit()

    created = suggest_links_for_text(db_session, text)
    db_session.commit()

    assert len(created) == 0
    assert db_session.query(TextWordLink).count() == 1
    refreshed = db_session.get(TextWordLink, link.id)
    assert refreshed.status == TextWordLinkStatus.REJECTED


def test_refresh_document_suggestions_rebuilds_for_all_texts(db_session: Session):
    user = _seed_user(db_session)
    language = _seed_language(db_session)
    document = _seed_document(db_session, user)
    text_primary = _seed_text(db_session, document, language, user, "Hello friend")
    text_secondary = _seed_text(db_session, document, language, user, "Friend of hello")
    _seed_lexeme_with_form(db_session, language, user, "Hello")
    _seed_lexeme_with_form(db_session, language, user, "Friend")
    db_session.commit()

    suggestions = refresh_document_suggestions(db_session, document.id, creator_id=user.id)
    db_session.commit()

    assert set(suggestions.keys()) == {text_primary.id, text_secondary.id}
    assert db_session.query(TextWordLink).count() >= 2
