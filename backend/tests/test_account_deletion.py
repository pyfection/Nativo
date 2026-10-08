"""
Tests for account deletion (POST /auth/delete-account).

The invariants that matter:
- Contributions stay, still pointing at the user row; the row is scrubbed
  (placeholder username/email, unusable password, inactive, no role).
- Personal data goes: API tokens, language memberships, learning progress.
- The old credentials stop working: login, API token, password reset.
- It needs the current password and a login session (not an API token),
  and the last admin can't delete themselves.
"""

import os
import uuid
from datetime import UTC, datetime

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

sqlalchemy = pytest.importorskip("sqlalchemy")
from app.api.deps import get_current_active_user, get_current_user  # noqa: E402
from app.api.v1.endpoints.auth import (  # noqa: E402
    delete_my_account,
    forgot_password,
    login,
)
from app.database import Base  # noqa: E402
from app.limiter import limiter  # noqa: E402
from app.models.api_token import ApiToken  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.learning import (  # noqa: E402
    DifficultyRating,
    UserLexemeKnowledge,
    UserTextProgress,
)
from app.models.text import DocumentType, Text  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.user_language import ProficiencyLevel, UserLanguage  # noqa: E402
from app.models.word import Lexeme, LexemeStatus  # noqa: E402
from app.schemas.user import DeleteAccountRequest, ForgotPasswordRequest  # noqa: E402
from app.services import auth_service  # noqa: E402
from app.utils.security import hash_password  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from fastapi.security import OAuth2PasswordRequestForm  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

engine = create_engine("sqlite:///:memory:", future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)

PASSWORD = "correct horse battery"


@pytest.fixture(autouse=True)
def database_schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def reset_rate_limits():
    limiter.reset()


@pytest.fixture(autouse=True)
def outbox(tmp_path, monkeypatch):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.setenv("EMAIL_OUTBOX_DIR", str(tmp_path))
    return tmp_path / "outbox.jsonl"


@pytest.fixture
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _request():
    """slowapi's decorator insists on a real starlette Request."""
    from starlette.requests import Request as StarletteRequest

    return StarletteRequest(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/delete-account",
            "headers": [],
            "query_string": b"",
            "client": ("127.0.0.1", 1234),
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )


def _user(db: Session, name: str, role: UserRole = UserRole.PUBLIC, superuser=False) -> User:
    now = datetime.now(UTC)
    user = User(
        id=uuid.uuid4(),
        email=f"{name}@example.com",
        username=name,
        hashed_password=hash_password(PASSWORD),
        role=role,
        is_active=True,
        is_superuser=superuser,
        email_verified_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    return user


def _session_token(user: User) -> str:
    return auth_service.create_access_token(user.id, user.role)


async def _delete(db: Session, user: User, password: str = PASSWORD, token: str | None = None):
    return await delete_my_account(
        _request(),
        DeleteAccountRequest(password=password),
        raw_token=token or _session_token(user),
        current_user=user,
        db=db,
    )


def _contributions(db: Session, user: User) -> tuple[Lexeme, Text]:
    """A word, a text, a membership, learning progress and an API token."""
    language = Language(id=uuid.uuid4(), name="Bavarian")
    db.add(language)
    db.flush()
    lexeme = Lexeme(
        id=uuid.uuid4(),
        language_id=language.id,
        lemma="dahoam",
        created_by_id=user.id,
        status=LexemeStatus.PUBLISHED,
    )
    document = Document(id=uuid.uuid4(), created_by_id=user.id)
    db.add_all([lexeme, document])
    db.flush()
    text = Text(
        id=uuid.uuid4(),
        document_id=document.id,
        language_id=language.id,
        title="Da Hund",
        content="I bin dahoam",
        document_type=DocumentType.STORY,
        created_by_id=user.id,
        is_primary=True,
    )
    db.add(text)
    db.flush()
    db.add_all(
        [
            UserLanguage(
                user_id=user.id,
                language_id=language.id,
                proficiency_level=ProficiencyLevel.NATIVE,
                can_edit=True,
                can_verify=True,
            ),
            UserLexemeKnowledge(user_id=user.id, lexeme_id=lexeme.id, score=1),
            UserTextProgress(
                user_id=user.id,
                text_id=text.id,
                difficulty_rating=DifficultyRating.EASY,
                completed_at=datetime.now(UTC),
            ),
        ]
    )
    db.commit()
    auth_service.create_api_token(db, user, "laptop")
    return lexeme, text


async def test_contributions_stay_and_personal_data_goes(db):
    user = _user(db, "mat")
    lexeme, text = _contributions(db, user)

    await _delete(db, user)

    db.expire_all()
    scrubbed = db.get(User, user.id)
    assert scrubbed.username.startswith("deleted-user-")
    assert scrubbed.email.endswith("@deleted.invalid")
    assert "mat" not in scrubbed.username and "mat" not in scrubbed.email
    assert scrubbed.is_active is False
    assert scrubbed.role == UserRole.PUBLIC
    assert scrubbed.email_verified_at is None

    # Contributions are still there, credited to the scrubbed row.
    assert db.get(Lexeme, lexeme.id).created_by_id == user.id
    assert db.get(Text, text.id).created_by_id == user.id

    for model in (ApiToken, UserLanguage, UserLexemeKnowledge, UserTextProgress):
        assert db.query(model).filter(model.user_id == user.id).count() == 0, model


async def test_old_credentials_stop_working(db, outbox):
    user = _user(db, "mat")
    session_token = _session_token(user)
    _, api_token = auth_service.create_api_token(db, user, "laptop")

    await _delete(db, user)

    for username in ("mat", "mat@example.com"):
        with pytest.raises(HTTPException) as exc:
            await login(OAuth2PasswordRequestForm(username=username, password=PASSWORD), db=db)
        assert exc.value.status_code == 401

    # A session token issued before deletion is refused (inactive)…
    still_signed_in = await get_current_user(token=session_token, db=db)
    with pytest.raises(HTTPException) as exc:
        await get_current_active_user(still_signed_in)
    assert exc.value.status_code == 403
    # …and the API token is gone.
    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=api_token, db=db)
    assert exc.value.status_code == 401

    # No reset email goes to the old address.
    await forgot_password(_request(), ForgotPasswordRequest(email="mat@example.com"), db=db)
    assert not outbox.exists()


async def test_wrong_password_changes_nothing(db):
    user = _user(db, "mat")

    with pytest.raises(HTTPException) as exc:
        await _delete(db, user, password="not my password")
    assert exc.value.status_code == 400

    db.expire_all()
    assert db.get(User, user.id).username == "mat"
    assert db.get(User, user.id).is_active is True


async def test_api_token_cannot_delete_account(db):
    user = _user(db, "mat")
    _, api_token = auth_service.create_api_token(db, user, "laptop")

    with pytest.raises(HTTPException) as exc:
        await _delete(db, user, token=api_token)
    assert exc.value.status_code == 403

    db.expire_all()
    assert db.get(User, user.id).is_active is True


async def test_last_admin_cannot_delete_themselves(db):
    admin = _user(db, "admin", role=UserRole.ADMIN)

    with pytest.raises(HTTPException) as exc:
        await _delete(db, admin)
    assert exc.value.status_code == 409

    # Once there's another admin (here a superuser), it works.
    _user(db, "root", superuser=True)
    await _delete(db, admin)
    db.expire_all()
    assert db.get(User, admin.id).is_active is False
