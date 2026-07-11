"""
Tests for text suggestions (suggester tier, Phase B).

The contract under test:
- A signed-in user WITHOUT can_edit creating a document/translation gets a
  Text with status PENDING_REVIEW (previously a 403); an editor's text is
  born PUBLISHED.
- Pending texts are invisible on the public read paths (document detail,
  document list) to everyone but their author.
- Approving publishes the text; rejecting archives it and keeps the reason
  in notes; only pending texts can be reviewed.
- The queue lists pending texts with the suggester's username and requires
  verify permission.
"""

import os
import uuid
from datetime import UTC, datetime

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

sqlalchemy = pytest.importorskip("sqlalchemy")
from app.api.v1.endpoints.documents import (  # noqa: E402
    add_translation,
    approve_text,
    create_document,
    get_document,
    list_documents,
    list_text_suggestions,
    reject_text,
)
from app.database import Base  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.text import DocumentType, TextStatus  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.user_language import ProficiencyLevel, UserLanguage  # noqa: E402
from app.schemas.text import TextCreate, TextRejection  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

engine = create_engine("sqlite:///:memory:", future=True)
# autoflush=False mirrors the app session (app/database.py).
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


def _user(db: Session, role: UserRole = UserRole.PUBLIC) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"u-{uuid.uuid4()}@example.com",
        username=f"user-{uuid.uuid4().hex[:8]}",
        hashed_password="x",
        role=role,
        is_active=True,
        is_superuser=role == UserRole.ADMIN,
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(user)
    db.flush()
    return user


def _language(db: Session) -> Language:
    lang = Language(
        id=uuid.uuid4(), name=f"L-{uuid.uuid4().hex[:6]}", created_at=_now(), updated_at=_now()
    )
    db.add(lang)
    db.flush()
    return lang


def _join(
    db: Session, user: User, lang: Language, can_edit=False, can_verify=False
) -> UserLanguage:
    ul = UserLanguage(
        user_id=user.id,
        language_id=lang.id,
        proficiency_level=ProficiencyLevel.INTERMEDIATE,
        can_edit=can_edit,
        can_verify=can_verify,
    )
    db.add(ul)
    db.flush()
    return ul


def _payload(lang: Language, title: str, content: str = "A gcihd mid a boa voat.") -> TextCreate:
    return TextCreate(
        title=title,
        content=content,
        document_type=DocumentType.STORY,
        language_id=lang.id,
    )


async def _suggest_document(db, suggester, lang, title):
    return await create_document(_payload(lang, title), current_user=suggester, db=db)


async def test_non_editor_document_lands_pending(db: Session):
    lang = _language(db)
    suggester = _user(db)
    _join(db, suggester, lang)  # viewer only

    document = await _suggest_document(db, suggester, lang, "Mei gcihd")
    assert document.texts[0].status == TextStatus.PENDING_REVIEW
    assert document.texts[0].created_by_id == suggester.id


async def test_editor_document_is_published(db: Session):
    lang = _language(db)
    editor = _user(db)
    _join(db, editor, lang, can_edit=True)

    document = await create_document(_payload(lang, "Lektion"), current_user=editor, db=db)
    assert document.texts[0].status == TextStatus.PUBLISHED


async def test_pending_translation_hidden_from_public_reads(db: Session):
    lang = _language(db)
    other_lang = _language(db)
    editor = _user(db)
    _join(db, editor, lang, can_edit=True)
    suggester = _user(db)
    _join(db, suggester, other_lang)

    document = await create_document(_payload(lang, "Lektion"), current_user=editor, db=db)
    pending = await add_translation(
        document.id, _payload(other_lang, "Lección"), current_user=suggester, db=db
    )
    assert pending.status == TextStatus.PENDING_REVIEW

    # Anonymous readers only see the published text...
    anon_view = await get_document(document.id, current_user=None, db=db)
    assert [t.title for t in anon_view.texts] == ["Lektion"]

    # ...the author still sees their own pending suggestion.
    author_view = await get_document(document.id, current_user=suggester, db=db)
    assert {t.title for t in author_view.texts} == {"Lektion", "Lección"}


async def test_document_with_only_pending_text_hidden_entirely(db: Session):
    lang = _language(db)
    suggester = _user(db)
    _join(db, suggester, lang)

    document = await _suggest_document(db, suggester, lang, "No ned gnemigt")

    with pytest.raises(HTTPException) as exc:
        await get_document(document.id, current_user=None, db=db)
    assert exc.value.status_code == 404

    listed = await list_documents(
        skip=0, limit=100, language_id=lang.id, search_term=None, current_user=None, db=db
    )
    assert listed == []

    # The author sees it in the list.
    listed = await list_documents(
        skip=0, limit=100, language_id=lang.id, search_term=None, current_user=suggester, db=db
    )
    assert [item.title for item in listed] == ["No ned gnemigt"]


async def test_approve_publishes(db: Session):
    lang = _language(db)
    suggester = _user(db)
    _join(db, suggester, lang)
    reviewer = _user(db)
    _join(db, reviewer, lang, can_verify=True)

    document = await _suggest_document(db, suggester, lang, "Mei gcihd")
    text = document.texts[0]
    approved = await approve_text(document.id, text.id, current_user=reviewer, db=db)
    assert approved.status == TextStatus.PUBLISHED

    anon_view = await get_document(document.id, current_user=None, db=db)
    assert [t.title for t in anon_view.texts] == ["Mei gcihd"]

    # Approving twice is a 400 — it's no longer pending.
    with pytest.raises(HTTPException) as exc:
        await approve_text(document.id, text.id, current_user=reviewer, db=db)
    assert exc.value.status_code == 400


async def test_reject_archives_with_reason(db: Session):
    lang = _language(db)
    suggester = _user(db)
    _join(db, suggester, lang)
    reviewer = _user(db)
    _join(db, reviewer, lang, can_verify=True)

    document = await _suggest_document(db, suggester, lang, "Mei gcihd")
    text = document.texts[0]
    rejected = await reject_text(
        document.id,
        text.id,
        payload=TextRejection(reason="duplicate of Lektion 1"),
        current_user=reviewer,
        db=db,
    )
    assert rejected.status == TextStatus.ARCHIVED
    assert "Rejected: duplicate of Lektion 1" in (rejected.notes or "")

    with pytest.raises(HTTPException) as exc:
        await reject_text(document.id, text.id, payload=None, current_user=reviewer, db=db)
    assert exc.value.status_code == 400


async def test_queue_lists_pending_with_username_and_requires_verify(db: Session):
    lang = _language(db)
    suggester = _user(db)
    _join(db, suggester, lang)
    reviewer = _user(db)
    _join(db, reviewer, lang, can_verify=True)

    await _suggest_document(db, suggester, lang, "Gcihd oans")
    await _suggest_document(db, suggester, lang, "Gcihd dsvoa")

    queue = await list_text_suggestions(lang.id, current_user=reviewer, db=db)
    assert [item.title for item in queue] == ["Gcihd oans", "Gcihd dsvoa"]
    assert all(item.creator_username == suggester.username for item in queue)

    with pytest.raises(HTTPException) as exc:
        await list_text_suggestions(lang.id, current_user=suggester, db=db)
    assert exc.value.status_code == 403
