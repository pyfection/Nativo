"""
Tests for the drafted-batch importer (backend/scripts/import_drafts.py).

- Validation rejects a form that isn't in the corpus exactly as spelled
  (accent typos included) or that uses letters outside the alphabet, and
  accepts forms explicitly marked inferred.
- Import creates pending suggestions by a bot account, reuses existing
  glosses, creates homographs within one batch, and is idempotent.
"""

import importlib.util
import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

sqlalchemy = pytest.importorskip("sqlalchemy")
from app.database import Base  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.word import Lexeme, LexemeStatus, WordForm  # noqa: E402
from app.services import lexeme_service  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "import_drafts.py"
spec = importlib.util.spec_from_file_location("import_drafts", SCRIPT)
import_drafts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(import_drafts)

engine = create_engine("sqlite:///:memory:", future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)

BAVARIAN = import_drafts.ALPHABETS["Bavarian"]

CORPUS = {
    "pasvoat": {
        "token": "pasvoat",
        "surfaces": ["Pasvoat", "pasvoat"],
        "examples": [
            {"text": "Gib dei pasvoat ei", "english": "Enter your password", "verified": True}
        ],
    },
    "pasveata": {
        "token": "pasveata",
        "surfaces": ["pasveata"],
        "examples": [
            {
                "text": "De pasveata san ned glaih",
                "english": "Passwords do not match",
                "verified": True,
            }
        ],
    },
    "kena": {
        "token": "kena",
        "surfaces": ["kena"],
        "examples": [{"text": "hód ned lón kena", "english": "Failed to load", "verified": True}],
    },
    "kenst": {
        "token": "kenst",
        "surfaces": ["Kenst"],
        "examples": [{"text": "Kenst a voat?", "english": "Know a word?", "verified": True}],
    },
    "lesn": {
        "token": "lesn",
        "surfaces": ["lésn"],
        "examples": [{"text": "As dokument lésn", "english": "Read the text", "verified": True}],
    },
}


def _entry(lemma, **extra):
    return {"lemma": lemma, "glosses": ["x"], "confidence": "high", **extra}


def test_validation_catches_typos_and_foreign_letters():
    assert import_drafts.validate([_entry("pasvoat")], CORPUS, BAVARIAN) == []
    # Accent typo: 'lesn' folds to the corpus token but isn't spelled that way.
    assert import_drafts.validate([_entry("lesn")], CORPUS, BAVARIAN)
    # Not in the corpus at all.
    assert import_drafts.validate([_entry("pasvort")], CORPUS, BAVARIAN)
    # Forbidden letter, even when marked inferred.
    errors = import_drafts.validate([_entry("wort", lemma_inferred=True)], CORPUS, BAVARIAN)
    assert any("uses 'w'" in e for e in errors)
    # Inferred forms are allowed without attestation.
    assert import_drafts.validate([_entry("nai", lemma_inferred=True)], CORPUS, BAVARIAN) == []
    # Missing gloss / bad confidence.
    assert import_drafts.validate(
        [{"lemma": "pasvoat", "glosses": [], "confidence": "sure"}], CORPUS, BAVARIAN
    )


@pytest.fixture
def db(monkeypatch):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(import_drafts, "SessionLocal", SessionLocal)
    session = SessionLocal()
    now = datetime.now(UTC)
    admin = User(
        id=uuid.uuid4(),
        email="a@example.com",
        username="admin",
        hashed_password="x",
        role=UserRole.ADMIN,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    bar = Language(id=uuid.uuid4(), name="Bavarian", created_at=now, updated_at=now)
    eng = Language(id=uuid.uuid4(), name="English", created_at=now, updated_at=now)
    session.add_all([admin, bar, eng])
    session.flush()
    # An existing (draft-status, as in prod) English gloss to be reused.
    password = Lexeme(
        language_id=eng.id, lemma="password", created_by_id=admin.id, status=LexemeStatus.DRAFT
    )
    session.add(password)
    session.flush()
    session.add(WordForm(lexeme_id=password.id, form="password", is_lemma=True))
    session.commit()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def _run(tmp_path, monkeypatch, entries):
    batch = tmp_path / "batch.json"
    batch.write_text(
        json.dumps(
            {
                "language": "Bavarian",
                "gloss_language": "English",
                "source": "test batch",
                "entries": entries,
            }
        )
    )
    candidates = tmp_path / "candidates.json"
    candidates.write_text(json.dumps(list(CORPUS.values())))
    monkeypatch.setattr("sys.argv", ["import_drafts", str(batch), "--candidates", str(candidates)])
    import_drafts.main()


def test_import_creates_pending_bot_suggestions(db, tmp_path, monkeypatch):
    entries = [
        _entry(
            "pasvoat",
            pos="noun",
            glosses=["password"],
            forms=[{"form": "pasveata", "notes": "plural"}],
            why="Neuter.",
        ),
        _entry("kena", pos="verb", glosses=["can"]),
        _entry(
            "kena",
            pos="verb",
            glosses=["to know"],
            confidence="medium",
            lemma_inferred=True,
            forms=[{"form": "kenst"}],
        ),
    ]
    _run(tmp_path, monkeypatch, entries)

    bot = db.query(User).filter(User.username == import_drafts.BOT_USERNAME).one()
    assert bot.is_bot
    words = db.query(Lexeme).filter(Lexeme.created_by_id == bot.id).all()
    bavarian = sorted(
        (w.lemma, w.draft_confidence) for w in words if w.lemma != "can" and w.lemma != "to know"
    )
    assert bavarian == [("kena", "high"), ("kena", "medium"), ("pasvoat", "high")]
    assert all(w.status == LexemeStatus.PENDING_REVIEW for w in words)

    pasvoat = next(w for w in words if w.lemma == "pasvoat")
    assert 'Attested: "Gib dei pasvoat ei"' in pasvoat.notes
    assert sorted(f.form for f in pasvoat.forms) == ["pasveata", "pasvoat"]
    # The existing English 'password' was reused, not duplicated.
    assert [t.lemma for t in lexeme_service.list_translations(db, pasvoat.id)] == ["password"]
    assert db.query(Lexeme).filter(Lexeme.lemma == "password").count() == 1
    # A missing gloss is drafted as a pending entry by the bot.
    can = db.query(Lexeme).filter(Lexeme.lemma == "can").one()
    assert can.status == LexemeStatus.PENDING_REVIEW and can.created_by_id == bot.id

    # Re-running changes nothing.
    before = db.query(Lexeme).count()
    _run(tmp_path, monkeypatch, entries)
    db.expire_all()
    assert db.query(Lexeme).count() == before
