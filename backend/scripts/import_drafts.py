"""
Import an LLM-drafted word batch into the review queue.

Step 3 of a drafted batch (after `draft_candidates.py` and drafting). Every
entry lands as a PENDING_REVIEW suggestion by a bot account, never as
published content; a reviewer approves, fixes or rejects it on /review.

Quality gates, all enforced before anything is written:
- Every form must appear *exactly as spelled* (accents included) in the
  harvested corpus, unless the entry marks it `"inferred": true`. This makes
  a typo in a drafted word an import error instead of a dictionary entry.
- Forms must use only the language's alphabet (see ALPHABETS).
- Words already in the dictionary (any spelling-folded form match) are
  skipped, so re-running a batch is safe.

The reviewer sees, per word: the drafter's reasoning, the corpus strings it
was taken from (with their English UI counterparts) and which forms are
inferred. Glosses reuse existing entries of the gloss language; missing ones
are drafted as pending entries that follow their word on approve/reject.

    DATABASE_URL=... uv run python backend/scripts/import_drafts.py \\
        backend/scripts/drafts/bar-001.json --candidates candidates.json [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.database import SessionLocal  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.word import Lexeme, LexemeStatus, WordForm  # noqa: E402
from app.schemas.word import LexemeCreate, TranslationCreate, WordFormCreateNested  # noqa: E402
from app.services import lexeme_service  # noqa: E402
from app.utils.security import hash_password  # noqa: E402
from app.utils.text_normalize import fold_for_match  # noqa: E402

# Letters a standard spelling may use (lower-cased), plus the apostrophe of
# clitics. Bavarian: no j q w x y z, no umlauts or ß; á é ó carry vowel depth.
ALPHABETS = {
    "Bavarian": set("abcdefghiklmnoprstuváéó'"),
}

BOT_USERNAME = "claude-drafts"
BOT_EMAIL = "claude-drafts@example.com"  # reserved domain: never delivers


def _bot(db) -> User:
    bot = db.query(User).filter(User.username == BOT_USERNAME).first()
    if bot is None:
        bot = User(
            username=BOT_USERNAME,
            email=BOT_EMAIL,
            # Random, never stored anywhere: the account can't be logged into.
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            role=UserRole.PUBLIC,
            is_active=True,
            is_bot=True,
        )
        db.add(bot)
        db.commit()
    elif not bot.is_bot:
        sys.exit(f"User {BOT_USERNAME!r} exists but is not flagged is_bot; refusing.")
    return bot


def _language(db, name: str) -> Language:
    language = db.query(Language).filter(Language.name == name).first()
    if language is None:
        sys.exit(f"No language named {name!r}")
    return language


def _all_forms(entry: dict) -> list[dict]:
    lemma = {"form": entry["lemma"], "inferred": entry.get("lemma_inferred", False)}
    return [lemma, *entry.get("forms", [])]


def validate(entries: list[dict], corpus: dict[str, dict], alphabet: set[str]) -> list[str]:
    errors = []
    for entry in entries:
        for form in _all_forms(entry):
            text = form["form"]
            bad = set(text.lower()) - alphabet
            if bad:
                errors.append(f"{entry['lemma']}: {text!r} uses {''.join(sorted(bad))!r}")
            if form.get("inferred"):
                continue
            seen = corpus.get(fold_for_match(text))
            if seen is None or text.lower() not in {s.lower() for s in seen["surfaces"]}:
                errors.append(
                    f"{entry['lemma']}: {text!r} is not in the corpus as spelled "
                    "(fix the spelling or mark it inferred)"
                )
        if entry.get("confidence") not in {"high", "medium", "low"}:
            errors.append(f"{entry['lemma']}: confidence must be high/medium/low")
        if not entry.get("glosses"):
            errors.append(f"{entry['lemma']}: needs at least one gloss")
    return errors


def _notes(entry: dict, corpus: dict[str, dict]) -> str:
    lines = [entry["why"]] if entry.get("why") else []
    quoted = set()
    for form in _all_forms(entry):
        if form.get("inferred"):
            continue
        for example in corpus[fold_for_match(form["form"])]["examples"]:
            if example["verified"] and example["text"] not in quoted and len(quoted) < 3:
                quoted.add(example["text"])
                lines.append(f'Attested: "{example["text"]}" (UI: "{example["english"]}")')
    inferred = [f["form"] for f in _all_forms(entry) if f.get("inferred")]
    if inferred:
        lines.append(f"Inferred, not in the corpus: {', '.join(inferred)}")
    return "\n".join(lines)


def _form_note(form: dict) -> str | None:
    parts = [form["notes"]] if form.get("notes") else []
    if form.get("inferred"):
        parts.append("inferred")
    return "; ".join(parts) or None


def _known_forms(db, language: Language) -> set[str]:
    """Folded forms already in the dictionary. Taken once, before importing,
    so homographs within a batch (two 'kena') are both created while a re-run
    skips everything the first run made."""
    rows = (
        db.query(WordForm.form)
        .join(Lexeme, Lexeme.id == WordForm.lexeme_id)
        .filter(Lexeme.language_id == language.id, Lexeme.status != LexemeStatus.ARCHIVED)
        .all()
    )
    return {fold_for_match(r.form) for r in rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("batch")
    parser.add_argument("--candidates", required=True, help="output of draft_candidates.py")
    parser.add_argument("--dry-run", action="store_true", help="validate only")
    args = parser.parse_args()

    batch = json.loads(Path(args.batch).read_text())
    corpus = {c["token"]: c for c in json.loads(Path(args.candidates).read_text())}
    entries = batch["entries"]

    errors = validate(entries, corpus, ALPHABETS[batch["language"]])
    if errors:
        print("Batch rejected:\n  " + "\n  ".join(errors), file=sys.stderr)
        sys.exit(1)
    print(f"{len(entries)} entries pass validation", file=sys.stderr)
    if args.dry_run:
        return

    db = SessionLocal()
    try:
        language = _language(db, batch["language"])
        gloss_language = _language(db, batch["gloss_language"])
        bot = _bot(db)
        known = _known_forms(db, language)
        created = skipped = 0
        for entry in entries:
            if fold_for_match(entry["lemma"]) in known:
                print(f"  skip {entry['lemma']}: already in the dictionary", file=sys.stderr)
                skipped += 1
                continue
            data = LexemeCreate(
                language_id=language.id,
                lemma=entry["lemma"],
                part_of_speech=entry.get("pos"),
                gender=entry.get("gender"),
                source=batch["source"],
                notes=_notes(entry, corpus),
                draft_confidence=entry["confidence"],
                lemma_form=WordFormCreateNested(
                    form=entry["lemma"],
                    notes=_form_note(
                        {"notes": entry.get("lemma_note"), "inferred": entry.get("lemma_inferred")}
                    ),
                ),
                additional_forms=[
                    WordFormCreateNested(form=f["form"], notes=_form_note(f))
                    for f in entry.get("forms", [])
                ]
                or None,
            )
            word = lexeme_service.create_lexeme(
                db, data, creator_id=bot.id, status=LexemeStatus.PENDING_REVIEW
            )
            for gloss in entry["glosses"]:
                target = lexeme_service.find_gloss_target(db, gloss_language.id, gloss)
                if target is None:
                    target = lexeme_service.create_lexeme(
                        db,
                        LexemeCreate(
                            language_id=gloss_language.id,
                            lemma=gloss,
                            part_of_speech=entry.get("pos"),
                            source=batch["source"],
                            lemma_form=WordFormCreateNested(form=gloss),
                        ),
                        creator_id=bot.id,
                        status=LexemeStatus.PENDING_REVIEW,
                    )
                lexeme_service.add_translation(
                    db, word.id, TranslationCreate(other_lexeme_id=target.id), creator_id=bot.id
                )
            created += 1
        print(f"Imported {created} suggestions ({skipped} skipped).", file=sys.stderr)
    finally:
        db.close()


if __name__ == "__main__":
    main()
