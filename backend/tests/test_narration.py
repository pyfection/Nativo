"""
Tests for text narration audio (Audio.text_id).

Uploads attach to a Text with edit permission on the text's language;
narrations list publicly per text; deleting removes the blob too.
"""

import io
import os
import uuid
from datetime import UTC, datetime

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

sqlalchemy = pytest.importorskip("sqlalchemy")
from fastapi import HTTPException, UploadFile  # noqa: E402
from starlette.datastructures import Headers  # noqa: E402

from app.api.v1.endpoints.audio import (  # noqa: E402
    delete_audio,
    list_text_audio,
    upload_audio,
)
from app.database import Base  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.text import DocumentType, Text  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.user_language import ProficiencyLevel, UserLanguage  # noqa: E402
from app.utils import file_storage  # noqa: E402
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
def local_uploads(tmp_path, monkeypatch):
    monkeypatch.delenv("BUCKET_NAME", raising=False)
    monkeypatch.delenv("S3_BUCKET", raising=False)
    monkeypatch.setattr(file_storage, "UPLOADS_ROOT", tmp_path)
    return tmp_path


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


def _language_with_text(db: Session, creator: User) -> tuple[Language, Text]:
    lang = Language(
        id=uuid.uuid4(), name=f"L-{uuid.uuid4().hex[:6]}", created_at=_now(), updated_at=_now()
    )
    db.add(lang)
    db.flush()
    text = Text(
        id=uuid.uuid4(),
        title="Lektion",
        content="A gcihd.",
        document_type=DocumentType.STORY,
        language_id=lang.id,
        created_by_id=creator.id,
    )
    db.add(text)
    db.flush()
    return lang, text


def _join(db: Session, user: User, lang: Language, can_edit=False) -> UserLanguage:
    ul = UserLanguage(
        user_id=user.id,
        language_id=lang.id,
        proficiency_level=ProficiencyLevel.INTERMEDIATE,
        can_edit=can_edit,
    )
    db.add(ul)
    db.flush()
    return ul


def _upload_file(data: bytes = b"opus-bytes") -> UploadFile:
    return UploadFile(
        file=io.BytesIO(data),
        filename="narration.webm",
        headers=Headers({"content-type": "audio/webm"}),
    )


async def test_editor_uploads_narration(db: Session, local_uploads):
    editor = _user(db)
    lang, text = _language_with_text(db, editor)
    _join(db, editor, lang, can_edit=True)

    result = await upload_audio(
        file=_upload_file(),
        word_form_id=None,
        text_id=text.id,
        duration=7,
        is_primary=False,
        current_user=editor,
        db=db,
    )
    assert result.text_id == text.id
    on_disk = local_uploads / result.file_path.removeprefix("/uploads/")
    assert on_disk.read_bytes() == b"opus-bytes"

    listed = list_text_audio(text.id, db=db)
    assert [a.id for a in listed] == [result.id]
    assert listed[0].uploader_username == editor.username

    # Deleting the narration removes the blob as well.
    delete_audio(result.id, current_user=editor, db=db)
    assert not on_disk.exists()
    assert list_text_audio(text.id, db=db) == []


async def test_narration_requires_edit_permission(db: Session):
    editor = _user(db)
    lang, text = _language_with_text(db, editor)
    viewer = _user(db)
    _join(db, viewer, lang)  # no can_edit

    with pytest.raises(HTTPException) as exc:
        await upload_audio(
            file=_upload_file(),
            word_form_id=None,
            text_id=text.id,
            duration=None,
            is_primary=False,
            current_user=viewer,
            db=db,
        )
    assert exc.value.status_code == 403


async def test_cannot_attach_to_form_and_text(db: Session):
    editor = _user(db)
    lang, text = _language_with_text(db, editor)
    _join(db, editor, lang, can_edit=True)

    with pytest.raises(HTTPException) as exc:
        await upload_audio(
            file=_upload_file(),
            word_form_id=uuid.uuid4(),
            text_id=text.id,
            duration=None,
            is_primary=False,
            current_user=editor,
            db=db,
        )
    assert exc.value.status_code == 400


async def test_narration_unknown_text_404s(db: Session):
    editor = _user(db)
    with pytest.raises(HTTPException) as exc:
        await upload_audio(
            file=_upload_file(),
            word_form_id=None,
            text_id=uuid.uuid4(),
            duration=None,
            is_primary=False,
            current_user=editor,
            db=db,
        )
    assert exc.value.status_code == 404
