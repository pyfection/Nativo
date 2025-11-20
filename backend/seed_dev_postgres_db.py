#!/usr/bin/env python3
"""
Seed script to populate PostgreSQL database with initial data.
This script recreates the data from nativo.db without requiring access to it.
"""
import os
import sys
from datetime import datetime
from uuid import UUID
from sqlalchemy import text

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.language import Language
from app.models.document import Document
from app.models.text import Text, DocumentType
from app.models.word.word import Word
from app.models.word.enums import (
    PartOfSpeech,
    Register,
    WordStatus,
    GrammaticalGender,
    Plurality,
    GrammaticalCase,
    VerbAspect,
    Animacy,
)
from app.utils.security import hash_password


def seed_database():
    """Seed the database with initial data"""
    db = SessionLocal()
    try:
        print("Starting database seeding...")

        # Check if data already exists
        if db.query(User).count() > 0:
            print("Database already contains data. Skipping seed.")
            return

        # Insert users
        user_5029c5d0 = User(
            id=UUID("5029c5d0-c4f6-401e-9257-a8d1055b121a"),
            email="admin@nativo.dev",
            username="admin",
            hashed_password=hash_password("admin123"),
            role=UserRole.ADMIN,
            is_active=True,
            is_superuser=True,
            created_at=datetime.fromisoformat("2025-11-02 02:22:52.213905"),
            updated_at=datetime.fromisoformat("2025-11-02 02:22:52.213909"),
        )
        db.add(user_5029c5d0)
        print(f"  Inserted 1 user(s)")

        # Commit users before adding languages (users are referenced by documents, texts, words, etc.)
        db.commit()

        # Insert languages
        lang_051e55a2 = Language(
            id=UUID("051e55a2-91d3-4303-b0bf-a23b733ced75"),
            name="Bavarian",
            native_name="Boaric",
            iso_639_3="bar",
            description="Upper German language spoken in Bavaria, Austria, and South Tyrol",
            is_endangered=True,
            managed=True,
            primary_color="#0099CC",
            secondary_color="#FFFFFF",
            accent_color="#0080C8",
            background_color="#E6F5FF",
            created_at=datetime.fromisoformat("2025-11-02 02:22:52.239213"),
            updated_at=datetime.fromisoformat("2025-11-02 02:29:54.496881"),
        )
        db.add(lang_051e55a2)
        lang_4aa42943 = Language(
            id=UUID("4aa42943-fa76-4226-9845-495543f4dfd3"),
            name="Lenape",
            native_name="Lënape",
            iso_639_3="umu",
            description="Algonquian language of the Lenape people",
            is_endangered=True,
            managed=True,
            primary_color="#8B4513",
            secondary_color="#D2691E",
            accent_color="#CD853F",
            background_color="#FFF8DC",
            created_at=datetime.fromisoformat("2025-11-02 02:22:52.239220"),
            updated_at=datetime.fromisoformat("2025-11-02 02:22:52.239221"),
        )
        db.add(lang_4aa42943)
        lang_71860d0c = Language(
            id=UUID("71860d0c-3bdc-47d2-98f3-6c6c7aef66a7"),
            name="Hawaiian",
            native_name="ʻŌlelo Hawaiʻi",
            iso_639_3="haw",
            description="Polynesian language native to Hawaii",
            is_endangered=True,
            managed=True,
            primary_color="#00A86B",
            secondary_color="#0080FF",
            accent_color="#FFD700",
            background_color="#F0F8FF",
            created_at=datetime.fromisoformat("2025-11-02 02:22:52.239223"),
            updated_at=datetime.fromisoformat("2025-11-02 02:22:52.239224"),
        )
        db.add(lang_71860d0c)
        lang_0b9fd658 = Language(
            id=UUID("0b9fd658-17c7-4ce7-908c-e33a95b0eca0"),
            name="Navajo",
            native_name="Diné bizaad",
            iso_639_3="nav",
            description="Na-Dené language of the Navajo people",
            is_endangered=False,
            managed=True,
            primary_color="#DC143C",
            secondary_color="#F4A460",
            accent_color="#8B4513",
            background_color="#FFFAF0",
            created_at=datetime.fromisoformat("2025-11-02 02:22:52.239226"),
            updated_at=datetime.fromisoformat("2025-11-02 02:22:52.239227"),
        )
        db.add(lang_0b9fd658)
        lang_f1f03197 = Language(
            id=UUID("f1f03197-c683-41b7-945a-bbecf031f7c2"),
            name="Ainu",
            native_name="アイヌ・イタㇰ",
            iso_639_3="ain",
            description="Language isolate spoken by the Ainu people of Japan",
            is_endangered=True,
            managed=True,
            primary_color="#E60012",
            secondary_color="#4169E1",
            accent_color="#2E8B57",
            background_color="#F5F5F5",
            created_at=datetime.fromisoformat("2025-11-02 02:22:52.239228"),
            updated_at=datetime.fromisoformat("2025-11-02 02:22:52.239229"),
        )
        db.add(lang_f1f03197)
        lang_54266e9b = Language(
            id=UUID("54266e9b-19de-4b17-9e9d-15595ce4e7af"),
            name="English",
            native_name="English",
            iso_639_3="eng",
            description="The English language",
            is_endangered=False,
            managed=False,
            primary_color="#FF0000",
            secondary_color="#FFFFFF",
            accent_color="#FF0000",
            background_color="#FFFFFF",
            created_at=datetime.fromisoformat("2025-11-03 02:01:29.707904"),
            updated_at=datetime.fromisoformat("2025-11-03 02:01:29.707907"),
        )
        db.add(lang_54266e9b)
        print(f"  Inserted 6 language(s)")

        # Commit languages before inserting user_languages to satisfy foreign key constraint
        db.commit()

        # Insert documents
        doc_26d30f6c = Document(
            id=UUID("26d30f6c-8d76-4d4a-b9a5-513b22c8a9df"),
            created_by_id=UUID("5029c5d0-c4f6-401e-9257-a8d1055b121a"),
            created_at=datetime.fromisoformat("2025-11-09 16:30:06.585458"),
            updated_at=datetime.fromisoformat("2025-11-09 16:30:06.585462"),
        )
        db.add(doc_26d30f6c)
        print(f"  Inserted 1 document(s)")

        # Commit documents before texts reference them
        db.commit()

        # Insert texts
        text_d5edacf8 = Text(
            id=UUID("d5edacf8-94fb-4739-9ff6-657139b1d8e1"),
            content="Des is a test dokument.\nMeara gibd's ned dsum sógn.",
            document_type=DocumentType.STORY,
            language_id=UUID("051e55a2-91d3-4303-b0bf-a23b733ced75"),
            source="Matthias Schreiber",
            notes=None,
            created_by_id=UUID("5029c5d0-c4f6-401e-9257-a8d1055b121a"),
            title="Test dokument",
            is_primary=False,
            document_id=UUID("26d30f6c-8d76-4d4a-b9a5-513b22c8a9df"),
            created_at=datetime.fromisoformat("2025-11-09 16:30:06.587175"),
            updated_at=datetime.fromisoformat("2025-11-09 16:43:16.126049"),
        )
        db.add(text_d5edacf8)
        print(f"  Inserted 1 text(s)")

        # Commit texts before text_word_links reference them
        db.commit()

        # Insert words
        word_b8f1722f = Word(
            id=UUID("b8f1722f-aeb8-43bb-aaa7-517a15c87625"),
            word="bua",
            language_id=UUID("051e55a2-91d3-4303-b0bf-a23b733ced75"),
            romanization="bua",
            ipa_pronunciation="",
            part_of_speech=PartOfSpeech.NOUN,
            gender=None,
            plurality=None,
            grammatical_case=None,
            verb_aspect=None,
            animacy=None,
            language_register=Register.NEUTRAL,
            confirmed_at_id=None,
            etymology_document_id=None,
            cultural_significance_document_id=None,
            created_by_id=UUID("5029c5d0-c4f6-401e-9257-a8d1055b121a"),
            verified_by_id=UUID("5029c5d0-c4f6-401e-9257-a8d1055b121a"),
            is_verified=True,
            status=WordStatus.PUBLISHED,
            source="",
            notes="",
            created_at=datetime.fromisoformat("2025-11-02 02:26:07.102976"),
            updated_at=datetime.fromisoformat("2025-11-04 21:37:37.452070"),
        )
        db.add(word_b8f1722f)
        word_2b9469f8 = Word(
            id=UUID("2b9469f8-50f8-434a-b28e-b7eff9c0d43b"),
            word="boy",
            language_id=UUID("54266e9b-19de-4b17-9e9d-15595ce4e7af"),
            romanization="",
            ipa_pronunciation="",
            part_of_speech=PartOfSpeech.NOUN,
            gender=None,
            plurality=None,
            grammatical_case=None,
            verb_aspect=None,
            animacy=None,
            language_register=Register.NEUTRAL,
            confirmed_at_id=None,
            etymology_document_id=None,
            cultural_significance_document_id=None,
            created_by_id=UUID("5029c5d0-c4f6-401e-9257-a8d1055b121a"),
            verified_by_id=None,
            is_verified=True,
            status=WordStatus.PUBLISHED,
            source="",
            notes="",
            created_at=datetime.fromisoformat("2025-11-03 02:57:50.063526"),
            updated_at=datetime.fromisoformat("2025-11-03 03:00:35.277089"),
        )
        db.add(word_2b9469f8)
        word_9840df93 = Word(
            id=UUID("9840df93-59e9-4274-9724-320e8680c9d5"),
            word="is",
            language_id=UUID("051e55a2-91d3-4303-b0bf-a23b733ced75"),
            romanization="is",
            ipa_pronunciation=None,
            part_of_speech=PartOfSpeech.VERB,
            gender=None,
            plurality=None,
            grammatical_case=None,
            verb_aspect=None,
            animacy=None,
            language_register=Register.NEUTRAL,
            confirmed_at_id=None,
            etymology_document_id=None,
            cultural_significance_document_id=None,
            created_by_id=UUID("5029c5d0-c4f6-401e-9257-a8d1055b121a"),
            verified_by_id=None,
            is_verified=False,
            status=WordStatus.DRAFT,
            source=None,
            notes=None,
            created_at=datetime.fromisoformat("2025-11-09 18:21:06.224407"),
            updated_at=datetime.fromisoformat("2025-11-09 18:21:06.224410"),
        )
        db.add(word_9840df93)
        word_efe2c93b = Word(
            id=UUID("efe2c93b-6a75-40d5-8e45-13d9176542f2"),
            word="des",
            language_id=UUID("051e55a2-91d3-4303-b0bf-a23b733ced75"),
            romanization=None,
            ipa_pronunciation=None,
            part_of_speech=None,
            gender=None,
            plurality=None,
            grammatical_case=None,
            verb_aspect=None,
            animacy=None,
            language_register=Register.NEUTRAL,
            confirmed_at_id=None,
            etymology_document_id=None,
            cultural_significance_document_id=None,
            created_by_id=UUID("5029c5d0-c4f6-401e-9257-a8d1055b121a"),
            verified_by_id=None,
            is_verified=False,
            status=WordStatus.DRAFT,
            source=None,
            notes=None,
            created_at=datetime.fromisoformat("2025-11-09 18:52:41.232685"),
            updated_at=datetime.fromisoformat("2025-11-09 18:52:41.232688"),
        )
        db.add(word_efe2c93b)
        word_adbc6a4e = Word(
            id=UUID("adbc6a4e-988a-4ab6-8859-329a888891b9"),
            word="test",
            language_id=UUID("051e55a2-91d3-4303-b0bf-a23b733ced75"),
            romanization="test",
            ipa_pronunciation=None,
            part_of_speech=PartOfSpeech.NOUN,
            gender=GrammaticalGender.MASCULINE,
            plurality=Plurality.SINGULAR,
            grammatical_case=None,
            verb_aspect=None,
            animacy=Animacy.INANIMATE,
            language_register=Register.NEUTRAL,
            confirmed_at_id=None,
            etymology_document_id=None,
            cultural_significance_document_id=None,
            created_by_id=UUID("5029c5d0-c4f6-401e-9257-a8d1055b121a"),
            verified_by_id=None,
            is_verified=False,
            status=WordStatus.DRAFT,
            source=None,
            notes=None,
            created_at=datetime.fromisoformat("2025-11-09 23:00:19.611532"),
            updated_at=datetime.fromisoformat("2025-11-09 23:00:19.611535"),
        )
        db.add(word_adbc6a4e)
        word_2658e326 = Word(
            id=UUID("2658e326-8ab7-4480-95e6-ac5f91458d77"),
            word="gibd",
            language_id=UUID("051e55a2-91d3-4303-b0bf-a23b733ced75"),
            romanization="gibd",
            ipa_pronunciation=None,
            part_of_speech=PartOfSpeech.VERB,
            gender=GrammaticalGender.NOT_APPLICABLE,
            plurality=Plurality.SINGULAR,
            grammatical_case=None,
            verb_aspect=None,
            animacy=None,
            language_register=Register.NEUTRAL,
            confirmed_at_id=None,
            etymology_document_id=None,
            cultural_significance_document_id=None,
            created_by_id=UUID("5029c5d0-c4f6-401e-9257-a8d1055b121a"),
            verified_by_id=None,
            is_verified=False,
            status=WordStatus.DRAFT,
            source=None,
            notes=None,
            created_at=datetime.fromisoformat("2025-11-09 23:02:52.269868"),
            updated_at=datetime.fromisoformat("2025-11-09 23:02:52.269870"),
        )
        db.add(word_2658e326)
        word_206d545e = Word(
            id=UUID("206d545e-a82f-4e41-9198-2c0afb5ea446"),
            word="ned",
            language_id=UUID("051e55a2-91d3-4303-b0bf-a23b733ced75"),
            romanization=None,
            ipa_pronunciation=None,
            part_of_speech=PartOfSpeech.ADVERB,
            gender=GrammaticalGender.NOT_APPLICABLE,
            plurality=None,
            grammatical_case=None,
            verb_aspect=None,
            animacy=None,
            language_register=Register.NEUTRAL,
            confirmed_at_id=None,
            etymology_document_id=None,
            cultural_significance_document_id=None,
            created_by_id=UUID("5029c5d0-c4f6-401e-9257-a8d1055b121a"),
            verified_by_id=None,
            is_verified=False,
            status=WordStatus.DRAFT,
            source=None,
            notes=None,
            created_at=datetime.fromisoformat("2025-11-09 23:04:28.590967"),
            updated_at=datetime.fromisoformat("2025-11-09 23:04:28.590971"),
        )
        db.add(word_206d545e)
        word_f5e98ccc = Word(
            id=UUID("f5e98ccc-8464-4282-b128-0f93652da13b"),
            word="meara",
            language_id=UUID("051e55a2-91d3-4303-b0bf-a23b733ced75"),
            romanization=None,
            ipa_pronunciation=None,
            part_of_speech=PartOfSpeech.ADJECTIVE,
            gender=GrammaticalGender.NOT_APPLICABLE,
            plurality=Plurality.NOT_APPLICABLE,
            grammatical_case=None,
            verb_aspect=None,
            animacy=None,
            language_register=Register.NEUTRAL,
            confirmed_at_id=None,
            etymology_document_id=None,
            cultural_significance_document_id=None,
            created_by_id=UUID("5029c5d0-c4f6-401e-9257-a8d1055b121a"),
            verified_by_id=None,
            is_verified=False,
            status=WordStatus.DRAFT,
            source=None,
            notes=None,
            created_at=datetime.fromisoformat("2025-11-09 23:06:21.584821"),
            updated_at=datetime.fromisoformat("2025-11-09 23:06:21.584824"),
        )
        db.add(word_f5e98ccc)
        print(f"  Inserted 8 word(s)")

        # Commit words before word_translations and text_word_links reference them
        db.commit()

        # Insert user_languages
        db.execute(
            text(
                """
            INSERT INTO user_languages (user_id, language_id, proficiency_level, can_edit, can_verify, created_at)
            VALUES ('5029c5d0-c4f6-401e-9257-a8d1055b121a'::uuid, '051e55a2-91d3-4303-b0bf-a23b733ced75'::uuid, 'NATIVE', FALSE, FALSE, '2025-11-04 21:14:43.665991'::timestamp)
        """
            )
        )
        db.execute(
            text(
                """
            INSERT INTO user_languages (user_id, language_id, proficiency_level, can_edit, can_verify, created_at)
            VALUES ('5029c5d0-c4f6-401e-9257-a8d1055b121a'::uuid, '54266e9b-19de-4b17-9e9d-15595ce4e7af'::uuid, 'FLUENT', FALSE, FALSE, '2025-11-04 21:43:38.327148'::timestamp)
        """
            )
        )
        print(f"  Inserted 2 user_language(s)")

        # Insert word_translations
        db.execute(
            text(
                """
            INSERT INTO word_translations (word_id, translation_id, notes, created_at, created_by_id)
            VALUES ('b8f1722f-aeb8-43bb-aaa7-517a15c87625'::uuid, '2b9469f8-50f8-434a-b28e-b7eff9c0d43b'::uuid, NULL, '2025-11-04 21:37:37.452690'::timestamp, NULL::uuid)
        """
            )
        )
        print(f"  Inserted 1 word_translation(s)")

        # Insert text_word_links
        db.execute(
            text(
                """
            INSERT INTO text_word_links (id, text_id, word_id, start_char, end_char, status, confidence, notes, created_by_id, verified_by_id, created_at, updated_at, verified_at)
            VALUES ('9bde105e-f6c2-4520-b57d-2994e8bf5ba4'::uuid, 'd5edacf8-94fb-4739-9ff6-657139b1d8e1'::uuid, '9840df93-59e9-4274-9724-320e8680c9d5'::uuid, 4, 6, 'CONFIRMED', NULL, NULL, '5029c5d0-c4f6-401e-9257-a8d1055b121a'::uuid, '5029c5d0-c4f6-401e-9257-a8d1055b121a'::uuid, '2025-11-09 18:48:03.745113'::timestamp, '2025-11-09 18:48:19.555873'::timestamp, '2025-11-09 18:48:19.554686'::timestamp)
        """
            )
        )
        db.execute(
            text(
                """
            INSERT INTO text_word_links (id, text_id, word_id, start_char, end_char, status, confidence, notes, created_by_id, verified_by_id, created_at, updated_at, verified_at)
            VALUES ('dcc6e5ee-27da-4e7f-87e0-f8dedd0156cf'::uuid, 'd5edacf8-94fb-4739-9ff6-657139b1d8e1'::uuid, 'efe2c93b-6a75-40d5-8e45-13d9176542f2'::uuid, 0, 3, 'CONFIRMED', NULL, NULL, '5029c5d0-c4f6-401e-9257-a8d1055b121a'::uuid, '5029c5d0-c4f6-401e-9257-a8d1055b121a'::uuid, '2025-11-09 18:52:41.262537'::timestamp, '2025-11-09 18:52:41.262538'::timestamp, '2025-11-09 18:52:41.262282'::timestamp)
        """
            )
        )
        db.execute(
            text(
                """
            INSERT INTO text_word_links (id, text_id, word_id, start_char, end_char, status, confidence, notes, created_by_id, verified_by_id, created_at, updated_at, verified_at)
            VALUES ('c0a1b99f-31aa-4c51-b3a5-79dfdd29117c'::uuid, 'd5edacf8-94fb-4739-9ff6-657139b1d8e1'::uuid, 'adbc6a4e-988a-4ab6-8859-329a888891b9'::uuid, 9, 13, 'CONFIRMED', NULL, NULL, '5029c5d0-c4f6-401e-9257-a8d1055b121a'::uuid, '5029c5d0-c4f6-401e-9257-a8d1055b121a'::uuid, '2025-11-09 23:00:19.641187'::timestamp, '2025-11-09 23:00:19.641188'::timestamp, '2025-11-09 23:00:19.640575'::timestamp)
        """
            )
        )
        db.execute(
            text(
                """
            INSERT INTO text_word_links (id, text_id, word_id, start_char, end_char, status, confidence, notes, created_by_id, verified_by_id, created_at, updated_at, verified_at)
            VALUES ('a2c60687-6d4f-4f1b-aa4c-eccf57a91f2f'::uuid, 'd5edacf8-94fb-4739-9ff6-657139b1d8e1'::uuid, '2658e326-8ab7-4480-95e6-ac5f91458d77'::uuid, 30, 34, 'CONFIRMED', NULL, NULL, '5029c5d0-c4f6-401e-9257-a8d1055b121a'::uuid, '5029c5d0-c4f6-401e-9257-a8d1055b121a'::uuid, '2025-11-09 23:02:52.295535'::timestamp, '2025-11-09 23:03:49.545029'::timestamp, '2025-11-09 23:03:49.544100'::timestamp)
        """
            )
        )
        db.execute(
            text(
                """
            INSERT INTO text_word_links (id, text_id, word_id, start_char, end_char, status, confidence, notes, created_by_id, verified_by_id, created_at, updated_at, verified_at)
            VALUES ('f9366deb-731d-4d57-a206-18155b8ca8ce'::uuid, 'd5edacf8-94fb-4739-9ff6-657139b1d8e1'::uuid, '206d545e-a82f-4e41-9198-2c0afb5ea446'::uuid, 37, 40, 'CONFIRMED', NULL, NULL, '5029c5d0-c4f6-401e-9257-a8d1055b121a'::uuid, '5029c5d0-c4f6-401e-9257-a8d1055b121a'::uuid, '2025-11-09 23:04:28.618069'::timestamp, '2025-11-09 23:04:28.618071'::timestamp, '2025-11-09 23:04:28.617819'::timestamp)
        """
            )
        )
        db.execute(
            text(
                """
            INSERT INTO text_word_links (id, text_id, word_id, start_char, end_char, status, confidence, notes, created_by_id, verified_by_id, created_at, updated_at, verified_at)
            VALUES ('4357d081-2d7c-4446-92f1-5dcdbcae69d1'::uuid, 'd5edacf8-94fb-4739-9ff6-657139b1d8e1'::uuid, 'f5e98ccc-8464-4282-b128-0f93652da13b'::uuid, 24, 29, 'CONFIRMED', NULL, NULL, '5029c5d0-c4f6-401e-9257-a8d1055b121a'::uuid, '5029c5d0-c4f6-401e-9257-a8d1055b121a'::uuid, '2025-11-09 23:06:21.610925'::timestamp, '2025-11-09 23:06:21.610927'::timestamp, '2025-11-09 23:06:21.610719'::timestamp)
        """
            )
        )
        print(f"  Inserted 6 text_word_link(s)")

        db.commit()
        print("Database seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
