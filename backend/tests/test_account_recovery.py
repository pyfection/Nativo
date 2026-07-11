"""
Tests for password reset and email verification.

The invariants that matter:
- forgot-password answers identically for known and unknown addresses, and
  only known ones get an email (into the dev outbox).
- A reset token sets a new password once; changing the password invalidates
  every outstanding token; garbage tokens are a 400.
- The verification token stamps email_verified_at and survives re-use
  idempotently; it dies if the address changed after issuing.
"""

import json
import os
import re
import uuid
from datetime import UTC, datetime

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

sqlalchemy = pytest.importorskip("sqlalchemy")
from app.api.v1.endpoints.auth import (  # noqa: E402
    forgot_password,
    request_verification,
    reset_password,
    verify_email,
)
from app.database import Base  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.schemas.user import (  # noqa: E402
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from app.services import auth_service  # noqa: E402
from app.utils.security import hash_password, verify_password  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

engine = create_engine("sqlite:///:memory:", future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


@pytest.fixture(autouse=True)
def database_schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


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
    """slowapi's decorator insists on a real starlette Request even for
    direct endpoint calls; build a minimal one."""
    from starlette.requests import Request as StarletteRequest

    return StarletteRequest(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/test",
            "headers": [],
            "query_string": b"",
            "client": ("127.0.0.1", 1234),
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )


def _read_outbox(path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()]


def _token_from(body: str) -> str:
    match = re.search(r"token=([^\s]+)", body)
    assert match, body
    return match.group(1)


def _user(db: Session, email: str = "mat@example.com") -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        username=f"user-{uuid.uuid4().hex[:8]}",
        hashed_password=hash_password("oldpassword1"),
        role=UserRole.PUBLIC,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(user)
    db.flush()
    return user


async def test_forgot_password_does_not_leak_accounts(db: Session, outbox):
    _user(db)
    known = await forgot_password(
        _request(), ForgotPasswordRequest(email="mat@example.com"), db=db
    )
    unknown = await forgot_password(
        _request(), ForgotPasswordRequest(email="nobody@example.com"), db=db
    )
    assert known == unknown  # identical response either way
    sent = _read_outbox(outbox)
    assert len(sent) == 1 and sent[0]["to"] == "mat@example.com"


async def test_reset_flow_and_token_invalidation(db: Session, outbox):
    user = _user(db)
    await forgot_password(_request(), ForgotPasswordRequest(email=user.email), db=db)
    token = _token_from(_read_outbox(outbox)[0]["body"])

    await reset_password(ResetPasswordRequest(token=token, new_password="newpassword1"), db=db)
    db.refresh(user)
    assert verify_password("newpassword1", user.hashed_password)

    # The same token is dead now — it was bound to the old password hash.
    with pytest.raises(HTTPException) as exc:
        await reset_password(ResetPasswordRequest(token=token, new_password="another123"), db=db)
    assert exc.value.status_code == 400


async def test_reset_rejects_garbage_and_expired_tokens(db: Session, monkeypatch):
    _user(db)
    with pytest.raises(HTTPException) as exc:
        await reset_password(
            ResetPasswordRequest(token="not-a-token", new_password="whatever12"), db=db
        )
    assert exc.value.status_code == 400

    # Simulate expiry by shrinking the max age to zero.
    user = db.query(User).first()
    token = auth_service.make_password_reset_token(user)
    monkeypatch.setattr(auth_service, "PASSWORD_RESET_MAX_AGE", -1)
    with pytest.raises(HTTPException) as exc:
        await reset_password(ResetPasswordRequest(token=token, new_password="whatever12"), db=db)
    assert exc.value.status_code == 400


async def test_email_verification_flow(db: Session, outbox):
    user = _user(db)
    assert user.email_verified_at is None

    await request_verification(_request(), current_user=user)
    token = _token_from(_read_outbox(outbox)[0]["body"])

    verified = await verify_email(VerifyEmailRequest(token=token), db=db)
    assert verified.email_verified_at is not None

    # Clicking the link twice is fine (idempotent), and re-requesting a
    # verification email once verified is a 400.
    again = await verify_email(VerifyEmailRequest(token=token), db=db)
    assert again.email_verified_at == verified.email_verified_at
    with pytest.raises(HTTPException) as exc:
        await request_verification(_request(), current_user=user)
    assert exc.value.status_code == 400


async def test_verification_token_dies_if_email_changes(db: Session):
    user = _user(db)
    token = auth_service.make_email_verify_token(user)
    user.email = "changed@example.com"
    db.flush()

    with pytest.raises(HTTPException) as exc:
        await verify_email(VerifyEmailRequest(token=token), db=db)
    assert exc.value.status_code == 400
