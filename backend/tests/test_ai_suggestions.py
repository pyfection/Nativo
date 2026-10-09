"""
Tests for AI suggestions on Quick Contribute word cards.

The contract under test:
- The prompt carries the passage, the language's writing standard and
  reviewed dictionary entries (with their meanings) as examples.
- Only words that occur in the given published text / snippet of the
  language can be asked about.
- One suggestion per (language, word, gloss language): later requests are
  served from `ai_suggestions` without calling the CLI again.
- Answers are cleaned: unknown parts of speech, a "standard spelling" equal
  to the word, and a gloss without a gloss language are dropped.
- Not configured → 503. The CLI runs with the OAuth token and without an
  inherited ANTHROPIC_API_KEY.
"""

import json
import os
import stat
import uuid
from datetime import UTC, datetime

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

sqlalchemy = pytest.importorskip("sqlalchemy")
from app.api.v1.endpoints.contribute import suggest_word  # noqa: E402
from app.config import settings  # noqa: E402
from app.database import Base  # noqa: E402
from app.models.ai_suggestion import AiSuggestion  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.text import DocumentType, Text, TextStatus  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.word import Lexeme, LexemeStatus, PartOfSpeech, WordForm  # noqa: E402
from app.services import lexeme_service  # noqa: E402
from app.utils import claude_cli  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

engine = create_engine("sqlite:///:memory:", future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)

ANSWER = {
    "lemma": "gem",
    "part_of_speech": "verb",
    "gloss": "there is",
    "standard_spelling": "gibds",
    "explanation": "gibd + 's (gibt es).",
}


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


class FakeClaude:
    """Stands in for the CLI: records prompts, returns `answer`."""

    def __init__(self):
        self.prompts: list[str] = []
        self.answer = dict(ANSWER)

    def __call__(self, prompt, *, system, schema):
        self.prompts.append(prompt)
        return dict(self.answer)


@pytest.fixture
def claude(monkeypatch) -> FakeClaude:
    fake = FakeClaude()
    monkeypatch.setattr(claude_cli, "ask_json", fake)
    return fake


def _now() -> datetime:
    return datetime.now(UTC)


def _user(db: Session) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"u-{uuid.uuid4()}@example.com",
        username=f"user-{uuid.uuid4().hex[:8]}",
        hashed_password="x",
        role=UserRole.PUBLIC,
        is_active=True,
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(user)
    db.flush()
    return user


def _language(db: Session, name: str) -> Language:
    lang = Language(id=uuid.uuid4(), name=name, created_at=_now(), updated_at=_now())
    db.add(lang)
    db.flush()
    return lang


def _text(db: Session, lang: Language, author: User, content: str, **kw) -> Text:
    document = Document(id=uuid.uuid4(), created_by_id=author.id)
    db.add(document)
    db.flush()
    text = Text(
        id=uuid.uuid4(),
        title="Sample",
        content=content,
        document_type=kw.get("document_type", DocumentType.STORY),
        status=kw.get("status", TextStatus.PUBLISHED),
        language_id=lang.id,
        document_id=document.id,
        created_by_id=author.id,
    )
    db.add(text)
    db.flush()
    return text


def _word(db: Session, lang: Language, author: User, lemma: str, pos=None) -> Lexeme:
    lexeme = Lexeme(
        id=uuid.uuid4(),
        language_id=lang.id,
        lemma=lemma,
        part_of_speech=pos,
        created_by_id=author.id,
        status=LexemeStatus.PUBLISHED,
    )
    db.add(lexeme)
    db.flush()
    db.add(WordForm(id=uuid.uuid4(), lexeme_id=lexeme.id, form=lemma, is_lemma=True))
    db.flush()
    return lexeme


def _setup(db: Session):
    bavarian, english = _language(db, "Bavarian"), _language(db, "English")
    user = _user(db)
    text = _text(db, bavarian, user, "Des is a test dokument. Meara gibd's ned dsum sógn.")
    return bavarian, english, user, text


def _suggest(db, lang, user, token, **kw):
    return suggest_word(
        lang.id,
        token=token,
        text_id=kw.get("text_id"),
        snippet_id=kw.get("snippet_id"),
        gloss_language_id=kw.get("gloss_language_id"),
        current_user=user,
        db=db,
    )


def test_prompt_has_passage_standard_and_examples(db: Session, claude):
    bavarian, english, user, text = _setup(db)
    standard = _text(
        db,
        bavarian,
        user,
        "No apostrophe unless a longer form exists.",
        document_type=DocumentType.WRITING_STANDARD,
    )
    bavarian.writing_standard_document_id = standard.document_id
    hund = _word(db, bavarian, user, "Hund", PartOfSpeech.NOUN)
    lexeme_service.add_gloss(db, hund, english.id, "dog", user.id, publish=True)
    db.commit()

    suggestion = _suggest(
        db, bavarian, user, "gibd's", text_id=text.id, gloss_language_id=english.id
    )

    assert suggestion.lemma == "gem"
    assert suggestion.part_of_speech == PartOfSpeech.VERB
    assert (suggestion.gloss, suggestion.standard_spelling) == ("there is", "gibds")
    [prompt] = claude.prompts
    assert "Meara gibd's ned" in prompt
    assert "No apostrophe unless a longer form exists." in prompt
    assert "Hund — noun — dog" in prompt
    assert "meaning in English" in prompt


def test_suggestion_is_made_once_per_word(db: Session, claude):
    bavarian, english, user, text = _setup(db)
    other = _text(db, bavarian, user, "Gibd's des?")

    first = _suggest(db, bavarian, user, "gibd's", text_id=text.id, gloss_language_id=english.id)
    again = _suggest(db, bavarian, user, "Gibd's", text_id=other.id, gloss_language_id=english.id)

    assert first == again
    assert len(claude.prompts) == 1
    assert db.query(AiSuggestion).count() == 1
    # Another meaning language is another suggestion.
    _suggest(db, bavarian, user, "gibd's", text_id=text.id)
    assert len(claude.prompts) == 2


def test_only_words_in_a_published_text_of_the_language(db: Session, claude):
    bavarian, english, user, text = _setup(db)
    draft = _text(db, bavarian, user, "gheim", status=TextStatus.PENDING_REVIEW)
    english_text = _text(db, english, user, "secret")

    for token, text_id in [("sonstwos", text.id), ("gheim", draft.id), ("secret", english_text.id)]:
        with pytest.raises(HTTPException) as exc:
            _suggest(db, bavarian, user, token, text_id=text_id)
        assert exc.value.status_code == 404
    assert claude.prompts == []


def test_answer_is_cleaned(db: Session, claude):
    bavarian, english, user, text = _setup(db)
    claude.answer = {**ANSWER, "part_of_speech": "verbish", "standard_spelling": "Gibd's"}

    suggestion = _suggest(db, bavarian, user, "gibd's", text_id=text.id)

    assert suggestion.part_of_speech is None
    assert suggestion.standard_spelling is None  # same as the word
    assert suggestion.gloss is None  # no meaning language asked for


def test_not_configured_is_503(db: Session, monkeypatch):
    bavarian, english, user, text = _setup(db)
    monkeypatch.setattr(settings, "CLAUDE_CODE_OAUTH_TOKEN", None)

    with pytest.raises(HTTPException) as exc:
        _suggest(db, bavarian, user, "gibd's", text_id=text.id)
    assert exc.value.status_code == 503
    assert db.query(AiSuggestion).count() == 0


def test_cli_gets_oauth_token_and_no_api_key(tmp_path, monkeypatch):
    """Run ask_json against a stand-in `claude` that reports its environment."""
    fake = tmp_path / "claude"
    fake.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "prompt = sys.stdin.read()\n"
        "answer = {'token': os.environ.get('CLAUDE_CODE_OAUTH_TOKEN'),\n"
        "          'api_key': os.environ.get('ANTHROPIC_API_KEY'),\n"
        "          'prompt': prompt, 'tools': sys.argv[sys.argv.index('--tools') + 1]}\n"
        "print(json.dumps({'type': 'result', 'is_error': False, 'structured_output': answer}))\n"
    )
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setattr(settings, "CLAUDE_CLI_PATH", str(fake))
    monkeypatch.setattr(settings, "CLAUDE_CODE_OAUTH_TOKEN", "sk-ant-oat-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api-should-not-leak")

    answer = claude_cli.ask_json("hello", system="sys", schema={"type": "object"})

    assert answer == {"token": "sk-ant-oat-test", "api_key": None, "prompt": "hello", "tools": ""}


def test_cli_error_is_unavailable(tmp_path, monkeypatch):
    fake = tmp_path / "claude"
    fake.write_text(
        "#!/usr/bin/env python3\n"
        f"print({json.dumps(json.dumps({'is_error': True, 'result': 'Invalid token'}))})\n"
    )
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setattr(settings, "CLAUDE_CLI_PATH", str(fake))
    monkeypatch.setattr(settings, "CLAUDE_CODE_OAUTH_TOKEN", "sk-ant-oat-test")

    with pytest.raises(claude_cli.ClaudeUnavailableError, match="Invalid token"):
        claude_cli.ask_json("hello", system="sys", schema={"type": "object"})
