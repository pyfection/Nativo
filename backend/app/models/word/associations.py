"""
Association tables for Lexeme and WordForm relationships.

Conventions:
- Lexeme-level associations attach to concept (definitions, synonyms,
  antonyms, related, translations, tags, images, texts).
- WordForm-level associations attach to surface form (audio recordings,
  attested locations).
- Symmetric self-referential M2Ms (synonyms, antonyms, related, translations)
  store rows canonically with `lexeme_id < other_id` and a CHECK constraint
  enforces that. Callers must swap the IDs at write time; readers see one
  undirected row, not two.
"""

import enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models.word.enums import AntonymType, SynonymNuance


class WordTextType(str, enum.Enum):
    """Types of Lexeme-Text relationships (language-specific commentary)."""

    LITERAL_TRANSLATION = "literal_translation"
    CONTEXT_NOTE = "context_note"
    USAGE_EXAMPLE = "usage_example"
    OTHER = "other"


# ---------------------------------------------------------------------------
# WordForm-level associations (one surface form)
# ---------------------------------------------------------------------------


word_form_audio = Table(
    "word_form_audio",
    Base.metadata,
    Column(
        "word_form_id",
        UUID(as_uuid=True),
        ForeignKey("word_forms.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "audio_id", UUID(as_uuid=True), ForeignKey("audio.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("is_primary", Boolean, default=False, nullable=False),
    Column("created_at", DateTime, nullable=False),
)


word_form_locations = Table(
    "word_form_locations",
    Base.metadata,
    Column(
        "word_form_id",
        UUID(as_uuid=True),
        ForeignKey("word_forms.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "location_id",
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("notes", String(500), nullable=True),
    Column("created_at", DateTime, nullable=False),
)


# ---------------------------------------------------------------------------
# Lexeme-level associations (concept)
# ---------------------------------------------------------------------------


lexeme_images = Table(
    "lexeme_images",
    Base.metadata,
    Column(
        "lexeme_id",
        UUID(as_uuid=True),
        ForeignKey("lexemes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "image_id",
        UUID(as_uuid=True),
        ForeignKey("images.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("is_primary", Boolean, default=False, nullable=False),
    Column("created_at", DateTime, nullable=False),
)


lexeme_tags = Table(
    "lexeme_tags",
    Base.metadata,
    Column(
        "lexeme_id",
        UUID(as_uuid=True),
        ForeignKey("lexemes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("created_at", DateTime, nullable=False),
)


lexeme_definitions = Table(
    "lexeme_definitions",
    Base.metadata,
    Column(
        "lexeme_id",
        UUID(as_uuid=True),
        ForeignKey("lexemes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "document_id",
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", DateTime, nullable=False),
)


lexeme_texts = Table(
    "lexeme_texts",
    Base.metadata,
    Column(
        "lexeme_id",
        UUID(as_uuid=True),
        ForeignKey("lexemes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "text_id", UUID(as_uuid=True), ForeignKey("texts.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "relationship_type",
        SQLEnum(WordTextType, name="wordtexttype", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        primary_key=True,
    ),
    Column("created_at", DateTime, nullable=False),
)


# ---------------------------------------------------------------------------
# Symmetric self-referential M2Ms (Lexeme ↔ Lexeme)
#
# `lexeme_id < other_id` is enforced by a CHECK constraint so each pair is
# stored exactly once. The lexeme service is responsible for swapping the IDs
# before INSERT.
# ---------------------------------------------------------------------------


lexeme_synonyms = Table(
    "lexeme_synonyms",
    Base.metadata,
    Column(
        "lexeme_id",
        UUID(as_uuid=True),
        ForeignKey("lexemes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "synonym_id",
        UUID(as_uuid=True),
        ForeignKey("lexemes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "nuance",
        SQLEnum(
            SynonymNuance, name="synonymnuance", values_callable=lambda e: [m.value for m in e]
        ),
        nullable=True,
    ),
    Column("notes", String(500), nullable=True),
    Column("created_at", DateTime, nullable=False),
    CheckConstraint("lexeme_id < synonym_id", name="ck_lexeme_synonyms_ordered"),
)


lexeme_antonyms = Table(
    "lexeme_antonyms",
    Base.metadata,
    Column(
        "lexeme_id",
        UUID(as_uuid=True),
        ForeignKey("lexemes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "antonym_id",
        UUID(as_uuid=True),
        ForeignKey("lexemes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "antonym_type",
        SQLEnum(AntonymType, name="antonymtype", values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    ),
    Column("notes", String(500), nullable=True),
    Column("created_at", DateTime, nullable=False),
    CheckConstraint("lexeme_id < antonym_id", name="ck_lexeme_antonyms_ordered"),
)


lexeme_related = Table(
    "lexeme_related",
    Base.metadata,
    Column(
        "lexeme_id",
        UUID(as_uuid=True),
        ForeignKey("lexemes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "related_lexeme_id",
        UUID(as_uuid=True),
        ForeignKey("lexemes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    # Directional relationships (derived_from, compound_part_of) are allowed
    # here; the type column carries the direction so we don't need to
    # canonicalize.
    Column("relationship_type", String(100), nullable=True),
    Column("created_at", DateTime, nullable=False),
)


lexeme_translations = Table(
    "lexeme_translations",
    Base.metadata,
    Column(
        "lexeme_id",
        UUID(as_uuid=True),
        ForeignKey("lexemes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "translation_id",
        UUID(as_uuid=True),
        ForeignKey("lexemes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("notes", Text, nullable=True),
    Column("created_at", DateTime, nullable=False),
    Column(
        "created_by_id",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    ),
    CheckConstraint("lexeme_id < translation_id", name="ck_lexeme_translations_ordered"),
)
