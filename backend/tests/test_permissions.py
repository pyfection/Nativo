import os
import uuid
from datetime import UTC, datetime

import pytest

# auth_service imports app.config, whose Settings require these at import time.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")

sqlalchemy = pytest.importorskip("sqlalchemy")
from app.database import Base  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.user_language import ProficiencyLevel, UserLanguage  # noqa: E402
from app.services.auth_service import (  # noqa: E402
    can_user_edit_language,
    can_user_verify_language,
    require_language_edit_permission,
    require_language_verify_permission,
)
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


def _user(session, *, role=UserRole.PUBLIC, is_superuser=False) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@e",
        username=str(uuid.uuid4()),
        hashed_password="h",
        role=role,
        is_active=True,
        is_superuser=is_superuser,
        created_at=_now(),
        updated_at=_now(),
    )
    session.add(user)
    return user


def _language(session) -> Language:
    lang = Language(
        id=uuid.uuid4(),
        name=str(uuid.uuid4()),
        native_name="x",
        iso_639_3=None,  # unique column — leave null so test languages don't collide
        managed=True,
        created_at=_now(),
        updated_at=_now(),
    )
    session.add(lang)
    return lang


def _grant(session, user, language, *, can_edit=False, can_verify=False) -> None:
    session.add(
        UserLanguage(
            user_id=user.id,
            language_id=language.id,
            proficiency_level=ProficiencyLevel.FLUENT,
            can_edit=can_edit,
            can_verify=can_verify,
        )
    )


# ---------------------------------------------------------------------------
# can_user_edit_language
# ---------------------------------------------------------------------------


def test_superuser_can_edit_any_language(db_session):
    user = _user(db_session, role=UserRole.PUBLIC, is_superuser=True)
    lang = _language(db_session)
    db_session.commit()
    assert can_user_edit_language(db_session, user.id, lang.id) is True


def test_admin_role_can_edit_any_language(db_session):
    user = _user(db_session, role=UserRole.ADMIN)
    lang = _language(db_session)
    db_session.commit()
    assert can_user_edit_language(db_session, user.id, lang.id) is True


def test_granted_editor_can_edit_that_language(db_session):
    user = _user(db_session)
    lang = _language(db_session)
    db_session.flush()
    _grant(db_session, user, lang, can_edit=True)
    db_session.commit()
    assert can_user_edit_language(db_session, user.id, lang.id) is True


def test_user_without_grant_cannot_edit(db_session):
    user = _user(db_session)
    lang = _language(db_session)
    db_session.commit()
    assert can_user_edit_language(db_session, user.id, lang.id) is False


def test_grant_without_can_edit_cannot_edit(db_session):
    user = _user(db_session)
    lang = _language(db_session)
    db_session.flush()
    _grant(db_session, user, lang, can_edit=False, can_verify=True)
    db_session.commit()
    assert can_user_edit_language(db_session, user.id, lang.id) is False


def test_edit_grant_is_per_language(db_session):
    user = _user(db_session)
    lang_a = _language(db_session)
    lang_b = _language(db_session)
    db_session.flush()
    _grant(db_session, user, lang_a, can_edit=True)
    db_session.commit()
    assert can_user_edit_language(db_session, user.id, lang_a.id) is True
    assert can_user_edit_language(db_session, user.id, lang_b.id) is False


# ---------------------------------------------------------------------------
# can_user_verify_language
# ---------------------------------------------------------------------------


def test_verify_requires_can_verify_flag(db_session):
    user = _user(db_session)
    lang = _language(db_session)
    db_session.flush()
    _grant(db_session, user, lang, can_edit=True, can_verify=False)
    db_session.commit()
    assert can_user_verify_language(db_session, user.id, lang.id) is False


def test_superuser_can_verify(db_session):
    user = _user(db_session, is_superuser=True)
    lang = _language(db_session)
    db_session.commit()
    assert can_user_verify_language(db_session, user.id, lang.id) is True


# ---------------------------------------------------------------------------
# require_* raise 403 when not permitted
# ---------------------------------------------------------------------------


def test_require_edit_raises_for_unauthorized(db_session):
    user = _user(db_session)
    lang = _language(db_session)
    db_session.commit()
    with pytest.raises(HTTPException) as exc:
        require_language_edit_permission(db_session, user, lang.id)
    assert exc.value.status_code == 403


def test_require_edit_passes_for_editor(db_session):
    user = _user(db_session)
    lang = _language(db_session)
    db_session.flush()
    _grant(db_session, user, lang, can_edit=True)
    db_session.commit()
    # Should not raise.
    require_language_edit_permission(db_session, user, lang.id)


def test_require_verify_raises_for_editor_without_verify(db_session):
    user = _user(db_session)
    lang = _language(db_session)
    db_session.flush()
    _grant(db_session, user, lang, can_edit=True, can_verify=False)
    db_session.commit()
    with pytest.raises(HTTPException) as exc:
        require_language_verify_permission(db_session, user, lang.id)
    assert exc.value.status_code == 403
