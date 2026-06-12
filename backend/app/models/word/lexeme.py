"""
Lexeme — the abstract dictionary entry.

A Lexeme is the concept/headword level: one entry per (language, sense). It
holds the things that are constant across all inflected forms — part of
speech, gender, definitions, etymology, cultural significance, synonyms,
antonyms, translations, tags.

The surface strings, IPA, inflection features, audio recordings, and
attested locations live on the related `WordForm` rows.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.word.associations import (
    lexeme_antonyms,
    lexeme_definitions,
    lexeme_images,
    lexeme_related,
    lexeme_synonyms,
    lexeme_tags,
    lexeme_texts,
    lexeme_translations,
)
from app.models.word.enums import (
    Animacy,
    GrammaticalGender,
    LexemeStatus,
    PartOfSpeech,
    Register,
)


def _now() -> datetime:
    return datetime.now(UTC)


class Lexeme(Base):
    __tablename__ = "lexemes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    language_id = Column(
        UUID(as_uuid=True),
        ForeignKey("languages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Denormalized citation form for search/display. The canonical WordForm
    # (the one with `is_lemma=True`) holds the authoritative string; this
    # mirrors it for cheap lookups and is kept in sync by the service layer.
    lemma = Column(String(255), nullable=False, index=True)

    # Concept-level grammatical category.
    # These enums were created by the initial schema (0824d074…) with UPPERCASE
    # Postgres labels matching the Python enum NAMES — so default SQLAlchemy
    # storage (.name → uppercase) is what Postgres expects. Do NOT add
    # values_callable here; lowercase .value would not match the PG labels.
    part_of_speech = Column(SQLEnum(PartOfSpeech, name="partofspeech"), nullable=True, index=True)
    gender = Column(SQLEnum(GrammaticalGender, name="grammaticalgender"), nullable=True)
    animacy = Column(SQLEnum(Animacy, name="animacy"), nullable=True)
    language_register = Column(
        SQLEnum(Register, name="register"), nullable=True, default=Register.NEUTRAL
    )

    # Concept-level documents (one each)
    etymology_document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    cultural_significance_document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )

    # Provenance
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    verified_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False, index=True)
    status = Column(
        SQLEnum(LexemeStatus, name="lexemestatus", values_callable=lambda e: [m.value for m in e]),
        default=LexemeStatus.DRAFT,
        nullable=False,
        index=True,
    )
    source = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    # Relationships
    language = relationship("Language", back_populates="lexemes")
    created_by = relationship(
        "User", foreign_keys=[created_by_id], back_populates="lexemes_created"
    )
    verified_by = relationship(
        "User", foreign_keys=[verified_by_id], back_populates="lexemes_verified"
    )

    forms = relationship(
        "WordForm",
        back_populates="lexeme",
        cascade="all, delete-orphan",
        order_by="WordForm.is_lemma.desc()",
    )

    tags = relationship("Tag", secondary=lexeme_tags, back_populates="lexemes")
    images = relationship("Image", secondary=lexeme_images, backref="lexemes")

    definitions = relationship(
        "Document", secondary=lexeme_definitions, backref="lexemes_with_definition"
    )
    etymology = relationship(
        "Document",
        foreign_keys=[etymology_document_id],
        backref="lexemes_with_etymology",
    )
    cultural_significance = relationship(
        "Document",
        foreign_keys=[cultural_significance_document_id],
        backref="lexemes_with_cultural_significance",
    )

    texts = relationship(
        "Text", secondary=lexeme_texts, back_populates="linked_lexemes", viewonly=True
    )

    # Symmetric self-referential M2Ms. Stored canonically (lexeme_id < other_id)
    # so we have to UNION both sides at read time to look undirected. The
    # service layer wraps this.
    synonyms_as_lower = relationship(
        "Lexeme",
        secondary=lexeme_synonyms,
        primaryjoin=id == lexeme_synonyms.c.lexeme_id,
        secondaryjoin=id == lexeme_synonyms.c.synonym_id,
        viewonly=True,
    )
    synonyms_as_upper = relationship(
        "Lexeme",
        secondary=lexeme_synonyms,
        primaryjoin=id == lexeme_synonyms.c.synonym_id,
        secondaryjoin=id == lexeme_synonyms.c.lexeme_id,
        viewonly=True,
    )

    antonyms_as_lower = relationship(
        "Lexeme",
        secondary=lexeme_antonyms,
        primaryjoin=id == lexeme_antonyms.c.lexeme_id,
        secondaryjoin=id == lexeme_antonyms.c.antonym_id,
        viewonly=True,
    )
    antonyms_as_upper = relationship(
        "Lexeme",
        secondary=lexeme_antonyms,
        primaryjoin=id == lexeme_antonyms.c.antonym_id,
        secondaryjoin=id == lexeme_antonyms.c.lexeme_id,
        viewonly=True,
    )

    translations_as_lower = relationship(
        "Lexeme",
        secondary=lexeme_translations,
        primaryjoin=id == lexeme_translations.c.lexeme_id,
        secondaryjoin=id == lexeme_translations.c.translation_id,
        viewonly=True,
    )
    translations_as_upper = relationship(
        "Lexeme",
        secondary=lexeme_translations,
        primaryjoin=id == lexeme_translations.c.translation_id,
        secondaryjoin=id == lexeme_translations.c.lexeme_id,
        viewonly=True,
    )

    # `lexeme_related` is directional; we keep the relationship single-sided.
    related_lexemes = relationship(
        "Lexeme",
        secondary=lexeme_related,
        primaryjoin=id == lexeme_related.c.lexeme_id,
        secondaryjoin=id == lexeme_related.c.related_lexeme_id,
        backref="related_to",
    )

    @property
    def synonyms(self) -> list["Lexeme"]:
        return [*self.synonyms_as_lower, *self.synonyms_as_upper]

    @property
    def antonyms(self) -> list["Lexeme"]:
        return [*self.antonyms_as_lower, *self.antonyms_as_upper]

    @property
    def translations(self) -> list["Lexeme"]:
        return [*self.translations_as_lower, *self.translations_as_upper]

    def __repr__(self) -> str:
        return f"<Lexeme(id={self.id}, lemma='{self.lemma}', language_id={self.language_id})>"
