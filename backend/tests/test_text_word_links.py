import uuid
from datetime import datetime

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.models.document import Document
from app.models.language import Language
from app.models.text import DocumentType, Text
from app.models.text_word_link import TextWordLink, TextWordLinkStatus
from app.models.user import User, UserRole
from app.models.word import Word, WordStatus
from app.services.document_service import refresh_document_suggestions, suggest_links_for_text


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


def _seed_user(session: Session) -> User:
    now = datetime.utcnow()
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
    now = datetime.utcnow()
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
    now = datetime.utcnow()
    document = Document(
        id=uuid.uuid4(),
        created_by_id=user.id,
        created_at=now,
        updated_at=now,
    )
    session.add(document)
    return document


def _seed_text(session: Session, document: Document, language: Language, user: User, content: str) -> Text:
    now = datetime.utcnow()
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


def _seed_word(session: Session, language: Language, user: User, word_value: str) -> Word:
    now = datetime.utcnow()
    word = Word(
        id=uuid.uuid4(),
        word=word_value,
        language_id=language.id,
        created_by_id=user.id,
        status=WordStatus.DRAFT,
        created_at=now,
        updated_at=now,
    )
    session.add(word)
    return word


def prepare_text_with_word(session: Session, content: str, word_value: str) -> Text:
    user = _seed_user(session)
    language = _seed_language(session)
    document = _seed_document(session, user)
    text = _seed_text(session, document, language, user, content)
    _seed_word(session, language, user, word_value)
    session.commit()
    session.refresh(text)
    return text


def test_suggest_links_for_text_creates_suggestion(db_session: Session):
    text = prepare_text_with_word(db_session, content="Hello world", word_value="Hello")

    created = suggest_links_for_text(db_session, text)
    db_session.commit()

    assert len(created) == 1
    stored_links = db_session.query(TextWordLink).all()
    assert len(stored_links) == 1
    link = stored_links[0]
    assert link.status == TextWordLinkStatus.SUGGESTED
    assert link.start_char == 0
    assert text.content[link.start_char:link.end_char] == "Hello"


def test_suggest_links_skips_existing_span(db_session: Session):
    text = prepare_text_with_word(db_session, content="Hello world", word_value="Hello")

    # First suggestion
    suggest_links_for_text(db_session, text)
    db_session.commit()

    # Run again without replacing existing suggestions
    created_again = suggest_links_for_text(db_session, text)
    db_session.commit()

    # No duplicate suggestions should be added
    assert len(created_again) == 0
    total_links = db_session.query(TextWordLink).count()
    assert total_links == 1


def test_suggest_links_respects_rejected_spans(db_session: Session):
    text = prepare_text_with_word(db_session, content="Hello world", word_value="Hello")

    suggest_links_for_text(db_session, text)
    db_session.commit()

    link = db_session.query(TextWordLink).first()
    link.status = TextWordLinkStatus.REJECTED
    db_session.commit()

    created = suggest_links_for_text(db_session, text)
    db_session.commit()

    # No new suggestion should be created for rejected span
    assert len(created) == 0
    total_links = db_session.query(TextWordLink).count()
    assert total_links == 1
    refreshed = db_session.get(TextWordLink, link.id)
    assert refreshed.status == TextWordLinkStatus.REJECTED


def test_refresh_document_suggestions_rebuilds_for_all_texts(db_session: Session):
    user = _seed_user(db_session)
    language = _seed_language(db_session)
    document = _seed_document(db_session, user)
    text_primary = _seed_text(db_session, document, language, user, "Hello friend")
    text_secondary = _seed_text(db_session, document, language, user, "Friend of hello")
    _seed_word(db_session, language, user, "Hello")
    _seed_word(db_session, language, user, "Friend")
    db_session.commit()

    suggestions = refresh_document_suggestions(db_session, document.id, creator_id=user.id)
    db_session.commit()

    assert set(suggestions.keys()) == {text_primary.id, text_secondary.id}
    total_links = db_session.query(TextWordLink).count()
    assert total_links >= 2

