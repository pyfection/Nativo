"""
Tests for the suggester tier: word suggestions, review queue, promotion.

The contract under test:
- A signed-in user WITHOUT can_edit creates a lexeme -> PENDING_REVIEW
  (previously a 403); an editor's create keeps the default flow (DRAFT).
- Approving (the existing verify endpoint) publishes and, once the
  suggester has AUTO_PROMOTE_AFTER_APPROVALS approved suggestions in the
  language, grants can_edit on their membership row.
- Rejecting archives the suggestion and keeps the reason in notes.
- The queue lists pending suggestions with the suggester's username and
  requires verify permission.
"""

import os
import uuid
from datetime import UTC, datetime

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

sqlalchemy = pytest.importorskip("sqlalchemy")
from fastapi import HTTPException  # noqa: E402

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
from app.models.word import LexemeStatus  # noqa: E402
from app.schemas.word import (  # noqa: E402
    LexemeCreate,
    LexemeRejection,
    WordFormCreateNested,
)
from app.services import auth_service  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

engine = create_engine("sqlite:///:memory:", future=True)
# autoflush=False mirrors the app session (app/database.py); the promotion
# helper must flush explicitly, and this config would catch a regression.
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
    lang = Language(id=uuid.uuid4(), name=f"L-{uuid.uuid4().hex[:6]}", created_at=_now(), updated_at=_now())
    db.add(lang)
    db.flush()
    return lang


def _join(db: Session, user: User, lang: Language, can_edit=False, can_verify=False) -> UserLanguage:
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


def _payload(lang: Language, lemma: str) -> LexemeCreate:
    return LexemeCreate(
        language_id=lang.id,
        lemma=lemma,
        lemma_form=WordFormCreateNested(form=lemma, is_lemma=True),
    )


async def _suggest(db, suggester, lang, lemma):
    return await create_lexeme(_payload(lang, lemma), current_user=suggester, db=db)


async def test_non_editor_create_lands_pending(db: Session):
    lang = _language(db)
    suggester = _user(db)
    _join(db, suggester, lang)  # viewer only

    lexeme = await _suggest(db, suggester, lang, "servus")
    assert lexeme.status == LexemeStatus.PENDING_REVIEW
    assert lexeme.created_by_id == suggester.id


async def test_editor_create_keeps_default_flow(db: Session):
    lang = _language(db)
    editor = _user(db)
    _join(db, editor, lang, can_edit=True)

    lexeme = await create_lexeme(_payload(lang, "servus"), current_user=editor, db=db)
    assert lexeme.status == LexemeStatus.DRAFT  # unchanged existing behaviour


async def test_approve_publishes_and_promotes_after_threshold(db: Session, monkeypatch):
    monkeypatch.setattr(auth_service, "AUTO_PROMOTE_AFTER_APPROVALS", 3)
    lang = _language(db)
    suggester = _user(db)
    membership = _join(db, suggester, lang)
    reviewer = _user(db)
    _join(db, reviewer, lang, can_verify=True)

    for i in range(3):
        lexeme = await _suggest(db, suggester, lang, f"voat{i}")
        approved = await verify_lexeme(lexeme.id, current_user=reviewer, db=db)
        assert approved.status == LexemeStatus.PUBLISHED
        assert approved.is_verified
        assert approved.verified_by_id == reviewer.id

    db.refresh(membership)
    assert membership.can_edit  # promoted at the third approval

    # And the next create goes straight to the editor flow.
    lexeme = await _suggest(db, suggester, lang, "extra")
    assert lexeme.status == LexemeStatus.DRAFT


async def test_no_promotion_below_threshold(db: Session, monkeypatch):
    monkeypatch.setattr(auth_service, "AUTO_PROMOTE_AFTER_APPROVALS", 5)
    lang = _language(db)
    suggester = _user(db)
    membership = _join(db, suggester, lang)
    reviewer = _user(db)
    _join(db, reviewer, lang, can_verify=True)

    lexeme = await _suggest(db, suggester, lang, "servus")
    await verify_lexeme(lexeme.id, current_user=reviewer, db=db)
    db.refresh(membership)
    assert not membership.can_edit


async def test_reject_archives_with_reason(db: Session):
    lang = _language(db)
    suggester = _user(db)
    _join(db, suggester, lang)
    reviewer = _user(db)
    _join(db, reviewer, lang, can_verify=True)

    lexeme = await _suggest(db, suggester, lang, "servus")
    rejected = await reject_lexeme(
        lexeme.id,
        payload=LexemeRejection(reason="already exists as Servus"),
        current_user=reviewer,
        db=db,
    )
    assert rejected.status == LexemeStatus.ARCHIVED
    assert "Rejected: already exists as Servus" in (rejected.notes or "")

    # Only pending suggestions can be rejected.
    with pytest.raises(HTTPException) as exc:
        await reject_lexeme(lexeme.id, payload=None, current_user=reviewer, db=db)
    assert exc.value.status_code == 400


async def test_queue_lists_pending_with_username_and_requires_verify(db: Session):
    lang = _language(db)
    suggester = _user(db)
    _join(db, suggester, lang)
    reviewer = _user(db)
    _join(db, reviewer, lang, can_verify=True)

    await _suggest(db, suggester, lang, "servus")
    await _suggest(db, suggester, lang, "bredsn")

    queue = await list_suggestions(lang.id, current_user=reviewer, db=db)
    assert [item.lemma for item in queue] == ["servus", "bredsn"]
    assert all(item.creator_username == suggester.username for item in queue)
    assert all(item.forms for item in queue)

    with pytest.raises(HTTPException) as exc:
        await list_suggestions(lang.id, current_user=suggester, db=db)
    assert exc.value.status_code == 403
