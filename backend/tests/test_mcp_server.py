"""
Tests for the MCP server and the personal API tokens that authenticate it.

The invariants that matter:
- Read tools work anonymously and only see published content.
- Write tools need a token; with one they follow the REST permission model —
  editors publish, everyone else's words land as pending suggestions.
- Over HTTP the caller is whoever the request's bearer token belongs to;
  the stdio token is never consulted for HTTP requests.
- API tokens are stored hashed, shown once, can't mint more tokens, and stop
  working when revoked.
"""

import os
import uuid
from datetime import UTC, datetime

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

sqlalchemy = pytest.importorskip("sqlalchemy")
import httpx2  # noqa: E402
from app import mcp_server  # noqa: E402
from app.api.deps import get_current_user  # noqa: E402
from app.api.v1.endpoints.auth import (  # noqa: E402
    create_personal_api_token,
    list_api_tokens,
    revoke_api_token,
)
from app.database import Base  # noqa: E402
from app.models.api_token import ApiToken  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.user_language import ProficiencyLevel, UserLanguage  # noqa: E402
from app.models.word import Lexeme, LexemeStatus, SpellingVariant, WordForm  # noqa: E402
from app.schemas.user import ApiTokenCreate  # noqa: E402
from app.services.auth_service import create_access_token, create_api_token  # noqa: E402
from app.utils.text_normalize import fold_for_match  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from mcp import Client  # noqa: E402
from mcp.client.streamable_http import streamable_http_client  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

# StaticPool: sync tools may run on a worker thread, and every thread must
# see the same in-memory database.
engine = create_engine(
    "sqlite:///:memory:",
    future=True,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


@pytest.fixture(autouse=True)
def database_schema(monkeypatch):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(mcp_server, "session_factory", SessionLocal)
    monkeypatch.setattr(mcp_server, "_local_token", None)
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


def _user(db: Session, name: str, role: UserRole = UserRole.PUBLIC) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"{name}@example.com",
        username=name,
        hashed_password="hashed",
        role=role,
        is_active=True,
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(user)
    db.flush()
    return user


def _language(db: Session, name: str = "Bavarian") -> Language:
    language = Language(
        id=uuid.uuid4(), name=name, is_endangered=True, created_at=_now(), updated_at=_now()
    )
    db.add(language)
    db.flush()
    return language


def _lexeme(
    db: Session,
    language: Language,
    creator: User,
    form: str,
    status: LexemeStatus = LexemeStatus.PUBLISHED,
) -> Lexeme:
    lexeme = Lexeme(
        id=uuid.uuid4(),
        language_id=language.id,
        lemma=form,
        created_by_id=creator.id,
        status=status,
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(lexeme)
    db.flush()
    db.add(
        WordForm(
            id=uuid.uuid4(),
            lexeme_id=lexeme.id,
            form=form,
            is_lemma=True,
            created_at=_now(),
            updated_at=_now(),
        )
    )
    db.flush()
    return lexeme


def _grant_edit(db: Session, user: User, language: Language) -> None:
    db.add(
        UserLanguage(
            user_id=user.id,
            language_id=language.id,
            proficiency_level=ProficiencyLevel.NATIVE,
            can_edit=True,
            can_verify=True,
        )
    )
    db.flush()


def _word_payload(language: Language, lemma: str) -> dict:
    word = {"language_id": str(language.id), "lemma": lemma, "lemma_form": {"form": lemma}}
    return {"word": word}


async def _call(tool: str, args: dict | None = None, token: str | None = None):
    """Call a tool in-process. In-memory transport has no HTTP headers, so
    the caller is `_local_token` — the same path stdio takes."""
    mcp_server._local_token = token
    async with Client(mcp_server.mcp) as client:
        return await client.call_tool(tool, args or {})


# ---------------------------------------------------------------------------
# Read tools
# ---------------------------------------------------------------------------


async def test_read_tools_work_anonymously_and_hide_unpublished(db: Session):
    author = _user(db, "author")
    language = _language(db)
    published = _lexeme(db, language, author, "aih")
    _lexeme(db, language, author, "aihgeh", status=LexemeStatus.PENDING_REVIEW)
    db.add(
        SpellingVariant(
            id=uuid.uuid4(),
            word_form_id=published.forms[0].id,
            variant="eich",
            normalized=fold_for_match("eich"),
            created_at=_now(),
            updated_at=_now(),
        )
    )
    db.commit()

    result = await _call("list_languages")
    assert not result.is_error
    assert [lang["name"] for lang in result.structured_content["result"]] == ["Bavarian"]

    # A non-standard spelling finds the standard entry; the pending one stays hidden.
    result = await _call("search_words", {"query": "eich", "language_id": str(language.id)})
    assert [w["lemma"] for w in result.structured_content["result"]] == ["aih"]
    result = await _call("search_words", {"query": "aih"})
    assert [w["lemma"] for w in result.structured_content["result"]] == ["aih"]

    result = await _call("get_word", {"lexeme_id": str(published.id)})
    assert result.structured_content["lemma"] == "aih"
    assert result.structured_content["forms"][0]["form"] == "aih"


async def test_check_spelling_proposes_standard_forms_without_saving(db: Session):
    author = _user(db, "author")
    language = _language(db)
    lexeme = _lexeme(db, language, author, "aih")
    db.add(
        SpellingVariant(
            id=uuid.uuid4(),
            word_form_id=lexeme.forms[0].id,
            variant="eich",
            normalized=fold_for_match("eich"),
            created_at=_now(),
            updated_at=_now(),
        )
    )
    db.commit()

    result = await _call(
        "check_spelling", {"language_id": str(language.id), "text": "i sog eich wos"}
    )
    corrections = result.structured_content["result"]
    assert len(corrections) == 1
    assert corrections[0]["original"] == "eich"
    assert corrections[0]["candidates"][0]["standard_form"] == "aih"

    result = await _call("resolve_spelling", {"language_id": str(language.id), "word": "aih"})
    assert result.structured_content["already_standard"] is True

    from app.models.text import Text

    assert db.query(Text).count() == 0


async def test_unknown_ids_are_tool_errors_not_crashes(db: Session):
    result = await _call("get_word", {"lexeme_id": str(uuid.uuid4())})
    assert result.is_error
    assert "Lexeme not found" in result.content[0].text


# ---------------------------------------------------------------------------
# Write tools
# ---------------------------------------------------------------------------


async def test_writes_need_a_token(db: Session):
    language = _language(db)
    db.commit()

    result = await _call("create_word", _word_payload(language, "Semmö"))
    assert result.is_error
    assert "API token" in result.content[0].text
    assert db.query(Lexeme).count() == 0


async def test_editor_publishes_and_non_editor_suggests(db: Session):
    language = _language(db)
    editor = _user(db, "editor")
    _grant_edit(db, editor, language)
    stranger = _user(db, "stranger")
    db.commit()
    _, editor_token = create_api_token(db, editor, "mcp")
    _, stranger_token = create_api_token(db, stranger, "mcp")

    result = await _call("create_word", _word_payload(language, "Semmö"), token=editor_token)
    assert not result.is_error, result.content
    # The editor path uses the model default, not PENDING_REVIEW.
    assert result.structured_content["status"] != LexemeStatus.PENDING_REVIEW.value

    result = await _call("create_word", _word_payload(language, "Brezn"), token=stranger_token)
    assert not result.is_error, result.content
    assert result.structured_content["status"] == LexemeStatus.PENDING_REVIEW.value

    # Editing an existing entry has no suggester path: a plain permission error.
    semmoe = db.query(Lexeme).filter(Lexeme.lemma == "Semmö").one()
    result = await _call(
        "update_word",
        {"lexeme_id": str(semmoe.id), "changes": {"notes": "hijack"}},
        token=stranger_token,
    )
    assert result.is_error

    # The reviewer sees the suggestion and approves it.
    result = await _call(
        "list_word_suggestions", {"language_id": str(language.id)}, token=editor_token
    )
    suggestions = result.structured_content["result"]
    assert [s["lemma"] for s in suggestions] == ["Brezn"]
    result = await _call("approve_word", {"lexeme_id": suggestions[0]["id"]}, token=editor_token)
    assert result.structured_content["status"] == LexemeStatus.PUBLISHED.value


async def test_invalid_token_is_rejected_even_for_reads(db: Session):
    result = await _call("whoami", token="nat_not-a-real-token")
    assert result.is_error
    assert "Invalid API token" in result.content[0].text


async def test_whoami_reports_language_rights(db: Session):
    language = _language(db)
    editor = _user(db, "editor")
    _grant_edit(db, editor, language)
    db.commit()
    _, token = create_api_token(db, editor, "mcp")

    anonymous = await _call("whoami")
    assert anonymous.structured_content["authenticated"] is False

    result = await _call("whoami", token=token)
    assert result.structured_content["username"] == "editor"
    assert result.structured_content["languages"][0]["can_edit"] is True


# ---------------------------------------------------------------------------
# HTTP transport
# ---------------------------------------------------------------------------


async def test_http_transport_authenticates_by_bearer_header_only(db: Session):
    editor = _user(db, "editor", role=UserRole.ADMIN)
    db.commit()
    _, token = create_api_token(db, editor, "mcp")
    # A stdio token lying around must not leak into HTTP requests.
    mcp_server._local_token = token

    app = mcp_server.http_app()

    async def whoami(headers: dict[str, str]) -> dict:
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app), base_url="http://nativo.test", headers=headers
        ) as http:
            transport = streamable_http_client("http://nativo.test/mcp", http_client=http)
            async with Client(transport) as client:
                result = await client.call_tool("whoami", {})
                return result.structured_content

    async with mcp_server.mcp.session_manager.run():
        assert (await whoami({}))["authenticated"] is False
        me = await whoami({"Authorization": f"Bearer {token}"})
        assert me["authenticated"] is True
        assert me["is_admin"] is True


# ---------------------------------------------------------------------------
# API tokens (REST)
# ---------------------------------------------------------------------------


async def test_api_token_lifecycle(db: Session):
    user = _user(db, "someone")
    db.commit()
    session_jwt = create_access_token(user.id, user.role)

    created = await create_personal_api_token(
        data=ApiTokenCreate(name="laptop"), raw_token=session_jwt, current_user=user, db=db
    )
    assert created.token.startswith("nat_")
    assert created.token_prefix == created.token[:12]
    # Only the hash is stored.
    assert db.query(ApiToken).one().token_hash != created.token

    # The token authenticates like a login session and stamps its last use.
    assert (await get_current_user(token=created.token, db=db)).id == user.id
    listed = await list_api_tokens(current_user=user, db=db)
    assert [t.name for t in listed] == ["laptop"]
    assert listed[0].last_used_at is not None
    assert not hasattr(listed[0], "token")

    # An API token can't mint more tokens.
    with pytest.raises(HTTPException) as excinfo:
        await create_personal_api_token(
            data=ApiTokenCreate(name="sneaky"), raw_token=created.token, current_user=user, db=db
        )
    assert excinfo.value.status_code == 403

    # Other users can't revoke it; its owner can, and then it's dead.
    other = _user(db, "other")
    db.commit()
    with pytest.raises(HTTPException) as excinfo:
        await revoke_api_token(token_id=created.id, current_user=other, db=db)
    assert excinfo.value.status_code == 404

    await revoke_api_token(token_id=created.id, current_user=user, db=db)
    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(token=created.token, db=db)
    assert excinfo.value.status_code == 401
