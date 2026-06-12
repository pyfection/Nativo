"""Refactor Word into Lexeme + WordForm

Revision ID: e9f1a2b3c4d5
Revises: c19788ebabb8
Create Date: 2026-06-12 00:00:00.000000

This migration is intentionally destructive: it drops the existing `words`
table and all word-related association tables (word_audio, word_image,
word_texts, word_definitions, word_synonyms, word_antonyms, word_related,
word_translations, word_tags) and recreates the lexicographic layer as:

- `lexemes`   : concept-level dictionary entries (one per language sense)
- `word_forms`: surface forms of a lexeme (with rhyme_key, inflection, etc.)
- `lexeme_*`  : concept-level associations (synonyms, antonyms, related,
                translations, tags, images, definitions, texts) — symmetric
                ones canonicalised with `lexeme_id < other_id` CHECK
                constraints + nuance / antonym_type metadata.
- `word_form_audio`, `word_form_locations`: form-level associations.

`text_word_links.word_id` is renamed to `word_form_id` and re-pointed at
`word_forms`. Existing rows are dropped — link suggestions are
auto-regenerated from text content.

Rationale for the destructive approach: the project has minimal lexical
data in production, and a clean cut is far simpler to reason about than
threading a multi-step data migration through a model split.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e9f1a2b3c4d5"
down_revision: Union[str, None] = "c19788ebabb8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Postgres ENUM types reused by the new tables. We assume the old enum types
# (partofspeech, grammaticalgender, etc.) already exist from the original
# schema. We DROP and RECREATE them so the type name carries the current
# value set — old/new value sets are identical for the existing enums, but
# `lexemestatus` is a rename of `wordstatus`.
_OLD_ENUMS = [
    "wordstatus",
    "wordtexttype",
]
_NEW_ENUMS = [
    "lexemestatus",
    "synonymnuance",
    "antonymtype",
]


def upgrade() -> None:
    # ---- 1. Drop everything that references words / word_* tables ----
    op.drop_table("text_word_links")
    op.drop_table("word_translations")
    op.drop_table("word_synonyms")
    op.drop_table("word_antonyms")
    op.drop_table("word_related")
    op.drop_table("word_definitions")
    op.drop_table("word_texts")
    op.drop_table("word_audio")
    op.drop_table("word_image")
    op.drop_table("word_tags")
    op.drop_table("words")

    # Drop renamed/retired enum types
    for enum_name in _OLD_ENUMS:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")

    # ---- 2. Create new enum types ----
    lexeme_status = postgresql.ENUM(
        "draft",
        "pending_review",
        "published",
        "deprecated",
        "archived",
        name="lexemestatus",
    )
    lexeme_status.create(op.get_bind(), checkfirst=True)

    word_text_type = postgresql.ENUM(
        "literal_translation",
        "context_note",
        "usage_example",
        "other",
        name="wordtexttype",
    )
    word_text_type.create(op.get_bind(), checkfirst=True)

    synonym_nuance = postgresql.ENUM(
        "exact",
        "near",
        "register_variant",
        "regional_variant",
        "hypernym",
        "hyponym",
        "other",
        name="synonymnuance",
    )
    synonym_nuance.create(op.get_bind(), checkfirst=True)

    antonym_type = postgresql.ENUM(
        "gradable",
        "complementary",
        "converse",
        "directional",
        "other",
        name="antonymtype",
    )
    antonym_type.create(op.get_bind(), checkfirst=True)

    # ---- 3. lexemes ----
    op.create_table(
        "lexemes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "language_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("languages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("lemma", sa.String(length=255), nullable=False),
        sa.Column(
            "part_of_speech",
            postgresql.ENUM(name="partofspeech", create_type=False),
            nullable=True,
        ),
        sa.Column(
            "gender",
            postgresql.ENUM(name="grammaticalgender", create_type=False),
            nullable=True,
        ),
        sa.Column(
            "animacy",
            postgresql.ENUM(name="animacy", create_type=False),
            nullable=True,
        ),
        sa.Column(
            "language_register",
            postgresql.ENUM(name="register", create_type=False),
            nullable=True,
        ),
        sa.Column(
            "etymology_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "cultural_significance_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "verified_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "status",
            postgresql.ENUM(name="lexemestatus", create_type=False),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("source", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_lexemes_language_id", "lexemes", ["language_id"])
    op.create_index("ix_lexemes_lemma", "lexemes", ["lemma"])
    op.create_index("ix_lexemes_part_of_speech", "lexemes", ["part_of_speech"])
    op.create_index("ix_lexemes_status", "lexemes", ["status"])
    op.create_index("ix_lexemes_is_verified", "lexemes", ["is_verified"])

    # ---- 4. word_forms ----
    op.create_table(
        "word_forms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "lexeme_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lexemes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("form", sa.String(length=255), nullable=False),
        sa.Column("romanization", sa.String(length=255), nullable=True),
        sa.Column("ipa_pronunciation", sa.String(length=255), nullable=True),
        sa.Column("rhyme_key", sa.String(length=255), nullable=True),
        sa.Column("near_rhyme_key", sa.String(length=255), nullable=True),
        sa.Column("is_lemma", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "plurality",
            postgresql.ENUM(name="plurality", create_type=False),
            nullable=True,
        ),
        sa.Column(
            "grammatical_case",
            postgresql.ENUM(name="grammaticalcase", create_type=False),
            nullable=True,
        ),
        sa.Column(
            "verb_aspect",
            postgresql.ENUM(name="verbaspect", create_type=False),
            nullable=True,
        ),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_word_forms_lexeme_id", "word_forms", ["lexeme_id"])
    op.create_index("ix_word_forms_form", "word_forms", ["form"])
    op.create_index("ix_word_forms_romanization", "word_forms", ["romanization"])
    op.create_index("ix_word_forms_rhyme_key", "word_forms", ["rhyme_key"])
    op.create_index("ix_word_forms_near_rhyme_key", "word_forms", ["near_rhyme_key"])
    op.create_index("ix_word_forms_is_lemma", "word_forms", ["is_lemma"])

    # ---- 5. WordForm-level associations ----
    op.create_table(
        "word_form_audio",
        sa.Column(
            "word_form_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("word_forms.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "audio_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audio.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "word_form_locations",
        sa.Column(
            "word_form_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("word_forms.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "location_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ---- 6. Lexeme-level associations ----
    op.create_table(
        "lexeme_tags",
        sa.Column(
            "lexeme_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lexemes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tag_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tags.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "lexeme_images",
        sa.Column(
            "lexeme_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lexemes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "image_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("images.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "lexeme_definitions",
        sa.Column(
            "lexeme_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lexemes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "lexeme_texts",
        sa.Column(
            "lexeme_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lexemes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "text_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("texts.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "relationship_type",
            postgresql.ENUM(name="wordtexttype", create_type=False),
            nullable=False,
            primary_key=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "lexeme_synonyms",
        sa.Column(
            "lexeme_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lexemes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "synonym_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lexemes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "nuance",
            postgresql.ENUM(name="synonymnuance", create_type=False),
            nullable=True,
        ),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("lexeme_id < synonym_id", name="ck_lexeme_synonyms_ordered"),
    )

    op.create_table(
        "lexeme_antonyms",
        sa.Column(
            "lexeme_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lexemes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "antonym_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lexemes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "antonym_type",
            postgresql.ENUM(name="antonymtype", create_type=False),
            nullable=True,
        ),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("lexeme_id < antonym_id", name="ck_lexeme_antonyms_ordered"),
    )

    op.create_table(
        "lexeme_related",
        sa.Column(
            "lexeme_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lexemes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "related_lexeme_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lexemes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("relationship_type", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "lexeme_translations",
        sa.Column(
            "lexeme_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lexemes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "translation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lexemes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.CheckConstraint(
            "lexeme_id < translation_id", name="ck_lexeme_translations_ordered"
        ),
    )

    # ---- 7. text_word_links pointing at word_forms ----
    op.create_table(
        "text_word_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "text_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("texts.id"),
            nullable=False,
        ),
        sa.Column(
            "word_form_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("word_forms.id"),
            nullable=False,
        ),
        sa.Column("start_char", sa.Integer(), nullable=False),
        sa.Column("end_char", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(name="textwordlinkstatus", create_type=False),
            nullable=False,
            server_default="suggested",
        ),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column(
            "verified_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint(
            "text_id", "start_char", "end_char", name="uq_text_word_links_unique_span"
        ),
    )
    op.create_index("ix_text_word_links_text_id", "text_word_links", ["text_id"])
    op.create_index(
        "ix_text_word_links_word_form_id", "text_word_links", ["word_form_id"]
    )


def downgrade() -> None:
    # The pre-refactor schema doesn't round-trip cleanly. Downgrade is a
    # best-effort drop of the new shape; restoring the old shape requires
    # reverting through the prior migrations and re-creating from scratch.
    op.drop_table("text_word_links")
    op.drop_table("lexeme_translations")
    op.drop_table("lexeme_related")
    op.drop_table("lexeme_antonyms")
    op.drop_table("lexeme_synonyms")
    op.drop_table("lexeme_texts")
    op.drop_table("lexeme_definitions")
    op.drop_table("lexeme_images")
    op.drop_table("lexeme_tags")
    op.drop_table("word_form_locations")
    op.drop_table("word_form_audio")
    op.drop_table("word_forms")
    op.drop_table("lexemes")

    for enum_name in _NEW_ENUMS:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
