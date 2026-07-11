"""
Tests for the recent-activity feed.

The feed is computed (no table of its own); what's worth pinning down is the
shape the frontend depends on for click-throughs: word_added items carry the
Lexeme id, text_added items carry the *Document* id (documents are what the
frontend routes on, not texts), contributor_joined carries no entity.
"""

import os
import uuid
from datetime import UTC, datetime

import pytest

# Importing the endpoint module pulls in app.config.Settings, which insists on
# these env vars. The tests never touch the real database or sign tokens.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

sqlalchemy = pytest.importorskip("sqlalchemy")
from app.api.v1.endpoints.activity import get_activity  # noqa: E402
from app.database import Base  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.text import DocumentType, Text  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.user_language import ProficiencyLevel, UserLanguage  # noqa: E402
from app.models.word import Lexeme, LexemeStatus, WordForm  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

engine = create_engine("sqlite:///:memory:", future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# The route function is wrapped by the rate limiter, which wants a real HTTP
# request; the business logic underneath doesn't use it, so test the
# unwrapped callable.
_get_activity = get_activity.__wrapped__


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


def _seed_language(session: Session) -> Language:
    now = _now()
    lang = Language(
        id=uuid.uuid4(),
        name="Test Language",
        native_name="Test Language",
        iso_639_3="tst",
        managed=True,
        created_at=now,
        updated_at=now,
    )
    session.add(lang)
    session.flush()
    return lang


def test_activity_items_carry_entity_ids(db_session: Session):
    user = _seed_user(db_session)
    language = _seed_language(db_session)

    lexeme = Lexeme(
        id=uuid.uuid4(),
        language_id=language.id,
        lemma="servus",
        created_by_id=user.id,
        status=LexemeStatus.PUBLISHED,
    )
    db_session.add(lexeme)
    db_session.flush()
    db_session.add(WordForm(id=uuid.uuid4(), lexeme_id=lexeme.id, form="servus", is_lemma=True))

    document = Document(id=uuid.uuid4(), created_by_id=user.id)
    db_session.add(document)
    db_session.flush()
    text = Text(
        id=uuid.uuid4(),
        document_id=document.id,
        language_id=language.id,
        title="A story",
        content="Once upon a time.",
        document_type=DocumentType.STORY,
        created_by_id=user.id,
        is_primary=True,
    )
    db_session.add(text)

    db_session.add(
        UserLanguage(
            user_id=user.id,
            language_id=language.id,
            proficiency_level=ProficiencyLevel.NATIVE,
        )
    )
    db_session.flush()

    items = _get_activity(request=None, language_id=language.id, limit=10, db=db_session)

    by_type = {item.type: item for item in items}
    assert set(by_type) == {"word_added", "text_added", "contributor_joined"}
    assert by_type["word_added"].entity_id == lexeme.id
    assert by_type["word_added"].subject == "servus"
    # Click-through target for a text is its parent document, not the text row.
    assert by_type["text_added"].entity_id == document.id
    assert by_type["text_added"].subject == "A story"
    assert by_type["contributor_joined"].entity_id is None
    assert by_type["contributor_joined"].subject == user.username
    assert by_type["contributor_joined"].detail == "native"


def test_activity_scoped_to_language(db_session: Session):
    user = _seed_user(db_session)
    language = _seed_language(db_session)
    other_language_id = uuid.uuid4()

    items = _get_activity(request=None, language_id=other_language_id, limit=10, db=db_session)
    assert items == []

    db_session.add(
        Lexeme(
            id=uuid.uuid4(),
            language_id=language.id,
            lemma="servus",
            created_by_id=user.id,
            status=LexemeStatus.PUBLISHED,
        )
    )
    db_session.flush()

    assert _get_activity(request=None, language_id=other_language_id, limit=10, db=db_session) == []
    assert len(_get_activity(request=None, language_id=language.id, limit=10, db=db_session)) == 1
