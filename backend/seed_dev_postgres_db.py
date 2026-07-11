#!/usr/bin/env python3
"""
Seed script to populate a fresh dev database with demo data.

Idempotent: skips entirely if any user already exists. Creates:
- the dev admin account (admin / admin123)
- six languages (same ids/colours as the original dev dataset)
- a small Bavarian vocabulary (Lexeme + lemma WordForm, published)
- English translations for a few words
- one free-reading story document
- three graded, fully word-linked "Lektion" texts so the guided
  learning path (/learn) works out of the box

Run inside the backend container (the dev compose entrypoint does this
automatically) or locally:
    cd backend && uv run python seed_dev_postgres_db.py
"""

import uuid
from datetime import UTC, datetime
from uuid import UUID

from app.database import SessionLocal
from app.models.document import Document
from app.models.language import Language
from app.models.text import DocumentType, Text
from app.models.text_word_link import TextWordLink, TextWordLinkStatus
from app.models.user import User, UserRole
from app.models.word import Lexeme, LexemeStatus, WordForm, lexeme_translations
from app.utils.security import hash_password
from sqlalchemy import insert, select


def _now() -> datetime:
    return datetime.now(UTC)


LANGUAGES = [
    # (id, name, native_name, iso, description, endangered, managed, colors)
    (
        "051e55a2-91d3-4303-b0bf-a23b733ced75",
        "Bavarian",
        "Boaric",
        "bar",
        "Upper German language spoken in Bavaria, Austria, and South Tyrol",
        True,
        True,
        ("#0099CC", "#FFFFFF", "#0080C8", "#E6F5FF"),
    ),
    (
        "4aa42943-fa76-4226-9845-495543f4dfd3",
        "Lenape",
        "Lënape",
        "umu",
        "Algonquian language of the Lenape people",
        True,
        True,
        ("#8B4513", "#D2691E", "#CD853F", "#FFF8DC"),
    ),
    (
        "71860d0c-3bdc-47d2-98f3-6c6c7aef66a7",
        "Hawaiian",
        "ʻŌlelo Hawaiʻi",
        "haw",
        "Polynesian language native to Hawaii",
        True,
        True,
        ("#00A86B", "#0080FF", "#FFD700", "#F0F8FF"),
    ),
    (
        "0b9fd658-17c7-4ce7-908c-e33a95b0eca0",
        "Navajo",
        "Diné bizaad",
        "nav",
        "Na-Dené language of the Navajo people",
        False,
        True,
        ("#DC143C", "#F4A460", "#8B4513", "#FFFAF0"),
    ),
    (
        "f1f03197-c683-41b7-945a-bbecf031f7c2",
        "Ainu",
        "アイヌ・イタㇰ",
        "ain",
        "Language isolate spoken by the Ainu people of Japan",
        True,
        True,
        ("#E60012", "#4169E1", "#2E8B57", "#F5F5F5"),
    ),
    (
        "54266e9b-19de-4b17-9e9d-15595ce4e7af",
        "English",
        "English",
        "eng",
        "The English language",
        False,
        False,
        ("#FF0000", "#FFFFFF", "#FF0000", "#FFFFFF"),
    ),
    (
        "8f2b6c1d-4e7a-4b3c-9d5e-2a1f8c6b4d90",
        "Spanish",
        "Español",
        "spa",
        "The Spanish language",
        False,
        False,
        ("#C60B1E", "#FFC400", "#AA151B", "#FFF8E7"),
    ),
]

# Bavarian demo vocabulary in the Nativo standard orthography:
# lemma -> glosses per target language ({} = no translations, e.g. names).
# Counterpart lexemes are deduplicated per (language, gloss), so da/de/d all
# point at the single English lexeme "the".
BAVARIAN_WORDS: dict[str, dict[str, str]] = {
    "Servus": {"English": "hello", "Spanish": "hola"},
    "i": {"English": "I", "Spanish": "yo"},
    "bin": {"English": "am", "Spanish": "soy"},
    "da": {"English": "the", "Spanish": "el"},
    "de": {"English": "the", "Spanish": "la"},
    "und": {"English": "and", "Spanish": "y"},
    "du": {"English": "you", "Spanish": "tú"},
    "Maks": {},
    "Áná": {},
    "gengan": {"English": "to go", "Spanish": "ir"},
    "af": {"English": "on", "Spanish": "en"},
    "d": {"English": "the", "Spanish": "la"},
    "óim": {"English": "alpine pasture", "Spanish": "prado alpino"},
    "esn": {"English": "to eat", "Spanish": "comer"},
    "a": {"English": "a", "Spanish": "un"},
    "bredsn": {"English": "pretzel", "Spanish": "pretzel"},
    "gcihdl": {"English": "little story", "Spanish": "cuentito"},
}

# Graded lessons: (title, content, words-to-link in reading order). Content
# and word list are separate because clitic articles attach with an
# apostrophe (d'Áná) — the article and the name are linked as two words.
LESSONS = [
    (
        "Lektion 1",
        "Servus i bin da Maks",
        ["Servus", "i", "bin", "da", "Maks"],
    ),
    (
        "Lektion 2",
        "Servus Maks i bin d'Áná und du",
        ["Servus", "Maks", "i", "bin", "d", "Áná", "und", "du"],
    ),
    (
        "Lektion 3",
        "da Maks und d'Áná gengan af d'óim und esn a bredsn",
        # fmt: off
        ["da", "Maks", "und", "d", "Áná", "gengan", "af", "d", "óim",
         "und", "esn", "a", "bredsn"],
        # fmt: on
    ),
]


def seed_database():
    """
    Additive and idempotent: every section checks what already exists and
    only inserts what's missing, so pulling an update and restarting the
    stack tops up new demo content without wiping the database.
    """
    db = SessionLocal()
    try:
        print("Starting database seeding (additive)...")

        # ------------------------------------------------------------------
        # Admin user
        # ------------------------------------------------------------------
        admin = db.query(User).filter(User.username == "admin").first()
        if admin is None:
            admin = User(
                id=UUID("5029c5d0-c4f6-401e-9257-a8d1055b121a"),
                email="admin@nativo.dev",
                username="admin",
                hashed_password=hash_password("admin123"),
                role=UserRole.ADMIN,
                is_active=True,
                is_superuser=True,
            )
            db.add(admin)
            db.commit()
            print("  Inserted admin user (admin / admin123)")

        # ------------------------------------------------------------------
        # Languages
        # ------------------------------------------------------------------
        langs: dict[str, Language] = {}
        added_langs = 0
        for lid, name, native, iso, desc, endangered, managed, colors in LANGUAGES:
            lang = db.query(Language).filter(Language.name == name).first()
            if lang is None:
                lang = Language(
                    id=UUID(lid),
                    name=name,
                    native_name=native,
                    iso_639_3=iso,
                    description=desc,
                    is_endangered=endangered,
                    managed=managed,
                    primary_color=colors[0],
                    secondary_color=colors[1],
                    accent_color=colors[2],
                    background_color=colors[3],
                )
                db.add(lang)
                added_langs += 1
            langs[name] = lang
        db.commit()
        print(f"  Languages: {added_langs} added, {len(LANGUAGES) - added_langs} already present")

        bavarian = langs["Bavarian"]

        # ------------------------------------------------------------------
        # Vocabulary: Bavarian lexemes + lemma forms, plus translation
        # counterparts per target language (deduplicated per gloss)
        # ------------------------------------------------------------------
        def get_or_create_lexeme(language_id: UUID, lemma: str) -> tuple[Lexeme, WordForm]:
            lexeme = (
                db.query(Lexeme)
                .filter(Lexeme.language_id == language_id, Lexeme.lemma == lemma)
                .first()
            )
            if lexeme is None:
                lexeme = Lexeme(
                    language_id=language_id,
                    lemma=lemma,
                    created_by_id=admin.id,
                    status=LexemeStatus.PUBLISHED,
                )
                db.add(lexeme)
                db.flush()
            form = (
                db.query(WordForm)
                .filter(WordForm.lexeme_id == lexeme.id, WordForm.is_lemma.is_(True))
                .first()
            )
            if form is None:
                form = WordForm(lexeme_id=lexeme.id, form=lemma, is_lemma=True)
                db.add(form)
                db.flush()
            return lexeme, form

        def ensure_translation(a: UUID, b: UUID) -> bool:
            # Undirected, stored canonically (lexeme_id < translation_id).
            lo, hi = sorted([a, b])
            exists = db.execute(
                select(lexeme_translations.c.lexeme_id).where(
                    lexeme_translations.c.lexeme_id == lo,
                    lexeme_translations.c.translation_id == hi,
                )
            ).first()
            if exists:
                return False
            db.execute(
                insert(lexeme_translations).values(
                    lexeme_id=lo,
                    translation_id=hi,
                    created_at=_now(),
                    created_by_id=admin.id,
                )
            )
            return True

        before = db.query(Lexeme).count()
        forms: dict[str, WordForm] = {}
        added_links = 0
        for lemma, glosses in BAVARIAN_WORDS.items():
            lexeme, form = get_or_create_lexeme(bavarian.id, lemma)
            forms[lemma] = form
            for lang_name, gloss in glosses.items():
                counterpart, _ = get_or_create_lexeme(langs[lang_name].id, gloss)
                if ensure_translation(lexeme.id, counterpart.id):
                    added_links += 1
        db.commit()
        print(
            f"  Vocabulary: {db.query(Lexeme).count() - before} lexemes added, "
            f"{added_links} translation links added"
        )

        # ------------------------------------------------------------------
        # Texts. Matched by title (case-insensitive) so renames in the seed
        # don't duplicate content in older dev databases.
        # ------------------------------------------------------------------
        def text_exists(title: str) -> bool:
            return (
                db.query(Text)
                .filter(
                    Text.language_id == bavarian.id,
                    Text.title.ilike(title),
                )
                .first()
                is not None
            )

        def create_text(title: str, content: str) -> Text:
            doc = Document(created_by_id=admin.id)
            db.add(doc)
            db.flush()
            text = Text(
                document_id=doc.id,
                language_id=bavarian.id,
                title=title,
                content=content,
                document_type=DocumentType.STORY,
                created_by_id=admin.id,
                is_primary=True,
            )
            db.add(text)
            db.flush()
            return text

        added_texts = 0

        # Free-reading story (not word-linked — regular Documents content)
        if not text_exists("A gcihdl"):
            create_text("A gcihdl", "Servus bainánd! Des is a gloans gcihdl af Boaric.")
            added_texts += 1

        # Graded lessons: fully linked so they qualify for /learn
        for title, content, words in LESSONS:
            if text_exists(title):
                continue
            text = create_text(title, content)
            offset = 0
            for word in words:
                start = content.index(word, offset)
                end = start + len(word)
                offset = end
                db.add(
                    TextWordLink(
                        id=uuid.uuid4(),
                        text_id=text.id,
                        word_form_id=forms[word].id,
                        start_char=start,
                        end_char=end,
                        status=TextWordLinkStatus.CONFIRMED,
                    )
                )
            added_texts += 1
        db.commit()
        print(f"  Texts: {added_texts} added")

        print("Seeding complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
